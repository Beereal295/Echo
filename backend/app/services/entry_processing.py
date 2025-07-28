"""
Entry Processing Service for handling the three processing modes:
1. Raw Transcription (no processing)
2. Enhanced Style (grammar and flow improvement)
3. Structured Summary (organized bullet points)
"""

from typing import Optional, Dict, Any
import json
import logging
from datetime import datetime

from app.core.config import settings
from app.services.ollama import OllamaService, get_ollama_service
from app.models.entry import Entry
from app.schemas.entry import ProcessingMode

logger = logging.getLogger(__name__)


class EntryProcessingService:
    """Service for processing journal entries through different AI modes."""
    
    def __init__(self, ollama_service: OllamaService):
        self.ollama_service = ollama_service
        self._enhanced_system_prompt = """You are a professional writing assistant that transforms raw speech transcripts into well-structured journal entries. Your task is to convert spoken language (with its natural pauses, repetitions, and informal flow) into coherent, well-formatted written text while preserving the author's authentic voice and emotional tone. Guidelines: 1) Fix grammar, punctuation, and sentence structure 2) Remove filler words, false starts, and repetitions 3) Organize thoughts into logical paragraphs 4) Maintain the original emotional tone and personal style 5) Keep all personal details, names, and specific information intact 6) Use natural, conversational language - not overly formal 7) Preserve the chronological flow of events as spoken 8) Do not add new information or interpretations 9) Keep the same level of detail as the original 10) Maintain first-person perspective throughout"""
        
        self._structured_system_prompt = """You are a personal journal assistant that creates structured summaries of diary entries. Your task is to extract and organize the key information from journal entries into clear, digestible points. Guidelines: 1) Create flat bulleted lists (no sub-bullets or nested lists) 2) Focus on concrete events, emotions, people, and outcomes 3) Keep each bullet point concise but meaningful 4) Maintain chronological order when relevant 5) Preserve important details and context 6) Use the author's own words and phrases when possible 7) Include emotional states and reactions 8) Capture both significant events and smaller meaningful moments 9) Avoid interpretation or analysis - stick to what was actually shared 10) Ensure the summary captures the essence of the original entry Format: Use simple bullet points (•) with clear, standalone statements."""

    async def process_entry(
        self, 
        raw_text: str, 
        mode: ProcessingMode, 
        existing_entry: Optional[Entry] = None
    ) -> Dict[str, Any]:
        """
        Process a journal entry according to the specified mode.
        
        Args:
            raw_text: The raw transcription text
            mode: Processing mode (raw, enhanced, structured)
            existing_entry: Optional existing entry to update
            
        Returns:
            Dict containing processed text and metadata
        """
        start_time = datetime.now()
        
        try:
            if mode == ProcessingMode.RAW:
                processed_text = raw_text
                processing_metadata = {
                    "mode": mode.value,
                    "processing_time_ms": 0,
                    "model_used": None,
                    "timestamp": start_time.isoformat()
                }
            
            elif mode == ProcessingMode.ENHANCED:
                processed_text = await self._process_enhanced_style(raw_text)
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                processing_metadata = {
                    "mode": mode.value,
                    "processing_time_ms": processing_time,
                    "model_used": settings.OLLAMA_DEFAULT_MODEL,
                    "timestamp": start_time.isoformat(),
                    "system_prompt_used": "enhanced_style"
                }
            
            elif mode == ProcessingMode.STRUCTURED:
                processed_text = await self._process_structured_summary(raw_text)
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                processing_metadata = {
                    "mode": mode.value,
                    "processing_time_ms": processing_time,
                    "model_used": settings.OLLAMA_DEFAULT_MODEL,
                    "timestamp": start_time.isoformat(),
                    "system_prompt_used": "structured_summary"
                }
            
            else:
                raise ValueError(f"Unknown processing mode: {mode}")
            
            # Calculate word count
            word_count = len(processed_text.split())
            
            return {
                "processed_text": processed_text,
                "word_count": word_count,
                "processing_metadata": processing_metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing entry with mode {mode}: {str(e)}")
            # Return raw text as fallback
            return {
                "processed_text": raw_text,
                "word_count": len(raw_text.split()),
                "processing_metadata": {
                    "mode": mode.value,
                    "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    "error": str(e),
                    "fallback_used": True,
                    "timestamp": start_time.isoformat()
                }
            }

    async def _process_enhanced_style(self, raw_text: str) -> str:
        """Process text using enhanced style mode."""
        try:
            response = await self.ollama_service.generate(
                prompt=raw_text,
                system=self._enhanced_system_prompt,
                model=settings.OLLAMA_DEFAULT_MODEL
            )
            return response.response.strip()
        except Exception as e:
            logger.error(f"Enhanced style processing failed: {str(e)}")
            raise

    async def _process_structured_summary(self, raw_text: str) -> str:
        """Process text using structured summary mode."""
        try:
            response = await self.ollama_service.generate(
                prompt=raw_text,
                system=self._structured_system_prompt,
                model=settings.OLLAMA_DEFAULT_MODEL
            )
            return response.response.strip()
        except Exception as e:
            logger.error(f"Structured summary processing failed: {str(e)}")
            raise

    async def reprocess_entry(
        self, 
        entry: Entry, 
        new_mode: ProcessingMode
    ) -> Dict[str, Any]:
        """
        Reprocess an existing entry with a different mode.
        
        Args:
            entry: Existing entry to reprocess
            new_mode: New processing mode to apply
            
        Returns:
            Dict containing reprocessed text and metadata
        """
        logger.info(f"Reprocessing entry {entry.id} from {entry.mode} to {new_mode}")
        
        # Always use the original raw_text as source
        return await self.process_entry(entry.raw_text, new_mode, entry)

    def get_processing_statistics(self, processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract processing statistics from metadata."""
        if not processing_metadata:
            return {}
        
        return {
            "processing_time_ms": processing_metadata.get("processing_time_ms", 0),
            "model_used": processing_metadata.get("model_used"),
            "has_error": "error" in processing_metadata,
            "fallback_used": processing_metadata.get("fallback_used", False),
            "processed_at": processing_metadata.get("timestamp")
        }


# Dependency injection
_entry_processing_service: Optional[EntryProcessingService] = None


async def get_entry_processing_service() -> EntryProcessingService:
    """Get the entry processing service instance."""
    global _entry_processing_service
    
    if _entry_processing_service is None:
        ollama_service = await get_ollama_service()
        _entry_processing_service = EntryProcessingService(ollama_service)
    
    return _entry_processing_service