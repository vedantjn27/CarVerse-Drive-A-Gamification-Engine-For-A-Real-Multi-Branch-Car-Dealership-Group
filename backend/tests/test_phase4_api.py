"""Fast Phase 4 race-track, quest, and boss-battle integration tests."""

from fastapi.testclient import TestClient

from tests.api_helpers import login_headers


def test_booking_race_exposes_real_state_machine_progress(client: TestClient) -> None:
    headers, _ = login_headers(client)
    response = client.get("/api/v1/bookings/L1/B1", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "WON"
    assert body["current_stage"] == "VEHICLE_DELIVERED"
    assert body["track"][-1]["reached"] is True
    assert {item["canonical_event"] for item in body["milestones"]} >= {"BOOKING_CREATED", "VEHICLE_DELIVERED"}


def test_active_race_list_is_filterable_and_excludes_terminal_bookings(client: TestClient) -> None:
    headers, _ = login_headers(client)
    response = client.get("/api/v1/bookings/active?location_code=L1", headers=headers)
    assert response.status_code == 200
    entries = response.json()["entries"]
    assert {entry["enquiry_no"] for entry in entries} == {"B2", "B4"}
    assert all(entry["status"] == "ACTIVE" for entry in entries)


def test_completed_quest_can_be_claimed_once_and_updates_progression(client: TestClient) -> None:
    headers, _ = login_headers(client)
    before = client.get("/api/v1/users/me", headers=headers).json()["total_xp"]
    board = client.get("/api/v1/quests/me", headers=headers)
    assert board.status_code == 200
    delivery = next(item for item in board.json()["quests"] if item["code"] == "DELIVERY_DRIVE")
    assert delivery["completed"] is True
    claim = client.post("/api/v1/quests/DELIVERY_DRIVE/claim", headers=headers)
    assert claim.status_code == 200
    assert claim.json()["reward_xp"] == 40
    assert client.get("/api/v1/users/me", headers=headers).json()["total_xp"] == before + 40
    assert client.post("/api/v1/quests/DELIVERY_DRIVE/claim", headers=headers).status_code == 409


def test_boss_battles_have_real_ledger_progress_and_detail_route(client: TestClient) -> None:
    headers, _ = login_headers(client)
    response = client.get("/api/v1/boss-battles/active", headers=headers)
    assert response.status_code == 200
    battles = response.json()["battles"]
    assert len(battles) == 5
    sales = next(item for item in battles if item["department"] == "SALES")
    assert sales["progress"] == 3
    assert client.get(f"/api/v1/boss-battles/{sales['id']}", headers=headers).status_code == 200
