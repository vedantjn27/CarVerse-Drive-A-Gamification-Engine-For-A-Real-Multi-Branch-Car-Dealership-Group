"""Development-only workstation actions for an interactive hackathon demo.

Production integrations submit the same verified milestones from the dealership
system. This route is deliberately labelled ``DEMO`` and only permits the next
valid, department-owned milestone once per booking.
"""

from datetime import UTC, datetime
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.scoring_rules import SCORING_RULES, CanonicalEvent
from app.core.security import Principal, get_current_principal
from app.core.state_machine import EVENT_STAGE, BookingStage, progress_percent
from app.db.models import Booking, Employee, XPLedger
from app.db.session import get_db_session
from app.services.gamification_service import materialize_gamification
from app.services.notification_service import leaderboard_broadcaster

router = APIRouter(prefix="/demo", tags=["demo workstation"])

_NEXT_STAGES: dict[str, tuple[CanonicalEvent, str]] = {
    "ENQUIRY_OPEN": (CanonicalEvent.BOOKING_CREATED, "SALES"),
    "BOOKING_CREATED": (CanonicalEvent.DOCUMENT_SET_COMPLETED, "SALES"),
    "DOCUMENTS_IN_PROGRESS": (CanonicalEvent.DOCUMENT_SET_COMPLETED, "SALES"),
    "DOCUMENT_SET_COMPLETED": (CanonicalEvent.DISCOUNT_APPROVED, "SALES"),
    "DISCOUNT_APPROVED": (CanonicalEvent.FINANCE_APPROVED, "FINANCE"),
    "FINANCE_APPROVED": (CanonicalEvent.INVOICE_APPROVED, "ACCOUNTS"),
    "INVOICE_APPROVED": (CanonicalEvent.GATEPASS_ISSUED, "ACCOUNTS"),
    "GATEPASS_ISSUED": (CanonicalEvent.INSURANCE_APPROVED, "CUSTOMER CARE"),
    "INSURANCE_APPROVED": (CanonicalEvent.RTO_REGISTRATION_COMPLETED, "RTO / REGN TEAM"),
    "RTO_REGISTRATION_COMPLETED": (CanonicalEvent.PDI_COMPLETED, "PDI"),
    "PDI_COMPLETED": (CanonicalEvent.DISPATCHED, "PDI"),
    "DISPATCHED": (CanonicalEvent.VEHICLE_DELIVERED, "SALES"),
}

_ROLE_WORK_LABELS = {
    "EDP": "Verify invoice and registration handoff",
    "ACCESSORIES": "Confirm accessory fitment handoff",
    "TRUEVALUE": "Confirm exchange valuation handoff",
    "SECURITY": "Confirm vehicle clearance handoff",
    "SERVICE": "Confirm service-readiness handoff",
    "TRANSPORT": "Confirm vehicle transit handoff",
    "CCM": "Confirm customer coordination handoff",
}


class CompleteAction(BaseModel):
    location_code: str = Field(min_length=1, max_length=32)
    enquiry_no: str = Field(min_length=1, max_length=32)


@router.get("/workstation")
async def workstation(
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, object]:
    employee = await session.get(Employee, principal.employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    core = employee.department in {"SALES", "FINANCE", "ACCOUNTS", "CUSTOMER CARE", "RTO / REGN TEAM", "PDI"}
    return {"department": employee.department, "mode": "LIFECYCLE" if core else "OPERATIONS", "title": _ROLE_WORK_LABELS.get(employee.department, "Complete department work handoff"), "description": "A real source integration supplies this event in production. Demo mode validates one work item per employee and day."}


@router.post("/complete-role-work")
async def complete_role_work(
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, object]:
    if settings.environment == "production":
        raise HTTPException(status_code=403, detail="Demo workstation is disabled in production")
    employee = await session.get(Employee, principal.employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    now = datetime.now(UTC).replace(tzinfo=None)
    dedupe_key = f"demo-role-work:{employee.id}:{now.date().isoformat()}"
    if await session.scalar(select(XPLedger.id).where(XPLedger.dedupe_key == dedupe_key)) is not None:
        raise HTTPException(status_code=409, detail="Today's department work handoff is already recorded")
    rule = SCORING_RULES[CanonicalEvent.OPERATIONAL_HANDOFF_COMPLETED]
    session.add(XPLedger(dedupe_key=dedupe_key, user_id=employee.id, actor_user_id=employee.id, partner_user_id=None, source_event_id=-int(now.timestamp() * 1_000_000), canonical_event=CanonicalEvent.OPERATIONAL_HANDOFF_COMPLETED.value, department=employee.department, location_code=employee.loc_code, enquiry_no=None, base_points=rule.base_xp, awarded_points=rule.base_xp, leaderboard_points=rule.base_xp, rework_discounted=False, earned_at=now, reason=f"DEMO WORKSTATION: {_ROLE_WORK_LABELS.get(employee.department, 'department work handoff')}", metadata_json=json.dumps({"mode":"demo_workstation","verified_by":"department_work_order","department":employee.department})))
    await session.commit()
    await materialize_gamification(session)
    await leaderboard_broadcaster.publish("xp_gain", {"employee_id": employee.id, "canonical_event": CanonicalEvent.OPERATIONAL_HANDOFF_COMPLETED.value, "points": rule.base_xp, "mode": "demo_workstation"})
    await leaderboard_broadcaster.publish("boss_progress", {"department": employee.department, "canonical_event": CanonicalEvent.OPERATIONAL_HANDOFF_COMPLETED.value, "mode": "demo_workstation"})
    return {"canonical_event": CanonicalEvent.OPERATIONAL_HANDOFF_COMPLETED.value, "points": rule.base_xp, "title": _ROLE_WORK_LABELS.get(employee.department, "Department work handoff"), "mode": "demo_workstation"}


@router.post("/check-in")
async def check_in(
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, object]:
    """One low-value daily demo check-in, available to every active department."""
    if settings.environment == "production":
        raise HTTPException(status_code=403, detail="Demo workstation is disabled in production")
    employee = await session.get(Employee, principal.employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    now = datetime.now(UTC).replace(tzinfo=None)
    dedupe_key = f"demo-checkin:{employee.id}:{now.date().isoformat()}"
    if await session.scalar(select(XPLedger.id).where(XPLedger.dedupe_key == dedupe_key)) is not None:
        raise HTTPException(status_code=409, detail="Daily demo check-in already recorded")
    rule = SCORING_RULES[CanonicalEvent.DAILY_LOGIN_STREAK]
    session.add(XPLedger(dedupe_key=dedupe_key, user_id=employee.id, actor_user_id=employee.id, partner_user_id=None, source_event_id=-int(now.timestamp() * 1_000_000), canonical_event=CanonicalEvent.DAILY_LOGIN_STREAK.value, department=employee.department, location_code=employee.loc_code, enquiry_no=None, base_points=rule.base_xp, awarded_points=rule.base_xp, leaderboard_points=rule.base_xp, rework_discounted=False, earned_at=now, reason="DEMO WORKSTATION: first daily shift check-in", metadata_json=json.dumps({"mode":"demo_workstation","verified_by":"daily_cap"})))
    await session.commit()
    await materialize_gamification(session)
    await leaderboard_broadcaster.publish("xp_gain", {"employee_id": employee.id, "canonical_event": CanonicalEvent.DAILY_LOGIN_STREAK.value, "points": rule.base_xp, "mode": "demo_workstation"})
    return {"canonical_event": CanonicalEvent.DAILY_LOGIN_STREAK.value, "points": rule.base_xp, "mode": "demo_workstation"}


@router.post("/complete-next")
async def complete_next(
    payload: CompleteAction,
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, object]:
    if settings.environment == "production":
        raise HTTPException(status_code=403, detail="Demo workstation is disabled in production")
    booking = await session.get(Booking, {"location_code": payload.location_code, "enquiry_no": payload.enquiry_no})
    employee = await session.get(Employee, principal.employee_id)
    if booking is None or employee is None or booking.status != "ACTIVE":
        raise HTTPException(status_code=404, detail="An active demo booking was not found")
    item = _NEXT_STAGES.get(booking.current_stage)
    if item is None:
        raise HTTPException(status_code=409, detail="This booking has no remaining demo milestone")
    event, required_department = item
    if employee.department != required_department:
        raise HTTPException(status_code=403, detail=f"Next verified action belongs to {required_department}")
    dedupe_key = f"demo:{booking.location_code}:{booking.enquiry_no}:{event.value}"
    existing = await session.scalar(select(XPLedger.id).where(XPLedger.dedupe_key == dedupe_key))
    if existing is not None:
        raise HTTPException(status_code=409, detail="This demo milestone has already been completed")
    now = datetime.now(UTC).replace(tzinfo=None)
    rule = SCORING_RULES[event]
    stage = EVENT_STAGE[event]
    synthetic_id = -int(now.timestamp() * 1_000_000)
    session.add(XPLedger(dedupe_key=dedupe_key, user_id=employee.id, actor_user_id=employee.id, partner_user_id=None, source_event_id=synthetic_id, canonical_event=event.value, department=employee.department, location_code=booking.location_code, enquiry_no=booking.enquiry_no, base_points=rule.base_xp, awarded_points=rule.base_xp, leaderboard_points=rule.base_xp, rework_discounted=False, earned_at=now, reason="DEMO WORKSTATION: validated next dealership milestone", metadata_json=json.dumps({"mode":"demo_workstation","verified_by":"state_machine"})))
    booking.current_stage = stage.name
    booking.stage_order = int(stage)
    booking.progress_percent = progress_percent(stage)
    booking.last_event_at = now
    if stage is BookingStage.VEHICLE_DELIVERED:
        booking.status = "WON"
        booking.delivered_at = now
    touched = set(json.loads(booking.departments_touched))
    touched.add(employee.department)
    booking.departments_touched = json.dumps(sorted(touched))
    await session.commit()
    await materialize_gamification(session)
    await leaderboard_broadcaster.publish("xp_gain", {"employee_id": employee.id, "canonical_event": event.value, "points": rule.base_xp, "booking": payload.enquiry_no, "mode": "demo_workstation"})
    await leaderboard_broadcaster.publish("boss_progress", {"department": employee.department, "canonical_event": event.value, "mode": "demo_workstation"})
    return {"canonical_event": event.value, "points": rule.base_xp, "booking": payload.enquiry_no, "next_stage": booking.current_stage, "mode": "demo_workstation"}
