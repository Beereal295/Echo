"""
Service coordinator to manage service dependencies and initialization
"""

import asyncio
import logging
from typing import Optional

from .stt import get_stt_service
from .hotkey import get_hotkey_service
from .websocket import get_websocket_manager
from .patterns import PatternDetector
from app.db.repositories import get_preferences_repository

logger = logging.getLogger(__name__)


class ServiceCoordinator:
    """Coordinates service initialization and dependencies"""
    
    def __init__(self):
        self.stt_service = None
        self.hotkey_service = None
        self.websocket_manager = None
        self.preferences_repo = None
        self.pattern_detector = None
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
            
            # Initialize WebSocket manager
            self.websocket_manager = await get_websocket_manager()
            logger.info("WebSocket manager initialized")
            
            # Set up service dependencies
            self.hotkey_service.set_stt_service(self.stt_service)
            self.hotkey_service.set_preferences_repository(self.preferences_repo)
            
            # Set up WebSocket manager dependencies
            self.websocket_manager.set_stt_service(self.stt_service)
            self.websocket_manager.set_hotkey_service(self.hotkey_service)
            
            # Set up callbacks
            self.hotkey_service.set_callbacks(
                on_start=self._on_recording_start,
                on_stop=self._on_recording_stop,
                on_error=self._on_recording_error
            )
            
            # Set up STT service callbacks to WebSocket manager
            self.stt_service.set_callbacks(
                state_callback=self.websocket_manager.on_stt_state_change,
                transcription_callback=self.websocket_manager.on_transcription_result,
                error_callback=self.websocket_manager.on_stt_error
            )
            
            # Initialize pattern detector
            self.pattern_detector = PatternDetector()
            logger.info("Pattern detector initialized")
            
            # Refresh patterns on startup
            await self._refresh_patterns()
            
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
    
    async def _refresh_patterns(self):
        """Refresh patterns based on current threshold setting"""
        try:
            # Get pattern detection threshold from preferences
            threshold = await self.preferences_repo.get_value(
                "pattern_detection_threshold", default=30
            )
            
            # Check if threshold is met
            if await self.pattern_detector.check_threshold_met(threshold):
                logger.info(f"Pattern detection threshold met ({threshold} entries), refreshing patterns...")
                
                # Run pattern analysis
                patterns = await self.pattern_detector.analyze_entries(min_entries=threshold)
                logger.info(f"Pattern analysis complete, found {len(patterns)} patterns")
                
                # Mark pattern unlock as shown if this is the first time
                if not await self.preferences_repo.get_value("pattern_unlock_shown", default=False):
                    await self.preferences_repo.set_value(
                        "pattern_unlock_shown", True, "bool",
                        "Whether pattern unlock celebration was shown"
                    )
            else:
                logger.info(f"Pattern detection threshold not met (requires {threshold} entries)")
                
        except Exception as e:
            logger.error(f"Error refreshing patterns: {e}")
    
    async def cleanup(self):
        """Clean up all services"""
        try:
            if self.websocket_manager:
                await self.websocket_manager.cleanup()
            
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
            "websocket_manager": self.websocket_manager is not None,
            "preferences_repo": self.preferences_repo is not None,
            "pattern_detector": self.pattern_detector is not None,
            "stt_status": self.stt_service.get_state_info() if self.stt_service else None,
            "hotkey_status": self.hotkey_service.get_status() if self.hotkey_service else None,
            "websocket_status": self.websocket_manager.get_connection_stats() if self.websocket_manager else None
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