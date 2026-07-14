"""Phase 3 progression, badge, and aggregate tests."""

import sqlite3
from datetime import date

from fastapi.testclient import TestClient

from app.core.config import BACKEND_ROOT
from app.services.gamification_service import _streaks, level_for_xp, xp_required_for_level


def test_level_curve_is_monotonic_and_starts_at_level_one() -> None:
    assert xp_required_for_level(1) == 0
    assert level_for_xp(0) == 1
    assert level_for_xp(xp_required_for_level(10)) == 10
    assert xp_required_for_level(11) > xp_required_for_level(10)


def test_streaks_require_consecutive_real_milestone_dates() -> None:
    days = {date(2026, 6, 27), date(2026, 6, 28), date(2026, 6, 30)}
    assert _streaks(days, date(2026, 6, 30)) == (1, 2)
    assert _streaks(days, date(2026, 7, 1)) == (0, 2)


def test_fast_materialization_reconciles_profiles_and_aggregates(
    client: TestClient,
) -> None:
    del client
    with sqlite3.connect(BACKEND_ROOT / "data" / "test_carverse.db") as connection:
        users = connection.execute("SELECT COUNT(*) FROM user_stats").fetchone()[0]
        badges = connection.execute("SELECT COUNT(*) FROM badges").fetchone()[0]
        locations = connection.execute("SELECT COUNT(*) FROM location_stats").fetchone()[0]
        bad_reputation = connection.execute(
            "SELECT COUNT(*) FROM user_stats WHERE reputation < 0 OR reputation > 100"
        ).fetchone()[0]
        empty_department_normalized = connection.execute(
            "SELECT COUNT(*) FROM department_stats WHERE bookings_touched = 0 AND normalized_score <> 0"
        ).fetchone()[0]
        progression_bonuses = connection.execute(
            "SELECT COUNT(*) FROM progression_bonuses"
        ).fetchone()[0]
        inconsistent_xp = connection.execute(
            """
            SELECT COUNT(*)
            FROM user_stats AS stats
            WHERE stats.total_xp <> stats.streak_bonus_xp + COALESCE((
                SELECT SUM(ledger.awarded_points)
                FROM xp_ledger AS ledger
                WHERE ledger.user_id = stats.user_id
            ), 0)
            """
        ).fetchone()[0]
    assert users == 7
    assert badges == 8
    assert locations == 2
    assert bad_reputation == 0
    assert empty_department_normalized == 0
    assert progression_bonuses > 0
    assert inconsistent_xp == 0
