"""FastAPI application for SolfaFlow."""

from fastapi import FastAPI
from .schemas import ConvertRequest, ConvertResponse, SolfaNote
from .solfa import pitch_to_solfa

app = FastAPI(
    title="SolfaFlow API",
    description="Convert timed musical notes into movable-do tonic solfa.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "solfaflow-api"}


@app.post("/api/solfa/convert", response_model=ConvertResponse)
def convert_to_solfa(request: ConvertRequest) -> ConvertResponse:
    converted = []
    for note in request.notes:
        mapping = pitch_to_solfa(
            pitch_midi=note.pitch_midi,
            tonic_midi=request.tonic_midi,
            mode=request.mode,
            chromatic_style=request.chromatic_style,
        )
        converted.append(
            SolfaNote(
                pitch_midi=note.pitch_midi,
                syllable=mapping.syllable,
                start=note.start,
                end=note.end,
                confidence=note.confidence,
                voice=note.voice,
            )
        )
    return ConvertResponse(tonic_midi=request.tonic_midi, mode=request.mode, notes=converted)
