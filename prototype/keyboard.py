"""Keyboard-oriented post-processing of transcribed melody notes.

Takes raw note events with float pitches (as produced by a singing
transcription model) and turns them into keyboard-playable solfa:

1. estimate the recording's global tuning offset (how far it sits between keys),
2. snap every note to the nearest keyboard key (semitone),
3. drop notes too short to press,
4. estimate which key is "do" (movable do; minor keys are la-based, so they
   share do with their relative major),
5. label each note with a solfa syllable, an octave mark, and a key name.

Everything here is deterministic. Key estimation is a heuristic and the
result should always be user-correctable.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from solfaflow.solfa import pitch_to_solfa  # noqa: E402

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

# Krumhansl-Kessler key profiles, indexed by semitones above the tonic.
MAJOR_PROFILE = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
MINOR_PROFILE = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)


@dataclass(frozen=True)
class RawNote:
    start: float
    end: float
    pitch: float  # MIDI semitones, may be fractional


@dataclass(frozen=True)
class KeyNote:
    start: float
    end: float
    pitch_midi: int
    raw_pitch: float
    tuned_pitch: float  # raw pitch with the tuning offset removed (still fractional)


@dataclass(frozen=True)
class KeyEstimate:
    do_pitch_class: int
    minor: bool  # True if the melody centres on la (relative minor)
    score: float


@dataclass(frozen=True)
class SolfaKeyNote:
    start: float
    end: float
    pitch_midi: int  # after slide cleanup: the key to play
    syllable: str
    octave_mark: str
    key_name: str
    raw_pitch: float
    tuned_pitch: float
    exact_pitch_midi: int  # nearest key to what was sung, before cleanup


def estimate_tuning_offset(notes: list[RawNote]) -> float:
    """Duration-weighted circular mean of each note's distance from the nearest key.

    Returns semitones in [-0.5, 0.5). A positive value means the recording is sharp.
    """
    x = y = 0.0
    for note in notes:
        weight = note.end - note.start
        angle = 2 * math.pi * note.pitch
        x += weight * math.cos(angle)
        y += weight * math.sin(angle)
    if x == 0 and y == 0:
        return 0.0
    offset = math.atan2(y, x) / (2 * math.pi)
    return -0.5 if offset >= 0.5 else offset


def estimate_tuning_curve(notes: list[RawNote], window: float = 10.0) -> list[float]:
    """Per-note tuning offset that follows gradual pitch drift.

    Unaccompanied singers often sag or rise over a song. Each note gets the
    circular-mean offset of the notes within +/- window seconds, and the
    sequence is unwrapped so drift past half a semitone keeps tracking
    instead of jumping to the neighbouring key. Abrupt key changes land on
    whole semitones and so do not move the curve.
    """
    ordered = sorted(notes, key=lambda n: n.start)
    local = [
        estimate_tuning_offset([m for m in ordered if abs(m.start - note.start) <= window])
        for note in ordered
    ]
    curve = []
    for offset in local:
        if curve:
            offset += round(curve[-1] - offset)
        curve.append(offset)
    return curve


def snap_to_keys(
    notes: list[RawNote],
    tuning_offset: float | list[float],
    min_duration: float = 0.07,
) -> list[KeyNote]:
    """Snap pitches to keyboard keys after removing the tuning offset.

    tuning_offset is either one value for the whole song or one per note
    (in start-time order, as returned by estimate_tuning_curve).
    """
    ordered = sorted(notes, key=lambda n: n.start)
    offsets = tuning_offset if isinstance(tuning_offset, list) else [tuning_offset] * len(ordered)
    snapped = []
    for note, offset in zip(ordered, offsets):
        if note.end - note.start < min_duration:
            continue
        pitch = round(note.pitch - offset)
        if not 0 <= pitch <= 127:
            continue
        snapped.append(KeyNote(note.start, note.end, pitch, note.pitch, note.pitch - offset))
    return snapped


def _correlation(a: list[float], b: tuple[float, ...]) -> float:
    mean_a = sum(a) / len(a)
    mean_b = sum(b) / len(b)
    num = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    den = math.sqrt(sum((x - mean_a) ** 2 for x in a) * sum((y - mean_b) ** 2 for y in b))
    return num / den if den else 0.0


FINAL_NOTE_BONUS = 0.05


def estimate_do(notes: list[KeyNote], harmony: list[float] | None = None) -> list[KeyEstimate]:
    """Rank the 12 possible "do" keys for a melody, best first.

    Each candidate do is scored by the better of its major key and its
    relative minor (tonic = la = do + 9 semitones). Melodies usually end on
    their tonic, so a key whose tonic is the final note gets a small bonus;
    this breaks near-ties such as a tune that dwells on so (La Cucaracha).

    harmony, if given, is seconds per pitch class sounding in the
    accompaniment's chords (chords.tone_histogram). Melody and harmony get
    equal weight: a simple tune like Mary Had a Little Lamb uses only four
    notes and sits on mi, which alone looks like E minor, but its C, F and
    G chords point straight at C.
    """
    final_pc = max(notes, key=lambda n: n.end).pitch_midi % 12 if notes else None
    histogram = [0.0] * 12
    for note in notes:
        histogram[note.pitch_midi % 12] += note.end - note.start
    if not any(histogram):
        raise ValueError("no notes to estimate a key from")
    if harmony and any(harmony):
        melody_total, harmony_total = sum(histogram), sum(harmony)
        histogram = [m / melody_total + h / harmony_total for m, h in zip(histogram, harmony)]

    estimates = []
    for do in range(12):
        rotated_major = histogram[do:] + histogram[:do]
        la = (do + 9) % 12
        rotated_minor = histogram[la:] + histogram[:la]
        major_score = _correlation(rotated_major, MAJOR_PROFILE) + FINAL_NOTE_BONUS * (final_pc == do)
        minor_score = _correlation(rotated_minor, MINOR_PROFILE) + FINAL_NOTE_BONUS * (final_pc == la)
        estimates.append(KeyEstimate(do, minor_score > major_score, max(major_score, minor_score)))
    return sorted(estimates, key=lambda e: e.score, reverse=True)


MAJOR_SCALE = (0, 2, 4, 5, 7, 9, 11)
SI = 8  # raised so: the leading tone of a la-based minor key, so it is part of that key
KEEP_CHROMATIC_SECONDS = 0.6
KEEP_CHROMATIC_TOLERANCE = 0.25
PASSING_SPAN = 4  # a passing step fills a third (do-re-mi); wider gaps are slides, not steps


def scale_pitch_classes(do_pitch_class: int, minor: bool) -> set[int]:
    steps = MAJOR_SCALE + ((SI,) if minor else ())
    return {(do_pitch_class + s) % 12 for s in steps}


def clean_slides(notes: list[KeyNote], do_pitch_class: int, minor: bool) -> list[KeyNote]:
    """Move notes that land on a sharp/flat only because the singer slid into a note.

    Singers scoop into notes and pass quickly between them; the transcriber
    then reports pitches between two keys, which snap to a chromatic key
    (e.g. "do ri mi" for a sung "do re mi"). An out-of-key note is moved to
    the nearer in-key neighbour, unless it is held long and sung squarely on
    the chromatic key, which suggests a deliberate chromatic note. If the
    nearer neighbour would just repeat the previous or next note while the
    other neighbour lies between them, and those two are at most a third
    apart, the note is a passing step and goes to the other neighbour
    ("mi ri do" becomes "mi re do", not "mi mi do").

    Mirrored in player_template.html (cleanSlides) so changing do re-cleans.
    """
    scale = scale_pitch_classes(do_pitch_class, minor)
    cleaned: list[KeyNote] = []
    for i, note in enumerate(notes):
        pitch = note.pitch_midi
        held = note.end - note.start >= KEEP_CHROMATIC_SECONDS
        centred = abs(note.tuned_pitch - pitch) <= KEEP_CHROMATIC_TOLERANCE
        if pitch % 12 not in scale and not (held and centred):
            below = next(p for p in range(pitch - 1, pitch - 13, -1) if p % 12 in scale)
            above = next(p for p in range(pitch + 1, pitch + 13) if p % 12 in scale)
            near, far = (below, above) if note.tuned_pitch - below <= above - note.tuned_pitch else (above, below)
            prev = cleaned[-1].pitch_midi if cleaned else None
            nxt = notes[i + 1].pitch_midi if i + 1 < len(notes) else None
            passing = (prev is not None and nxt is not None and abs(prev - nxt) <= PASSING_SPAN
                       and near in (prev, nxt) and min(prev, nxt) < far < max(prev, nxt))
            if passing:
                near = far
            pitch = near
        cleaned.append(KeyNote(note.start, note.end, pitch, note.raw_pitch, note.tuned_pitch))
    return cleaned


def home_do_midi(notes: list[KeyNote], do_pitch_class: int) -> int:
    """The do that puts the melody's median note in the unmarked octave."""
    pitches = sorted(n.pitch_midi for n in notes)
    median = pitches[len(pitches) // 2]
    return median - (median - do_pitch_class) % 12


def key_name(pitch_midi: int) -> str:
    return f"{NOTE_NAMES[pitch_midi % 12]}{pitch_midi // 12 - 1}"


def octave_mark(octave: int) -> str:
    return "'" * octave if octave > 0 else "," * -octave


def label_solfa(notes: list[KeyNote], do_pitch_class: int, minor: bool = False) -> list[SolfaKeyNote]:
    home = home_do_midi(notes, do_pitch_class)
    labelled = []
    for exact, note in zip(notes, clean_slides(notes, do_pitch_class, minor)):
        mapping = pitch_to_solfa(note.pitch_midi, home, mode="major")
        labelled.append(SolfaKeyNote(
            start=note.start,
            end=note.end,
            pitch_midi=note.pitch_midi,
            syllable=mapping.syllable,
            octave_mark=octave_mark(mapping.octave),
            key_name=key_name(note.pitch_midi),
            raw_pitch=note.raw_pitch,
            tuned_pitch=round(note.tuned_pitch, 3),
            exact_pitch_midi=exact.pitch_midi,
        ))
    return labelled


def to_solfa(
    raw_notes: list[RawNote],
    do_pitch_class: int | None = None,
    min_duration: float = 0.07,
    harmony: list[float] | None = None,
) -> dict:
    """Full keyboard post-processing; returns a JSON-serialisable result."""
    offset = estimate_tuning_offset(raw_notes)
    curve = estimate_tuning_curve(raw_notes)
    notes = snap_to_keys(raw_notes, curve, min_duration=min_duration)
    if not notes:
        raise ValueError("no playable notes were detected")
    candidates = estimate_do(notes, harmony)
    chosen = do_pitch_class if do_pitch_class is not None else candidates[0].do_pitch_class
    minor_by_do = [False] * 12
    for c in candidates:
        minor_by_do[c.do_pitch_class] = c.minor
    return {
        "tuning_offset_semitones": round(offset, 3),
        "tuning_drift_semitones": round(curve[-1] - curve[0], 2),
        "do": NOTE_NAMES[chosen],
        "do_pitch_class": chosen,
        "do_source": "user" if do_pitch_class is not None else "estimated",
        "key_evidence": "melody + chords" if harmony and any(harmony) else "melody",
        "key_candidates": [
            {"do": NOTE_NAMES[c.do_pitch_class], "do_pitch_class": c.do_pitch_class,
             "minor": c.minor, "score": round(c.score, 3)}
            for c in candidates[:3]
        ],
        "minor": minor_by_do[chosen],
        "minor_by_do": minor_by_do,  # lets the player re-clean slides when the user changes do
        "notes": [asdict(n) for n in label_solfa(notes, chosen, minor_by_do[chosen])],
    }
