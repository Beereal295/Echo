"""
TTS API endpoints for text-to-speech synthesis.

This module provides endpoints for:
- Text-to-speech synthesis with piper-tts
- Voice pack management and selection
- Streaming audio generation for conversational use
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.schemas import SuccessResponse, ErrorResponse
from app.services.tts_service import get_tts_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["tts"])


# Request Models
class TTSSynthesizeRequest(BaseModel):
    """Request model for TTS synthesis."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice: str = Field("hfc_female", description="Voice pack to use for synthesis")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech speed multiplier")
    stream: bool = Field(True, description="Whether to stream audio for faster response")


class TTSVoiceRequest(BaseModel):
    """Request model for setting voice pack."""
    voice_pack: str = Field(..., description="Name of the voice pack to use")


# Response Models
class TTSModelInfoResponse(BaseModel):
    """Response model for TTS model information."""
    model_name: str = Field(..., description="Name of the TTS model")
    device: str = Field(..., description="Device the model is running on")
    voice_pack: str = Field(..., description="Currently selected voice pack")
    is_initialized: bool = Field(..., description="Whether the model is initialized")
    available_voices: list[str] = Field(..., description="List of available voice packs")


class TTSVoicesResponse(BaseModel):
    """Response model for available voices."""
    voices: list[str] = Field(..., description="List of available voice packs")
    current_voice: str = Field(..., description="Currently selected voice pack")


@router.post("/synthesize")
async def synthesize_speech(request: TTSSynthesizeRequest):
    """
    Convert text to speech using piper-tts.
    
    Args:
        request: TTS synthesis parameters
        
    Returns:
        Audio file (WAV) as response or streaming response
        
    Raises:
        HTTPException: If synthesis fails
    """
    try:
        logger.error("=== TTS ENDPOINT CALLED ===")
        logger.error(f"TTS request - text: '{request.text[:50]}...', voice: {request.voice}, stream: {request.stream}")
        
        tts_service = get_tts_service()
        logger.error("Got TTS service")
        
        # Generate speech audio
        logger.error("About to synthesize speech")
        audio_result = await tts_service.synthesize_speech(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            stream=request.stream
        )
        logger.error(f"Generated audio result type: {type(audio_result)}, size: {len(audio_result) if isinstance(audio_result, bytes) else 'N/A'}")
        
        if request.stream:
            # Return streaming response for faster conversational experience
            async def audio_generator():
                async for chunk in audio_result:
                    yield chunk
            
            return StreamingResponse(
                audio_generator(),
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "inline; filename=speech.wav",
                    "Cache-Control": "no-cache"
                }
            )
        else:
            # Return complete audio file
            return Response(
                content=audio_result,
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "inline; filename=speech.wav",
                    "Content-Length": str(len(audio_result))
                }
            )
        
    except ValueError as e:
        logger.error(f"Invalid TTS request: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Speech synthesis failed: {str(e)}"
        )


@router.get("/voices", response_model=SuccessResponse[TTSVoicesResponse])
async def get_available_voices():
    """
    Get list of available voice packs.
    
    Returns:
        List of available voices and current selection
        
    Raises:
        HTTPException: If voice retrieval fails
    """
    try:
        tts_service = get_tts_service()
        
        available_voices = await tts_service.get_available_voices()
        current_voice = tts_service.voice_pack
        
        response_data = TTSVoicesResponse(
            voices=available_voices,
            current_voice=current_voice
        )
        
        return SuccessResponse(
            success=True,
            message=f"Retrieved {len(available_voices)} available voices",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Failed to get available voices: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve voices: {str(e)}"
        )


@router.post("/voice", response_model=SuccessResponse[dict])
async def set_voice_pack(request: TTSVoiceRequest):
    """
    Set the default voice pack for TTS.
    
    Args:
        request: Voice pack selection
        
    Returns:
        Success response with voice pack status
        
    Raises:
        HTTPException: If voice pack setting fails
    """
    try:
        tts_service = get_tts_service()
        
        success = await tts_service.set_voice_pack(request.voice_pack)
        
        if not success:
            available_voices = await tts_service.get_available_voices()
            raise HTTPException(
                status_code=400,
                detail=f"Voice pack '{request.voice_pack}' not available. Available voices: {available_voices}"
            )
        
        return SuccessResponse(
            success=True,
            message=f"Voice pack set to '{request.voice_pack}'",
            data={
                "voice_pack": request.voice_pack,
                "status": "active"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set voice pack: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set voice pack: {str(e)}"
        )


@router.get("/model-info", response_model=SuccessResponse[TTSModelInfoResponse])
async def get_tts_model_info():
    """
    Get information about the loaded TTS model.
    
    Returns:
        TTS model information and status
        
    Raises:
        HTTPException: If model info retrieval fails
    """
    try:
        tts_service = get_tts_service()
        
        model_info = await tts_service.get_model_info()
        
        response_data = TTSModelInfoResponse(**model_info)
        
        return SuccessResponse(
            success=True,
            message="TTS model information retrieved successfully",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Failed to get TTS model info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model information: {str(e)}"
        )


@router.post("/initialize", response_model=SuccessResponse[dict])
async def initialize_tts_model():
    """
    Initialize the TTS model.
    
    This endpoint triggers model loading and can be used to warm up the service.
    
    Returns:
        Success response indicating initialization status
        
    Raises:
        HTTPException: If initialization fails
    """
    try:
        tts_service = get_tts_service()
        
        await tts_service.initialize()
        
        return SuccessResponse(
            success=True,
            message="TTS model initialized successfully",
            data={
                "status": "initialized",
                "voice_pack": tts_service.voice_pack,
                "device": tts_service.device
            }
        )
        
    except Exception as e:
        logger.error(f"TTS initialization failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize TTS model: {str(e)}"
        )


@router.get("/status", response_model=SuccessResponse[dict])
async def get_tts_status():
    """
    Get current TTS service status.
    
    Returns:
        TTS service status and readiness
    """
    try:
        tts_service = get_tts_service()
        
        is_ready = tts_service.is_ready()
        
        return SuccessResponse(
            success=True,
            message="TTS status retrieved successfully",
            data={
                "is_ready": is_ready,
                "is_initialized": tts_service._is_initialized,
                "voice_pack": tts_service.voice_pack,
                "device": tts_service.device
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get TTS status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get TTS status: {str(e)}"
        )