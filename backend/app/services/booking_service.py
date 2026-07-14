"""Read models for the frontend booking race-track visualization."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scoring_rules import CanonicalEvent
from app.core.state_machine import BookingStage
from app.db.models import Booking, Employee, XPLedger


RACE_TRACK = (
    ("ENQUIRY_OPEN", "Enquiry Open", "SALES", 0, None),
    ("BOOKING_CREATED", "Booking Created", "SALES", 10, CanonicalEvent.BOOKING_CREATED.value),
    ("DOCUMENT_SET_COMPLETED", "Documents Ready", "SALES", 20, CanonicalEvent.DOCUMENT_SET_COMPLETED.value),
    ("DISCOUNT_APPROVED", "Discount Approved", "SALES", 30, CanonicalEvent.DISCOUNT_APPROVED.value),
    ("FINANCE_APPROVED", "Finance Approved", "FINANCE", 40, CanonicalEvent.FINANCE_APPROVED.value),
    ("INVOICE_APPROVED", "Invoice Approved", "ACCOUNTS", 50, CanonicalEvent.INVOICE_APPROVED.value),
    ("GATEPASS_ISSUED", "Gatepass Issued", "ACCOUNTS", 60, CanonicalEvent.GATEPASS_ISSUED.value),
    ("INSURANCE_APPROVED", "Insurance Approved", "CUSTOMER CARE", 70, CanonicalEvent.INSURANCE_APPROVED.value),
    ("RTO_REGISTRATION_COMPLETED", "Registration Complete", "RTO / REGN TEAM", 80, CanonicalEvent.RTO_REGISTRATION_COMPLETED.value),
    ("PDI_COMPLETED", "PDI Complete", "PDI", 90, CanonicalEvent.PDI_COMPLETED.value),
    ("DISPATCHED", "Dispatched", "PDI / CUSTOMER CARE", 100, CanonicalEvent.DISPATCHED.value),
    ("VEHICLE_DELIVERED", "Delivered", "SALES", 110, CanonicalEvent.VEHICLE_DELIVERED.value),
)

# A department's pit queue must contain only work that is waiting for that
# department now.  Historical ``departments_touched`` data is intentionally
# not used here; using it leaks the same booking into previous teams' queues.
NEXT_ACTION_DEPARTMENT = {
    "ENQUIRY_OPEN": "SALES",
    "BOOKING_CREATED": "SALES",
    "DOCUMENTS_IN_PROGRESS": "SALES",
    "DOCUMENT_SET_COMPLETED": "SALES",
    "DISCOUNT_APPROVED": "FINANCE",
    "FINANCE_APPROVED": "ACCOUNTS",
    "INVOICE_APPROVED": "ACCOUNTS",
    "GATEPASS_ISSUED": "CUSTOMER CARE",
    "INSURANCE_APPROVED": "RTO / REGN TEAM",
    "RTO_REGISTRATION_COMPLETED": "PDI",
    "PDI_COMPLETED": "PDI",
    "DISPATCHED": "SALES",
}


@dataclass(frozen=True, slots=True)
class BookingRace:
    booking: Booking
    owner_name: str | None
    track: list[dict[str, object]]
    milestones: list[dict[str, object]]


async def booking_race(session: AsyncSession, location_code: str, enquiry_no: str) -> BookingRace:
    booking = await session.get(Booking, {"location_code": location_code, "enquiry_no": enquiry_no})
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    awards = list((await session.execute(
        select(XPLedger).where(XPLedger.location_code == location_code, XPLedger.enquiry_no == enquiry_no).order_by(XPLedger.earned_at, XPLedger.id)
    )).scalars())
    current_order = int(BookingStage[booking.current_stage])
    owner = await session.get(Employee, booking.sales_owner_user_id) if booking.sales_owner_user_id else None
    track = [
        {"stage": stage, "label": label, "responsible_department": department, "order": order,
         # A later state-machine position proves the car passed every earlier
         # stage, even if the supplied event export did not include a separate
         # row for an intermediate milestone.
         "reached": order <= current_order, "current": booking.current_stage == stage}
        for stage, label, department, order, event in RACE_TRACK
    ]
    milestones = [
        {"canonical_event": award.canonical_event, "earned_at": award.earned_at,
         "department": award.department, "user_id": award.user_id, "points": award.awarded_points}
        for award in awards
        if award.canonical_event in {item[4] for item in RACE_TRACK if item[4]}
    ]
    return BookingRace(booking, owner.name if owner else None, track, milestones)


async def active_races(session: AsyncSession, location_code: str | None, department: str | None, limit: int, offset: int) -> tuple[int, list[Booking]]:
    statement = select(Booking).where(Booking.status == "ACTIVE")
    if location_code:
        statement = statement.where(Booking.location_code == location_code)
    rows = list((await session.execute(statement.order_by(Booking.progress_percent.desc(), Booking.last_event_at.desc()))).scalars())
    if department:
        wanted = department.strip().upper()
        rows = [row for row in rows if NEXT_ACTION_DEPARTMENT.get(row.current_stage) == wanted]
    return len(rows), rows[offset : offset + limit]
