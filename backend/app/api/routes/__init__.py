from .entries import router as entries_router
from .preferences import router as preferences_router  
from .health import router as health_router
from .stt import router as stt_router
from .hotkey import router as hotkey_router

__all__ = [
    "entries_router",
    "preferences_router",
    "health_router",
    "stt_router",
    "hotkey_router"
]