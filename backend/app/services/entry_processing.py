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
from app.db.repositories.preferences_repository import PreferencesRepository

logger = logging.getLogger(__name__)


class EntryProcessingService:
    """Service for processing journal entries through different AI modes."""
    
    def __init__(self, ollama_service: OllamaService):
        self.ollama_service = ollama_service
        self._enhanced_system_prompt = """You are a writing assistant that turns raw speech transcripts into clear, structured journal entries.
Your job is to preserve the speaker's voice while improving readability and flow.

Guidelines:

Correct grammar, punctuation, and sentence structure.

Remove filler words, false starts, and repetitions.

Combine related ideas into coherent, well-structured paragraphs.

Preserve the emotional tone and personal style of the speaker.

Keep all names, personal details, and specific information intact.

Use natural, conversational language (not overly formal).

Maintain the original order and flow of events.

Do not add new information or change meaning.

Match the level of detail in the original.

Always write in the first person.

Do not add titles, headers, summaries, or any extra formatting—only return the journal-style paragraphs.

Do not include any introductory text, closing remarks, or signatures in your response."""
        
        self._structured_system_prompt = """You are a personal journal assistant that rewrites freeform diary entries into flat, structured bullet points in first person.
Your task is to preserve every important detail while improving structure.

Guidelines:
Write only flat bullet points (•), no headers, summaries, or prose.
Keep all key events, emotions, thoughts, people, and moments intact.
Use first-person voice ("I", "my") and preserve the author's tone and wording.
Do not interpret, rephrase creatively, or remove meaningful content.
Expand or reorganize for clarity, but never shorten or skip details.
Maintain chronological flow when it exists.
Each bullet must be a standalone, meaningful statement.
Do not add any text before or after the bullet list. Only return clean bullets.

Example Output Format:
• I had a long call with Sarah this morning and told her about the issues at work.
• Felt frustrated that things are still unresolved with my manager.
• I went for a short walk afterward to clear my head, which helped a bit.
• I'm still unsure about what to do next, but talking to Sarah helped."""

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
                model_used = await PreferencesRepository.get_value('ollama_model', settings.OLLAMA_DEFAULT_MODEL)
                processing_metadata = {
                    "mode": mode.value,
                    "processing_time_ms": processing_time,
                    "model_used": model_used,
                    "timestamp": start_time.isoformat(),
                    "system_prompt_used": "enhanced_style"
                }
            
            elif mode == ProcessingMode.STRUCTURED:
                processed_text = await self._process_structured_summary(raw_text)
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                model_used = await PreferencesRepository.get_value('ollama_model', settings.OLLAMA_DEFAULT_MODEL)
                processing_metadata = {
                    "mode": mode.value,
                    "processing_time_ms": processing_time,
                    "model_used": model_used,
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
            # Get preferences from database
            model = await PreferencesRepository.get_value('ollama_model', settings.OLLAMA_DEFAULT_MODEL)
            temperature = await PreferencesRepository.get_value('ollama_temperature', 0.7)
            context_window = await PreferencesRepository.get_value('ollama_context_window', 4096)
            
            response = await self.ollama_service.generate(
                prompt=raw_text,
                system=self._enhanced_system_prompt,
                model=model,
                temperature=temperature,
                num_ctx=context_window
            )
            return response.response.strip()
        except Exception as e:
            logger.error(f"Enhanced style processing failed: {str(e)}")
            raise

    async def _process_structured_summary(self, raw_text: str) -> str:
        """Process text using structured summary mode."""
        try:
            # Get preferences from database
            model = await PreferencesRepository.get_value('ollama_model', settings.OLLAMA_DEFAULT_MODEL)
            temperature = await PreferencesRepository.get_value('ollama_temperature', 0.7)
            context_window = await PreferencesRepository.get_value('ollama_context_window', 4096)
            
            response = await self.ollama_service.generate(
                prompt=raw_text,
                system=self._structured_system_prompt,
                model=model,
                temperature=temperature,
                num_ctx=context_window
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