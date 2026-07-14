"""Milestone derivation and once-only scoring tests."""

from datetime import datetime, timedelta

from app.core.scoring_rules import REQUIRED_DOCUMENT_ACTIONS, SCORING_RULES, CanonicalEvent
from app.services.scoring_engine import ScoringReplayEngine
from tests.scoring_helpers import raw_event


START = datetime(2026, 5, 4, 10, 0, 0)


def test_scoring_contract_has_exactly_eighteen_unique_rules() -> None:
    assert len(SCORING_RULES) == 18
    assert len(SCORING_RULES) <= 20
    assert set(SCORING_RULES) == set(CanonicalEvent)


def _awards(engine: ScoringReplayEngine, event: CanonicalEvent) -> list[dict]:
    return [row for row in engine.ledger_rows if row["canonical_event"] == event.value]


def test_double_invoice_approved_only_pays_once() -> None:
    engine = ScoringReplayEngine()
    engine.process(raw_event(1, "INVOICE_APPROVED_SALES", created_at=START))
    engine.process(
        raw_event(2, "INVOICE_APPROVED_EDP", created_at=START + timedelta(minutes=5),
                  user_id="edp-1", department="EDP")
    )

    invoice_awards = _awards(engine, CanonicalEvent.INVOICE_APPROVED)
    assert len(invoice_awards) == 1
    assert invoice_awards[0]["awarded_points"] == 25


def test_document_set_scores_only_after_all_exact_slots() -> None:
    engine = ScoringReplayEngine()
    engine.process(raw_event(1, "DOCUMENTS_PANIC BUTTON", created_at=START))
    for index, action in enumerate(sorted(REQUIRED_DOCUMENT_ACTIONS), start=2):
        engine.process(raw_event(index, action, created_at=START + timedelta(minutes=index)))

    awards = _awards(engine, CanonicalEvent.DOCUMENT_SET_COMPLETED)
    assert len(awards) == 1
    assert awards[0]["source_event_id"] == len(REQUIRED_DOCUMENT_ACTIONS) + 1


def test_delivery_xp_goes_to_sales_owner_not_incidental_gatepass_actor() -> None:
    engine = ScoringReplayEngine()
    engine.process(raw_event(1, "BOOKING_CREATED", created_at=START))
    engine.process(
        raw_event(2, "GATEPASS_ISSUED_BY_ACCOUNTS", created_at=START + timedelta(days=2),
                  user_id="accounts-1", department="ACCOUNTS", stage="DELIVERED")
    )

    delivery = _awards(engine, CanonicalEvent.VEHICLE_DELIVERED)
    assert len(delivery) == 1
    assert delivery[0]["user_id"] == "sales-1"
    assert delivery[0]["actor_user_id"] == "accounts-1"
    assert not _awards(engine, CanonicalEvent.CROSS_DEPT_ASSIST)
