# SolfaFlow

Turn audio into readable tonic solfa — with rhythm-aware notation and synchronized playback.

**Status:** Early development. Transcription engines are still being evaluated; no model is claimed to deliver perfect transcription.

## Product direction

SolfaFlow aims to let a user upload a recording, extract a melody, convert pitches to tonic solfa, and follow the result as each syllable highlights during playback.

### Core principles
- Separate audio transcription from music-theory conversion and presentation.
- Preserve note onset, duration, rests, and phrase boundaries.
- Support movable-do and chromatic syllables.
- Make uncertainty visible rather than pretending every transcription is correct.
- Keep the transcription engine replaceable until real recordings establish which model works best.
- Respect model/code licenses before using any engine commercially.

## Planned pipeline
1. Upload and validate audio.
2. Transcribe note events using a pluggable engine.
3. Determine or let the user choose the tonal center and solfa convention.
4. Map pitches to solfa syllables while preserving note timing.
5. Display readable notation and highlight the current syllable during playback.
6. Let users correct uncertain notes and export the result.

## Current implementation
The initial backend focuses on the deterministic music-theory layer and the shared note-event format. Audio-to-note inference is deliberately kept behind an interface while candidate engines are benchmarked.

## Development
The backend uses Python and FastAPI.

    cd backend
    python -m venv .venv
    # Windows PowerShell
    .\.venv\Scripts\Activate.ps1
    pip install -e ".[dev]"
    uvicorn solfaflow.main:app --reload

API docs: http://127.0.0.1:8000/docs

Run tests with: pytest

## License
Project license and model-specific licensing decisions are pending. Do not assume third-party model weights are commercially usable just because their source code is open source.

## Handoff and research documents

If you're an AI agent or developer picking up this repository, read these first:

- [Agent instructions](AGENTS.md)
- [Full project handoff and conversation notes](docs/PROJECT_HANDOFF.md)
- [Engine research and evaluation plan](docs/ENGINE_RESEARCH.md)
- [Architecture and roadmap](docs/ARCHITECTURE_AND_ROADMAP.md)
- [Decisions and open questions](docs/DECISIONS.md)

These documents distinguish what the user asked for, what is currently scaffolded, and what remains unverified. In particular, no transcription model has yet been benchmarked in this project.
