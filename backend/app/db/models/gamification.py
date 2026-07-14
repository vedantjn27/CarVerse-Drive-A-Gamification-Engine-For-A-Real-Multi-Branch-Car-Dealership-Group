"""Materialized progression, badge, and aggregate gamification models."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LevelTitle(Base):
    __tablename__ = "level_titles"

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(96), unique=True)
    minimum_level: Mapped[int] = mapped_column(Integer, unique=True)
    description: Mapped[str] = mapped_column(String(256))


class UserStats(Base):
    __tablename__ = "user_stats"
    __table_args__ = (
        Index("ix_user_stats_department_rank", "department", "department_rank"),
        Index("ix_user_stats_location_rank", "location_code", "location_rank"),
    )

    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("employees.id"), primary_key=True
    )
    department: Mapped[str | None] = mapped_column(String(64), index=True)
    location_code: Mapped[str | None] = mapped_column(String(32), index=True)
    total_xp: Mapped[int] = mapped_column(Integer, index=True)
    leaderboard_xp: Mapped[int] = mapped_column(Integer)
    streak_bonus_xp: Mapped[int] = mapped_column(Integer)
    level: Mapped[int] = mapped_column(Integer, index=True)
    title_code: Mapped[str] = mapped_column(String(64), ForeignKey("level_titles.code"))
    current_level_xp: Mapped[int] = mapped_column(Integer)
    next_level_xp: Mapped[int] = mapped_column(Integer)
    current_streak: Mapped[int] = mapped_column(Integer)
    longest_streak: Mapped[int] = mapped_column(Integer)
    reputation: Mapped[int] = mapped_column(Integer, index=True)
    total_awards: Mapped[int] = mapped_column(Integer)
    milestone_awards: Mapped[int] = mapped_column(Integer)
    deliveries: Mapped[int] = mapped_column(Integer)
    clean_bookings: Mapped[int] = mapped_column(Integer)
    fast_deliveries: Mapped[int] = mapped_column(Integer)
    escalations_resolved: Mapped[int] = mapped_column(Integer)
    cancellation_saves: Mapped[int] = mapped_column(Integer)
    cross_dept_assists: Mapped[int] = mapped_column(Integer)
    rework_discounted_awards: Mapped[int] = mapped_column(Integer)
    all_time_rank: Mapped[int | None] = mapped_column(Integer, index=True)
    department_rank: Mapped[int | None] = mapped_column(Integer)
    location_rank: Mapped[int | None] = mapped_column(Integer)
    last_earned_at: Mapped[datetime | None] = mapped_column(DateTime)


class Badge(Base):
    __tablename__ = "badges"

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(96), unique=True)
    description: Mapped[str] = mapped_column(String(256))
    icon: Mapped[str] = mapped_column(String(64))
    criteria_type: Mapped[str] = mapped_column(String(32))
    canonical_event: Mapped[str | None] = mapped_column(String(64))
    threshold: Mapped[int] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer)


class UserBadge(Base):
    __tablename__ = "user_badges"

    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("employees.id"), primary_key=True
    )
    badge_code: Mapped[str] = mapped_column(
        String(64), ForeignKey("badges.code"), primary_key=True
    )
    awarded_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    evidence: Mapped[str] = mapped_column(Text)


class ProgressionBonus(Base):
    __tablename__ = "progression_bonuses"

    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("employees.id"), primary_key=True
    )
    bonus_code: Mapped[str] = mapped_column(String(64), primary_key=True)
    points: Mapped[int] = mapped_column(Integer)
    awarded_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    reason: Mapped[str] = mapped_column(String(256))


class DepartmentStats(Base):
    __tablename__ = "department_stats"

    department: Mapped[str] = mapped_column(String(64), primary_key=True)
    total_xp: Mapped[int] = mapped_column(Integer)
    leaderboard_xp: Mapped[int] = mapped_column(Integer, index=True)
    active_users: Mapped[int] = mapped_column(Integer)
    bookings_touched: Mapped[int] = mapped_column(Integer)
    normalized_score: Mapped[float] = mapped_column(Float, index=True)
    rank: Mapped[int] = mapped_column(Integer)


class LocationStats(Base):
    __tablename__ = "location_stats"

    location_code: Mapped[str] = mapped_column(
        String(32), ForeignKey("locations.location_code"), primary_key=True
    )
    total_xp: Mapped[int] = mapped_column(Integer)
    leaderboard_xp: Mapped[int] = mapped_column(Integer, index=True)
    active_users: Mapped[int] = mapped_column(Integer)
    booking_attempts: Mapped[int] = mapped_column(Integer)
    normalized_score: Mapped[float] = mapped_column(Float, index=True)
    raw_rank: Mapped[int] = mapped_column(Integer)
    normalized_rank: Mapped[int] = mapped_column(Integer)
