import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from chords import Chord, absorb_short, bridge_gaps, clip, join, numeral, recognise, tone_histogram  # noqa: E402

SR = 22050


def triad(root_midi: int, minor: bool, seconds: float) -> np.ndarray:
    t = np.arange(int(seconds * SR)) / SR
    tones = (0, 3 if minor else 4, 7)
    return sum(np.sin(2 * np.pi * 440 * 2 ** ((root_midi + i - 69) / 12) * t) for i in tones) / 3


def test_recognises_a_simple_progression():
    # C - F - G - Am, two seconds each, as plain sine-wave triads.
    audio = np.concatenate([triad(60, False, 2), triad(65, False, 2), triad(67, False, 2), triad(57, True, 2)])
    chords = recognise(audio.astype(np.float32), SR)
    assert [c.name for c in chords] == ["C", "F", "G", "Am"]
    assert chords[1].start == pytest.approx(2.0, abs=0.25)


def test_silence_is_no_chord():
    audio = np.concatenate([triad(60, False, 2), np.zeros(SR * 2), triad(67, False, 2)])
    names = [c.name for c in recognise(audio.astype(np.float32), SR)]
    assert names == ["C", "G"]


def test_chord_rings_through_short_gaps_between_strums():
    # Strummed C then G: 0.35 s hits with 0.25 s of near-silence between them.
    hit = lambda root: np.concatenate([triad(root, False, 0.35), np.zeros(int(0.25 * SR))])
    audio = np.concatenate([hit(60) for _ in range(5)] + [hit(67) for _ in range(5)])
    chords = recognise(audio.astype(np.float32), SR)
    assert [c.name for c in chords] == ["C", "G"]


def test_long_silence_is_not_bridged():
    chords = [Chord(0, 2, 0, "maj"), Chord(3, 5, 7, "maj")]
    assert [(c.start, c.end) for c in bridge_gaps(chords)] == [(0, 2), (3, 5)]


def test_short_chord_is_folded_into_previous():
    chords = [Chord(0, 2, 0, "maj"), Chord(2, 2.3, 2, "min"), Chord(2.3, 4, 0, "maj")]
    assert [(c.name, c.end) for c in absorb_short(chords)] == [("C", 4)]


def test_clip_and_join_across_chunk_boundary():
    first = clip([Chord(8, 14, 0, "maj")], 0, 11)
    second = clip([Chord(8, 14, 0, "maj"), Chord(14, 20, 7, "maj")], 11, 33)
    assert [(c.name, c.start, c.end) for c in join(first + second)] == [("C", 8, 14), ("G", 14, 20)]


def test_numerals_are_relative_to_do():
    assert numeral(Chord(0, 1, 5, "maj"), do_pitch_class=0) == "IV"
    assert numeral(Chord(0, 1, 9, "min"), do_pitch_class=0) == "vi"
    assert numeral(Chord(0, 1, 2, "maj"), do_pitch_class=9) == "IV"  # D chord in A


def test_tone_histogram_counts_chord_tones():
    histogram = tone_histogram([Chord(0, 2, 0, "maj")])
    assert [histogram[pc] for pc in (0, 4, 7)] == [2, 2, 2]
    assert sum(histogram) == 6
