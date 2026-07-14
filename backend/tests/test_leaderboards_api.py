"""Phase 3 scoped and normalized leaderboard API tests."""

from fastapi.testclient import TestClient

from tests.api_helpers import login_headers


def test_leaderboards_require_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/leaderboards/individual").status_code == 401


def test_individual_week_scope_anchors_to_latest_dataset_timestamp(
    client: TestClient,
) -> None:
    headers, _ = login_headers(client)
    response = client.get(
        "/api/v1/leaderboards/individual?scope=week&limit=10",
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["anchor_at"].startswith("2026-06-30")
    assert body["starts_at"].startswith("2026-06-29")
    assert body["entries"]


def test_branch_board_is_sorted_by_normalized_score(client: TestClient) -> None:
    headers, _ = login_headers(client)
    response = client.get("/api/v1/leaderboards/branch?scope=all", headers=headers)
    assert response.status_code == 200
    entries = response.json()["entries"]
    scores = [entry["normalized_score"] for entry in entries]
    assert scores == sorted(scores, reverse=True)
    assert all(entry["booking_attempts"] > 0 for entry in entries)


def test_department_board_contains_only_five_active_departments(
    client: TestClient,
) -> None:
    headers, _ = login_headers(client)
    response = client.get("/api/v1/leaderboards/department", headers=headers)
    assert response.status_code == 200
    departments = {entry["department"] for entry in response.json()["entries"]}
    assert departments == {"SALES", "FINANCE", "ACCOUNTS", "CUSTOMER CARE", "PDI"}

