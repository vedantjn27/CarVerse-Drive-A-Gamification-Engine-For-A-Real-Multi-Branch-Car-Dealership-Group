"""Authenticated API helpers backed by the seeded employee dataset."""

import sqlite3

from fastapi.testclient import TestClient

from app.core.config import BACKEND_ROOT


def login_headers(client: TestClient) -> tuple[dict[str, str], str]:
    with sqlite3.connect(BACKEND_ROOT / "data" / "test_carverse.db") as connection:
        employee_id, otp = connection.execute(
            """
            SELECT employee.id, employee.otp
            FROM employees AS employee
            JOIN user_stats AS stats ON stats.user_id = employee.id
            WHERE employee.status = 1
              AND employee.otp IS NOT NULL
              AND employee.otp <> ''
              AND stats.total_xp > 0
            ORDER BY stats.total_xp DESC
            LIMIT 1
            """
        ).fetchone()
    response = client.post(
        "/api/v1/auth/login",
        json={"employee_id": employee_id, "otp": otp},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}, employee_id
