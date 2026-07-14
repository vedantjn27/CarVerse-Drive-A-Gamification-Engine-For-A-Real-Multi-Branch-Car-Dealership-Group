"""Deterministic materialization of levels, streaks, reputation, badges, and ranks."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.scoring_rules import CanonicalEvent, RuleType, SCORING_RULES
from app.db.models import (
    Badge, Booking, DepartmentStats, Employee, LevelTitle, Location,
    LocationStats, ProgressionBonus, UserBadge, UserStats, XPLedger,
)
from app.seed.seed_badges import BADGES, LEVEL_TITLES


@dataclass(frozen=True, slots=True)
class GamificationSummary:
    users: int
    users_with_xp: int
    badges_awarded: int
    departments: int
    locations: int


def xp_required_for_level(level: int) -> int:
    if level <= 1:
        return 0
    return math.floor(settings.level_xp_base * ((level - 1) ** settings.level_xp_exponent))


def level_for_xp(total_xp: int) -> int:
    level = 1
    while xp_required_for_level(level + 1) <= total_xp:
        level += 1
    return level


def _streaks(days: set[date], cutoff: date | None) -> tuple[int, int]:
    if not days:
        return 0, 0
    ordered = sorted(days)
    longest = run = 1
    for previous, current in zip(ordered, ordered[1:], strict=False):
        run = run + 1 if current == previous + timedelta(days=1) else 1
        longest = max(longest, run)
    current = run if cutoff is not None and ordered[-1] == cutoff else 0
    return current, longest


def _streak_achievement_dates(days: set[date]) -> dict[int, date]:
    achievements: dict[int, date] = {}
    run = 0
    previous: date | None = None
    for current in sorted(days):
        run = run + 1 if previous is not None and current == previous + timedelta(days=1) else 1
        for threshold in settings.streak_bonuses:
            if run == threshold and threshold not in achievements:
                achievements[threshold] = current
        previous = current
    return achievements


def _rank(values: dict[str, int], groups: dict[str, str | None] | None = None) -> dict[str, int]:
    result: dict[str, int] = {}
    buckets: dict[str | None, list[str]] = defaultdict(list)
    for key in values:
        buckets[groups.get(key) if groups else None].append(key)
    for keys in buckets.values():
        for position, key in enumerate(sorted(keys, key=lambda item: (-values[item], item)), start=1):
            result[key] = position
    return result


async def materialize_gamification(session: AsyncSession) -> GamificationSummary:
    weights = (
        settings.reputation_clean_weight
        + settings.reputation_recovery_weight
        + settings.reputation_quality_weight
    )
    if weights != 100:
        raise ValueError("Reputation weights must total 100")

    for model, rows, key in (
        (LevelTitle, LEVEL_TITLES, "code"),
        (Badge, BADGES, "code"),
    ):
        statement = sqlite_insert(model)
        excluded = statement.excluded
        await session.execute(
            statement.on_conflict_do_update(
                index_elements=[key],
                set_={column.name: getattr(excluded, column.name) for column in model.__table__.columns if column.name != key},
            ),
            list(rows),
        )

    employees = list((await session.execute(select(Employee))).scalars())
    ledger = list((await session.execute(select(XPLedger).order_by(XPLedger.earned_at, XPLedger.id))).scalars())
    bookings = list((await session.execute(select(Booking))).scalars())
    locations = list((await session.execute(select(Location))).scalars())
    cutoff = max((row.earned_at.date() for row in ledger), default=None)

    by_user: dict[str, list[XPLedger]] = defaultdict(list)
    for row in ledger:
        by_user[row.user_id].append(row)
    employee_department = {item.id: item.department for item in employees}
    employee_location = {item.id: item.loc_code for item in employees}
    real_events = {
        event.value for event, rule in SCORING_RULES.items()
        if rule.rule_type != RuleType.GUARDED_REPEATABLE
    }
    streak_cache: dict[str, tuple[int, int]] = {}
    bonus_rows: list[dict[str, Any]] = []
    bonus_points: dict[str, int] = defaultdict(int)
    for employee in employees:
        milestone_rows = [row for row in by_user[employee.id] if row.canonical_event in real_events]
        streak_days = {row.earned_at.date() for row in milestone_rows}
        streak_cache[employee.id] = _streaks(streak_days, cutoff)
        earned_on = _streak_achievement_dates(streak_days)
        first_on_day = {}
        for row in milestone_rows:
            first_on_day.setdefault(row.earned_at.date(), row.earned_at)
        for threshold, achieved_date in earned_on.items():
            points = settings.streak_bonuses[threshold]
            bonus_points[employee.id] += points
            bonus_rows.append({"user_id": employee.id, "bonus_code": f"STREAK_{threshold}", "points": points, "awarded_at": first_on_day[achieved_date], "reason": f"Reached a {threshold}-day real-milestone streak"})
    if bonus_rows:
        statement = sqlite_insert(ProgressionBonus)
        excluded = statement.excluded
        await session.execute(statement.on_conflict_do_update(index_elements=["user_id", "bonus_code"], set_={"points": excluded.points, "awarded_at": excluded.awarded_at, "reason": excluded.reason}), bonus_rows)
    persisted_bonus_points: dict[str, int] = defaultdict(int)
    for bonus in (await session.execute(select(ProgressionBonus))).scalars():
        persisted_bonus_points[bonus.user_id] += bonus.points
    xp_values = {item.id: sum(row.awarded_points for row in by_user[item.id]) + persisted_bonus_points[item.id] for item in employees}
    all_ranks = _rank(xp_values)
    department_ranks = _rank(xp_values, employee_department)
    location_ranks = _rank(xp_values, employee_location)

    title_rows = sorted(LEVEL_TITLES, key=lambda item: item["minimum_level"])
    user_rows: list[dict[str, Any]] = []
    event_dates: dict[str, dict[str, list[datetime]]] = defaultdict(lambda: defaultdict(list))
    user_longest: dict[str, int] = {}
    for employee in employees:
        rows = by_user[employee.id]
        total_xp = xp_values[employee.id]
        leaderboard_xp = sum(row.leaderboard_points for row in rows)
        level = level_for_xp(total_xp)
        title = max((item for item in title_rows if item["minimum_level"] <= level), key=lambda item: item["minimum_level"])
        milestone_rows = [row for row in rows if row.canonical_event in real_events]
        current_streak, longest_streak = streak_cache[employee.id]
        user_longest[employee.id] = longest_streak
        for row in rows:
            event_dates[employee.id][row.canonical_event].append(row.earned_at)
        event_count = lambda event: len(event_dates[employee.id][event.value])
        rework = sum(row.rework_discounted for row in milestone_rows)
        deliveries = event_count(CanonicalEvent.VEHICLE_DELIVERED)
        clean = event_count(CanonicalEvent.CLEAN_BOOKING_BONUS)
        resolved = event_count(CanonicalEvent.ESCALATION_RESOLVED)
        clean_score = clean / deliveries if deliveries else 0.5
        recovery_score = resolved / (resolved + rework) if resolved + rework else 0.5
        quality_score = 1 - (rework / len(milestone_rows)) if milestone_rows else 0.5
        reputation = round(100 * (
            settings.reputation_clean_weight * min(clean_score, 1)
            + settings.reputation_recovery_weight * recovery_score
            + settings.reputation_quality_weight * quality_score
        ) / 100)
        user_rows.append({
            "user_id": employee.id, "department": employee.department,
            "location_code": employee.loc_code, "total_xp": total_xp,
            "leaderboard_xp": leaderboard_xp, "streak_bonus_xp": bonus_points[employee.id], "level": level,
            "title_code": title["code"],
            "current_level_xp": total_xp - xp_required_for_level(level),
            "next_level_xp": xp_required_for_level(level + 1) - xp_required_for_level(level),
            "current_streak": current_streak, "longest_streak": longest_streak,
            "reputation": max(0, min(reputation, 100)), "total_awards": len(rows),
            "milestone_awards": len(milestone_rows), "deliveries": deliveries,
            "clean_bookings": clean, "fast_deliveries": event_count(CanonicalEvent.FAST_DELIVERY_BONUS),
            "escalations_resolved": resolved, "cancellation_saves": event_count(CanonicalEvent.CANCELLATION_SAVE),
            "cross_dept_assists": event_count(CanonicalEvent.CROSS_DEPT_ASSIST),
            "rework_discounted_awards": rework, "all_time_rank": all_ranks[employee.id],
            "department_rank": department_ranks[employee.id], "location_rank": location_ranks[employee.id],
            "last_earned_at": rows[-1].earned_at if rows else None,
        })

    department_groups: dict[str, list[XPLedger]] = defaultdict(list)
    location_groups: dict[str, list[XPLedger]] = defaultdict(list)
    for row in ledger:
        department_groups[row.department].append(row)
        if row.location_code:
            location_groups[row.location_code].append(row)
    department_rows = []
    for department, rows in department_groups.items():
        booking_keys = {(row.location_code, row.enquiry_no) for row in rows if row.location_code and row.enquiry_no}
        score = sum(row.leaderboard_points for row in rows)
        department_rows.append({"department": department, "total_xp": sum(row.awarded_points for row in rows), "leaderboard_xp": score, "active_users": len({row.user_id for row in rows}), "bookings_touched": len(booking_keys), "normalized_score": round(score / len(booking_keys), 4) if booking_keys else 0.0, "rank": 0})
    for rank, row in enumerate(sorted(department_rows, key=lambda item: (-item["leaderboard_xp"], item["department"])), 1):
        row["rank"] = rank

    booking_counts: dict[str, int] = defaultdict(int)
    for booking in bookings:
        booking_counts[booking.location_code] += 1
    location_rows = []
    for location in locations:
        rows = location_groups[location.location_code]
        score = sum(row.leaderboard_points for row in rows)
        attempts = booking_counts[location.location_code]
        location_rows.append({"location_code": location.location_code, "total_xp": sum(row.awarded_points for row in rows), "leaderboard_xp": score, "active_users": len({row.user_id for row in rows}), "booking_attempts": attempts, "normalized_score": round(score / attempts, 4) if attempts else 0.0, "raw_rank": 0, "normalized_rank": 0})
    for rank, row in enumerate(sorted(location_rows, key=lambda item: (-item["leaderboard_xp"], item["location_code"])), 1):
        row["raw_rank"] = rank
    for rank, row in enumerate(sorted(location_rows, key=lambda item: (-item["normalized_score"], item["location_code"])), 1):
        row["normalized_rank"] = rank

    async def upsert(model: type[Any], rows: list[dict[str, Any]], keys: list[str]) -> None:
        if not rows:
            return
        statement = sqlite_insert(model)
        excluded = statement.excluded
        await session.execute(statement.on_conflict_do_update(index_elements=keys, set_={column.name: getattr(excluded, column.name) for column in model.__table__.columns if column.name not in keys}), rows)

    await upsert(UserStats, user_rows, ["user_id"])
    await upsert(DepartmentStats, department_rows, ["department"])
    await upsert(LocationStats, location_rows, ["location_code"])

    monthly_branch: dict[str, list[Any]] = defaultdict(lambda: [0, set()])
    if cutoff is not None:
        for row in ledger:
            if (
                row.location_code
                and row.enquiry_no
                and row.earned_at.year == cutoff.year
                and row.earned_at.month == cutoff.month
            ):
                monthly_branch[row.location_code][0] += row.leaderboard_points
                monthly_branch[row.location_code][1].add(row.enquiry_no)
    winning_branch = (
        min(
            monthly_branch,
            key=lambda code: (
                -monthly_branch[code][0] / max(len(monthly_branch[code][1]), 1),
                code,
            ),
        )
        if monthly_branch
        else None
    )
    badge_rows = []
    for badge in BADGES:
        for employee in employees:
            awarded_at: datetime | None = None
            evidence: dict[str, Any] = {}
            if badge["criteria_type"] == "EVENT_COUNT":
                dates = event_dates[employee.id][badge["canonical_event"]]
                if len(dates) >= badge["threshold"]:
                    awarded_at = dates[badge["threshold"] - 1]
                    evidence = {"canonical_event": badge["canonical_event"], "count": len(dates)}
            elif badge["criteria_type"] == "ANY_MILESTONE" and len(milestone_rows) >= badge["threshold"]:
                awarded_at = milestone_rows[badge["threshold"] - 1].earned_at
                evidence = {"milestone_count": len(milestone_rows)}
            elif badge["criteria_type"] == "MIN_LEVEL" and level_for_xp(xp_values[employee.id]) >= badge["threshold"]:
                awarded_at = by_user[employee.id][-1].earned_at if by_user[employee.id] else datetime.min
                evidence = {"level": level_for_xp(xp_values[employee.id])}
            elif badge["criteria_type"] == "LONGEST_STREAK" and user_longest[employee.id] >= badge["threshold"]:
                awarded_at = by_user[employee.id][-1].earned_at if by_user[employee.id] else datetime.min
                evidence = {"longest_streak": user_longest[employee.id]}
            elif badge["criteria_type"] == "BRANCH_CHAMPION" and employee.loc_code == winning_branch and xp_values[employee.id] > 0:
                awarded_at = by_user[employee.id][-1].earned_at
                evidence = {
                    "location_code": winning_branch,
                    "normalized_monthly_rank": 1,
                    "period": cutoff.strftime("%Y-%m") if cutoff else None,
                }
            if awarded_at is not None:
                badge_rows.append({"user_id": employee.id, "badge_code": badge["code"], "awarded_at": awarded_at, "evidence": json.dumps(evidence, sort_keys=True)})
    await upsert(UserBadge, badge_rows, ["user_id", "badge_code"])
    await session.commit()
    return GamificationSummary(len(employees), sum(value > 0 for value in xp_values.values()), len(badge_rows), len(department_rows), len(location_rows))
