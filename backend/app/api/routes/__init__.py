from .entries import router as entries_router
from .preferences import router as preferences_router  
from .health import router as health_router

__all__ = [
    "entries_router",
    "preferences_router",
    "health_router"
]