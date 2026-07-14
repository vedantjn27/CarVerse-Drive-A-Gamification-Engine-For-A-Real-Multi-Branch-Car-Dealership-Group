"""Canonical booking state-machine tests."""

from app.core.state_machine import BookingStage, max_reached, progress_percent


def test_state_machine_never_regresses_on_out_of_order_events() -> None:
    current = BookingStage.INVOICE_APPROVED
    assert max_reached(current, BookingStage.DISCOUNT_APPROVED) == current


def test_delivery_is_the_full_progress_terminal_stage() -> None:
    assert progress_percent(BookingStage.ENQUIRY_OPEN) == 0
    assert progress_percent(BookingStage.VEHICLE_DELIVERED) == 100

