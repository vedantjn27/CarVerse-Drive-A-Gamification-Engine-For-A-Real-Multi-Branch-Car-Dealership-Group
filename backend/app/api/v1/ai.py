"""Optional AI enrichment endpoints; all return deterministic fallbacks when offline."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, get_current_principal
from app.db.session import get_db_session
from app.services.ai_feature_service import anomaly_explanation, boss_flavour, nudge_for_user, quest_flavour, recap_for_target

router = APIRouter(prefix="/ai", tags=["AI enrichment"])


@router.get("/nudge/me")
async def nudge(principal: Annotated[Principal, Depends(get_current_principal)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, str]:
    return await nudge_for_user(session, principal.employee_id)


@router.get("/recap/{target}")
async def recap(target: str, _: Annotated[Principal, Depends(get_current_principal)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, str]:
    try:
        return await recap_for_target(session, target)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/quests/me")
async def quests(principal: Annotated[Principal, Depends(get_current_principal)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, object]:
    return await quest_flavour(session, principal.employee_id)


@router.get("/boss-battles/{battle_id}/flavour")
async def boss(battle_id: str, _: Annotated[Principal, Depends(get_current_principal)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, object]:
    result = await boss_flavour(session, battle_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Boss battle not found")
    return result


@router.get("/anomalies/{review_id}/explanation")
async def explain_anomaly(review_id: int, _: Annotated[Principal, Depends(get_current_principal)], session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, str]:
    result = await anomaly_explanation(session, review_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Anomaly review not found")
    return result
