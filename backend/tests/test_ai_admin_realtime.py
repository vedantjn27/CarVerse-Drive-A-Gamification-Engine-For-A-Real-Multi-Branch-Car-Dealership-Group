"""Phases 5-7: deterministic AI fallback, controls, and realtime feed tests."""

from fastapi.testclient import TestClient

from app.services.notification_service import leaderboard_broadcaster
from tests.api_helpers import login_headers


def test_ai_endpoints_use_cached_deterministic_fallback_without_provider_keys(client: TestClient) -> None:
    headers, _ = login_headers(client)
    first = client.get("/api/v1/ai/nudge/me", headers=headers)
    assert first.status_code == 200
    assert first.json()["provider"] == "deterministic"
    assert first.json()["cached"] == "false"
    second = client.get("/api/v1/ai/nudge/me", headers=headers)
    assert second.json()["cached"] == "true"
    assert client.get("/api/v1/ai/recap/SALES", headers=headers).status_code == 200
    quests = client.get("/api/v1/ai/quests/me", headers=headers)
    assert quests.status_code == 200
    assert quests.json()["dynamic_quests"]
    assert all("completion_criteria" in item for item in quests.json()["dynamic_quests"])


def test_admin_controls_are_role_gated_and_review_routes_are_human_only(client: TestClient) -> None:
    headers, _ = login_headers(client)
    assert client.get("/api/v1/admin/anomalies", headers=headers).status_code == 403
    admin = client.post("/api/v1/auth/login", json={"employee_id": "admin-1", "otp": "otp-admin-1"})
    assert admin.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin.json()['access_token']}"}
    assert client.get("/api/v1/admin/anomalies", headers=admin_headers).status_code == 200
    assert client.post("/api/v1/admin/anomalies/999/resolve", headers=admin_headers, json={"resolution_note": "Checked by manager"}).status_code == 404


def test_websocket_requires_jwt_and_receives_broadcast_events(client: TestClient) -> None:
    headers, _ = login_headers(client)
    token = headers["Authorization"].split(" ", 1)[1]
    with client.websocket_connect(f"/ws/leaderboard?token={token}") as socket:
        assert socket.receive_json()["type"] == "connected"
        import asyncio
        asyncio.run(leaderboard_broadcaster.publish("xp_gain", {"user_id": "sales-1", "points": 20}))
        message = socket.receive_json()
        assert message == {"type": "xp_gain", "payload": {"user_id": "sales-1", "points": 20}}
