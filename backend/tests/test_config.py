"""Phase 0 environment configuration tests."""

from app.core.config import settings


def test_active_departments_are_canonical_and_bounded() -> None:
    assert settings.active_department_names == (
        "SALES",
        "FINANCE",
        "ACCOUNTS",
        "CUSTOMER CARE",
        "PDI",
    )
    assert len(settings.active_department_names) <= 5


def test_cors_allows_every_origin_for_the_hackathon_backend() -> None:
    assert settings.cors_origins == ["*"]
