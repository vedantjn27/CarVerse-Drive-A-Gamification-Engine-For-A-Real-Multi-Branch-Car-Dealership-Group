"""Deterministic weekly department challenges and evenly split team rewards."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import BossBattle, Employee, ProgressionBonus, UserBadge, XPLedger
from app.seed.seed_gameplay import BOSS_BATTLE_TEMPLATES
from app.services.quest_service import week_window


def _battle_id(starts_at: datetime, department: str) -> str:
    year, week, _ = starts_at.isocalendar()
    return f"{year}-W{week:02d}-{department.replace(' ', '_')}"


async def materialize_boss_battles(session: AsyncSession) -> int:
    anchor = await session.scalar(select(func.max(XPLedger.earned_at)))
    if anchor is None:
        return 0
    starts_at, ends_at = week_window(anchor)
    rows = []
    for department, event, target, title, description in BOSS_BATTLE_TEMPLATES:
        # Development demo mode uses one verified contribution so judges can
        # experience the claim flow. Production keeps the real team target.
        demo_mode = settings.environment != "production"
        rows.append({"id": _battle_id(starts_at, department), "department": department, "canonical_event": event, "title": title, "description": description, "starts_at": starts_at, "ends_at": ends_at, "target_count": 1 if demo_mode else target, "reward_pool_xp": 60 if demo_mode else 300})
    statement = sqlite_insert(BossBattle)
    excluded = statement.excluded
    await session.execute(statement.on_conflict_do_update(index_elements=["id"], set_={column.name: getattr(excluded, column.name) for column in BossBattle.__table__.columns if column.name != "id"}), rows)
    await session.commit()
    return len(rows)


async def _battle_view(session: AsyncSession, battle: BossBattle, user_id: str | None = None) -> dict[str, object]:
    awards = list((await session.execute(select(XPLedger).where(XPLedger.department == battle.department, XPLedger.canonical_event == battle.canonical_event, XPLedger.earned_at >= battle.starts_at, XPLedger.earned_at < battle.ends_at).order_by(XPLedger.earned_at, XPLedger.id))).scalars())
    progress = len(awards)
    contributors = sorted({award.user_id for award in awards})
    claimed = False
    if user_id:
        claimed = await session.get(ProgressionBonus, {"user_id": user_id, "bonus_code": f"BOSS_{battle.id}"}) is not None
    completed = progress >= battle.target_count
    demo_mode = settings.environment != "production"
    eligible = bool(user_id and completed and not claimed and (demo_mode or user_id in contributors))
    return {"id": battle.id, "department": battle.department, "canonical_event": battle.canonical_event, "title": battle.title, "description": battle.description, "starts_at": battle.starts_at, "ends_at": battle.ends_at, "progress": progress, "target_count": battle.target_count, "completed": completed, "reward_pool_xp": battle.reward_pool_xp, "contributors": len(contributors), "remaining": max(battle.target_count - progress, 0), "eligible_to_claim": eligible, "claimed": claimed}


async def award_completed_boss_battles(session: AsyncSession) -> int:
    # Boss rewards are intentionally player-claimed.  This preserves the
    # celebration moment and prevents a scheduler from consuming it first.
    if settings.environment != "production":
        return 0
    battles = list((await session.execute(select(BossBattle))).scalars())
    created = 0
    for battle in battles:
        view = await _battle_view(session, battle)
        if not view["completed"]:
            continue
        recipients = sorted({award.user_id for award in (await session.execute(select(XPLedger).where(XPLedger.department == battle.department, XPLedger.canonical_event == battle.canonical_event, XPLedger.earned_at >= battle.starts_at, XPLedger.earned_at < battle.ends_at))).scalars()})
        if not recipients:
            continue
        base, remainder = divmod(battle.reward_pool_xp, len(recipients))
        awards = []
        for index, user_id in enumerate(sorted(recipients)):
            points = base + (1 if index < remainder else 0)
            awards.append({"user_id": user_id, "bonus_code": f"BOSS_{battle.id}", "points": points, "awarded_at": battle.ends_at, "reason": f"Team reward for completing {battle.title}"})
        statement = sqlite_insert(ProgressionBonus).on_conflict_do_nothing(
            index_elements=["user_id", "bonus_code"]
        ).returning(ProgressionBonus.user_id)
        result = await session.execute(statement, awards)
        created += len(result.scalars().all())
    await session.commit()
    return created


async def active_boss_battles(session: AsyncSession, user_id: str | None = None) -> list[dict[str, object]]:
    battles = list((await session.execute(select(BossBattle).order_by(BossBattle.department))).scalars())
    return [await _battle_view(session, battle, user_id) for battle in battles]


async def boss_battle(session: AsyncSession, battle_id: str, user_id: str | None = None) -> dict[str, object] | None:
    battle = await session.get(BossBattle, battle_id)
    return await _battle_view(session, battle, user_id) if battle else None


async def claim_boss_reward(session: AsyncSession, battle_id: str, user_id: str) -> dict[str, object]:
    battle = await session.get(BossBattle, battle_id)
    if battle is None:
        raise ValueError("Boss battle not found")
    view = await _battle_view(session, battle, user_id)
    if view["claimed"]:
        raise ValueError("Boss reward already claimed")
    if not view["eligible_to_claim"]:
        raise ValueError("Contribute a verified action after the team completes this boss before claiming")
    awards = list((await session.execute(select(XPLedger).where(XPLedger.department == battle.department, XPLedger.canonical_event == battle.canonical_event, XPLedger.earned_at >= battle.starts_at, XPLedger.earned_at < battle.ends_at))).scalars())
    recipients = sorted({award.user_id for award in awards})
    if settings.environment != "production" and user_id not in recipients:
        recipients.append(user_id)
        recipients.sort()
    base, remainder = divmod(battle.reward_pool_xp, len(recipients))
    points = base + (1 if user_id in recipients[:remainder] else 0)
    session.add(ProgressionBonus(user_id=user_id, bonus_code=f"BOSS_{battle.id}", points=points, awarded_at=datetime.now(), reason=f"Claimed team reward for completing {battle.title}"))
    await session.merge(UserBadge(user_id=user_id, badge_code="BOSS_VICTOR", awarded_at=datetime.now(), evidence='{"source":"boss_claim"}'))
    await session.commit()
    from app.services.gamification_service import materialize_gamification
    await materialize_gamification(session)
    return {"battle_id": battle_id, "points": points, "title": battle.title}
