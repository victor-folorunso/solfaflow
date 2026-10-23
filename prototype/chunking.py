"""Split a song into overlapping chunks and stitch per-chunk notes back together.

Progressive processing: each chunk is separated and transcribed on its own so
the first notes are ready long before the whole song is done.

Quality safeguards:
- Cuts go at the quietest moment near each target time, which is usually a
  breath or a gap between phrases.
- Every chunk is processed with `pad` seconds of extra audio on each side, so
  both models see context around the part we keep (the "core").
- A note belongs to the chunk whose core contains its onset. Notes starting in
  the padding are dropped because the neighbouring chunk owns them, and a
  note that starts near the end of a core can run on into the padding, so a
  cut never splits a note.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from keyboard import RawNote

FIRST_CHUNK_SECONDS = 12.0  # small, so the first result appears quickly
SECOND_CHUNK_SECONDS = 20.0
CHUNK_SECONDS = 30.0  # later chunks are bigger: padding overhead is a smaller share
PAD_SECONDS = 3.0
CUT_SEARCH_SECONDS = 3.0
ENERGY_HOP_SECONDS = 0.05


@dataclass(frozen=True)
class Chunk:
    index: int
    core_start: float
    core_end: float
    start: float  # core_start minus padding, clamped to the song
    end: float  # core_end plus padding, clamped to the song


def energy_envelope(audio: np.ndarray, sample_rate: int, hop_seconds: float = ENERGY_HOP_SECONDS) -> np.ndarray:
    """RMS energy per hop of a mono or (samples, channels) signal."""
    mono = audio.mean(axis=1) if audio.ndim == 2 else audio
    hop = max(1, int(hop_seconds * sample_rate))
    frames = len(mono) // hop
    if frames == 0:
        return np.zeros(1)
    framed = mono[: frames * hop].reshape(frames, hop)
    return np.sqrt((framed ** 2).mean(axis=1))


def chunk_lengths(duration: float) -> list[float]:
    lengths = []
    total = 0.0
    while total < duration:
        size = (FIRST_CHUNK_SECONDS, SECOND_CHUNK_SECONDS)[len(lengths)] if len(lengths) < 2 else CHUNK_SECONDS
        lengths.append(size)
        total += size
    return lengths


def quietest_time(energy: np.ndarray, target: float, search: float, hop: float) -> float:
    lo = max(0, int((target - search) / hop))
    hi = min(len(energy), int((target + search) / hop) + 1)
    if hi <= lo:
        return target
    return (lo + int(np.argmin(energy[lo:hi]))) * hop


def plan_chunks(
    duration: float,
    energy: np.ndarray | None = None,
    hop: float = ENERGY_HOP_SECONDS,
    pad: float = PAD_SECONDS,
) -> list[Chunk]:
    """Plan chunk cores covering [0, duration) and their padded extents."""
    cuts = [0.0]
    target = 0.0
    for length in chunk_lengths(duration)[:-1]:
        target += length
        # A last chunk shorter than a few seconds is merged into the previous one.
        if duration - target < CUT_SEARCH_SECONDS * 2:
            break
        cut = quietest_time(energy, target, CUT_SEARCH_SECONDS, hop) if energy is not None else target
        if cut <= cuts[-1] + 1.0:
            cut = target
        cuts.append(cut)
        target = cut
    cuts.append(duration)
    return [
        Chunk(i, cuts[i], cuts[i + 1], max(0.0, cuts[i] - pad), min(duration, cuts[i + 1] + pad))
        for i in range(len(cuts) - 1)
    ]


def stitch(chunk: Chunk, local_notes: list[RawNote], is_last: bool) -> list[RawNote]:
    """Shift chunk-local notes to song time and keep the ones this chunk owns."""
    owned = []
    for note in local_notes:
        start = note.start + chunk.start
        in_core = chunk.core_start <= start < chunk.core_end or (is_last and start == chunk.core_end)
        if in_core:
            owned.append(RawNote(start, note.end + chunk.start, note.pitch))
    return owned
