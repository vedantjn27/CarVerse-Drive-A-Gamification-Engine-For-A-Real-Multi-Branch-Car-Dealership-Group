"""Application and database readiness endpoints."""

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db_session


router = APIRouter(tags=["health"])
PROCESS_STARTED_AT = datetime.now(UTC)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str
    database: Literal["connected"]
    timestamp: datetime
    process_started_at: datetime


@router.get("/health", response_model=HealthResponse, summary="Check API readiness")
async def health_check(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> HealthResponse:
    """Return healthy only when both the API and database are reachable."""

    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from exc

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
        database="connected",
        timestamp=datetime.now(UTC),
        process_started_at=PROCESS_STARTED_AT,
    )
