"""Full organizer-data ingestion and normalization verification."""

import asyncio
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import BACKEND_ROOT, settings
from app.services.gamification_service import materialize_gamification
from app.services.boss_battle_service import award_completed_boss_battles, materialize_boss_battles
from app.services.quest_service import seed_quest_templates
from app.services.anomaly_service import scan_anomalies
from app.services.ingestion_service import (
    EMPLOYEE_FILE,
    EVENT_FILE,
    LOCATION_FILE,
    ingest_all,
    normalize_action_code,
    normalize_department,
    reset_schema_and_seed,
)
from app.services.scoring_engine import score_all_events
from app.services.notification_service import leaderboard_broadcaster
from app.scheduler.jobs import weekly_league_rollover


pytestmark = pytest.mark.full_data


EXPECTED_COUNTS = {
    "locations": 41,
    "employees": 6_037,
    "raw_events": 170_162,
}


def _database() -> sqlite3.Connection:
    connection = sqlite3.connect(BACKEND_ROOT / "data" / "test_carverse.db")
    connection.row_factory = sqlite3.Row
    return connection


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@pytest.fixture(scope="module", autouse=True)
def full_dataset() -> None:
    async def seed() -> None:
        await reset_schema_and_seed(settings.resolved_data_directory)
        test_engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        try:
            async with session_factory() as session:
                await score_all_events(session)
                await materialize_gamification(session)
                await seed_quest_templates(session)
                await materialize_boss_battles(session)
                await award_completed_boss_battles(session)
                await materialize_gamification(session)
                await scan_anomalies(session)
        finally:
            await test_engine.dispose()

    asyncio.run(seed())


def test_full_dataset_ingestion_matches_supplied_csv_counts(
    client: TestClient,
) -> None:
    del client
    with _database() as connection:
        actual = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in EXPECTED_COUNTS
        }

    assert actual == EXPECTED_COUNTS


def test_deployed_csv_copies_are_identical_to_organizer_files(
    client: TestClient,
) -> None:
    del client
    organizer_directory = settings.resolved_data_directory.parents[1] / "carverse files"
    for filename in (LOCATION_FILE, EMPLOYEE_FILE, EVENT_FILE):
        assert _sha256(settings.resolved_data_directory / filename) == _sha256(
            organizer_directory / filename
        )


def test_known_noisy_action_families_normalize_and_preserve_raw_values(
    client: TestClient,
) -> None:
    del client
    with _database() as connection:
        documents_other = connection.execute(
            "SELECT COUNT(*) FROM raw_events WHERE action_code = 'DOCUMENTS_OTHER'"
        ).fetchone()[0]
        misspelled_registration = connection.execute(
            """
            SELECT COUNT(*)
            FROM raw_events
            WHERE (action_code_raw LIKE 'RGISTRATION%'
                   OR action_code_raw LIKE 'REGISTARTION%')
              AND action_code LIKE 'REGISTRATION%'
            """
        ).fetchone()[0]
        all_rows_containing_registration_misspelling = connection.execute(
            """
            SELECT COUNT(*)
            FROM raw_events
            WHERE action_code_raw LIKE '%RGISTRATION%'
               OR action_code_raw LIKE '%REGISTARTION%'
            """
        ).fetchone()[0]
        document_text_containing_misspelling = connection.execute(
            """
            SELECT COUNT(*)
            FROM raw_events
            WHERE (action_code_raw LIKE '%RGISTRATION%'
                   OR action_code_raw LIKE '%REGISTARTION%')
              AND action_code = 'DOCUMENTS_OTHER'
            """
        ).fetchone()[0]
        raw_variant = connection.execute(
            """
            SELECT action_code_raw
            FROM raw_events
            WHERE action_code = 'DOCUMENTS_OTHER'
              AND action_code_raw <> 'DOCUMENTS_OTHER'
            LIMIT 1
            """
        ).fetchone()

    assert documents_other == 23_251
    assert all_rows_containing_registration_misspelling == 5_938
    assert misspelled_registration == 5_937
    assert document_text_containing_misspelling == 1
    assert raw_variant is not None


def test_booking_nulls_and_relational_references_match_source_quality(
    client: TestClient,
) -> None:
    del client
    with _database() as connection:
        login_context_rows = connection.execute(
            """
            SELECT COUNT(*)
            FROM raw_events
            WHERE enquiry_no_raw = '-'
              AND location_code_raw = '-'
              AND enquiry_no IS NULL
              AND location_code IS NULL
            """
        ).fetchone()[0]
        orphan_users = connection.execute(
            """
            SELECT COUNT(*)
            FROM raw_events AS event
            LEFT JOIN employees AS employee ON employee.id = event.user_id
            WHERE employee.id IS NULL
            """
        ).fetchone()[0]
        orphan_event_locations = connection.execute(
            """
            SELECT COUNT(*)
            FROM raw_events AS event
            LEFT JOIN locations AS location
              ON location.location_code = event.location_code
            WHERE event.location_code IS NOT NULL
              AND location.location_code IS NULL
            """
        ).fetchone()[0]
        employees_with_unexported_home_locations = connection.execute(
            """
            SELECT COUNT(*)
            FROM employees AS employee
            LEFT JOIN locations AS location
              ON location.location_code = employee.loc_code
            WHERE employee.loc_code IS NOT NULL
              AND location.location_code IS NULL
            """
        ).fetchone()[0]

    assert login_context_rows == 27_801
    assert orphan_users == 0
    assert orphan_event_locations == 0
    assert employees_with_unexported_home_locations == 4_636


def test_normalizers_do_not_invent_action_codes() -> None:
    assert normalize_action_code(" RGISTRATION_CREATED_EDP ") == (
        "REGISTRATION_CREATED_EDP"
    )
    assert normalize_action_code("REGISTARTION_ESCALATED") == (
        "REGISTRATION_ESCALATED"
    )
    assert normalize_action_code("documents_other - Delivery Photos") == (
        "DOCUMENTS_OTHER"
    )
    assert normalize_action_code("DOCUMENTS_PANIC BUTTON") == (
        "DOCUMENTS_PANIC BUTTON"
    )
    assert normalize_department("ccm") == "CUSTOMER CARE"
    assert normalize_department(" rto ") == "RTO / REGN TEAM"


def test_reingesting_every_source_row_does_not_create_duplicates(
    client: TestClient,
) -> None:
    del client

    async def reingest() -> tuple[int, int, int]:
        test_engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        session_factory = async_sessionmaker(
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        try:
            async with session_factory() as session:
                summary = await ingest_all(
                    session,
                    settings.resolved_data_directory,
                    batch_size=settings.ingest_batch_size,
                )
                scoring = await score_all_events(session)
                return (
                    summary.total_rows_inserted,
                    summary.total_rows_skipped,
                    scoring.awards_inserted,
                )
        finally:
            await test_engine.dispose()

    inserted, skipped, scoring_inserted = asyncio.run(reingest())
    assert inserted == 0
    assert skipped == sum(EXPECTED_COUNTS.values())
    assert scoring_inserted == 0


def test_full_scoring_replay_has_one_delivery_per_won_booking(
    client: TestClient,
) -> None:
    del client
    with _database() as connection:
        won = connection.execute(
            "SELECT COUNT(*) FROM bookings WHERE status = 'WON'"
        ).fetchone()[0]
        deliveries = connection.execute(
            "SELECT COUNT(*) FROM xp_ledger WHERE canonical_event = 'VEHICLE_DELIVERED'"
        ).fetchone()[0]
        duplicate_keys = connection.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT dedupe_key FROM xp_ledger
                GROUP BY dedupe_key HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]
        booking_count = connection.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]

    assert booking_count == 3_800
    assert won == 1_578
    assert deliveries == won
    assert duplicate_keys == 0


def test_full_data_api_scheduler_websocket_and_admin_smoke(client: TestClient) -> None:
    with _database() as connection:
        employee_id, otp = connection.execute(
            """
            SELECT employee.id, employee.otp
            FROM employees AS employee
            JOIN user_stats AS stats ON stats.user_id = employee.id
            WHERE employee.status = 1 AND employee.otp IS NOT NULL AND employee.otp <> ''
            ORDER BY stats.total_xp DESC, employee.id
            LIMIT 1
            """
        ).fetchone()
        location_code, enquiry_no = connection.execute(
            "SELECT location_code, enquiry_no FROM bookings WHERE status = 'ACTIVE' ORDER BY last_event_at DESC LIMIT 1"
        ).fetchone()
        admin_id, admin_otp = connection.execute(
            """
            SELECT id, otp FROM employees
            WHERE status = 1 AND otp IS NOT NULL AND otp <> ''
              AND UPPER(COALESCE(role_rights, '')) IN ('ADMIN', 'SUPER ADMIN')
            ORDER BY id LIMIT 1
            """
        ).fetchone()

    login = client.post("/api/v1/auth/login", json={"employee_id": employee_id, "otp": otp})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/users/me", headers=headers).status_code == 200
    assert client.get(f"/api/v1/users/{employee_id}/stats", headers=headers).status_code == 200
    for board in ("individual", "branch", "department"):
        assert client.get(f"/api/v1/leaderboards/{board}?scope=week", headers=headers).status_code == 200
    race = client.get(f"/api/v1/bookings/{location_code}/{enquiry_no}", headers=headers)
    assert race.status_code == 200 and race.json()["track"]
    assert client.get("/api/v1/bookings/active?limit=5", headers=headers).status_code == 200
    assert client.get("/api/v1/quests/me", headers=headers).status_code == 200
    bosses = client.get("/api/v1/boss-battles/active", headers=headers)
    assert bosses.status_code == 200 and len(bosses.json()["battles"]) == 5
    battle_id = bosses.json()["battles"][0]["id"]
    assert client.get(f"/api/v1/boss-battles/{battle_id}", headers=headers).status_code == 200
    assert client.get("/api/v1/ai/nudge/me", headers=headers).status_code == 200
    assert client.get("/api/v1/ai/recap/SALES", headers=headers).status_code == 200
    ai_quests = client.get("/api/v1/ai/quests/me", headers=headers)
    assert ai_quests.status_code == 200 and ai_quests.json()["dynamic_quests"]
    assert client.get(f"/api/v1/ai/boss-battles/{battle_id}/flavour", headers=headers).status_code == 200

    with client.websocket_connect(f"/ws/leaderboard?token={login.json()['access_token']}") as socket:
        assert socket.receive_json()["type"] == "connected"
        asyncio.run(leaderboard_broadcaster.publish("rank_change", {"user_id": employee_id, "rank": 1}))
        assert socket.receive_json()["type"] == "rank_change"

    async def snapshot() -> None:
        await weekly_league_rollover()

    asyncio.run(snapshot())
    with _database() as connection:
        assert connection.execute("SELECT COUNT(*) FROM leaderboard_snapshots").fetchone()[0] > 0

    admin_login = client.post("/api/v1/auth/login", json={"employee_id": admin_id, "otp": admin_otp})
    assert admin_login.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    assert client.get("/api/v1/admin/anomalies", headers=admin_headers).status_code == 200


def test_live_scoring_rule_tune_replays_full_data_for_admin(client: TestClient) -> None:
    with _database() as connection:
        admin_id, admin_otp = connection.execute(
            """
            SELECT id, otp FROM employees
            WHERE status = 1 AND otp IS NOT NULL AND otp <> ''
              AND UPPER(COALESCE(role_rights, '')) IN ('ADMIN', 'SUPER ADMIN')
            ORDER BY id LIMIT 1
            """
        ).fetchone()
    login = client.post("/api/v1/auth/login", json={"employee_id": admin_id, "otp": admin_otp})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = client.post("/api/v1/admin/scoring-rules", headers=headers, json={"canonical_event": "FOLLOW_UP_LOGGED", "base_xp": 2})
    assert response.status_code == 200
    assert response.json()["base_xp"] == 2
    assert response.json()["rebuild"]["events"] == 170_162


def test_two_full_cold_reseeds_produce_identical_materialized_state() -> None:
    async def cold_reseed_fingerprint() -> tuple[tuple[int, ...], list[tuple[object, ...]], list[tuple[object, ...]]]:
        await reset_schema_and_seed(settings.resolved_data_directory)
        test_engine = create_async_engine(settings.database_url)
        session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with session_factory() as session:
                await score_all_events(session)
                await materialize_gamification(session)
                await seed_quest_templates(session)
                await materialize_boss_battles(session)
                await award_completed_boss_battles(session)
                await materialize_gamification(session)
                await scan_anomalies(session)
        finally:
            await test_engine.dispose()
        with _database() as connection:
            counts = tuple(
                connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("raw_events", "bookings", "xp_ledger", "user_stats", "progression_bonuses", "user_badges", "boss_battles", "anomaly_reviews")
            )
            rows = [tuple(row) for row in connection.execute(
                """
                SELECT user_id, total_xp, leaderboard_xp, level, reputation,
                       all_time_rank, department_rank, location_rank
                FROM user_stats ORDER BY user_id
                """
            ).fetchall()]
            bonuses = [tuple(row) for row in connection.execute(
                "SELECT user_id, bonus_code, points FROM progression_bonuses ORDER BY user_id, bonus_code"
            ).fetchall()]
        return counts, rows, bonuses

    first = asyncio.run(cold_reseed_fingerprint())
    second = asyncio.run(cold_reseed_fingerprint())
    assert first[0] == second[0]
    assert first[1] == second[1], next(
        (f"first differing user stats: {left!r} != {right!r}" for left, right in zip(first[1], second[1], strict=True) if left != right),
        "user stat row counts differ",
    )
    assert first[2] == second[2], next(
        (f"first differing progression bonus: {left!r} != {right!r}" for left, right in zip(first[2], second[2], strict=True) if left != right),
        "progression bonus row counts differ",
    )
