"""Persisted Phase 4 quest and department challenge definitions and claims."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QuestTemplate(Base):
    __tablename__ = "quest_templates"

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(String(256))
    department: Mapped[str | None] = mapped_column(String(64), index=True)
    canonical_event: Mapped[str] = mapped_column(String(64), index=True)
    target_count: Mapped[int] = mapped_column(Integer)
    reward_xp: Mapped[int] = mapped_column(Integer)
    period: Mapped[str] = mapped_column(String(16))
    sort_order: Mapped[int] = mapped_column(Integer)


class UserQuestClaim(Base):
    __tablename__ = "user_quest_claims"

    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("employees.id"), primary_key=True)
    quest_code: Mapped[str] = mapped_column(String(64), ForeignKey("quest_templates.code"), primary_key=True)
    period_start: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    claimed_at: Mapped[datetime] = mapped_column(DateTime)
    reward_xp: Mapped[int] = mapped_column(Integer)


class BossBattle(Base):
    __tablename__ = "boss_battles"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    department: Mapped[str] = mapped_column(String(64), index=True)
    canonical_event: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    target_count: Mapped[int] = mapped_column(Integer)
    reward_pool_xp: Mapped[int] = mapped_column(Integer)
