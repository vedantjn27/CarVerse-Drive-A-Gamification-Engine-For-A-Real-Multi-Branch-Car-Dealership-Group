"""Append-only XP awards with deterministic anti-duplication keys."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class XPLedger(Base):
    __tablename__ = "xp_ledger"
    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_xp_ledger_dedupe_key"),
        UniqueConstraint(
            "source_event_id",
            "canonical_event",
            "user_id",
            name="uq_xp_ledger_source_event_beneficiary",
        ),
        Index("ix_xp_ledger_user_earned", "user_id", "earned_at"),
        Index("ix_xp_ledger_booking", "location_code", "enquiry_no"),
        Index("ix_xp_ledger_event_earned", "canonical_event", "earned_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dedupe_key: Mapped[str] = mapped_column(String(256), nullable=False)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    actor_user_id: Mapped[str] = mapped_column(String(32), index=True)
    partner_user_id: Mapped[str | None] = mapped_column(String(32))
    source_event_id: Mapped[int] = mapped_column(Integer, index=True)
    canonical_event: Mapped[str] = mapped_column(String(64), index=True)
    department: Mapped[str] = mapped_column(String(64), index=True)
    location_code: Mapped[str | None] = mapped_column(String(32), index=True)
    enquiry_no: Mapped[str | None] = mapped_column(String(32))
    base_points: Mapped[int] = mapped_column(Integer)
    awarded_points: Mapped[int] = mapped_column(Integer)
    leaderboard_points: Mapped[int] = mapped_column(Integer)
    rework_discounted: Mapped[bool] = mapped_column(Boolean)
    earned_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    reason: Mapped[str] = mapped_column(String(256))
    metadata_json: Mapped[str] = mapped_column(Text)
