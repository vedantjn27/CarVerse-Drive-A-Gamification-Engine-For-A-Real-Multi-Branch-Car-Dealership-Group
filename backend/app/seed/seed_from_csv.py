"""Command-line entrypoint for deterministic organizer CSV ingestion."""

import argparse
import asyncio
from pathlib import Path

from app.core.config import settings
from app.db.session import AsyncSessionFactory, close_database
from app.services.ingestion_service import ingest_all, reset_schema_and_seed
from app.services.scoring_engine import score_all_events
from app.services.gamification_service import materialize_gamification


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-directory",
        type=Path,
        default=settings.resolved_data_directory,
        help="Directory containing the three organizer CSV files.",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Keep the schema and idempotently insert only missing source rows.",
    )
    return parser.parse_args()


async def _run() -> None:
    arguments = _arguments()
    data_directory = arguments.data_directory.resolve()
    try:
        if arguments.no_reset:
            async with AsyncSessionFactory() as session:
                summary = await ingest_all(session, data_directory)
        else:
            summary = await reset_schema_and_seed(data_directory)

        async with AsyncSessionFactory() as session:
            scoring = await score_all_events(session)
        async with AsyncSessionFactory() as session:
            gamification = await materialize_gamification(session)

        for item in summary.files:
            print(
                f"{item.filename}: read={item.rows_read}, "
                f"inserted={item.rows_inserted}, skipped={item.rows_skipped}"
            )
        print(
            f"Total: read={summary.total_rows_read}, "
            f"inserted={summary.total_rows_inserted}, "
            f"skipped={summary.total_rows_skipped}"
        )
        print(
            f"Scoring: events={scoring.events_processed}, "
            f"bookings={scoring.bookings_processed}, "
            f"awards_inserted={scoring.awards_inserted}, xp={scoring.total_xp}"
        )
        for canonical_event, count in scoring.event_counts.items():
            print(f"  {canonical_event}: {count} awards")
        print(
            f"Gamification: users={gamification.users}, "
            f"users_with_xp={gamification.users_with_xp}, "
            f"badges={gamification.badges_awarded}, "
            f"departments={gamification.departments}, "
            f"locations={gamification.locations}"
        )
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(_run())
