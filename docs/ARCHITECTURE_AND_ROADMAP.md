# SolfaFlow — architecture and roadmap

## Architecture principle

Keep the system modular so that changing the transcription model does not require rewriting solfa mapping, the API, or the playback UI.

```text
Audio upload
   |
Validation / normalization
   |
Optional stem separation (only if benchmark proves useful)
   |
TranscriptionEngine adapter
   |  note events: pitch, start, end, confidence, voice/part?
   v
Tonic/key estimation or user-selected tonic
   |
Solfa mapper (deterministic)
   |
Timed SolfaNote sequence + uncertainty metadata
   |
Playback UI: syllables, durations/rests, synchronized highlighting
   |
User corrections / reference annotations
```

This is a proposed architecture, not an implemented end-to-end system.

## Existing code boundaries

- `backend/solfaflow/schemas.py`: shared data contracts.
- `backend/solfaflow/solfa.py`: deterministic pitch-to-syllable mapping.
- `backend/solfaflow/transcription.py`: pluggable transcription interface; currently only an unconfigured placeholder.
- `backend/solfaflow/main.py`: current FastAPI endpoints `/health` and `/api/solfa/convert`.
- `backend/tests/test_solfa.py`: mapper unit tests.
- `.github/workflows/backend-tests.yml`: pytest CI workflow.

Inspect the real repository before editing; this document records the scaffold as last reported, not a fresh runtime inspection.

## Suggested data model

At minimum, each note event should carry:
- `pitch_midi`: integer MIDI pitch.
- `start_seconds`: onset relative to the audio timeline.
- `end_seconds`: offset; must be greater than onset.
- `confidence`: optional calibrated/uncalibrated confidence; document what it means.
- `voice`: optional source/part label if model supports it.

A production representation may also need:
- stable event ID,
- source track/voice,
- estimated pitch bend/vibrato metadata if useful,
- transcription status/uncertainty,
- bar/beat or tempo information if rhythm notation is added,
- user-corrected values and provenance,
- explicit rests/gaps (these can also be derived from gaps, but semantics must be consistent),
- audio duration and processing/model metadata.

Avoid overdesigning before the MVP scope is known. Store event times in seconds as the source of truth; derive display timing from them.

## Key/tonic estimation

Key estimation is not implemented. It should be a separate module/service from transcription and solfa mapping.

Possible interaction model:
1. Estimate tonic and mode with a confidence score.
2. Show the estimate and let the user correct it.
3. Recompute solfa labels instantly when tonic/mode changes.
4. Preserve raw detected pitches so a tonic correction does not require rerunning transcription.

Be explicit about ambiguity: a short melody may not contain enough context to determine a unique key. The UI may need a “choose tonic” control instead of pretending certainty.

## Solfa convention requirements

The current mapper is only a starting point:
- Major scale degrees: do, re, mi, fa, so, la, ti.
- Current natural-minor convention: tonic is la, followed by ti, do, re, mi, fa, so.
- Current chromatic raised-degree map uses di, ri, fi, si, li at the corresponding semitone offsets.
- A generic chromatic fallback marks a syllable with `+`.

Before expanding it, choose and document the convention. Chromatic naming varies by pedagogy and context (e.g. raised vs lowered degrees, major vs minor context). Do not assume one notation fits every community. Test octave handling and enharmonic spelling, even though MIDI pitch itself does not encode spelling.

## API evolution proposal

Current endpoints:
- `GET /health`
- `POST /api/solfa/convert` — converts supplied note events; this is not audio transcription.

Potential next endpoints, only after contracts are designed:
- `POST /api/transcriptions` — accept audio upload and create a job.
- `GET /api/transcriptions/{id}` — retrieve status/result.
- `GET /api/transcriptions/{id}/events` — retrieve timed note/solfa events if large.
- `PATCH /api/transcriptions/{id}/events/{event_id}` — save user corrections.

For small synchronous local test clips, a direct request may be adequate initially. For production/long clips, use background jobs and explicit processing states. Never keep long-running model inference inside an unbounded request handler without considering timeouts and concurrency.

Upload safety and operations:
- validate allowed audio types using content inspection, not only filename;
- set file-size and duration limits;
- use generated storage names and avoid trusting user paths;
- clean up temporary uploads;
- enforce request timeouts and resource limits;
- avoid logging raw audio or sensitive metadata unnecessarily;
- document retention/deletion behavior;
- prevent concurrent jobs from exhausting CPU/GPU/memory.

## Synchronized highlighting

For each playback position (t), the active note is the event whose interval contains it:
`start_seconds <= t < end_seconds`.

Implementation concerns:
- handle gaps/rests with no active syllable;
- long notes remain highlighted for their full duration;
- multiple simultaneous events require a display policy (stacked voices, separate lines, or explicitly unsupported in melody MVP);
- seek, pause, playback-rate changes, and audio loading must not desynchronize the highlight;
- use the audio player's current playback time as the clock, not a separate accumulating timer;
- if events overlap due to transcription noise, define deterministic handling;
- show low-confidence events for review rather than silently hiding them.

## Roadmap / gates

### Milestone 0 — establish a reliable baseline
- Inspect repo and run tests in a real environment.
- Confirm packaging and CI status.
- Add documented setup/format/lint commands if useful.
- Keep this milestone independent of large ML dependencies.

### Milestone 1 — choose scope and define data
- Decide melody-only vs choir/polyphonic.
- Specify input formats, maximum duration, and processing target.
- Define solfa convention and expected output.
- Define minimum acceptable quality and user-correction requirements.

### Milestone 2 — benchmark model candidates
- Create legal, representative clips and human-verified annotations.
- Run Basic Pitch baseline and a singing-focused candidate; add MT3 for polyphonic needs.
- Evaluate note, onset, offset, tonic, solfa, robustness, speed, memory, and license.
- Document reproducible results and failure examples.
- Gate: no production engine selected until results and license review exist.

### Milestone 3 — integrate one engine
- Implement a real adapter behind `TranscriptionEngine`.
- Add model integration tests and one or more fixed audio fixtures where redistribution is permitted.
- Include model version/checkpoint and processing metadata in results.
- Test error handling for silence, unsupported formats, long files, and no detected notes.

### Milestone 4 — end-to-end MVP
- Audio upload/validation.
- Processing status and error UI.
- Timed solfa output and synchronized playback.
- Tonic correction and manual note/syllable edits.
- User-facing explanation of limitations.

### Milestone 5 — quality iteration
- Gather consented/legally usable failure cases.
- Improve annotation and benchmark coverage.
- Test on actual target users.
- Add choir support only if it is in scope and evaluated independently.

## Definition of done for a transcription engine

Do not mark an engine integrated simply because it runs on one sample. Require:
- reproducible installation and inference instructions;
- verified license compatibility for code, model weights, dependencies, and evaluation assets;
- performance metrics on the agreed evaluation set;
- known failure modes documented;
- API adapter and error handling;
- regression tests;
- human review of representative outputs.
