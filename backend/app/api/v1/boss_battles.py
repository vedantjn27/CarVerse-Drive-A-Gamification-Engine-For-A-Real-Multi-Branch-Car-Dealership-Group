"""Authenticated department boss-battle APIs."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, get_current_principal
from app.db.session import get_db_session
from app.services.boss_battle_service import active_boss_battles, boss_battle, claim_boss_reward

router = APIRouter(prefix="/boss-battles", tags=["boss battles"])


@router.get("/active")
async def active(principal: Annotated[Principal, Depends(get_current_principal)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, object]:
    return {"battles": await active_boss_battles(session, principal.employee_id)}


@router.get("/{battle_id}")
async def detail(battle_id: str, principal: Annotated[Principal, Depends(get_current_principal)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, object]:
    result = await boss_battle(session, battle_id, principal.employee_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Boss battle not found")
    return result


@router.post("/{battle_id}/claim")
async def claim(battle_id: str, principal: Annotated[Principal, Depends(get_current_principal)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, object]:
    try:
        return await claim_boss_reward(session, battle_id, principal.employee_id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
