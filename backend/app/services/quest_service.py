"""Deterministic weekly quests backed only by canonical ledger events."""

from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Employee, ProgressionBonus, QuestTemplate, UserQuestClaim, XPLedger
from app.seed.seed_gameplay import QUEST_TEMPLATES


def week_window(anchor: datetime) -> tuple[datetime, datetime]:
    start = (anchor - timedelta(days=anchor.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=7)


async def seed_quest_templates(session: AsyncSession) -> None:
    statement = sqlite_insert(QuestTemplate)
    excluded = statement.excluded
    await session.execute(statement.on_conflict_do_update(index_elements=["code"], set_={column.name: getattr(excluded, column.name) for column in QuestTemplate.__table__.columns if column.name != "code"}), list(QUEST_TEMPLATES))
    await session.commit()


async def quest_board(session: AsyncSession, user_id: str) -> dict[str, object]:
    employee = await session.get(Employee, user_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    anchor = await session.scalar(select(func.max(XPLedger.earned_at)))
    if anchor is None:
        raise HTTPException(status_code=409, detail="No scored activity is available")
    starts_at, ends_at = week_window(anchor)
    templates = list((await session.execute(select(QuestTemplate).where((QuestTemplate.department.is_(None)) | (QuestTemplate.department == employee.department)).order_by(QuestTemplate.sort_order))).scalars())
    rows = []
    for template in templates:
        progress = await session.scalar(select(func.count(XPLedger.id)).where(XPLedger.user_id == user_id, XPLedger.canonical_event == template.canonical_event, XPLedger.earned_at >= starts_at, XPLedger.earned_at < ends_at)) or 0
        claim = await session.get(UserQuestClaim, {"user_id": user_id, "quest_code": template.code, "period_start": starts_at})
        rows.append({"code": template.code, "title": template.title, "description": template.description, "canonical_event": template.canonical_event, "progress": progress, "target_count": template.target_count, "reward_xp": template.reward_xp, "completed": progress >= template.target_count, "claimed": claim is not None})
    return {"anchor_at": anchor, "starts_at": starts_at, "ends_at": ends_at, "quests": rows}


async def claim_quest(session: AsyncSession, user_id: str, quest_code: str) -> dict[str, object]:
    board = await quest_board(session, user_id)
    quest = next((item for item in board["quests"] if item["code"] == quest_code), None)
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not available to this employee")
    if not quest["completed"]:
        raise HTTPException(status_code=409, detail="Quest is not complete")
    if quest["claimed"]:
        raise HTTPException(status_code=409, detail="Quest reward already claimed")
    starts_at = board["starts_at"]
    claimed_at = board["anchor_at"]
    template = await session.get(QuestTemplate, quest_code)
    assert template is not None
    session.add(UserQuestClaim(user_id=user_id, quest_code=quest_code, period_start=starts_at, claimed_at=claimed_at, reward_xp=template.reward_xp))
    await session.execute(sqlite_insert(ProgressionBonus).on_conflict_do_nothing(index_elements=["user_id", "bonus_code"]), [{"user_id": user_id, "bonus_code": f"QUEST_{starts_at.date().isoformat()}_{quest_code}", "points": template.reward_xp, "awarded_at": claimed_at, "reason": f"Claimed completed quest: {template.title}"}])
    await session.commit()
    # A claimed reward is a persisted progression bonus, so refresh the
    # materialized profile/leaderboard views immediately for live UI updates.
    from app.services.gamification_service import materialize_gamification
    await materialize_gamification(session)
    return {"quest_code": quest_code, "reward_xp": template.reward_xp, "claimed_at": claimed_at}
