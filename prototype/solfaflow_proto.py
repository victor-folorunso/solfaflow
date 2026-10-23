"""SolfaFlow prototype: song in, keyboard solfa + synced player out.

Pipeline (progressive: the song is processed in overlapping chunks and the
player updates after each one, so playing can start before the end is done):
  1. decode the song to 44.1 kHz WAV (ffmpeg via imageio-ffmpeg),
  2. plan chunks cut at quiet moments, each padded with context (chunking.py),
  3. per chunk: separate the lead vocal (Mel-Band RoFormer via audio-separator)
     and transcribe it into notes (openvpi GAME); models stay loaded (engines.py),
  4. stitch owned notes into song time, then keyboard post-processing over
     everything so far (tuning drift, snap to keys, key estimate, solfa),
  5. publish solfa.json, a synth rendering and the HTML player.

Usage:
  python solfaflow_proto.py SONG [--out DIR] [--do G] [--skip-separation]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable

import imageio_ffmpeg
import numpy as np
import soundfile as sf

import engines
from chunking import Chunk, energy_envelope, plan_chunks, stitch
from keyboard import NOTE_NAMES, RawNote, to_solfa

HERE = Path(__file__).resolve().parent
SAMPLE_RATE = 44100


def log(msg: str) -> None:
    print(f"[solfaflow] {msg}", flush=True)


def ensure_ffmpeg_on_path() -> None:
    """audio-separator shells out to `ffmpeg`; expose imageio-ffmpeg's binary under that name."""
    bin_dir = HERE / "bin"
    shim = bin_dir / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if not shim.exists():
        bin_dir.mkdir(exist_ok=True)
        shutil.copy(imageio_ffmpeg.get_ffmpeg_exe(), shim)
    if str(bin_dir) not in os.environ["PATH"]:
        os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ["PATH"]


def decode(song: Path, out_wav: Path, seconds: float | None = None) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    limit = ["-t", str(seconds)] if seconds else []
    subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error", "-i", str(song), *limit, "-ac", "2", "-ar", str(SAMPLE_RATE), str(out_wav)],
        check=True,
    )


def replace_with_retry(tmp: Path, target: Path, attempts: int = 20) -> None:
    """os.replace, retrying while Windows has the target open (e.g. the web server is sending it)."""
    for attempt in range(attempts):
        try:
            os.replace(tmp, target)
            return
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.1)


def write_text_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    replace_with_retry(tmp, path)


def render_synth(notes: list[dict], duration: float, out_wav: Path) -> None:
    """Simple keyboard-like tone for each note so the user can hear the transcription."""
    audio = np.zeros(int(duration * SAMPLE_RATE) + SAMPLE_RATE, dtype=np.float32)
    for note in notes:
        freq = 440.0 * 2 ** ((note["pitch_midi"] - 69) / 12)
        start = int(note["start"] * SAMPLE_RATE)
        n = int((note["end"] - note["start"]) * SAMPLE_RATE)
        t = np.arange(n) / SAMPLE_RATE
        tone = sum(np.sin(2 * math.pi * freq * k * t) / k**1.5 for k in (1, 2, 3, 4))
        envelope = np.exp(-t * 2.5) * np.minimum(1.0, t / 0.005)
        release = np.minimum(1.0, (n - np.arange(n)) / (0.02 * SAMPLE_RATE))
        audio[start:start + n] += (0.3 * tone * envelope * release).astype(np.float32)
    peak = float(np.abs(audio).max()) or 1.0
    sf.write(out_wav, audio / max(peak, 1.0), SAMPLE_RATE)


def write_player(result: dict, out_dir: Path, song_name: str) -> Path:
    template = (HERE / "player_template.html").read_text(encoding="utf-8")
    html = template.replace("/*SOLFA_DATA*/null", json.dumps(result)).replace("__TITLE__", song_name)
    player = out_dir / "player.html"
    write_text_atomic(player, html)
    return player


def process_chunk(chunk: Chunk, mix: np.ndarray, work: Path, skip_separation: bool, reuse: bool) -> list[RawNote]:
    """Separate and transcribe one padded chunk; returns notes in chunk-local time."""
    chunk_wav = work / f"chunk_{chunk.index:03d}.wav"
    vocal_wav = work / f"chunk_{chunk.index:03d}_vocals.wav"
    notes_csv = vocal_wav.with_suffix(".csv")
    if reuse and notes_csv.exists():
        with open(notes_csv, newline="") as f:
            return [RawNote(float(r["onset"]), float(r["offset"]), float(r["pitch"])) for r in csv.DictReader(f)]

    sf.write(chunk_wav, mix[int(chunk.start * SAMPLE_RATE):int(chunk.end * SAMPLE_RATE)], SAMPLE_RATE)
    if skip_separation:
        shutil.copy(chunk_wav, vocal_wav)
    elif not (reuse and vocal_wav.exists()):
        engines.separator().separate(chunk_wav, vocal_wav)
    return [RawNote(*n) for n in engines.game().transcribe(vocal_wav)]


def publish(notes: list[RawNote], out_dir: Path, *, title: str, duration: float, processed: float,
            complete: bool, version: int, do: str | None, min_duration: float, extra: dict) -> dict:
    """Label everything transcribed so far and write solfa.json, the synth track and the player."""
    do_pitch_class = NOTE_NAMES.index(do) if do else None
    try:
        result = to_solfa(notes, do_pitch_class=do_pitch_class, min_duration=min_duration)
    except ValueError:  # nothing playable yet, e.g. an instrumental intro
        result = {"notes": [], "do": None, "do_pitch_class": None, "do_source": None, "key_candidates": [],
                  "tuning_offset_semitones": 0.0, "tuning_drift_semitones": 0.0}
    synth_name = f"synth_{version:03d}.wav"
    render_synth(result["notes"], duration, out_dir / synth_name)
    result.update(extra, duration=duration, processed_seconds=round(processed, 2), complete=complete,
                  version=version, synth_file=synth_name)
    write_text_atomic(out_dir / "solfa.json", json.dumps(result, indent=2))
    write_player(result, out_dir, title)
    for old in out_dir.glob("synth_*.wav"):  # best effort: an older one may still be streaming
        if old.name != synth_name:
            try:
                old.unlink()
            except PermissionError:
                pass
    return result


def run(
    song: Path,
    out_dir: Path,
    do: str | None = None,
    skip_separation: bool = False,
    reuse: bool = False,
    seconds: float | None = None,
    min_duration: float = 0.07,
    title: str | None = None,
    on_progress: Callable[[dict], None] = lambda progress: None,
) -> dict:
    """Run the whole pipeline progressively.

    on_progress receives {"stage", "chunk", "chunks", "processed_seconds",
    "total_seconds", "player_ready"} as work advances.
    """
    out_dir = out_dir.resolve()
    work = out_dir / "work"
    work.mkdir(parents=True, exist_ok=True)
    ensure_ffmpeg_on_path()
    title = title or song.stem
    started = time.perf_counter()

    on_progress({"stage": "decoding", "player_ready": False})
    mix_wav = work / "mix.wav"
    decode(song, mix_wav, seconds)
    mix, _ = sf.read(mix_wav, dtype="float32")
    duration = len(mix) / SAMPLE_RATE
    shutil.copy(mix_wav, out_dir / "song.wav")
    chunks = plan_chunks(duration, energy_envelope(mix, SAMPLE_RATE))
    log(f"decoded {song.name} ({duration:.1f}s) into {len(chunks)} chunks")

    engine_info = {"separator": None if skip_separation else engines.SEPARATOR_MODEL,
                   "transcriber": "openvpi GAME 1.0 medium",
                   "chunks": [{"core": [round(c.core_start, 2), round(c.core_end, 2)],
                               "padded": [round(c.start, 2), round(c.end, 2)]} for c in chunks]}
    # Publish an empty result straight away so the player opens and the song can already be heard.
    publish([], out_dir, title=title, duration=duration, processed=0.0, complete=False, version=0, do=do,
            min_duration=min_duration, extra={"engine": engine_info})
    progress = {"stage": "loading models", "chunk": 0, "chunks": len(chunks), "processed_seconds": 0.0,
                "total_seconds": round(duration, 2), "player_ready": True}
    on_progress(progress)
    if not skip_separation:
        engines.separator()
    engines.game()

    notes: list[RawNote] = []
    chunk_seconds = []
    result = {}
    for chunk in chunks:
        t = time.perf_counter()
        is_last = chunk is chunks[-1]
        on_progress(progress | {"stage": "transcribing", "chunk": chunk.index + 1})
        local = process_chunk(chunk, mix, work, skip_separation, reuse)
        notes.extend(stitch(chunk, local, is_last=is_last))
        notes.sort(key=lambda n: n.start)
        chunk_seconds.append(round(time.perf_counter() - t, 1))
        result = publish(notes, out_dir, title=title, duration=duration, processed=chunk.core_end,
                         complete=is_last, version=chunk.index + 1, do=do, min_duration=min_duration,
                         extra={"engine": engine_info,
                                "timings_seconds": {"chunks": chunk_seconds,
                                                    "total": round(time.perf_counter() - started, 1)}})
        progress = progress | {"processed_seconds": round(chunk.core_end, 2)}
        log(f"chunk {chunk.index + 1}/{len(chunks)} done in {chunk_seconds[-1]}s: up to {chunk.core_end:.1f}s, "
            f"{len(result['notes'])} notes, do = {result['do']}")

    on_progress(progress | {"stage": "done"})
    log(f"finished in {time.perf_counter() - started:.0f}s; open {out_dir / 'player.html'}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("song", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--do", choices=NOTE_NAMES, default=None, help="override the estimated do key")
    parser.add_argument("--skip-separation", action="store_true", help="input is already a solo vocal")
    parser.add_argument("--reuse", action="store_true", help="reuse per-chunk vocals / notes from a previous run")
    parser.add_argument("--seconds", type=float, default=None, help="only process the first N seconds")
    parser.add_argument("--min-duration", type=float, default=0.07, help="drop notes shorter than this (s)")
    args = parser.parse_args()
    run(args.song, args.out or HERE / "output" / args.song.stem, do=args.do, skip_separation=args.skip_separation,
        reuse=args.reuse, seconds=args.seconds, min_duration=args.min_duration)


if __name__ == "__main__":
    main()
