"""Deterministic event replay from normalized raw history into booking and XP state."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from statistics import median
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.scoring_rules import (
    RAW_MILESTONE_SIGNALS,
    REQUIRED_DOCUMENT_ACTIONS,
    SCORING_RULES,
    CanonicalEvent,
)
from app.core.state_machine import (
    EVENT_STAGE,
    BookingStage,
    BookingStatus,
    max_reached,
    progress_percent,
)
from app.db.models import Booking, RawEvent, ScoringRuleOverride, XPLedger
from app.services.notification_service import leaderboard_broadcaster


@dataclass(slots=True)
class MilestoneHit:
    canonical_event: CanonicalEvent
    stage: BookingStage
    source_event_id: int
    user_id: str
    department: str
    achieved_at: datetime


@dataclass(slots=True)
class Escalation:
    source_event_id: int
    family: str
    user_id: str
    department: str
    occurred_at: datetime


@dataclass(slots=True)
class BookingReplay:
    location_code: str
    enquiry_no: str
    first_event_at: datetime
    last_event_at: datetime
    raw_stage: str
    current_stage: BookingStage = BookingStage.ENQUIRY_OPEN
    status: BookingStatus = BookingStatus.ACTIVE
    total_events: int = 0
    milestones: set[CanonicalEvent] = field(default_factory=set)
    documents: set[str] = field(default_factory=set)
    escalation_count: int = 0
    open_escalations: dict[str, list[Escalation]] = field(
        default_factory=lambda: defaultdict(list)
    )
    has_cancellation_request: bool = False
    has_cancellation_approval: bool = False
    cancellation_request_user_id: str | None = None
    booking_created_at: datetime | None = None
    delivered_at: datetime | None = None
    sales_owner_user_id: str | None = None
    departments_touched: set[str] = field(default_factory=set)
    contributors: dict[str, str] = field(default_factory=dict)
    last_forward_milestone: MilestoneHit | None = None
    cross_dept_assists: int = 0


@dataclass(frozen=True, slots=True)
class ScoringSummary:
    events_processed: int
    bookings_processed: int
    awards_computed: int
    awards_inserted: int
    total_xp: int
    leaderboard_xp: int
    event_counts: dict[str, int]


class ScoringReplayEngine:
    """Stateful in-memory replay whose outputs are fully deterministic."""

    def __init__(self, rules: dict[CanonicalEvent, Any] | None = None) -> None:
        self.rules = rules or dict(SCORING_RULES)
        self.bookings: dict[tuple[str, str], BookingReplay] = {}
        self.ledger_rows: list[dict[str, Any]] = []
        self.events_processed = 0
        self.login_days: set[tuple[str, date]] = set()
        self.follow_up_counts: dict[tuple[str, str, date], int] = defaultdict(int)
        self.daily_leaderboard_xp: dict[tuple[str, date], int] = defaultdict(int)
        self.weekly_leaderboard_xp: dict[tuple[str, int, int], int] = defaultdict(int)
        self.daily_delivery_counts: dict[tuple[str, date], int] = defaultdict(int)
        self.branch_cycle_days: dict[str, list[float]] = defaultdict(list)
        self.event_counts: dict[str, int] = defaultdict(int)

    def process(self, event: RawEvent) -> None:
        self.events_processed += 1
        if event.action_code == "USER_LOGGED_IN":
            self._process_login(event)
        if event.enquiry_no is None or event.location_code is None:
            return

        key = (event.location_code, event.enquiry_no)
        booking = self.bookings.get(key)
        if booking is None:
            booking = BookingReplay(
                location_code=event.location_code,
                enquiry_no=event.enquiry_no,
                first_event_at=event.created_date,
                last_event_at=event.created_date,
                raw_stage=event.stage,
            )
            self.bookings[key] = booking

        booking.total_events += 1
        booking.last_event_at = event.created_date
        booking.raw_stage = event.stage
        booking.departments_touched.add(event.department)
        if event.department == "SALES" and booking.sales_owner_user_id is None:
            booking.sales_owner_user_id = event.user_id

        if booking.status == BookingStatus.WON:
            return
        if booking.status == BookingStatus.DORMANT and event.stage != "DORMANT":
            booking.status = BookingStatus.ACTIVE

        if event.action_code == "BOOKING_CANCELLATION_REQUEST_CREATED":
            booking.has_cancellation_request = True
            booking.cancellation_request_user_id = event.user_id
        elif event.action_code == "BOOKING_CANCELLATION_REQUEST_APPROVED":
            booking.has_cancellation_approval = True

        event_is_frozen = event.stage in {"DORMANT", "CANCELLED"}
        if booking.status != BookingStatus.LOST and not event_is_frozen:
            self._track_escalation_or_resolution(booking, event)
            self._process_follow_up(booking, event)
            self._process_documents(booking, event)
            canonical = RAW_MILESTONE_SIGNALS.get(event.action_code)
            if canonical is not None:
                self._award_milestone(booking, event, canonical)
            if event.stage == "DELIVERED" and booking.delivered_at is None:
                self._process_delivery(booking, event)

        if event.stage == "CANCELLED" and booking.status != BookingStatus.WON:
            booking.status = BookingStatus.LOST
        elif event.stage == "DORMANT" and booking.status == BookingStatus.ACTIVE:
            booking.status = BookingStatus.DORMANT

    def _process_login(self, event: RawEvent) -> None:
        key = (event.user_id, event.created_date.date())
        if key in self.login_days:
            return
        self.login_days.add(key)
        self._add_award(
            dedupe_key=f"login:{event.user_id}:{event.created_date.date().isoformat()}",
            user_id=event.user_id,
            actor_user_id=event.user_id,
            partner_user_id=None,
            source_event_id=event.id,
            canonical_event=CanonicalEvent.DAILY_LOGIN_STREAK,
            department=event.department,
            location_code=None,
            enquiry_no=None,
            points=self.rules[CanonicalEvent.DAILY_LOGIN_STREAK].base_xp,
            earned_at=event.created_date,
            reason="First login of the calendar day",
        )

    def _process_follow_up(self, booking: BookingReplay, event: RawEvent) -> None:
        if event.action_code != "BOOKING_NOTE_ADDED" or event.department != "SALES":
            return
        key = (booking.location_code, booking.enquiry_no, event.created_date.date())
        if self.follow_up_counts[key] >= 3:
            return
        self.follow_up_counts[key] += 1
        self._add_award(
            dedupe_key=f"followup:{event.id}", user_id=event.user_id,
            actor_user_id=event.user_id, partner_user_id=None,
            source_event_id=event.id, canonical_event=CanonicalEvent.FOLLOW_UP_LOGGED,
            department=event.department, location_code=booking.location_code,
            enquiry_no=booking.enquiry_no,
            points=self.rules[CanonicalEvent.FOLLOW_UP_LOGGED].base_xp,
            earned_at=event.created_date,
            reason="Guarded booking follow-up within the three-per-day cap",
        )

    def _process_documents(self, booking: BookingReplay, event: RawEvent) -> None:
        if event.action_code not in REQUIRED_DOCUMENT_ACTIONS:
            return
        booking.documents.add(event.action_code)
        booking.current_stage = max_reached(
            booking.current_stage, BookingStage.DOCUMENTS_IN_PROGRESS
        )
        if REQUIRED_DOCUMENT_ACTIONS.issubset(booking.documents):
            self._award_milestone(
                booking, event, CanonicalEvent.DOCUMENT_SET_COMPLETED
            )

    def _award_milestone(
        self,
        booking: BookingReplay,
        event: RawEvent,
        canonical: CanonicalEvent,
        *,
        beneficiary_user_id: str | None = None,
        beneficiary_department: str | None = None,
    ) -> None:
        if canonical in booking.milestones:
            return
        stage = EVENT_STAGE[canonical]
        user_id = beneficiary_user_id or event.user_id
        department = beneficiary_department or event.department
        rule = self.rules[canonical]
        discounted = booking.escalation_count >= 2
        points = rule.base_xp
        if discounted:
            points = points * (100 - settings.rework_discount_percent) // 100

        prior_stage = booking.current_stage
        booking.milestones.add(canonical)
        booking.current_stage = max_reached(booking.current_stage, stage)
        booking.contributors.setdefault(department, user_id)
        if canonical == CanonicalEvent.BOOKING_CREATED:
            booking.booking_created_at = event.created_date
            if event.department == "SALES":
                booking.sales_owner_user_id = event.user_id

        self._add_award(
            dedupe_key=f"milestone:{booking.location_code}:{booking.enquiry_no}:{canonical.value}",
            user_id=user_id, actor_user_id=event.user_id, partner_user_id=None,
            source_event_id=event.id, canonical_event=canonical,
            department=department, location_code=booking.location_code,
            enquiry_no=booking.enquiry_no, points=points,
            base_points=rule.base_xp, earned_at=event.created_date,
            reason="First valid milestone occurrence for this booking",
            rework_discounted=discounted,
        )

        hit = MilestoneHit(
            canonical_event=canonical, stage=stage, source_event_id=event.id,
            user_id=user_id, department=department, achieved_at=event.created_date,
        )
        if stage > prior_stage:
            self._maybe_award_cross_department_assist(
                booking, booking.last_forward_milestone, hit
            )
            booking.last_forward_milestone = hit

    def _maybe_award_cross_department_assist(
        self,
        booking: BookingReplay,
        previous: MilestoneHit | None,
        current: MilestoneHit,
    ) -> None:
        if previous is None or booking.cross_dept_assists >= settings.max_cross_dept_assists_per_booking:
            return
        if previous.source_event_id == current.source_event_id:
            return
        if previous.user_id == current.user_id or previous.department == current.department:
            return
        if not self._within_business_hours(previous.achieved_at, current.achieved_at):
            return
        booking.cross_dept_assists += 1
        rule = self.rules[CanonicalEvent.CROSS_DEPT_ASSIST]
        handoff = f"{previous.canonical_event.value}>{current.canonical_event.value}"
        for side, hit, partner in (
            ("from", previous, current), ("to", current, previous)
        ):
            self._add_award(
                dedupe_key=f"assist:{booking.location_code}:{booking.enquiry_no}:{handoff}:{side}",
                user_id=hit.user_id, actor_user_id=current.user_id,
                partner_user_id=partner.user_id, source_event_id=current.source_event_id,
                canonical_event=CanonicalEvent.CROSS_DEPT_ASSIST,
                department=hit.department, location_code=booking.location_code,
                enquiry_no=booking.enquiry_no, points=rule.base_xp,
                earned_at=current.achieved_at,
                reason=f"Cross-department handoff completed within {settings.cross_dept_assist_business_hours} business hours",
                metadata={"handoff": handoff, "side": side},
            )

    def _track_escalation_or_resolution(
        self, booking: BookingReplay, event: RawEvent
    ) -> None:
        if event.action_code.endswith("_ESCALATED"):
            family = event.action_code.removesuffix("_ESCALATED")
            booking.escalation_count += 1
            booking.open_escalations[family].append(
                Escalation(event.id, family, event.user_id, event.department, event.created_date)
            )
            return
        if "APPROVED" not in event.action_code and "COMPLETED" not in event.action_code:
            return
        for family, escalations in booking.open_escalations.items():
            if not escalations or not event.action_code.startswith(family):
                continue
            escalation = escalations.pop()
            elapsed = event.created_date - escalation.occurred_at
            if not timedelta(0) <= elapsed <= timedelta(hours=settings.escalation_resolution_hours):
                continue
            if escalation.user_id == event.user_id or escalation.department == event.department:
                continue
            self._add_award(
                dedupe_key=f"escalation:{escalation.source_event_id}",
                user_id=event.user_id, actor_user_id=event.user_id,
                partner_user_id=escalation.user_id, source_event_id=event.id,
                canonical_event=CanonicalEvent.ESCALATION_RESOLVED,
                department=event.department, location_code=booking.location_code,
                enquiry_no=booking.enquiry_no,
                points=self.rules[CanonicalEvent.ESCALATION_RESOLVED].base_xp,
                earned_at=event.created_date,
                reason=f"{family} escalation resolved within {settings.escalation_resolution_hours} hours",
                metadata={"escalation_event_id": escalation.source_event_id, "family": family},
            )
            break

    def _process_delivery(self, booking: BookingReplay, event: RawEvent) -> None:
        sales_user = booking.sales_owner_user_id or event.user_id
        sales_department = "SALES" if booking.sales_owner_user_id else event.department
        self._award_milestone(
            booking, event, CanonicalEvent.VEHICLE_DELIVERED,
            beneficiary_user_id=sales_user,
            beneficiary_department=sales_department,
        )
        booking.delivered_at = event.created_date
        booking.status = BookingStatus.WON

        if booking.has_cancellation_request and not booking.has_cancellation_approval:
            save_user = booking.cancellation_request_user_id or sales_user
            self._add_award(
                dedupe_key=f"cancellation-save:{booking.location_code}:{booking.enquiry_no}",
                user_id=save_user, actor_user_id=event.user_id, partner_user_id=None,
                source_event_id=event.id, canonical_event=CanonicalEvent.CANCELLATION_SAVE,
                department="SALES", location_code=booking.location_code,
                enquiry_no=booking.enquiry_no,
                points=self.rules[CanonicalEvent.CANCELLATION_SAVE].base_xp,
                earned_at=event.created_date,
                reason="Cancellation request avoided and vehicle delivered",
            )

        if not booking.has_cancellation_request and booking.escalation_count == 0:
            self._split_team_bonus(
                booking, event, CanonicalEvent.CLEAN_BOOKING_BONUS
            )

        if booking.booking_created_at is not None:
            cycle_days = (
                event.created_date - booking.booking_created_at
            ).total_seconds() / 86_400
            if 0 <= cycle_days <= settings.fast_delivery_max_days:
                history = self.branch_cycle_days[booking.location_code]
                benchmark = median(history) if history else None
                if benchmark is not None and cycle_days <= benchmark:
                    self._split_team_bonus(
                        booking, event, CanonicalEvent.FAST_DELIVERY_BONUS,
                        metadata={"cycle_days": cycle_days, "prior_branch_median_days": benchmark},
                    )
                history.append(cycle_days)

    def _split_team_bonus(
        self,
        booking: BookingReplay,
        event: RawEvent,
        canonical: CanonicalEvent,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        contributors = sorted(booking.contributors.items())
        if not contributors:
            contributors = [(event.department, event.user_id)]
        total = self.rules[canonical].base_xp
        quotient, remainder = divmod(total, len(contributors))
        for index, (department, user_id) in enumerate(contributors):
            share = quotient + (1 if index < remainder else 0)
            self._add_award(
                dedupe_key=f"bonus:{booking.location_code}:{booking.enquiry_no}:{canonical.value}:{department}",
                user_id=user_id, actor_user_id=event.user_id, partner_user_id=None,
                source_event_id=event.id, canonical_event=canonical,
                department=department, location_code=booking.location_code,
                enquiry_no=booking.enquiry_no, points=share, base_points=share,
                earned_at=event.created_date,
                reason=f"{canonical.value} team share",
                metadata={"pool_xp": total, "contributors": len(contributors), **(metadata or {})},
            )

    def _within_business_hours(self, start: datetime, end: datetime) -> bool:
        if end < start or end - start > timedelta(
            hours=settings.cross_dept_assist_business_hours * 18
        ):
            return False
        total = timedelta(0)
        current_date = start.date()
        while current_date <= end.date():
            if current_date.weekday() in settings.working_weekdays:
                window_start = datetime.combine(
                    current_date, time(settings.business_day_start_hour)
                )
                window_end = datetime.combine(
                    current_date, time(settings.business_day_end_hour)
                )
                total += max(
                    min(end, window_end) - max(start, window_start), timedelta(0)
                )
            current_date += timedelta(days=1)
        return total <= timedelta(hours=settings.cross_dept_assist_business_hours)

    def _add_award(
        self, *, dedupe_key: str, user_id: str, actor_user_id: str,
        partner_user_id: str | None, source_event_id: int,
        canonical_event: CanonicalEvent, department: str,
        location_code: str | None, enquiry_no: str | None, points: int,
        earned_at: datetime, reason: str, base_points: int | None = None,
        rework_discounted: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        daily_key = (user_id, earned_at.date())
        iso_year, iso_week, _ = earned_at.isocalendar()
        weekly_key = (user_id, iso_year, iso_week)
        leaderboard_points = points
        if canonical_event == CanonicalEvent.VEHICLE_DELIVERED:
            if self.daily_delivery_counts[daily_key] >= settings.daily_delivery_leaderboard_cap:
                leaderboard_points = 0
            self.daily_delivery_counts[daily_key] += 1
        leaderboard_points = min(
            leaderboard_points,
            max(settings.daily_leaderboard_xp_cap - self.daily_leaderboard_xp[daily_key], 0),
            max(settings.weekly_leaderboard_xp_cap - self.weekly_leaderboard_xp[weekly_key], 0),
        )
        self.daily_leaderboard_xp[daily_key] += leaderboard_points
        self.weekly_leaderboard_xp[weekly_key] += leaderboard_points
        self.event_counts[canonical_event.value] += 1
        self.ledger_rows.append({
            "dedupe_key": dedupe_key, "user_id": user_id,
            "actor_user_id": actor_user_id, "partner_user_id": partner_user_id,
            "source_event_id": source_event_id,
            "canonical_event": canonical_event.value, "department": department,
            "location_code": location_code, "enquiry_no": enquiry_no,
            "base_points": points if base_points is None else base_points,
            "awarded_points": points, "leaderboard_points": leaderboard_points,
            "rework_discounted": rework_discounted, "earned_at": earned_at,
            "reason": reason,
            "metadata_json": json.dumps(metadata or {}, sort_keys=True, separators=(",", ":")),
        })

    def booking_rows(self) -> list[dict[str, Any]]:
        return [{
            "location_code": item.location_code, "enquiry_no": item.enquiry_no,
            "current_stage": item.current_stage.name,
            "stage_order": int(item.current_stage),
            "progress_percent": progress_percent(item.current_stage),
            "status": item.status.value, "raw_stage": item.raw_stage,
            "first_event_at": item.first_event_at, "last_event_at": item.last_event_at,
            "booking_created_at": item.booking_created_at,
            "delivered_at": item.delivered_at,
            "sales_owner_user_id": item.sales_owner_user_id,
            "total_events": item.total_events,
            "milestone_count": len(item.milestones),
            "escalation_count": item.escalation_count,
            "has_cancellation_request": item.has_cancellation_request,
            "has_cancellation_approval": item.has_cancellation_approval,
            "departments_touched": json.dumps(sorted(item.departments_touched)),
        } for item in self.bookings.values()]


async def score_all_events(session: AsyncSession) -> ScoringSummary:
    """Replay the complete normalized history and append only unseen awards."""

    rules = dict(SCORING_RULES)
    for override in (await session.execute(select(ScoringRuleOverride))).scalars():
        event = CanonicalEvent(override.canonical_event)
        rules[event] = replace(rules[event], base_xp=override.base_xp)
    replay = ScoringReplayEngine(rules)
    statement = (
        select(RawEvent)
        .order_by(RawEvent.created_date, RawEvent.id)
        .execution_options(yield_per=settings.scoring_batch_size)
    )
    stream = await session.stream_scalars(statement)
    async for event in stream:
        replay.process(event)

    existing_keys = set((await session.execute(select(XPLedger.dedupe_key))).scalars())
    new_ledger_rows = [
        row for row in replay.ledger_rows if row["dedupe_key"] not in existing_keys
    ]
    booking_rows = replay.booking_rows()
    try:
        for offset in range(0, len(new_ledger_rows), settings.scoring_batch_size):
            await session.execute(
                sqlite_insert(XPLedger).on_conflict_do_nothing(
                    index_elements=["dedupe_key"]
                ),
                new_ledger_rows[offset : offset + settings.scoring_batch_size],
            )
        for offset in range(0, len(booking_rows), settings.scoring_batch_size):
            statement = sqlite_insert(Booking)
            excluded = statement.excluded
            await session.execute(
                statement.on_conflict_do_update(
                    index_elements=["location_code", "enquiry_no"],
                    set_={
                        column.name: getattr(excluded, column.name)
                        for column in Booking.__table__.columns
                        if column.name not in {"location_code", "enquiry_no"}
                    },
                ),
                booking_rows[offset : offset + settings.scoring_batch_size],
            )
        await session.commit()
        if leaderboard_broadcaster.subscriber_count:
            for row in new_ledger_rows:
                await leaderboard_broadcaster.publish("xp_gain", {"user_id": row["user_id"], "canonical_event": row["canonical_event"], "points": row["awarded_points"], "leaderboard_points": row["leaderboard_points"], "earned_at": row["earned_at"].isoformat()})
                if row["enquiry_no"]:
                    await leaderboard_broadcaster.publish("boss_progress", {"department": row["department"], "canonical_event": row["canonical_event"], "location_code": row["location_code"], "enquiry_no": row["enquiry_no"]})
    except Exception:
        await session.rollback()
        raise

    return ScoringSummary(
        events_processed=replay.events_processed,
        bookings_processed=len(replay.bookings),
        awards_computed=len(replay.ledger_rows),
        awards_inserted=len(new_ledger_rows),
        total_xp=sum(row["awarded_points"] for row in replay.ledger_rows),
        leaderboard_xp=sum(row["leaderboard_points"] for row in replay.ledger_rows),
        event_counts=dict(sorted(replay.event_counts.items())),
    )
