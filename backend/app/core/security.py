"""JWT issuance, validation, and demo-role authorization."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Employee
from app.db.session import get_db_session


class AppRole(StrEnum):
    AGENT = "AGENT"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


@dataclass(frozen=True, slots=True)
class Principal:
    employee_id: str
    role: AppRole


bearer = HTTPBearer(auto_error=False)


def role_for_employee(employee: Employee) -> AppRole:
    rights = (employee.role_rights or "").strip().upper()
    if rights in {"ADMIN", "SUPER ADMIN"}:
        return AppRole.ADMIN
    if rights in {"MANAGER", "TEAM LEADER", "TL"}:
        return AppRole.MANAGER
    return AppRole.AGENT


def create_access_token(employee: Employee) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": employee.id,
            "role": role_for_employee(employee).value,
            "iat": now,
            "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "typ": "access",
        },
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


async def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Principal:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise error
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
        employee_id = payload.get("sub")
        role = AppRole(payload.get("role"))
        if not employee_id or payload.get("typ") != "access":
            raise error
    except (InvalidTokenError, ValueError, TypeError) as exc:
        raise error from exc
    employee = await session.get(Employee, employee_id)
    if employee is None or employee.status != 1:
        raise error
    return Principal(employee_id=employee.id, role=role)


def require_roles(*roles: AppRole):
    async def dependency(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return principal
    return dependency

