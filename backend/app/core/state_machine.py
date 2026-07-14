"""Canonical booking progress ordering used by scoring and race APIs."""

from enum import IntEnum, StrEnum

from app.core.scoring_rules import CanonicalEvent


class BookingStage(IntEnum):
    ENQUIRY_OPEN = 0
    BOOKING_CREATED = 10
    DOCUMENTS_IN_PROGRESS = 15
    DOCUMENT_SET_COMPLETED = 20
    DISCOUNT_APPROVED = 30
    FINANCE_APPROVED = 40
    INVOICE_APPROVED = 50
    GATEPASS_ISSUED = 60
    INSURANCE_APPROVED = 70
    RTO_REGISTRATION_COMPLETED = 80
    PDI_COMPLETED = 90
    DISPATCHED = 100
    VEHICLE_DELIVERED = 110


class BookingStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DORMANT = "DORMANT"
    WON = "WON"
    LOST = "LOST"


EVENT_STAGE = {
    CanonicalEvent.BOOKING_CREATED: BookingStage.BOOKING_CREATED,
    CanonicalEvent.DOCUMENT_SET_COMPLETED: BookingStage.DOCUMENT_SET_COMPLETED,
    CanonicalEvent.DISCOUNT_APPROVED: BookingStage.DISCOUNT_APPROVED,
    CanonicalEvent.FINANCE_APPROVED: BookingStage.FINANCE_APPROVED,
    CanonicalEvent.INVOICE_APPROVED: BookingStage.INVOICE_APPROVED,
    CanonicalEvent.GATEPASS_ISSUED: BookingStage.GATEPASS_ISSUED,
    CanonicalEvent.INSURANCE_APPROVED: BookingStage.INSURANCE_APPROVED,
    CanonicalEvent.RTO_REGISTRATION_COMPLETED: BookingStage.RTO_REGISTRATION_COMPLETED,
    CanonicalEvent.PDI_COMPLETED: BookingStage.PDI_COMPLETED,
    CanonicalEvent.DISPATCHED: BookingStage.DISPATCHED,
    CanonicalEvent.VEHICLE_DELIVERED: BookingStage.VEHICLE_DELIVERED,
}


def max_reached(current: BookingStage, candidate: BookingStage) -> BookingStage:
    return max(current, candidate)


def progress_percent(stage: BookingStage) -> int:
    return round(100 * int(stage) / int(BookingStage.VEHICLE_DELIVERED))

