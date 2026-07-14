"""Phase 3 authentication and user profile API tests."""

from fastapi.testclient import TestClient

from tests.api_helpers import login_headers


def test_invalid_login_is_rejected_without_identifying_the_bad_field(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"employee_id": "does-not-exist", "otp": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid employee ID or OTP"


def test_login_and_me_return_progress_without_sensitive_employee_fields(
    client: TestClient,
) -> None:
    headers, employee_id = login_headers(client)
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["employee_id"] == employee_id
    assert body["total_xp"] > 0
    assert 0 <= body["reputation"] <= 100
    assert "otp" not in body
    assert "mobile" not in body


def test_protected_user_endpoint_rejects_missing_token(client: TestClient) -> None:
    assert client.get("/api/v1/users/me").status_code == 401


def test_authenticated_user_can_view_another_employee_stats(client: TestClient) -> None:
    headers, employee_id = login_headers(client)
    response = client.get(f"/api/v1/users/{employee_id}/stats", headers=headers)
    assert response.status_code == 200
    assert response.json()["employee_id"] == employee_id

