# SolfaFlow — decisions and open questions

This log separates established choices from provisional implementation details and unresolved product decisions.

## Established from the user's direction

- **Project name:** SolfaFlow.
- **Repository:** `victor-folorunso/solfaflow`.
- **Core experience:** audio input → tonic solfa output, with syllables highlighted in sync with audio playback.
- **Timing matters:** the display must communicate pacing and held notes, not only pitch sequence.
- **Usability:** don't make piano roll/MIDI visualization the primary singer-facing output.
- **Engineering preference:** reuse and rigorously evaluate strong existing engines instead of writing an unproven transcription model from scratch.
- **Handoff requirement:** repository documentation should capture the product idea, prior reasoning, existing scaffold, candidate models, limitations, and next steps so another AI can resume quickly.

## Scope decisions (product owner, 2026-10-22)

- **Target user:** keyboard/piano players who want to play a song's tune from tonic solfa. Not choirs.
- **Output:** the main melody only (usually the lead vocal), one note at a time, snapped to keyboard keys (semitones), with held-note durations.
- **Price:** free or near-free (not open source). Paid competitors exist; low running cost is a hard constraint, so prefer CPU/on-device inference.
- **No shared library** of transcriptions: user uploads a song and gets solfa for their own use.
- Keyboard-specific needs: global tuning-offset correction before snapping to keys, octave marks, showing which key is "do", optional transpose (e.g. to C), and dropping notes too short to play.

## Provisional code choices (not product-final)

- Backend scaffold uses Python 3.11+, FastAPI, Pydantic, Uvicorn, pytest.
- Note events use MIDI pitch plus start/end seconds.
- Solfa mapping is deterministic once pitch, tonic, mode, and convention are known.
- A `TranscriptionEngine` interface is intended to keep model implementation replaceable.
- GitHub Actions workflow runs pytest on pushes/PRs/manual dispatch.
- Current solfa mapping supports an initial major and natural-minor convention plus basic chromatic syllables. This needs review before calling it musically complete.

## Candidate engine hypotheses — not decisions

| Candidate | Hypothesized role | Status |
|---|---|---|
| GAME | Singing-voice-to-MIDI; possible best fit for a vocal-melody MVP | Not run; canonical repo/checkpoint still needs verification |
| Spotify Basic Pitch | Accessible audio-to-MIDI baseline, especially single prominent pitched source | Not run; check current code/weights license and limitations |
| Google Magenta MT3 | Multi-instrument transcription for complex mixtures | Not run; heavier research/deployment stack likely |
| Demucs | Optional stem separation before vocal transcription | Not a transcription engine; use only if ablation proves it helps |
| NeuralNote / MuScriptor | General audio-to-MIDI candidates | Verify exact repo/assets and license; prior discussion flagged CC BY-NC 4.0 weights concern |

## Unresolved product questions

1. **Target input:** one singer / one dominant melody, or choir and simultaneous parts?
2. **Accompaniment:** should the first release handle voice over full instrumental music?
3. **Audience/use case:** personal practice, choir rehearsal, music teaching, transcription service, or another setting?
4. **Solfa convention:** major movable-do, natural-minor convention, chromatic variants, fixed-do, or user-selectable conventions?
5. **Tonic:** automatic key/tonic estimate only, or always allow the user to select/correct tonic?
6. **Output:** syllable sequence only, or include rhythmic notation, lyric alignment, bar/beat grid, and rests?
7. **Audio constraints:** accepted formats, max file size/duration, real-time versus offline/server processing?
8. **Deployment:** local/offline, hosted API, or hybrid?
9. **Commercial licensing:** is commercial deployment required from the beginning? Assume that licenses must be compatible until clarified.
10. **Quality target:** what note/solfa accuracy is acceptable and when should the app request user correction?
11. **Languages/accessibility:** any target language, solfa spelling, or display needs not yet captured?

## Decisions that must not be made by assumption

- Do not declare an engine the winner without running a common benchmark.
- Do not silently scope choir transcription into the MVP.
- Do not assume automatic key detection is always reliable.
- Do not assume code licenses cover downloaded model weights.
- Do not promise perfect output.
- Do not replace the solfa-first UI with a piano roll.
- Do not treat a passing unit test suite as proof that audio transcription is accurate.
