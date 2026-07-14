"""APScheduler jobs for the disposable, auto-reseeded demo database."""

from __future__ import annotations

import json
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.core.config import settings
from app.db.models import LeaderboardSnapshot, ScoringRuleOverride, UserStats
from app.db.session import AsyncSessionFactory
from app.services.ai_feature_service import quest_flavour
from app.services.anomaly_service import scan_anomalies
from app.services.boss_battle_service import award_completed_boss_battles, materialize_boss_battles
from app.services.gamification_service import materialize_gamification
from app.services.ingestion_service import reset_schema_and_seed
from app.services.leaderboard_service import LeaderboardScope, branch_leaderboard, department_leaderboard, individual_leaderboard
from app.services.notification_service import leaderboard_broadcaster
from app.services.quest_service import seed_quest_templates
from app.services.scoring_engine import score_all_events

logger = logging.getLogger(__name__)


async def nightly_reingest() -> None:
    """Rebuild from the exact organizer files while preserving live tuning rows."""
    async with AsyncSessionFactory() as session:
        overrides = [{"canonical_event": row.canonical_event, "base_xp": row.base_xp, "updated_at": row.updated_at, "updated_by_user_id": row.updated_by_user_id} for row in (await session.execute(select(ScoringRuleOverride))).scalars()]
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
    await leaderboard_broadcaster.publish("leaderboard_rebuilt", {"events": summary.events.rows_inserted, "awards": scoring.awards_inserted, "anomalies": anomalies})
    logger.info("Nightly re-ingest complete: events=%d awards=%d anomalies=%d", summary.events.rows_inserted, scoring.awards_inserted, anomalies)


async def nightly_quest_generation() -> None:
    """Refresh cache-backed personalised quest flavour for active players."""
    async with AsyncSessionFactory() as session:
        users = list((await session.execute(select(UserStats.user_id).where(UserStats.total_awards > 0).order_by(UserStats.total_xp.desc()).limit(25))).scalars())
        for user_id in users:
            await quest_flavour(session, user_id)
    logger.info("Generated quest flavour for %d active players", len(users))


async def nightly_anomaly_scan() -> None:
    async with AsyncSessionFactory() as session:
        count = await scan_anomalies(session)
    logger.info("Nightly anomaly scan created %d open review flags", count)


async def weekly_league_rollover() -> None:
    """Freeze weekly board results before the next scheduled reporting period."""
    async with AsyncSessionFactory() as session:
        results = {
            "individual": await individual_leaderboard(session, LeaderboardScope.WEEK, None, 100, 0),
            "branch": await branch_leaderboard(session, LeaderboardScope.WEEK, 100, 0),
            "department": await department_leaderboard(session, LeaderboardScope.WEEK, 100, 0),
        }
        rows = []
        for board, result in results.items():
            if result.starts_at is None or result.anchor_at is None:
                continue
            for entry in result.entries:
                entity_key = str(entry.get("user_id") or entry.get("location_code") or entry.get("department"))
                rows.append({"snapshot_key": f"{result.starts_at.date().isoformat()}:{board}:{entity_key}", "period_start": result.starts_at, "period_end": result.anchor_at, "board": board, "rank": entry["rank"], "entity_key": entity_key, "leaderboard_xp": entry["leaderboard_xp"], "normalized_score": entry.get("normalized_score"), "payload_json": json.dumps(entry, default=str, sort_keys=True)})
        if rows:
            statement = sqlite_insert(LeaderboardSnapshot)
            excluded = statement.excluded
            await session.execute(statement.on_conflict_do_update(index_elements=["snapshot_key"], set_={column.name: getattr(excluded, column.name) for column in LeaderboardSnapshot.__table__.columns if column.name != "snapshot_key"}), rows)
            await session.commit()
    await leaderboard_broadcaster.publish("league_rollover", {"snapshots": len(rows)})
    logger.info("Weekly league rollover stored %d snapshot rows", len(rows))
