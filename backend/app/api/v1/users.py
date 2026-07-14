"""Authenticated employee progression and badge APIs."""

import json
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, get_current_principal
from app.db.models import Badge, Employee, LevelTitle, UserBadge, UserStats
from app.db.session import get_db_session


router = APIRouter(prefix="/users", tags=["users"])


class BadgeResponse(BaseModel):
    code: str
    name: str
    description: str
    icon: str
    awarded_at: datetime
    evidence: dict[str, Any]


class UserProfileResponse(BaseModel):
    employee_id: str
    name: str | None
    designation: str | None
    department: str | None
    location_code: str | None
    role: str | None
    total_xp: int
    leaderboard_xp: int
    streak_bonus_xp: int
    level: int
    title: str
    current_level_xp: int
    next_level_xp: int
    current_streak: int
    longest_streak: int
    reputation: int
    total_awards: int
    milestone_awards: int
    deliveries: int
    clean_bookings: int
    fast_deliveries: int
    escalations_resolved: int
    cancellation_saves: int
    cross_dept_assists: int
    rework_discounted_awards: int
    all_time_rank: int | None
    department_rank: int | None
    location_rank: int | None
    last_earned_at: datetime | None
    badges: list[BadgeResponse]


async def _profile(session: AsyncSession, user_id: str) -> UserProfileResponse:
    employee = await session.get(Employee, user_id)
    stats = await session.get(UserStats, user_id)
    if employee is None or stats is None:
        raise HTTPException(status_code=404, detail="Employee stats not found")
    title = await session.get(LevelTitle, stats.title_code)
    badge_rows = (
        await session.execute(
            select(UserBadge, Badge)
            .join(Badge, Badge.code == UserBadge.badge_code)
            .where(UserBadge.user_id == user_id)
            .order_by(Badge.sort_order)
        )
    ).all()
    return UserProfileResponse(
        employee_id=employee.id, name=employee.name, designation=employee.designation,
        department=employee.department, location_code=employee.loc_code, role=employee.role_rights,
        total_xp=stats.total_xp, leaderboard_xp=stats.leaderboard_xp,
        streak_bonus_xp=stats.streak_bonus_xp,
        level=stats.level, title=title.display_name if title else stats.title_code,
        current_level_xp=stats.current_level_xp, next_level_xp=stats.next_level_xp,
        current_streak=stats.current_streak, longest_streak=stats.longest_streak,
        reputation=stats.reputation, total_awards=stats.total_awards,
        milestone_awards=stats.milestone_awards, deliveries=stats.deliveries,
        clean_bookings=stats.clean_bookings, fast_deliveries=stats.fast_deliveries,
        escalations_resolved=stats.escalations_resolved,
        cancellation_saves=stats.cancellation_saves,
        cross_dept_assists=stats.cross_dept_assists,
        rework_discounted_awards=stats.rework_discounted_awards,
        all_time_rank=stats.all_time_rank, department_rank=stats.department_rank,
        location_rank=stats.location_rank, last_earned_at=stats.last_earned_at,
        badges=[BadgeResponse(code=badge.code, name=badge.name, description=badge.description, icon=badge.icon, awarded_at=user_badge.awarded_at, evidence=json.loads(user_badge.evidence)) for user_badge, badge in badge_rows],
    )


@router.get("/me", response_model=UserProfileResponse)
async def me(
    principal: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserProfileResponse:
    return await _profile(session, principal.employee_id)


@router.get("/{user_id}/stats", response_model=UserProfileResponse)
async def user_stats(
    user_id: str,
    _: Annotated[Principal, Depends(get_current_principal)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserProfileResponse:
    return await _profile(session, user_id)
