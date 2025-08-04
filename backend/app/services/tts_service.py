"""
TTS Service for text-to-speech synthesis using piper-tts.

This service handles:
- Loading and managing the piper-tts voice models
- Generating speech audio from text with hfc_female voice
- Streaming audio output for fast response times
- Voice pack management and switching
"""

import asyncio
import logging
import os
import tempfile
import io
import wave
from typing import Optional, Union, Dict, Any, AsyncGenerator
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class TTSService:
    """Service for text-to-speech synthesis using piper-tts."""
    
    def __init__(self, voice_name: str = "hfc_female", model_quality: str = "medium"):
        """
        Initialize the TTS service.
        
        Args:
            voice_name: The piper voice to use (hfc_female)
            model_quality: Model quality (medium, high)
        """
        self.voice_name = voice_name
        self.model_quality = model_quality
        self.model = None
        self.voice_pack = "hfc_female"  # Default voice pack
        self.device = "cpu"  # Piper runs on CPU
        self._model_loading_lock = asyncio.Lock()
        self._is_initialized = False
        
        # Model file paths
        self.model_dir = Path(__file__).parent.parent.parent / "STT_MODEL"
        self.model_file = self.model_dir / f"en_US-{voice_name}-{model_quality}.onnx"
        
        # Check for the actual config file name (it might have a different naming pattern)
        possible_config_names = [
            f"en_US-{voice_name}-{model_quality}.onnx.json",
            f"en_en_US_{voice_name}_{model_quality}_en_US-{voice_name}-{model_quality}.onnx.json"
        ]
        
        self.config_file = None
        for config_name in possible_config_names:
            config_path = self.model_dir / config_name
            if config_path.exists():
                self.config_file = config_path
                break
        
        if self.config_file is None:
            # Default to expected name for error reporting
            self.config_file = self.model_dir / f"en_US-{voice_name}-{model_quality}.onnx.json"
        
        logger.info(f"Initializing TTSService with voice: {voice_name}-{model_quality}")
        logger.info(f"Model path: {self.model_file}")
        logger.info(f"Config path: {self.config_file}")
    
    def _check_model_files(self) -> bool:
        """Check if required model files exist."""
        if not self.model_file.exists():
            logger.error(f"Model file not found: {self.model_file}")
            # List all files in the directory for debugging
            try:
                files = list(self.model_dir.glob("*"))
                logger.info(f"Files in {self.model_dir}: {[f.name for f in files]}")
            except Exception as e:
                logger.error(f"Could not list files in {self.model_dir}: {e}")
            return False
        
        # Note: piper-tts doesn't actually require the JSON config file for basic operation
        # The JSON file is mainly for metadata, so we'll just warn if it's missing
        if not self.config_file.exists():
            logger.warning(f"Config file not found: {self.config_file}")
            logger.info("Continuing without config file (piper-tts can work without it)")
        
        return True
    
    async def initialize(self) -> None:
        """Initialize the piper-tts model if not already loaded."""
        if self._is_initialized:
            return
        
        async with self._model_loading_lock:
            if self._is_initialized:
                return
            
            try:
                logger.info("Loading piper-tts model...")
                
                # Check if model files exist
                if not self._check_model_files():
                    raise FileNotFoundError(f"Required model files not found in {self.model_dir}")
                
                # Load piper-tts model
                await self._load_piper_model()
                
                self._is_initialized = True
                logger.info(f"Piper-TTS model loaded successfully: {self.voice_name}-{self.model_quality}")
                
            except Exception as e:
                logger.error(f"Failed to load piper-tts model: {e}")
                raise
    
    async def _load_piper_model(self) -> None:
        """Load the piper-tts model."""
        try:
            logger.info(f"Attempting to load piper model from: {self.model_file}")
            logger.info(f"Config file location: {self.config_file}")
            logger.info(f"Model file exists: {self.model_file.exists()}")
            logger.info(f"Config file exists: {self.config_file.exists()}")
            
            # Import piper-tts
            try:
                from piper import PiperVoice
                logger.info("Successfully imported piper-tts")
            except ImportError as e:
                logger.error(f"Failed to import piper-tts: {e}")
                logger.error("Please install piper-tts: pip install piper-tts")
                raise ImportError(f"piper-tts not installed: {e}")
            
            # Load the voice model in a thread pool to avoid blocking
            logger.info("Loading piper voice model...")
            loop = asyncio.get_event_loop()
            
            def load_piper_sync():
                try:
                    # Use the config file we found, not the default piper behavior
                    if self.config_file and self.config_file.exists():
                        logger.info(f"Loading piper with config file: {self.config_file}")
                        return PiperVoice.load(str(self.model_file), str(self.config_file))
                    else:
                        # Try without config file
                        logger.info("Loading piper without config file")
                        return PiperVoice.load(str(self.model_file))
                except Exception as e:
                    logger.error(f"Piper model loading error: {e}")
                    raise
            
            self.model = await loop.run_in_executor(None, load_piper_sync)
            
            logger.info(f"Piper voice model loaded successfully from {self.model_file}")
            
        except ImportError:
            # Re-raise ImportError as is
            raise
        except Exception as e:
            logger.error(f"Failed to load piper model: {e}")
            logger.error(f"Model file path: {self.model_file}")
            logger.error(f"Config file path: {self.config_file}")
            # List directory contents for debugging
            try:
                files = list(self.model_dir.glob("*"))
                logger.error(f"Available files in {self.model_dir}: {[f.name for f in files]}")
            except Exception as list_error:
                logger.error(f"Could not list directory: {list_error}")
            raise RuntimeError(f"Failed to load piper model: {e}")
    
    async def synthesize_speech(
        self, 
        text: str, 
        voice: str = "hfc_female",
        speed: float = 1.0,
        stream: bool = True
    ) -> Union[bytes, AsyncGenerator[bytes, None]]:
        """
        Synthesize speech from text using piper-tts.
        
        Args:
            text: Text to convert to speech
            voice: Voice pack to use (default: hfc_female)
            speed: Speech speed multiplier (default: 1.0)
            stream: Whether to stream audio chunks for faster response
            
        Returns:
            Audio data as bytes or async generator of audio chunks
        """
        await self.initialize()
        
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            logger.info(f"Synthesizing speech for text: '{text[:50]}...' with piper-tts")
            
            if stream:
                return self._synthesize_streaming(text, speed)
            else:
                return await self._synthesize_complete(text, speed)
                
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            raise
    
    async def _synthesize_complete(self, text: str, speed: float) -> bytes:
        """Synthesize complete audio file using piper-tts."""
        try:
            # Run synthesis in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            wav_bytes = await loop.run_in_executor(
                None,
                self._piper_synthesize,
                text
            )
            
            # Apply speed adjustment if needed
            if speed != 1.0:
                wav_bytes = await self._adjust_speed(wav_bytes, speed)
            
            logger.info(f"Generated {len(wav_bytes)} bytes of audio with piper-tts")
            return wav_bytes
            
        except Exception as e:
            logger.error(f"Failed to synthesize complete audio: {e}")
            raise
    
    def _piper_synthesize(self, text: str) -> bytes:
        """Synchronous piper synthesis (runs in thread pool)."""
        import tempfile
        import wave
        
        logger.error(f"_piper_synthesize called with text: '{text[:100]}...'")
        logger.error(f"Model initialized: {self._is_initialized}, Model object: {self.model}")
        
        # Create a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            logger.error(f"Created temp file: {temp_path}")
            
            # Open WAV file for writing with proper configuration
            with wave.open(temp_path, 'wb') as wav_file:
                # Configure WAV file parameters for piper output
                wav_file.setnchannels(1)  # Mono audio
                wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
                wav_file.setframerate(22050)  # Default piper sample rate
                
                logger.error("Configured WAV file, about to call model.synthesize")
                
                # Generate audio using piper
                logger.error("Starting audio generation with piper")
                
                try:
                    # Use the original text for synthesis
                    self.model.synthesize(text, wav_file)
                    logger.error("Piper synthesize completed")
                except Exception as e:
                    logger.error(f"Audio generation failed: {e}")
                    raise
            
            # Read the WAV file back as bytes
            with open(temp_path, 'rb') as f:
                wav_bytes = f.read()
            
            logger.error(f"Read {len(wav_bytes)} bytes from WAV file")
            
            # Debug: Show first 44 bytes in hex to see what's in the WAV header
            if len(wav_bytes) <= 50:
                import binascii
                logger.error(f"WAV file content (hex): {binascii.hexlify(wav_bytes)}")
                
            # Check if this is just a WAV header with no audio data
            if len(wav_bytes) == 44:
                logger.error("WARNING: WAV file contains only header, no audio data!")
                
            return wav_bytes
            
        finally:
            # Clean up temporary file
            import os
            try:
                os.unlink(temp_path)
            except OSError:
                pass
    
    async def _synthesize_streaming(self, text: str, speed: float) -> AsyncGenerator[bytes, None]:
        """Synthesize audio in streaming chunks using piper-tts."""
        try:
            # Split text into sentences for streaming
            sentences = self._split_text_for_streaming(text)
            
            for sentence in sentences:
                if sentence.strip():
                    # Generate audio for this sentence chunk
                    audio_chunk = await self._synthesize_complete(sentence, speed)
                    yield audio_chunk
                    
                    # Small delay for streaming effect
                    await asyncio.sleep(0.05)
                    
        except Exception as e:
            logger.error(f"Failed to synthesize streaming audio: {e}")
            raise
    
    def _split_text_for_streaming(self, text: str) -> list[str]:
        """Split text into chunks suitable for streaming."""
        # Split by sentences, but keep punctuation
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        # If no sentence breaks, split by commas or at reasonable intervals
        if len(sentences) == 1 and len(text) > 100:
            sentences = re.split(r'(?<=,)\s+', text)
        
        # Ensure no empty sentences
        return [s.strip() for s in sentences if s.strip()]
    
    def _numpy_to_wav_bytes(self, wav_data: np.ndarray, sample_rate: int = 22050) -> bytes:
        """Convert numpy audio data to WAV bytes."""
        try:
            # Create a BytesIO buffer
            wav_buffer = io.BytesIO()
            
            # Ensure audio data is in the right format
            if wav_data.dtype != np.int16:
                # Convert float to int16
                if wav_data.dtype == np.float32 or wav_data.dtype == np.float64:
                    wav_data = (wav_data * 32767).astype(np.int16)
                else:
                    wav_data = wav_data.astype(np.int16)
            
            # Write WAV file to buffer
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes per sample (int16)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(wav_data.tobytes())
            
            # Get the bytes
            wav_bytes = wav_buffer.getvalue()
            wav_buffer.close()
            
            return wav_bytes
            
        except Exception as e:
            logger.error(f"Failed to convert numpy to WAV bytes: {e}")
            raise
    
    async def _adjust_speed(self, wav_bytes: bytes, speed: float) -> bytes:
        """Adjust audio speed (placeholder implementation)."""
        # For now, just return original audio
        # Speed adjustment would require audio processing libraries like librosa
        logger.info(f"Speed adjustment requested: {speed}x (not implemented yet)")
        return wav_bytes
    
    async def get_available_voices(self) -> list[str]:
        """Get list of available voice packs."""
        await self.initialize()
        
        # Return the current voice (could be expanded to scan for more models)
        return ["hfc_female"]
    
    async def set_voice_pack(self, voice_pack: str) -> bool:
        """
        Set the default voice pack.
        
        Args:
            voice_pack: Name of the voice pack to use
            
        Returns:
            True if voice pack was set successfully
        """
        available_voices = await self.get_available_voices()
        
        if voice_pack not in available_voices:
            logger.warning(f"Voice pack '{voice_pack}' not available. Available: {available_voices}")
            return False
        
        self.voice_pack = voice_pack
        logger.info(f"Voice pack set to: {voice_pack}")
        return True
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded TTS model."""
        await self.initialize()
        
        return {
            "model_name": f"piper-tts-{self.voice_name}-{self.model_quality}",
            "device": self.device,
            "voice_pack": self.voice_pack,
            "is_initialized": self._is_initialized,
            "available_voices": await self.get_available_voices()
        }
    
    def is_ready(self) -> bool:
        """Check if the TTS service is ready to synthesize speech."""
        return self._is_initialized and self.model is not None


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