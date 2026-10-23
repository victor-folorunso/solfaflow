# SolfaFlow prototype

Rough end-to-end test: **song in → keyboard tonic solfa + synced player out.** Not production code, and no
accuracy claims beyond what is recorded in [docs/PROTOTYPE_RESULTS.md](../docs/PROTOTYPE_RESULTS.md).

## Progressive processing

The song is cut into chunks (12 s, then 20 s, then 30 s each), at the quietest moment near each target time. Every chunk
is separated and transcribed with 3 s of extra audio on each side for context, and a note belongs to the chunk its
onset falls in, so a cut never splits or duplicates a note (`chunking.py`). Both models load once and stay in memory
(`engines.py`). After each chunk, everything so far is re-labelled (instant), so the key estimate improves as more of
the song arrives. The player polls `solfa.json` and fills in without reloading or losing your place.

The player opens a few seconds after upload and the song can be played straight away; solfa appears as each chunk
finishes. Compare runs or score against a reference with `compare_notes.py`.

## Pipeline

| Step | Tool | Why this one |
|---|---|---|
| Separate lead vocal | [audio-separator](https://github.com/nomadkaraoke/python-audio-separator) (MIT) with `vocals_mel_band_roformer.ckpt` (Mel-Band RoFormer, Kimberley Jensen) | Highest vocal SDR (12.6) of the models audio-separator lists; RoFormer models lead current vocal-separation leaderboards |
| Vocal → notes | [openvpi/GAME](https://github.com/openvpi/GAME) 1.0 medium (code MIT; weights licence not stated) | Singing-specific note transcriber released 2026; outputs onset/offset seconds and float pitch; claims robustness to noise, reverb and leftover accompaniment; ONNX export exists for a cheaper deployment later |
| Keyboard post-processing | `keyboard.py` (deterministic) | Tuning-drift tracking, snap to semitone keys, drop unplayably short notes, estimate "do", solfa + octave marks + key names |
| Player | `player_template.html` | Highlights the current syllable and keyboard key from the audio clock; hear original, detected notes, or both; change do; transpose key names to C; 0.5×/0.75× speed |

Considered but not used yet: **VocalParse** (May 2026, Qwen3-ASR-1.7B fine-tune; needs a GPU, outputs note values + BPM rather
than seconds) and **ROSVOT** (ACL 2024). Worth benchmarking against GAME later.

## Setup (Windows, CPU only)

```bash
cd prototype
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe torch torchaudio --index-url https://download.pytorch.org/whl/cpu
git clone --depth 1 https://github.com/openvpi/GAME vendor/GAME
uv pip install --python .venv/Scripts/python.exe -r vendor/GAME/requirements.txt "audio-separator[cpu]" imageio-ffmpeg soundfile pytest "numpy<2"
curl -L -o models/game-medium.zip https://github.com/openvpi/GAME/releases/download/v1.0.0/GAME-1.0-medium.zip
unzip models/game-medium.zip -d models/game-medium
```

The separator model (~900 MB) downloads on first run into `models/separator/`.

## Run the web UI

```bash
.venv/Scripts/python.exe -m uvicorn server:app --port 8765
```

Open http://localhost:8765, upload a song, and press **Open** when it's ready. Jobs run one at a time. Uploads go to
`uploads/` and results to `output/<job id>/`. (From the repo root, `.claude/launch.json` starts the same server.)

## Run from the command line

```bash
.venv/Scripts/python.exe solfaflow_proto.py path/to/song.mp3
```

Then open `output/<song>/player.html` in a browser. Options: `--do G` to force the key, `--skip-separation` for solo-voice
recordings, `--reuse` to skip separation/transcription already done for that song.

Tests: `.venv/Scripts/python.exe -m pytest -q tests`
