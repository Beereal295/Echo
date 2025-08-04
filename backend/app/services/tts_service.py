"""
TTS Service for text-to-speech synthesis using piper-tts.

This service handles:
- Loading the piper-tts voice model
- Generating speech audio from text
- Streaming audio output for fast response times
"""

import asyncio
import logging
import wave
import io
from typing import Optional, Union, AsyncGenerator
from pathlib import Path

from piper import PiperVoice

logger = logging.getLogger(__name__)


class TTSService:
    """Service for text-to-speech synthesis using piper-tts."""
    
    def __init__(self):
        """Initialize the TTS service."""
        self.voice: Optional[PiperVoice] = None
        self._model_loading_lock = asyncio.Lock()
        self._is_initialized = False
        
        # Model file path
        self.model_path = Path("D:/AI works/Softwares/Created by me/echo/backend/STT_MODEL/en_US-hfc_female-medium.onnx")
        
        # Audio configuration from the voice model
        self.sample_rate = 22050
        self.sample_width = 2  # 16-bit audio
        self.channels = 1  # Mono
        
        logger.info(f"Initializing TTSService with model: {self.model_path}")
    
    async def initialize(self) -> None:
        """Initialize the piper-tts model if not already loaded."""
        if self._is_initialized:
            return
        
        async with self._model_loading_lock:
            if self._is_initialized:
                return
            
            try:
                logger.info("Loading piper-tts model...")
                
                # Check if model file exists
                if not self.model_path.exists():
                    raise FileNotFoundError(f"Model file not found: {self.model_path}")
                
                # Load model in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                self.voice = await loop.run_in_executor(
                    None,
                    PiperVoice.load,
                    str(self.model_path)
                )
                
                self._is_initialized = True
                logger.info("Piper-TTS model loaded successfully")
                
            except Exception as e:
                logger.error(f"Failed to load piper-tts model: {e}")
                raise
    
    async def synthesize_speech(
        self, 
        text: str, 
        stream: bool = True
    ) -> Union[bytes, AsyncGenerator[bytes, None]]:
        """
        Synthesize speech from text using piper-tts.
        
        Args:
            text: Text to convert to speech (already cleaned by ChatModal)
            stream: Whether to stream audio chunks for faster response
            
        Returns:
            Audio data as bytes or async generator of audio chunks
        """
        await self.initialize()
        
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            logger.info(f"Synthesizing speech for text: '{text[:50]}...' (stream={stream})")
            
            if stream:
                return self._synthesize_streaming(text)
            else:
                return await self._synthesize_complete(text)
                
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            raise
    
    async def _synthesize_complete(self, text: str) -> bytes:
        """Synthesize complete audio file using piper-tts."""
        try:
            # Create WAV buffer
            wav_buffer = io.BytesIO()
            
            # Run synthesis in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._synthesize_wav_sync,
                text,
                wav_buffer
            )
            
            # Get the WAV bytes
            wav_buffer.seek(0)
            wav_bytes = wav_buffer.read()
            wav_buffer.close()
            
            logger.info(f"Generated {len(wav_bytes)} bytes of audio")
            return wav_bytes
            
        except Exception as e:
            logger.error(f"Failed to synthesize complete audio: {e}")
            raise
    
    def _synthesize_wav_sync(self, text: str, wav_buffer: io.BytesIO) -> None:
        """Synchronous WAV synthesis (runs in thread pool)."""
        with wave.open(wav_buffer, 'wb') as wav_file:
            # Set WAV parameters
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(self.sample_width)
            wav_file.setframerate(self.sample_rate)
            
            # Synthesize audio
            self.voice.synthesize_wav(text, wav_file)
    
    async def _synthesize_streaming(self, text: str) -> AsyncGenerator[bytes, None]:
        """Synthesize audio in streaming chunks using piper-tts."""
        try:
            # Run streaming synthesis in thread pool
            loop = asyncio.get_event_loop()
            
            # Use the actual piper streaming method to collect all raw audio data
            def stream_audio():
                all_audio_data = bytearray()
                sample_rate = None
                sample_width = None
                channels = None
                
                for chunk in self.voice.synthesize(text):
                    # Store audio parameters from first chunk
                    if sample_rate is None:
                        sample_rate = chunk.sample_rate
                        sample_width = chunk.sample_width
                        channels = chunk.sample_channels
                    
                    # Append raw audio data (not WAV formatted)
                    all_audio_data.extend(chunk.audio_int16_bytes)
                
                return bytes(all_audio_data), sample_rate, sample_width, channels
            
            # Get all audio data in thread pool
            audio_data, sample_rate, sample_width, channels = await loop.run_in_executor(None, stream_audio)
            
            # Create a single WAV file from all the audio data
            wav_bytes = self._create_wav_from_raw_audio(audio_data, sample_rate, sample_width, channels)
            
            # For streaming effect, we can split the final WAV into smaller chunks
            # But ensure we don't break the WAV structure
            chunk_size = len(wav_bytes) // 4  # Split into 4 parts for streaming effect
            if chunk_size < 1024:  # Minimum chunk size
                yield wav_bytes
            else:
                # For streaming, just return the complete audio since WAV can't be properly split
                yield wav_bytes
                    
        except Exception as e:
            logger.error(f"Failed to synthesize streaming audio: {e}")
            raise
    
    def _create_wav_from_raw_audio(self, audio_data: bytes, sample_rate: int, sample_width: int, channels: int) -> bytes:
        """Create a single WAV file from raw audio data."""
        try:
            # Create a BytesIO buffer
            wav_buffer = io.BytesIO()
            
            # Write WAV file to buffer
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)
            
            # Get the bytes
            wav_bytes = wav_buffer.getvalue()
            wav_buffer.close()
            
            return wav_bytes
            
        except Exception as e:
            logger.error(f"Failed to create WAV from raw audio: {e}")
            raise
    
    async def get_model_info(self) -> dict:
        """Get information about the loaded TTS model."""
        await self.initialize()
        
        return {
            "model_name": "en_US-hfc_female-medium",
            "is_initialized": self._is_initialized,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "model_path": str(self.model_path)
        }
    
    def is_ready(self) -> bool:
        """Check if the TTS service is ready to synthesize speech."""
        return self._is_initialized and self.voice is not None


# Global TTS service instance
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Get the global TTS service instance."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service


async def initialize_tts_service() -> None:
    """Initialize the global TTS service."""
    service = get_tts_service()
    await service.initialize()