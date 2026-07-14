"""Phase 8 scheduler and Phase 9 packaging checks without full-data replay."""

import asyncio
from pathlib import Path

from sqlalchemy import func, select

from app.db.models import LeaderboardSnapshot
from app.db.session import AsyncSessionFactory
from app.scheduler.jobs import weekly_league_rollover
from app.scheduler.scheduler import create_scheduler


def test_scheduler_registers_exactly_the_four_operational_jobs() -> None:
    scheduler = create_scheduler()
    assert {job.id for job in scheduler.get_jobs()} == {
        "nightly_reingest", "nightly_quest_generation", "nightly_anomaly_scan", "weekly_league_rollover",
    }


def test_weekly_rollover_persists_snapshot_rows() -> None:
    async def run() -> int:
        await weekly_league_rollover()
        async with AsyncSessionFactory() as session:
            return (await session.scalar(select(func.count()).select_from(LeaderboardSnapshot))) or 0

    assert asyncio.run(run()) > 0


def test_render_blueprint_and_backend_start_files_are_present() -> None:
    root = Path(__file__).resolve().parents[2]
    blueprint = (root / "render.yaml").read_text(encoding="utf-8")
    assert "rootDir: backend" in blueprint
    assert "disk:" not in blueprint
    assert "uvicorn app.main:app --host 0.0.0.0 --port $PORT" in blueprint
    assert (root / "backend" / "Procfile").read_text(encoding="utf-8").startswith("web: uvicorn app.main:app")
    assert (root / "backend" / ".python-version").read_text(encoding="utf-8").strip() == "3.12.11"
