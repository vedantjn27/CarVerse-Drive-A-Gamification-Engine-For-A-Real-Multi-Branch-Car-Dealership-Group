"""ADMIN-only re-ingestion, anomaly review, and live scoring-rule controls."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.scoring_rules import CanonicalEvent
from app.core.security import AppRole, Principal, require_roles
from app.db.models import AnomalyReview, ScoringRuleOverride
from app.db.session import AsyncSessionFactory, get_db_session
from app.services.anomaly_service import scan_anomalies
from app.services.boss_battle_service import award_completed_boss_battles, materialize_boss_battles
from app.services.gamification_service import materialize_gamification
from app.services.ingestion_service import reset_schema_and_seed
from app.services.notification_service import leaderboard_broadcaster
from app.services.quest_service import seed_quest_templates
from app.services.scoring_engine import score_all_events

router = APIRouter(prefix="/admin", tags=["admin"])
Admin = Annotated[Principal, Depends(require_roles(AppRole.ADMIN))]


class RuleUpdate(BaseModel):
    canonical_event: CanonicalEvent
    base_xp: int = Field(ge=0, le=500)


class ResolveReview(BaseModel):
    resolution_note: str = Field(min_length=1, max_length=1000)


async def _rebuild(overrides: list[dict[str, object]]) -> dict[str, int]:
    summary = await reset_schema_and_seed(settings.resolved_data_directory)
    async with AsyncSessionFactory() as session:
        if overrides:
            statement = sqlite_insert(ScoringRuleOverride)
            excluded = statement.excluded
            await session.execute(statement.on_conflict_do_update(index_elements=["canonical_event"], set_={"base_xp": excluded.base_xp, "updated_at": excluded.updated_at, "updated_by_user_id": excluded.updated_by_user_id}), overrides)
            await session.commit()
        scoring = await score_all_events(session)
        await materialize_gamification(session)
        await seed_quest_templates(session)
        await materialize_boss_battles(session)
        await award_completed_boss_battles(session)
        await materialize_gamification(session)
        anomalies = await scan_anomalies(session)
    await leaderboard_broadcaster.publish("leaderboard_rebuilt", {"events": scoring.events_processed, "awards": scoring.awards_inserted})
    return {"locations": summary.locations.rows_inserted, "employees": summary.employees.rows_inserted, "events": summary.events.rows_inserted, "awards": scoring.awards_inserted, "anomalies": anomalies}


@router.post("/ingest")
async def ingest(_: Admin, session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, int]:
    overrides = [{"canonical_event": item.canonical_event, "base_xp": item.base_xp, "updated_at": item.updated_at, "updated_by_user_id": item.updated_by_user_id} for item in (await session.execute(select(ScoringRuleOverride))).scalars()]
    await session.rollback()
    return await _rebuild(overrides)


@router.get("/anomalies")
async def anomalies(_: Admin, session: Annotated[AsyncSession, Depends(get_db_session)], status: str = "OPEN") -> dict[str, object]:
    rows = list((await session.execute(select(AnomalyReview).where(AnomalyReview.status == status.upper()).order_by(AnomalyReview.detected_at.desc()))).scalars())
    return {"reviews": [{"id": row.id, "user_id": row.user_id, "department": row.department, "metric": row.metric, "metric_value": row.metric_value, "cohort_mean": row.cohort_mean, "cohort_stddev": row.cohort_stddev, "z_score": row.z_score, "threshold": row.threshold, "explanation": row.explanation, "status": row.status, "detected_at": row.detected_at, "resolution_note": row.resolution_note} for row in rows]}


@router.post("/anomalies/{review_id}/resolve")
async def resolve(review_id: int, payload: ResolveReview, principal: Admin, session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, object]:
    review = await session.get(AnomalyReview, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Anomaly review not found")
    review.status, review.resolution_note, review.resolved_by_user_id = "RESOLVED", payload.resolution_note, principal.employee_id
    review.resolved_at = datetime.now(UTC).replace(tzinfo=None)
    await session.commit()
    return {"id": review.id, "status": review.status}


@router.post("/scoring-rules")
async def tune_rule(payload: RuleUpdate, principal: Admin, session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, object]:
    existing = [{"canonical_event": item.canonical_event, "base_xp": item.base_xp, "updated_at": item.updated_at, "updated_by_user_id": item.updated_by_user_id} for item in (await session.execute(select(ScoringRuleOverride))).scalars() if item.canonical_event != payload.canonical_event.value]
    await session.rollback()
    existing.append({"canonical_event": payload.canonical_event.value, "base_xp": payload.base_xp, "updated_at": datetime.now(UTC).replace(tzinfo=None), "updated_by_user_id": principal.employee_id})
    result = await _rebuild(existing)
    return {"canonical_event": payload.canonical_event.value, "base_xp": payload.base_xp, "rebuild": result}
