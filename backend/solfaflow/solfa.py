"""Deterministic pitch-to-solfa mapping.

This module does not perform audio transcription or key detection. It maps
already-detected MIDI pitches relative to a user-supplied tonic.
"""

from dataclasses import dataclass

MAJOR_DEGREES = ("do", "re", "mi", "fa", "so", "la", "ti")
MINOR_DEGREES = ("la", "ti", "do", "re", "mi", "fa", "so")
RAISED_SYLLABLES = {1: "di", 3: "ri", 4: "fi", 6: "si", 8: "li"}
MAJOR_OFFSETS = (0, 2, 4, 5, 7, 9, 11)
NATURAL_MINOR_OFFSETS = (0, 2, 3, 5, 7, 8, 10)


@dataclass(frozen=True)
class SolfaMapping:
    syllable: str
    semitone_from_tonic: int
    octave: int


def pitch_to_solfa(
    pitch_midi: int,
    tonic_midi: int,
    mode: str = "major",
    chromatic_style: str = "raised",
) -> SolfaMapping:
    """Map a MIDI pitch to movable-do syllables relative to a tonic.

    Octave does not change the syllable; it is returned separately so a
    renderer can distinguish low, middle, and high registers.

    The raised style uses conventional raised chromatic syllables where
    available. The scale_degree style marks chromatic pitches with a plus
    sign rather than assuming one universal chromatic naming convention.
    """
    if not 0 <= pitch_midi <= 127 or not 0 <= tonic_midi <= 127:
        raise ValueError("MIDI pitches must be between 0 and 127")
    if mode not in {"major", "minor"}:
        raise ValueError("mode must be 'major' or 'minor'")
    if chromatic_style not in {"raised", "scale_degree"}:
        raise ValueError("unsupported chromatic style")

    offsets = MAJOR_OFFSETS if mode == "major" else NATURAL_MINOR_OFFSETS
    degrees = MAJOR_DEGREES if mode == "major" else MINOR_DEGREES
    relative = pitch_midi - tonic_midi
    octave, pitch_class = divmod(relative, 12)

    if pitch_class in offsets:
        degree_index = offsets.index(pitch_class)
        return SolfaMapping(degrees[degree_index], relative, octave)

    lower_degree = max(i for i, offset in enumerate(offsets) if offset < pitch_class)
    if chromatic_style == "raised":
        raised_name = RAISED_SYLLABLES.get(pitch_class)
        if raised_name:
            return SolfaMapping(raised_name, relative, octave)

    return SolfaMapping(f"{degrees[lower_degree]}+", relative, octave)
