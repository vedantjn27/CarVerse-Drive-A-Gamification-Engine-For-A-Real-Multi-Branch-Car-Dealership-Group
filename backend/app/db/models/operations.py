"""Optional-AI cache and human-reviewable operational controls."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AICache(Base):
    __tablename__ = "ai_cache"

    cache_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    feature: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(32))
    response_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class AnomalyReview(Base):
    __tablename__ = "anomaly_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    department: Mapped[str | None] = mapped_column(String(64), index=True)
    metric: Mapped[str] = mapped_column(String(96))
    metric_value: Mapped[float] = mapped_column(Float)
    cohort_mean: Mapped[float] = mapped_column(Float)
    cohort_stddev: Mapped[float] = mapped_column(Float)
    z_score: Mapped[float] = mapped_column(Float, index=True)
    threshold: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    resolved_by_user_id: Mapped[str | None] = mapped_column(String(32))
    resolution_note: Mapped[str | None] = mapped_column(Text)


class ScoringRuleOverride(Base):
    __tablename__ = "scoring_rule_overrides"

    canonical_event: Mapped[str] = mapped_column(String(64), primary_key=True)
    base_xp: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    updated_by_user_id: Mapped[str] = mapped_column(String(32))


class LeaderboardSnapshot(Base):
    __tablename__ = "leaderboard_snapshots"

    snapshot_key: Mapped[str] = mapped_column(String(192), primary_key=True)
    period_start: Mapped[datetime] = mapped_column(DateTime, index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime)
    board: Mapped[str] = mapped_column(String(32), index=True)
    rank: Mapped[int] = mapped_column(Integer)
    entity_key: Mapped[str] = mapped_column(String(96), index=True)
    leaderboard_xp: Mapped[int] = mapped_column(Integer)
    normalized_score: Mapped[float | None] = mapped_column(Float)
    payload_json: Mapped[str] = mapped_column(Text)
