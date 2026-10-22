import pytest
from solfaflow.solfa import pitch_to_solfa


def test_c_major_scale_maps_to_movable_do():
    tonic = 60  # C4
    pitches = [60, 62, 64, 65, 67, 69, 71, 72]
    syllables = [pitch_to_solfa(pitch, tonic).syllable for pitch in pitches]
    assert syllables == ["do", "re", "mi", "fa", "so", "la", "ti", "do"]


def test_same_melody_transposes_with_tonic():
    assert pitch_to_solfa(64, 60).syllable == "mi"
    assert pitch_to_solfa(66, 62).syllable == "mi"


def test_raised_chromatic_pitch():
    assert pitch_to_solfa(61, 60).syllable == "di"


def test_raised_fourth_is_fi():
    assert pitch_to_solfa(66, 60).syllable == "fi"


def test_raised_sixth_is_si():
    assert pitch_to_solfa(68, 60).syllable == "si"


def test_raised_seventh_is_li():
    assert pitch_to_solfa(70, 60).syllable == "li"


def test_fallback_chromatic_pitch_has_marker():
    assert pitch_to_solfa(61, 60, chromatic_style="scale_degree").syllable == "do+"


def test_minor_scale_uses_relative_movable_do_convention():
    tonic = 60
    pitches = [60, 62, 63, 65, 67, 68, 70]
    syllables = [pitch_to_solfa(pitch, tonic, mode="minor").syllable for pitch in pitches]
    assert syllables == ["la", "ti", "do", "re", "mi", "fa", "so"]


def test_invalid_mode_rejected():
    with pytest.raises(ValueError):
        pitch_to_solfa(60, 60, mode="dorian")
