"""Deterministic aggregate for one composite-key dealership booking."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_bookings_status_stage", "status", "stage_order"),
        Index("ix_bookings_location_status", "location_code", "status"),
    )

    location_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    enquiry_no: Mapped[str] = mapped_column(String(32), primary_key=True)
    current_stage: Mapped[str] = mapped_column(String(64), index=True)
    stage_order: Mapped[int] = mapped_column(Integer)
    progress_percent: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), index=True)
    raw_stage: Mapped[str | None] = mapped_column(String(32))
    first_event_at: Mapped[datetime] = mapped_column(DateTime)
    last_event_at: Mapped[datetime] = mapped_column(DateTime)
    booking_created_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
    sales_owner_user_id: Mapped[str | None] = mapped_column(String(32), index=True)
    total_events: Mapped[int] = mapped_column(Integer)
    milestone_count: Mapped[int] = mapped_column(Integer)
    escalation_count: Mapped[int] = mapped_column(Integer)
    has_cancellation_request: Mapped[bool] = mapped_column(Boolean)
    has_cancellation_approval: Mapped[bool] = mapped_column(Boolean)
    departments_touched: Mapped[str] = mapped_column(Text)

