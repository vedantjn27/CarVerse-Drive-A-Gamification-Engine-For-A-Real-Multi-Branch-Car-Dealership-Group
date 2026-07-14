"""Named tests for every structural anti-gaming control in Phase 2."""

from datetime import datetime, timedelta

from app.core.config import settings
from app.core.scoring_rules import CanonicalEvent
from app.services.scoring_engine import ScoringReplayEngine
from tests.scoring_helpers import raw_event


START = datetime(2026, 5, 4, 10, 0, 0)


def _event_awards(engine: ScoringReplayEngine, event: CanonicalEvent) -> list[dict]:
    return [row for row in engine.ledger_rows if row["canonical_event"] == event.value]


def test_fifty_logins_does_not_give_fifty_x_points() -> None:
    engine = ScoringReplayEngine()
    for index in range(50):
        engine.process(
            raw_event(index + 1, "USER_LOGGED_IN", created_at=START + timedelta(minutes=index),
                      enquiry_no=None, location_code=None)
        )

    awards = _event_awards(engine, CanonicalEvent.DAILY_LOGIN_STREAK)
    assert len(awards) == 1
    assert sum(item["awarded_points"] for item in awards) == 2


def test_fifty_notes_are_capped_at_three_per_booking_day() -> None:
    engine = ScoringReplayEngine()
    for index in range(50):
        engine.process(
            raw_event(index + 1, "BOOKING_NOTE_ADDED", created_at=START + timedelta(minutes=index))
        )
    assert len(_event_awards(engine, CanonicalEvent.FOLLOW_UP_LOGGED)) == 3


def test_rework_discount_applies_after_two_escalations() -> None:
    engine = ScoringReplayEngine()
    engine.process(raw_event(1, "DISCOUNT_ESCALATED", created_at=START))
    engine.process(raw_event(2, "DISCOUNT_ESCALATED", created_at=START + timedelta(minutes=1)))
    engine.process(raw_event(3, "INVOICE_APPROVED_EDP", created_at=START + timedelta(minutes=2),
                             user_id="edp-1", department="EDP"))
    invoice = _event_awards(engine, CanonicalEvent.INVOICE_APPROVED)[0]
    assert invoice["rework_discounted"] is True
    assert invoice["awarded_points"] == 25 * (100 - settings.rework_discount_percent) // 100


def test_user_cannot_collaborate_with_themselves_across_departments() -> None:
    engine = ScoringReplayEngine()
    engine.process(raw_event(1, "BOOKING_CREATED", created_at=START, user_id="same-user"))
    engine.process(raw_event(2, "CREDIT_APPROVED", created_at=START + timedelta(hours=1),
                             user_id="same-user", department="ACCOUNTS"))
    assert not _event_awards(engine, CanonicalEvent.CROSS_DEPT_ASSIST)


def test_valid_fast_cross_department_handoff_rewards_both_sides_once() -> None:
    engine = ScoringReplayEngine()
    engine.process(raw_event(1, "BOOKING_CREATED", created_at=START))
    engine.process(raw_event(2, "CREDIT_APPROVED", created_at=START + timedelta(hours=1),
                             user_id="accounts-1", department="ACCOUNTS"))
    assists = _event_awards(engine, CanonicalEvent.CROSS_DEPT_ASSIST)
    assert len(assists) == 2
    assert {item["user_id"] for item in assists} == {"sales-1", "accounts-1"}


def test_cancelled_booking_is_frozen_from_future_milestone_scoring() -> None:
    engine = ScoringReplayEngine()
    engine.process(raw_event(1, "BOOKING_CANCELLATION_REQUEST_APPROVED", created_at=START,
                             stage="CANCELLED"))
    engine.process(raw_event(2, "INVOICE_APPROVED_EDP", created_at=START + timedelta(hours=1),
                             user_id="edp-1", department="EDP"))
    assert not _event_awards(engine, CanonicalEvent.INVOICE_APPROVED)


def test_sixth_daily_delivery_keeps_lifetime_xp_but_not_leaderboard_xp() -> None:
    engine = ScoringReplayEngine()
    for index in range(6):
        engine.process(
            raw_event(
                index + 1,
                "UNSCORED_DELIVERY_CONTEXT",
                created_at=START + timedelta(minutes=index),
                stage="DELIVERED",
                enquiry_no=f"ENQ-{index}",
            )
        )

    deliveries = _event_awards(engine, CanonicalEvent.VEHICLE_DELIVERED)
    assert len(deliveries) == 6
    assert sum(item["awarded_points"] for item in deliveries) == 600
    assert deliveries[-1]["leaderboard_points"] == 0
    assert sum(item["leaderboard_points"] for item in engine.ledger_rows) == 500
