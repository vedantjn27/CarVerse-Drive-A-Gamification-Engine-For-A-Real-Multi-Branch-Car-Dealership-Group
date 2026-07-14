"""Authenticated realtime leaderboard feed for the current disposable instance."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import jwt
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Employee
from app.db.session import AsyncSessionFactory
from app.services.notification_service import leaderboard_broadcaster

router = APIRouter()


async def _valid_employee_id(token: str | None) -> str | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=[settings.jwt_algorithm], issuer=settings.jwt_issuer, audience=settings.jwt_audience)
        user_id = payload.get("sub")
        if not user_id or payload.get("typ") != "access":
            return None
    except (InvalidTokenError, TypeError, ValueError):
        return None
    async with AsyncSessionFactory() as session:
        employee = await session.get(Employee, user_id)
        return employee.id if employee is not None and employee.status == 1 else None


@router.websocket("/ws/leaderboard")
async def leaderboard(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if await _valid_employee_id(token) is None:
        await websocket.close(code=1008)
        return
    await leaderboard_broadcaster.connect(websocket)
    try:
        await websocket.send_json({"type": "connected", "payload": {"message": "Leaderboard feed connected"}})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await leaderboard_broadcaster.disconnect(websocket)
