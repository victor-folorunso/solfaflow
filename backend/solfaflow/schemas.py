"""API schemas shared by transcription, solfa conversion, and playback."""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class NoteEvent(BaseModel):
    """A detected note, with times expressed in seconds."""
    pitch_midi: int = Field(ge=0, le=127, description="MIDI pitch number")
    start: float = Field(ge=0, description="Note onset in seconds")
    end: float = Field(gt=0, description="Note offset in seconds")
    confidence: float | None = Field(default=None, ge=0, le=1)
    voice: str | None = Field(default=None, description="Optional part/voice label")

    @model_validator(mode="after")
    def end_after_start(self) -> "NoteEvent":
        if self.end <= self.start:
            raise ValueError("Note end must be later than note start")
        return self


class SolfaNote(BaseModel):
    pitch_midi: int
    syllable: str
    start: float
    end: float
    confidence: float | None = None
    voice: str | None = None


class ConvertRequest(BaseModel):
    notes: list[NoteEvent]
    tonic_midi: int = Field(ge=0, le=127, description="MIDI pitch of the tonic")
    mode: Literal["major", "minor"] = "major"
    chromatic_style: Literal["raised", "scale_degree"] = "raised"


class ConvertResponse(BaseModel):
    tonic_midi: int
    mode: Literal["major", "minor"]
    notes: list[SolfaNote]
