from fastapi import APIRouter

from app.api.routes import (
    entries_router,
    preferences_router,
    health_router,
    stt_router,
    hotkey_router,
    websocket_router,
    ollama_router
)
from app.core.config import settings

# Create main API router
api_router = APIRouter(prefix=settings.API_V1_STR)

# Include all route modules
api_router.include_router(entries_router)
api_router.include_router(preferences_router)
api_router.include_router(health_router)
api_router.include_router(stt_router)
api_router.include_router(hotkey_router)
api_router.include_router(websocket_router)
api_router.include_router(ollama_router)