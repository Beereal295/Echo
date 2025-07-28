"""
Service coordinator to manage service dependencies and initialization
"""

import asyncio
import logging
from typing import Optional

from .stt import get_stt_service
from .hotkey import get_hotkey_service
from app.db.repositories import get_preferences_repository

logger = logging.getLogger(__name__)


class ServiceCoordinator:
    """Coordinates service initialization and dependencies"""
    
    def __init__(self):
        self.stt_service = None
        self.hotkey_service = None
        self.preferences_repo = None
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize all services with proper dependencies"""
        if self.initialized:
            logger.info("Services already initialized")
            return True
        
        try:
            logger.info("Starting service initialization...")
            
            # Initialize database repository
            self.preferences_repo = await get_preferences_repository()
            
            # Initialize STT service first
            self.stt_service = await get_stt_service()
            logger.info("STT service initialized")
            
            # Initialize hotkey service
            self.hotkey_service = await get_hotkey_service()
            logger.info("Hotkey service initialized")
            
            # Set up service dependencies
            self.hotkey_service.set_stt_service(self.stt_service)
            self.hotkey_service.set_preferences_repository(self.preferences_repo)
            
            # Set up callbacks
            self.hotkey_service.set_callbacks(
                on_start=self._on_recording_start,
                on_stop=self._on_recording_stop,
                on_error=self._on_recording_error
            )
            
            self.initialized = True
            logger.info("All services initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            return False
    
    def _on_recording_start(self):
        """Callback when recording starts via hotkey"""
        logger.info("Recording started via hotkey")
    
    def _on_recording_stop(self):
        """Callback when recording stops via hotkey"""
        logger.info("Recording stopped via hotkey")
    
    def _on_recording_error(self, error: str):
        """Callback when recording error occurs"""
        logger.error(f"Recording error via hotkey: {error}")
    
    async def cleanup(self):
        """Clean up all services"""
        try:
            if self.hotkey_service:
                self.hotkey_service.cleanup()
            
            if self.stt_service:
                self.stt_service.cleanup()
            
            self.initialized = False
            logger.info("All services cleaned up")
            
        except Exception as e:
            logger.error(f"Error during service cleanup: {e}")
    
    def get_status(self) -> dict:
        """Get status of all services"""
        return {
            "initialized": self.initialized,
            "stt_service": self.stt_service is not None,
            "hotkey_service": self.hotkey_service is not None,
            "preferences_repo": self.preferences_repo is not None,
            "stt_status": self.stt_service.get_state_info() if self.stt_service else None,
            "hotkey_status": self.hotkey_service.get_status() if self.hotkey_service else None
        }


# Global coordinator instance
_coordinator: Optional[ServiceCoordinator] = None


async def get_service_coordinator() -> ServiceCoordinator:
    """Get global service coordinator instance"""
    global _coordinator
    
    if _coordinator is None:
        _coordinator = ServiceCoordinator()
        await _coordinator.initialize()
    
    return _coordinator


async def ensure_services_initialized():
    """Ensure all services are initialized"""
    coordinator = await get_service_coordinator()
    return coordinator.initialized