"""SQLAlchemy models registered with the shared declarative metadata."""

from app.db.models.employee import Employee
from app.db.models.booking import Booking
from app.db.models.location import Location
from app.db.models.raw_event import RawEvent
from app.db.models.xp_ledger import XPLedger
from app.db.models.gamification import (
    Badge,
    DepartmentStats,
    LevelTitle,
    LocationStats,
    ProgressionBonus,
    UserBadge,
    UserStats,
)
from app.db.models.gameplay import BossBattle, QuestTemplate, UserQuestClaim
from app.db.models.operations import AICache, AnomalyReview, LeaderboardSnapshot, ScoringRuleOverride

__all__ = [
    "AICache", "AnomalyReview", "Badge", "Booking", "BossBattle", "DepartmentStats", "Employee", "LevelTitle",
    "LeaderboardSnapshot", "Location", "LocationStats", "ProgressionBonus", "QuestTemplate", "RawEvent", "ScoringRuleOverride", "UserBadge", "UserQuestClaim", "UserStats",
    "XPLedger",
]
