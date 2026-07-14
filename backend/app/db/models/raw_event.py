"""Immutable normalized event model sourced from the organizer event log."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RawEvent(Base):
    __tablename__ = "raw_events"
    __table_args__ = (
        Index(
            "ix_raw_events_booking_timeline",
            "location_code",
            "enquiry_no",
            "created_date",
            "id",
        ),
        Index("ix_raw_events_user_timeline", "user_id", "created_date"),
        Index("ix_raw_events_action_timeline", "action_code", "created_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    group_id: Mapped[int | None] = mapped_column(Integer)

    stage_raw: Mapped[str] = mapped_column(String(32))
    stage: Mapped[str] = mapped_column(String(32), index=True)
    categories_raw: Mapped[str] = mapped_column(String(64))
    categories: Mapped[str] = mapped_column(String(64), index=True)
    department_raw: Mapped[str] = mapped_column(String(64))
    department: Mapped[str] = mapped_column(String(64), index=True)

    username: Mapped[str | None] = mapped_column(String(160))
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("employees.id"), index=True
    )
    enquiry_no_raw: Mapped[str] = mapped_column(String(32))
    enquiry_no: Mapped[str | None] = mapped_column(String(32))
    location_code_raw: Mapped[str] = mapped_column(String(32))
    location_code: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("locations.location_code")
    )
    message: Mapped[str | None] = mapped_column(Text)

    action_code_raw: Mapped[str] = mapped_column(String(256))
    action_code: Mapped[str] = mapped_column(String(128), index=True)
    source_raw: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(32))
    created_date: Mapped[datetime] = mapped_column(DateTime, index=True)
