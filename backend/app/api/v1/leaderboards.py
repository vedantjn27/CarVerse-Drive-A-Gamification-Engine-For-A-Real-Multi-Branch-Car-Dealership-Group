"""Authenticated scoped leaderboard APIs."""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, get_current_principal
from app.db.session import get_db_session
from app.services.leaderboard_service import (
    LeaderboardResult, LeaderboardScope, branch_leaderboard,
    department_leaderboard, individual_leaderboard,
)


router = APIRouter(prefix="/leaderboards", tags=["leaderboards"])


class LeaderboardResponse(BaseModel):
    scope: str
    anchor_at: datetime | None
    starts_at: datetime | None
    dealership_score: int
    entries: list[dict[str, Any]]


def _response(result: LeaderboardResult) -> LeaderboardResponse:
    return LeaderboardResponse(
        scope=result.scope,
        anchor_at=result.anchor_at,
        starts_at=result.starts_at,
        dealership_score=result.dealership_score,
        entries=result.entries,
    )


@router.get("/individual", response_model=LeaderboardResponse)
async def individuals(
    _: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    scope: LeaderboardScope = LeaderboardScope.ALL,
    department: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LeaderboardResponse:
    return _response(await individual_leaderboard(session, scope, department, limit, offset))


@router.get("/branch", response_model=LeaderboardResponse)
async def branches(
    _: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    scope: LeaderboardScope = LeaderboardScope.ALL,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LeaderboardResponse:
    return _response(await branch_leaderboard(session, scope, limit, offset))


@router.get("/department", response_model=LeaderboardResponse)
async def departments(
    _: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    scope: LeaderboardScope = LeaderboardScope.ALL,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LeaderboardResponse:
    return _response(await department_leaderboard(session, scope, limit, offset))
