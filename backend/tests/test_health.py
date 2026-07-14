"""Phase 0 application readiness tests."""

from fastapi.testclient import TestClient


def test_health_endpoint_reports_database_connection(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["service"] == "CarVerse Drive API"


def test_versioned_health_endpoint_is_available(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200


def test_wildcard_cors_does_not_enable_credential_sharing(
    client: TestClient,
) -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "https://any-frontend.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in response.headers

