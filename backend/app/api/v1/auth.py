"""Demo-grade employee OTP authentication."""

import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, role_for_employee
from app.db.models import Employee
from app.db.session import get_db_session


router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    employee_id: str = Field(min_length=1, max_length=32)
    otp: str = Field(min_length=1, max_length=32)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    employee_id: str
    role: str


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    employee = await session.get(Employee, payload.employee_id.strip())
    valid = (
        employee is not None
        and employee.status == 1
        and employee.otp is not None
        and hmac.compare_digest(employee.otp, payload.otp.strip())
    )
    if not valid or employee is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid employee ID or OTP",
        )
    return TokenResponse(
        access_token=create_access_token(employee),
        expires_in_seconds=settings.jwt_expire_minutes * 60,
        employee_id=employee.id,
        role=role_for_employee(employee).value,
    )

