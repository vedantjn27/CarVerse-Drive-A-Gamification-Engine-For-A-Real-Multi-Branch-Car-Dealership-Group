"""Lifecycle wrapper for the in-process async scheduler."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.scheduler.jobs import nightly_anomaly_scan, nightly_quest_generation, nightly_reingest, weekly_league_rollover


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
    common = {"replace_existing": True, "coalesce": True, "max_instances": 1, "misfire_grace_time": 3600}
    scheduler.add_job(nightly_reingest, "cron", id="nightly_reingest", hour=settings.scheduler_nightly_hour, minute=settings.scheduler_nightly_minute, **common)
    scheduler.add_job(nightly_quest_generation, "cron", id="nightly_quest_generation", hour=settings.scheduler_nightly_hour, minute=(settings.scheduler_nightly_minute + 5) % 60, **common)
    scheduler.add_job(nightly_anomaly_scan, "cron", id="nightly_anomaly_scan", hour=settings.scheduler_nightly_hour, minute=(settings.scheduler_nightly_minute + 10) % 60, **common)
    scheduler.add_job(weekly_league_rollover, "cron", id="weekly_league_rollover", day_of_week=settings.scheduler_weekly_day, hour=settings.scheduler_nightly_hour, minute=(settings.scheduler_nightly_minute + 15) % 60, **common)
    return scheduler
