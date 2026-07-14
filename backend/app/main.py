"""FastAPI application factory and process lifecycle."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.api.v1.ws import router as websocket_router
from app.core.config import settings
from app.db.session import AsyncSessionFactory, close_database, initialize_database
from app.services.ingestion_service import reset_schema_and_seed
from app.services.scoring_engine import score_all_events
from app.services.gamification_service import materialize_gamification
from app.services.quest_service import seed_quest_templates
from app.services.boss_battle_service import award_completed_boss_battles, materialize_boss_battles
from app.services.anomaly_service import scan_anomalies
from app.scheduler.scheduler import create_scheduler


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    scheduler = None
    if settings.auto_reseed_on_startup:
        summary = await reset_schema_and_seed(settings.resolved_data_directory)
        logger.info(
            "Organizer data reseed complete: locations=%d employees=%d events=%d",
            summary.locations.rows_inserted,
            summary.employees.rows_inserted,
            summary.events.rows_inserted,
        )
    else:
        await initialize_database()
    async with AsyncSessionFactory() as session:
        scoring = await score_all_events(session)
    logger.info(
        "Scoring replay complete: bookings=%d awards=%d xp=%d",
        scoring.bookings_processed,
        scoring.awards_inserted,
        scoring.total_xp,
    )
    async with AsyncSessionFactory() as session:
        gamification = await materialize_gamification(session)
        await seed_quest_templates(session)
        await materialize_boss_battles(session)
        boss_awards = await award_completed_boss_battles(session)
        if boss_awards:
            gamification = await materialize_gamification(session)
        anomalies = await scan_anomalies(session)
    logger.info(
        "Gamification materialization complete: users=%d badges=%d locations=%d anomalies=%d",
        gamification.users,
        gamification.badges_awarded,
        gamification.locations,
        anomalies,
    )
    if settings.scheduler_enabled and settings.environment != "test":
        scheduler = create_scheduler()
        scheduler.start()
        logger.info("Scheduler started with jobs: %s", [job.id for job in scheduler.get_jobs()])
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)
        await close_database()


def create_app() -> FastAPI:
    """Build a fully configured CarVerse API instance."""

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Backend API for the CarVerse Drive dealership gamification engine.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials="*" not in settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health_router)
    application.include_router(api_router)
    application.include_router(websocket_router)
    return application


app = create_app()
