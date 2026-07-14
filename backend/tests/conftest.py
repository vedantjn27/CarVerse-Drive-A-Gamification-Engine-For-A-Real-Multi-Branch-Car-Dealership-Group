"""Fast integration fixtures; full CSV replay is explicitly marked separately."""

import asyncio
import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

# These values must be set before importing application settings and its engine.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test_carverse.db"
os.environ["AUTO_RESEED_ON_STARTUP"] = "false"
os.environ["ENVIRONMENT"] = "test"
os.environ["MISTRAL_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["SCHEDULER_ENABLED"] = "false"

from app.main import app
from tests.fast_seed import seed_fast_database


@pytest.fixture(scope="session", autouse=True)
def seeded_test_database() -> Iterator[None]:
    asyncio.run(seed_fast_database())
    yield


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """Start the API once against a compact deterministic test database."""

    with TestClient(app) as test_client:
        yield test_client
