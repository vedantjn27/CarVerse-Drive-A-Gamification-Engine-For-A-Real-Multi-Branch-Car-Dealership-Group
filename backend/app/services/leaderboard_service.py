"""Scoped individual, department, and normalized branch leaderboards."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Employee, Location, XPLedger


class LeaderboardScope(StrEnum):
    WEEK = "week"
    MONTH = "month"
    ALL = "all"


@dataclass(frozen=True, slots=True)
class LeaderboardResult:
    scope: str
    anchor_at: datetime | None
    starts_at: datetime | None
    dealership_score: int
    entries: list[dict]


async def _window(session: AsyncSession, scope: LeaderboardScope) -> tuple[datetime | None, datetime | None]:
    anchor = await session.scalar(select(func.max(XPLedger.earned_at)))
    if anchor is None or scope == LeaderboardScope.ALL:
        return anchor, None
    if scope == LeaderboardScope.WEEK:
        return anchor, datetime.combine(anchor.date() - timedelta(days=anchor.weekday()), datetime.min.time())
    return anchor, datetime(anchor.year, anchor.month, 1)


async def _ledger_rows(session: AsyncSession, scope: LeaderboardScope) -> tuple[datetime | None, datetime | None, list[XPLedger]]:
    anchor, start = await _window(session, scope)
    statement = select(XPLedger)
    if start is not None:
        statement = statement.where(XPLedger.earned_at >= start)
    return anchor, start, list((await session.execute(statement)).scalars())


async def individual_leaderboard(session: AsyncSession, scope: LeaderboardScope, department: str | None, limit: int, offset: int) -> LeaderboardResult:
    anchor, start, rows = await _ledger_rows(session, scope)
    employees = {item.id: item for item in (await session.execute(select(Employee))).scalars()}
    totals: dict[str, list[int]] = {}
    for row in rows:
        employee = employees.get(row.user_id)
        if employee is None or (department and employee.department != department.upper()):
            continue
        aggregate = totals.setdefault(row.user_id, [0, 0, 0])
        aggregate[0] += row.leaderboard_points
        aggregate[1] += row.awarded_points
        aggregate[2] += 1
    ordered = sorted(totals, key=lambda user_id: (-totals[user_id][0], -totals[user_id][1], user_id))
    entries = [{"rank": rank, "user_id": user_id, "name": employees[user_id].name, "department": employees[user_id].department, "location_code": employees[user_id].loc_code, "leaderboard_xp": totals[user_id][0], "lifetime_xp_in_scope": totals[user_id][1], "awards": totals[user_id][2]} for rank, user_id in enumerate(ordered, 1)]
    return LeaderboardResult(scope.value, anchor, start, sum(row.leaderboard_points for row in rows), entries[offset:offset + limit])


async def branch_leaderboard(session: AsyncSession, scope: LeaderboardScope, limit: int, offset: int) -> LeaderboardResult:
    anchor, start, rows = await _ledger_rows(session, scope)
    locations = {item.location_code: item for item in (await session.execute(select(Location))).scalars()}
    scores: dict[str, list] = defaultdict(lambda: [0, 0, set(), set()])
    for row in rows:
        if not row.location_code:
            continue
        item = scores[row.location_code]
        item[0] += row.leaderboard_points
        item[1] += row.awarded_points
        item[2].add(row.user_id)
        if row.enquiry_no:
            item[3].add(row.enquiry_no)
    ordered = sorted(scores, key=lambda code: (-(scores[code][0] / max(len(scores[code][3]), 1)), -scores[code][0], code))
    entries = []
    for rank, code in enumerate(ordered, 1):
        raw, lifetime, users, bookings = scores[code]
        location = locations.get(code)
        entries.append({"rank": rank, "location_code": code, "location_name": location.location_name if location else None, "outlet_type": location.outlet_type if location else None, "leaderboard_xp": raw, "lifetime_xp_in_scope": lifetime, "booking_attempts": len(bookings), "active_users": len(users), "normalized_score": round(raw / max(len(bookings), 1), 4)})
    return LeaderboardResult(scope.value, anchor, start, sum(row.leaderboard_points for row in rows), entries[offset:offset + limit])


async def department_leaderboard(session: AsyncSession, scope: LeaderboardScope, limit: int, offset: int) -> LeaderboardResult:
    anchor, start, rows = await _ledger_rows(session, scope)
    scores: dict[str, list] = defaultdict(lambda: [0, 0, set(), set()])
    for row in rows:
        if row.department not in settings.active_department_names:
            continue
        item = scores[row.department]
        item[0] += row.leaderboard_points
        item[1] += row.awarded_points
        item[2].add(row.user_id)
        if row.location_code and row.enquiry_no:
            item[3].add((row.location_code, row.enquiry_no))
    ordered = sorted(scores, key=lambda item: (-scores[item][0], item))
    entries = [{"rank": rank, "department": department, "leaderboard_xp": scores[department][0], "lifetime_xp_in_scope": scores[department][1], "active_users": len(scores[department][2]), "bookings_touched": len(scores[department][3]), "normalized_score": round(scores[department][0] / max(len(scores[department][3]), 1), 4)} for rank, department in enumerate(ordered, 1)]
    return LeaderboardResult(scope.value, anchor, start, sum(row.leaderboard_points for row in rows), entries[offset:offset + limit])
