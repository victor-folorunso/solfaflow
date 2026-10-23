"""Chord recognition from the accompaniment (instrument) track.

Method: the classic chroma + triad-template baseline (Fujishima, 1999) with
Viterbi smoothing. Each ~0.1 s frame gets a 12-bin chroma vector (how much of
each pitch class sounds); it is compared to the 24 major/minor triads, and a
dynamic-programming pass picks the best chord sequence while charging a
penalty for every chord change, so labels do not flicker. Quiet frames are
"no chord".

This is a deliberately simple, deterministic baseline: it only knows major
and minor triads (sevenths, suspensions and slash chords map to the nearest
triad), and its accuracy on real songs has not been measured yet.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
HOP = 4096  # ~93 ms at 44.1 kHz
CHANGE_PENALTY = 0.35  # in cosine-similarity units; higher = fewer chord changes
MIN_CHORD_SECONDS = 0.6
MAX_BRIDGED_GAP_SECONDS = 0.5
SILENCE_RATIO = 0.08  # frames quieter than this share of the loudest frame are "no chord"
NO_CHORD = -1

# Major triad (root, major third, fifth) and minor triad (root, minor third, fifth).
_QUALITIES = {"maj": (0, 4, 7), "min": (0, 3, 7)}
TEMPLATES = []  # (root pitch class, quality, unit vector)
for _quality, _intervals in _QUALITIES.items():
    for _root in range(12):
        _v = np.zeros(12)
        _v[[(_root + i) % 12 for i in _intervals]] = 1.0
        TEMPLATES.append((_root, _quality, _v / np.linalg.norm(_v)))


@dataclass(frozen=True)
class Chord:
    start: float
    end: float
    root: int  # pitch class 0-11
    quality: str  # "maj" or "min"

    @property
    def name(self) -> str:
        return NOTE_NAMES[self.root] + ("m" if self.quality == "min" else "")

    def tones(self) -> tuple[int, ...]:
        return tuple((self.root + i) % 12 for i in _QUALITIES[self.quality])


def chroma_frames(audio: np.ndarray, sample_rate: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (chroma [12, T] with unit-length columns, frame energy [T])."""
    import librosa

    mono = audio.mean(axis=1) if audio.ndim == 2 else audio
    chroma = librosa.feature.chroma_cqt(y=mono.astype(np.float32), sr=sample_rate, hop_length=HOP)
    energy = librosa.feature.rms(y=mono.astype(np.float32), hop_length=HOP)[0][: chroma.shape[1]]
    norms = np.linalg.norm(chroma, axis=0)
    return chroma / np.maximum(norms, 1e-9), energy


def decode(chroma: np.ndarray, energy: np.ndarray) -> list[int]:
    """Viterbi over chord states (template index, or NO_CHORD for quiet frames)."""
    frames = chroma.shape[1]
    if frames == 0:
        return []
    templates = np.stack([t[2] for t in TEMPLATES])  # [24, 12]
    similarity = templates @ chroma  # [24, T]
    loud = energy >= SILENCE_RATIO * (energy.max() or 1.0)
    # State 24 is "no chord": it wins on quiet frames and never on loud ones.
    scores = np.vstack([np.where(loud, similarity, -1.0), np.where(loud, -1.0, 1.0)])
    states = scores.shape[0]
    best = scores[:, 0].copy()
    back = np.zeros((states, frames), dtype=int)
    for t in range(1, frames):
        leader = int(np.argmax(best))
        switch = best[leader] - CHANGE_PENALTY
        stay = best
        back[:, t] = np.where(stay >= switch, np.arange(states), leader)
        best = np.maximum(stay, switch) + scores[:, t]
    path = [int(np.argmax(best))]
    for t in range(frames - 1, 0, -1):
        path.append(int(back[path[-1], t]))
    path.reverse()
    return [NO_CHORD if s == len(TEMPLATES) else s for s in path]


def segments(path: list[int], offset: float, frame_seconds: float) -> list[Chord]:
    chords = []
    start = 0
    for t in range(1, len(path) + 1):
        if t == len(path) or path[t] != path[start]:
            if path[start] != NO_CHORD:
                root, quality, _ = TEMPLATES[path[start]]
                chords.append(Chord(offset + start * frame_seconds, offset + t * frame_seconds, root, quality))
            start = t
    return chords


def bridge_gaps(chords: list[Chord], max_gap: float = MAX_BRIDGED_GAP_SECONDS) -> list[Chord]:
    """Let a chord ring through brief quiet moments, such as the space between strums or oom-pah beats.

    Without this, every quiet frame between accompaniment hits reads as
    "no chord" and splits one chord into many short pieces (seen on a real
    recording: 0.28 s gaps, median chord 0.47 s). Longer silences stay.
    """
    out: list[Chord] = []
    for chord in chords:
        if out and 0 < chord.start - out[-1].end <= max_gap:
            out[-1] = Chord(out[-1].start, chord.start, out[-1].root, out[-1].quality)
        out.append(chord)
    return out


def absorb_short(chords: list[Chord], min_seconds: float = MIN_CHORD_SECONDS) -> list[Chord]:
    """Fold chords shorter than min_seconds into the previous chord (passing harmony, not a change)."""
    out: list[Chord] = []
    for chord in chords:
        if out and (chord.end - chord.start < min_seconds or (chord.root, chord.quality) == (out[-1].root, out[-1].quality)):
            if abs(chord.start - out[-1].end) < 1e-6:
                out[-1] = Chord(out[-1].start, chord.end, out[-1].root, out[-1].quality)
                continue
        out.append(chord)
    return out


def recognise(audio: np.ndarray, sample_rate: int, offset: float = 0.0) -> list[Chord]:
    """Chords in an accompaniment signal; times are offset to song time."""
    chroma, energy = chroma_frames(audio, sample_rate)
    return absorb_short(bridge_gaps(segments(decode(chroma, energy), offset, HOP / sample_rate)))


def clip(chords: list[Chord], start: float, end: float) -> list[Chord]:
    """Keep the part of each chord inside [start, end): a chunk's core."""
    return [Chord(max(c.start, start), min(c.end, end), c.root, c.quality)
            for c in chords if c.end > start and c.start < end]


def join(chords: list[Chord]) -> list[Chord]:
    """Merge the same chord continuing across a chunk boundary."""
    out: list[Chord] = []
    for chord in sorted(chords, key=lambda c: c.start):
        if out and (chord.root, chord.quality) == (out[-1].root, out[-1].quality) and chord.start - out[-1].end < 0.2:
            out[-1] = Chord(out[-1].start, chord.end, chord.root, chord.quality)
        else:
            out.append(chord)
    return out


ROMAN = ("I", "bII", "II", "bIII", "III", "IV", "#IV", "V", "bVI", "VI", "bVII", "VII")


def numeral(chord: Chord, do_pitch_class: int) -> str:
    """Chord relative to do, the way keyboardists say "go to the four chord": IV, V, vi…"""
    degree = ROMAN[(chord.root - do_pitch_class) % 12]
    return degree.lower() if chord.quality == "min" else degree


def tone_histogram(chords: list[Chord]) -> list[float]:
    """Seconds each pitch class is part of the harmony; key evidence from the accompaniment."""
    histogram = [0.0] * 12
    for chord in chords:
        for tone in chord.tones():
            histogram[tone] += chord.end - chord.start
    return histogram
