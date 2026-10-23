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
import functools
import json
import math
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable

import imageio_ffmpeg
import numpy as np
import soundfile as sf

import chords as chord_rec
import engines
from chords import Chord
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


PIANO_PARTIALS = 8
PIANO_INHARMONICITY = 0.0004  # real strings' overtones run slightly sharp of exact multiples
PIANO_DETUNE_CENTS = 0.7  # two strings per key, a hair apart, give the shimmer of a real piano
PIANO_RELEASE_SECONDS = 0.12


@functools.lru_cache(maxsize=2048)  # songs repeat the same notes; results are re-rendered after every chunk
def piano_tone(pitch_midi: int, seconds: float) -> np.ndarray:
    """A synthetic piano-like note: struck, with overtones that fade faster the higher they are."""
    n = int((seconds + PIANO_RELEASE_SECONDS) * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    freq = 440.0 * 2 ** ((pitch_midi - 69) / 12)
    decay = 1.2 + freq / 400  # higher keys ring for less time
    tone = np.zeros(n)
    for k in range(1, PIANO_PARTIALS + 1):
        partial = k * freq * math.sqrt(1 + PIANO_INHARMONICITY * k * k)
        if partial > SAMPLE_RATE / 2:
            break
        amp = k ** -1.3 * np.exp(-t * decay * (1 + 0.5 * (k - 1)))
        for cents in (-PIANO_DETUNE_CENTS, PIANO_DETUNE_CENTS):
            tone += amp * np.sin(2 * math.pi * partial * 2 ** (cents / 1200) * t)
    attack = np.minimum(1.0, t / 0.004)
    # The key is lifted at the note's end: the damper stops it over the release time.
    release = np.clip(1 - (t - seconds) / PIANO_RELEASE_SECONDS, 0.0, 1.0)
    return tone * attack * release


# Off: measured on two real songs, chord-tone evidence fixed neither key and broke one. An I-V accompaniment
# (A and E in La Cucaracha) has the same notes as IV-I a fifth up, so it pulled do from A to E; Mary's C and G
# pulled toward G the same way. Kept switchable for experiments (keyboard.estimate_do accepts harmony).
USE_CHORDS_FOR_KEY = False

CHORD_LOW_MIDI = 48  # chords are voiced in the octave from C3, under the melody, like a left hand
CHORD_RESTRIKE_SECONDS = 2.0
CHORD_LEVEL = 0.07
MELODY_LEVEL = 0.18


def render_synth(notes: list[dict], duration: float, out_wav: Path, chords: list[Chord] = ()) -> None:
    """Play the detected melody, with the detected chords softly underneath, on a piano-like sound."""
    audio = np.zeros(int((duration + 1) * SAMPLE_RATE), dtype=np.float32)

    def add(pitch: int, start_s: float, seconds: float, level: float) -> None:
        start = int(start_s * SAMPLE_RATE)
        tone = piano_tone(pitch, round(seconds, 2))[: len(audio) - start]
        audio[start:start + len(tone)] += (level * tone).astype(np.float32)

    for chord in chords:
        root_midi = CHORD_LOW_MIDI + chord.root
        voicing = [root_midi + interval for interval in ((0, 3, 7) if chord.quality == "min" else (0, 4, 7))]
        t = chord.start
        while t < chord.end - 0.05:  # a long chord is re-struck, as a player would
            length = min(CHORD_RESTRIKE_SECONDS, chord.end - t)
            for pitch in voicing:
                add(pitch, t, length, CHORD_LEVEL)
            t += length
    for note in notes:
        add(note["pitch_midi"], note["start"], note["end"] - note["start"], MELODY_LEVEL)
    peak = float(np.abs(audio).max()) or 1.0
    sf.write(out_wav, audio / max(peak, 1.0), SAMPLE_RATE)


SITE_TAG = re.compile(r"[\s_-]*[\[(][^\])]*\.[a-z]{2,4}[\])]", re.IGNORECASE)  # "(mp3.pm)", "[example.com]"


def pretty_name(file_stem: str) -> str:
    """Turn a downloaded file name into a readable song title."""
    name = SITE_TAG.sub("", file_stem)
    if " " not in name:  # "Frozen_-_Let_It_Go" or "Mary-Had-a-Little-Lamb"
        name = re.sub(r"[_-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" _-")
    return name[:80] or file_stem[:80]


def write_player(result: dict, out_dir: Path, song_name: str) -> Path:
    template = (HERE / "player_template.html").read_text(encoding="utf-8")
    html = template.replace("/*SOLFA_DATA*/null", json.dumps(result)).replace("__TITLE__", song_name)
    player = out_dir / "player.html"
    write_text_atomic(player, html)
    return player


def chunk_chords(accompaniment_wav: Path, chunk: Chunk) -> list[Chord]:
    """Chords in the chunk's core, in song time (the padding gives the smoothing context)."""
    if not accompaniment_wav.exists():
        return []
    audio, sr = sf.read(accompaniment_wav, dtype="float32")
    return chord_rec.clip(chord_rec.recognise(audio, sr, offset=chunk.start), chunk.core_start, chunk.core_end)


def process_chunk(chunk: Chunk, mix: np.ndarray, work: Path, skip_separation: bool,
                  reuse: bool) -> tuple[list[RawNote], list[Chord]]:
    """Separate and transcribe one padded chunk.

    Returns notes in chunk-local time and the chunk core's chords in song time.
    Without separation there is no accompaniment track, so no chords.
    """
    chunk_wav = work / f"chunk_{chunk.index:03d}.wav"
    vocal_wav = work / f"chunk_{chunk.index:03d}_vocals.wav"
    accompaniment_wav = work / f"chunk_{chunk.index:03d}_accompaniment.wav"
    notes_csv = vocal_wav.with_suffix(".csv")
    if reuse and notes_csv.exists():
        with open(notes_csv, newline="") as f:
            notes = [RawNote(float(r["onset"]), float(r["offset"]), float(r["pitch"])) for r in csv.DictReader(f)]
        return notes, chunk_chords(accompaniment_wav, chunk)

    sf.write(chunk_wav, mix[int(chunk.start * SAMPLE_RATE):int(chunk.end * SAMPLE_RATE)], SAMPLE_RATE)
    if skip_separation:
        shutil.copy(chunk_wav, vocal_wav)
    elif not (reuse and vocal_wav.exists() and accompaniment_wav.exists()):
        engines.separator().separate(chunk_wav, vocal_wav, accompaniment_wav)
    notes = [RawNote(*n) for n in engines.game().transcribe(vocal_wav)]
    return notes, chunk_chords(accompaniment_wav, chunk)


def publish(notes: list[RawNote], out_dir: Path, *, title: str, duration: float, processed: float,
            complete: bool, version: int, do: str | None, min_duration: float, extra: dict,
            chords: list[Chord] = ()) -> dict:
    """Label everything transcribed so far and write solfa.json, the synth track and the player."""
    do_pitch_class = NOTE_NAMES.index(do) if do else None
    harmony = chord_rec.tone_histogram(chords) if chords and USE_CHORDS_FOR_KEY else None
    try:
        result = to_solfa(notes, do_pitch_class=do_pitch_class, min_duration=min_duration, harmony=harmony)
    except ValueError:  # nothing playable yet, e.g. an instrumental intro
        result = {"notes": [], "do": None, "do_pitch_class": None, "do_source": None, "key_candidates": [],
                  "tuning_offset_semitones": 0.0, "tuning_drift_semitones": 0.0}
    result["chords"] = [
        {"start": round(c.start, 2), "end": round(c.end, 2), "root": c.root, "quality": c.quality, "name": c.name,
         "numeral": chord_rec.numeral(c, result["do_pitch_class"]) if result["do_pitch_class"] is not None else None}
        for c in chords
    ]
    synth_name = f"synth_{version:03d}.wav"
    render_synth(result["notes"], duration, out_dir / synth_name, chords)
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
    title = title or pretty_name(song.stem)
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
    chords: list[Chord] = []
    chunk_seconds = []
    result = {}
    for chunk in chunks:
        t = time.perf_counter()
        is_last = chunk is chunks[-1]
        on_progress(progress | {"stage": "transcribing", "chunk": chunk.index + 1})
        local, chunk_chord_list = process_chunk(chunk, mix, work, skip_separation, reuse)
        notes.extend(stitch(chunk, local, is_last=is_last))
        notes.sort(key=lambda n: n.start)
        chords = chord_rec.join(chords + chunk_chord_list)
        chunk_seconds.append(round(time.perf_counter() - t, 1))
        result = publish(notes, out_dir, title=title, duration=duration, processed=chunk.core_end,
                         complete=is_last, version=chunk.index + 1, do=do, min_duration=min_duration,
                         chords=chords,
                         extra={"engine": engine_info,
                                "timings_seconds": {"chunks": chunk_seconds,
                                                    "total": round(time.perf_counter() - started, 1)}})
        progress = progress | {"processed_seconds": round(chunk.core_end, 2)}
        log(f"chunk {chunk.index + 1}/{len(chunks)} done in {chunk_seconds[-1]}s: up to {chunk.core_end:.1f}s, "
            f"{len(result['notes'])} notes, {len(chords)} chords, do = {result['do']}")

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
