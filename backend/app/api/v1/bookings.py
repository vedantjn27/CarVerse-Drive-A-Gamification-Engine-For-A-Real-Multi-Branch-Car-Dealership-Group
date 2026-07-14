"""Authenticated booking race-track APIs."""

import json
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, get_current_principal
from app.db.session import get_db_session
from app.services.booking_service import active_races, booking_race

router = APIRouter(prefix="/bookings", tags=["bookings"])


class BookingRaceResponse(BaseModel):
    location_code: str
    enquiry_no: str
    status: str
    current_stage: str
    progress_percent: int
    sales_owner_user_id: str | None
    sales_owner_name: str | None
    total_events: int
    milestone_count: int
    escalation_count: int
    first_event_at: datetime
    last_event_at: datetime
    booking_created_at: datetime | None
    delivered_at: datetime | None
    departments_touched: list[str]
    track: list[dict[str, Any]]
    milestones: list[dict[str, Any]]


@router.get("/active")
async def active(
    _: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    location_code: str | None = None,
    department: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, object]:
    total, rows = await active_races(session, location_code, department, limit, offset)
    return {"total": total, "entries": [{"location_code": row.location_code, "enquiry_no": row.enquiry_no, "status": row.status, "current_stage": row.current_stage, "progress_percent": row.progress_percent, "last_event_at": row.last_event_at, "departments_touched": json.loads(row.departments_touched)} for row in rows]}


@router.get("/{location_code}/{enquiry_no}", response_model=BookingRaceResponse)
async def detail(
    location_code: str,
    enquiry_no: str,
    _: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> BookingRaceResponse:
    result = await booking_race(session, location_code, enquiry_no)
    booking = result.booking
    return BookingRaceResponse(location_code=booking.location_code, enquiry_no=booking.enquiry_no, status=booking.status, current_stage=booking.current_stage, progress_percent=booking.progress_percent, sales_owner_user_id=booking.sales_owner_user_id, sales_owner_name=result.owner_name, total_events=booking.total_events, milestone_count=booking.milestone_count, escalation_count=booking.escalation_count, first_event_at=booking.first_event_at, last_event_at=booking.last_event_at, booking_created_at=booking.booking_created_at, delivered_at=booking.delivered_at, departments_touched=json.loads(booking.departments_touched), track=result.track, milestones=result.milestones)
