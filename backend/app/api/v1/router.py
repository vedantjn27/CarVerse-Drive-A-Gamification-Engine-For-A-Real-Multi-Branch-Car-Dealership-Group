"""Version 1 route composition."""

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.ai import router as ai_router
from app.api.v1.bookings import router as bookings_router
from app.api.v1.boss_battles import router as boss_battles_router
from app.api.v1.leaderboards import router as leaderboards_router
from app.api.v1.users import router as users_router
from app.api.v1.quests import router as quests_router
from app.api.v1.demo import router as demo_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(leaderboards_router)
api_router.include_router(bookings_router)
api_router.include_router(quests_router)
api_router.include_router(boss_battles_router)
api_router.include_router(demo_router)
api_router.include_router(ai_router)
api_router.include_router(admin_router)
