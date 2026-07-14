"""Builders for deterministic scoring-engine unit tests."""

from datetime import datetime

from app.db.models import RawEvent


def raw_event(
    event_id: int,
    action_code: str,
    *,
    created_at: datetime,
    user_id: str = "sales-1",
    department: str = "SALES",
    stage: str = "IBNA",
    enquiry_no: str | None = "ENQ-1",
    location_code: str | None = "WFR",
) -> RawEvent:
    raw_booking = enquiry_no or "-"
    raw_location = location_code or "-"
    return RawEvent(
        id=event_id,
        group_id=1,
        stage_raw=stage,
        stage=stage,
        categories_raw="TEST",
        categories="TEST",
        department_raw=department,
        department=department,
        username=user_id,
        user_id=user_id,
        enquiry_no_raw=raw_booking,
        enquiry_no=enquiry_no,
        location_code_raw=raw_location,
        location_code=location_code,
        message="test event",
        action_code_raw=action_code,
        action_code=action_code,
        source_raw="API",
        source="API",
        created_date=created_at,
    )

