"""Authenticated individual weekly quest APIs."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, get_current_principal
from app.db.session import get_db_session
from app.services.gamification_service import materialize_gamification
from app.services.quest_service import claim_quest, quest_board
from app.services.notification_service import leaderboard_broadcaster

router = APIRouter(prefix="/quests", tags=["quests"])


@router.get("/me")
async def mine(principal: Annotated[Principal, Depends(get_current_principal)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, object]:
    return await quest_board(session, principal.employee_id)


@router.post("/{quest_code}/claim")
async def claim(quest_code: str, principal: Annotated[Principal, Depends(get_current_principal)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, object]:
    result = await claim_quest(session, principal.employee_id, quest_code)
    await leaderboard_broadcaster.publish("xp_gain", {"employee_id": principal.employee_id, "canonical_event": "QUEST_REWARD", "points": result["reward_xp"], "quest_code": quest_code})
    return result
