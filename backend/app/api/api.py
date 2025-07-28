from fastapi import APIRouter

from app.api.endpoints import entries, patterns, preferences, ollama, milestones, stt

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(entries.router, prefix="/entry", tags=["entries"])
api_router.include_router(patterns.router, prefix="/patterns", tags=["patterns"])
api_router.include_router(preferences.router, prefix="/preferences", tags=["preferences"])
api_router.include_router(ollama.router, prefix="/ollama", tags=["ollama"])
api_router.include_router(milestones.router, prefix="/milestones", tags=["milestones"])
api_router.include_router(stt.router, prefix="/stt", tags=["stt"])