"""Interfaces for audio-to-note engines.

No specific model is hardwired here. Candidate models must be benchmarked on
representative recordings and checked for commercial licensing before adoption.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from .schemas import NoteEvent


class TranscriptionEngine(ABC):
    """Adapter contract implemented by a selected audio transcription engine."""
    name: str

    @abstractmethod
    def transcribe(self, audio_path: Path) -> list[NoteEvent]:
        """Return timed note events for an audio file."""
        raise NotImplementedError


class EngineNotConfiguredError(RuntimeError):
    """Raised when a transcription is requested without a configured engine."""


class UnconfiguredTranscriptionEngine(TranscriptionEngine):
    name = "unconfigured"

    def transcribe(self, audio_path: Path) -> list[NoteEvent]:
        raise EngineNotConfiguredError(
            "No transcription engine is configured yet. Engine selection is "
            "pending comparative accuracy and license evaluation."
        )
