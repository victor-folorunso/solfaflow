# SolfaFlow — project handoff

**Purpose:** let a new AI/developer continue the project without needing the original conversation.

**Repository:** https://github.com/victor-folorunso/solfaflow  
**Project name:** SolfaFlow  
**State:** early scaffold; no production transcription model integrated; tests have been authored but have not been run/verified in the working environment.

## 1. Product idea

The user wants an application where a person supplies an audio recording and receives **tonic sol-fa / movable-do notation**, with syllables highlighted in sync with playback so a singer can follow the melody and understand pacing, held notes, and note transitions.

The core user experience is not merely “convert audio to MIDI.” MIDI/piano-roll views are hard for many singers to read. The desired output should be immediately singable/readable: solfa syllables with timing, and active syllables highlighted as the audio plays.

Conceptual flow:
1. User uploads or selects an audio recording.
2. System detects note events: pitch, start time, end time, confidence, and potentially voice/part.
3. System estimates the tonal center/key and mode, or lets the user choose/correct it.
4. System maps detected pitches to solfa syllables under a clearly stated convention.
5. System presents the syllables with rhythm/duration and rests.
6. During playback, the currently active syllable is highlighted according to event timing.
7. User can correct transcription/key/solfa when the model is uncertain.

**Important separation:** transcription, key estimation, solfa mapping, and playback highlighting are distinct components. The solfa mapper can be deterministic given pitch events and a tonic; the hard part is getting accurate note events and tonic from real audio.

## 2. Conversation history and ideas discussed

- The user wanted to investigate robust, existing open-source engines rather than build a half-baked transcription model from scratch.
- The user explicitly said not to “piece it together yet” while the options were still being explored. Later, the user said to build the project and created the repository named **SolfaFlow**.
- The product idea is audio in → tonic solfa out, with syllable highlighting synchronized to the recording. Timing/pacing and held notes matter.
- A piano roll is not the desired primary user interface; it may be useful as an internal/debugging representation, but the singer-facing view should be solfa.
- Candidate engines discussed: Spotify Basic Pitch, Google Magenta MT3, GAME (singing-voice-to-MIDI), Demucs (source separation), and NeuralNote/MuScriptor.
- Tentative direction from that discussion: test a singing-oriented engine such as GAME for vocal melody, use Basic Pitch as a lightweight baseline, and consider MT3 for mixed/multi-instrument audio. This was a shortlist, **not a final engine choice**; no benchmark was run.
- NeuralNote/MuScriptor were flagged for a commercial-license concern: code and bundled model weights may have different terms; the model weights were described in the earlier discussion as CC BY-NC 4.0. Re-check current upstream licenses and exact assets before relying on this.
- Demucs was discussed as a possible stem-separation preprocessing step, not a guaranteed solution. Separation can introduce artifacts and should be evaluated only if it improves downstream transcription.
- Accuracy must be measured against human-verified references. The product should not promise 100% accuracy and should provide confidence/correction paths.
- The unresolved scope question is whether the MVP targets a **single prominent melody/singer** first or tries to transcribe **choirs/multiple simultaneous parts** from the start. Choir/polyphonic transcription is substantially harder and may need separation or multi-pitch transcription.
- No reliable evidence was gathered that any candidate was run in this environment. Do not describe any candidate as tested or selected.

## 3. Current repository scaffold

Files previously committed to the default branch:
- `README.md`
- `backend/pyproject.toml`
- `backend/solfaflow/__init__.py`
- `backend/solfaflow/schemas.py`
- `backend/solfaflow/solfa.py`
- `backend/solfaflow/transcription.py`
- `backend/solfaflow/main.py`
- `backend/tests/test_solfa.py`
- `.github/workflows/backend-tests.yml`

Key scaffold details:
- Python 3.11+ package with FastAPI, Pydantic, Uvicorn; pytest/httpx development dependencies.
- `schemas.py` defines `NoteEvent` (MIDI pitch, start/end seconds, optional confidence and voice), `SolfaNote`, `ConvertRequest` (tonic MIDI, major/minor mode, chromatic style), and `ConvertResponse`.
- `solfa.py` implements a deterministic first-pass pitch-to-solfa mapper. Major degrees are do/re/mi/fa/so/la/ti. The current natural-minor convention treats the tonic as la, then ti/do/re/mi/fa/so. Chromatic raised-degree syllables include di, ri, fi, si, li; a fallback marks chromatic notes with a plus sign. These conventions are provisional and need explicit documentation/tests for all intended musical contexts.
- `transcription.py` only defines a `TranscriptionEngine` interface and an `UnconfiguredTranscriptionEngine` that raises `EngineNotConfiguredError`. **It does not transcribe audio.**
- `main.py` exposes `/health` and `/api/solfa/convert`. It does not yet expose a real upload/transcription/playback flow.
- `test_solfa.py` contains unit tests for scale mapping, transposition, selected chromatic notes, fallback notation, minor mapping, and invalid mode.
- `.github/workflows/backend-tests.yml` is configured for push to main, pull requests, and manual dispatch. It installs the backend package and runs pytest. A successful run has not been verified in the work so far.

Known commit SHAs from earlier work:
- Workflow: `b67bb0c7f48ed7e37ba27304bf1d98a181bd62a0`
- Solfa mapping fix: `3d584b89fcb7b567452285f955ea3fd66edcb9a3`
- Tests: `639fa9d45c06b4a97c8966a72e9604ee14c01338`
- Packaging metadata fix: `e0bc7545786e7cefb0f69192598c9673a58c0f55`

The previous assistant removed `readme = "../README.md"` from `backend/pyproject.toml` because a readme path outside the package project directory can cause packaging issues.

## 4. How to pick up locally

From the repository root:
```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest -v
uvicorn solfaflow.main:app --reload
```

If PowerShell blocks activation, use the environment's permitted activation policy or call `.venv\Scripts\python.exe` directly. The user develops on Windows/VS Code, often using PowerShell.

Check GitHub Actions here:
https://github.com/victor-folorunso/solfaflow/actions

Do not infer that the tests pass merely because the workflow file exists.

## 5. Immediate priorities

1. Inspect the current repository and run the existing tests in a real environment; fix any failures and report actual results.
2. Decide MVP scope explicitly: one dominant melody/singer first, or multi-part/choir from the start. Recommend starting with the smallest scope that satisfies a real user need, but get the product owner's decision before treating it as final.
3. Build a small, legally usable, representative evaluation set of audio with human-verified note events and tonic/key labels. Include clean solo voice, accompaniment, noisy/phone recordings, and any target choir examples.
4. Re-check candidate repositories, installation steps, inference requirements, supported audio types, model-weight licenses, and dataset restrictions from upstream sources.
5. Run candidates on the same audio and score them with defined metrics. Do not pick an engine from marketing claims alone.
6. Wire the best verified candidate behind the existing `TranscriptionEngine` interface; keep the rest of the application independent of the model.
7. Add upload handling, file-size/type limits, background processing for long jobs, progress/errors, and a timed solfa response.
8. Implement synchronized playback highlighting from event start/end times, with rests and long notes represented correctly.
9. Add an edit/correction workflow and clearly communicate low-confidence sections.

## 6. Product quality principles

- Human-singer usability comes first; don't make a piano roll the primary output.
- Rhythm and timing are first-class data.
- Keep transcription engine pluggable.
- Use reproducible benchmarks and honest confidence reporting.
- Confirm commercial rights for code, weights, and evaluation data.
- Avoid premature complexity and don't build an expensive model stack before evaluating a minimal viable path.
