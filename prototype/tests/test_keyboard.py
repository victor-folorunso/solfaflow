import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from keyboard import (  # noqa: E402
    RawNote,
    estimate_do,
    estimate_tuning_curve,
    estimate_tuning_offset,
    snap_to_keys,
    to_solfa,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def scale(start_midi: int, steps=(0, 2, 4, 5, 7, 9, 11, 12), detune: float = 0.0):
    return [RawNote(i * 0.5, i * 0.5 + 0.4, start_midi + s + detune) for i, s in enumerate(steps)]


def test_tuning_offset_detects_sharp_recording():
    assert estimate_tuning_offset(scale(60, detune=0.3)) == pytest.approx(0.3, abs=1e-6)


def test_tuning_offset_handles_wraparound_near_half_semitone():
    # Recording 0.45 semitones flat must not be read as 0.55 sharp.
    assert estimate_tuning_offset(scale(60, detune=-0.45)) == pytest.approx(-0.45, abs=1e-6)


def test_detuned_recording_snaps_to_intended_keys():
    notes = snap_to_keys(scale(60, detune=0.45), estimate_tuning_offset(scale(60, detune=0.45)))
    assert [n.pitch_midi for n in notes] == [60, 62, 64, 65, 67, 69, 71, 72]


def test_gradual_drift_is_followed_but_key_change_is_kept():
    # Singer repeats a C-major scale while sagging about 2 semitones over
    # 160 seconds (a rate seen on a real a cappella recording); the snapped
    # scale must stay in C.
    steps = (0, 2, 4, 5, 7, 9, 11, 12)
    drifting = [RawNote(i * 4.0, i * 4.0 + 0.4, 60 + steps[i % 8] - 0.05 * i) for i in range(40)]
    result = to_solfa(drifting)
    assert result["do"] == "C"
    assert {n["syllable"] for n in result["notes"]} <= {"do", "re", "mi", "fa", "so", "la", "ti"}
    assert result["tuning_drift_semitones"] == pytest.approx(-1.95, abs=0.2)

    # An abrupt whole-tone key change stays a key change.
    jump = [RawNote(i * 0.5, i * 0.5 + 0.4, 60 + steps[i % 8] + (2 if i >= 24 else 0)) for i in range(48)]
    assert [n.pitch_midi for n in snap_to_keys(jump, estimate_tuning_curve(jump))][24] == 62


def test_notes_too_short_to_play_are_dropped():
    notes = [RawNote(0.0, 0.03, 60.0), RawNote(0.1, 0.6, 62.0)]
    assert [n.pitch_midi for n in snap_to_keys(notes, 0.0)] == [62]


def test_estimate_do_finds_g_major_scale():
    notes = snap_to_keys(scale(67), 0.0)
    assert estimate_do(notes)[0].do_pitch_class == 7


def test_real_la_cucaracha_transcription_is_keyed_in_a():
    # GAME notes from the separated vocal of Commons "La_Cucaracha.ogg" (CC BY-SA 3.0).
    # The singer dwells on E (so), which alone makes do = E look best; the
    # final-note bonus picks the true do = A, giving the known chorus s s s d m.
    with open(FIXTURES / "la_cucaracha_game_notes.csv", newline="") as f:
        raw = [RawNote(float(r["onset"]), float(r["offset"]), float(r["pitch"])) for r in csv.DictReader(f)]
    result = to_solfa(raw)
    assert result["do"] == "A"
    syllables = [n["syllable"] for n in result["notes"]]
    # "la cu-ca-ra-cha": s s s d m. The singer's scoop into the third "so" used to read as "si".
    assert syllables[:7] == ["so", "so", "so", "so", "do", "do", "mi"]
    assert all(s in {"do", "re", "mi", "fa", "so", "la", "ti"} for s in syllables)


MARY_VERSE = "mi re do re mi mi mi re re re mi so so mi re do re mi mi mi mi re re mi re do".split()


def edit_distance(a: list[str], b: list[str]) -> int:
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        diag, row[0] = row[0], i
        for j, y in enumerate(b, 1):
            diag, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, diag + (x != y))
    return row[-1]


def test_mary_had_a_little_lamb_matches_known_tune_after_slide_cleanup():
    # GAME notes from a user-supplied recording; reference is the standard tune, three verses in 36 s.
    # The singer slides between do and mi, which used to read as "ri".
    with open(FIXTURES / "mary_had_a_little_lamb_game_notes.csv", newline="") as f:
        raw = [RawNote(float(r["onset"]), float(r["offset"]), float(r["pitch"])) for r in csv.DictReader(f)]
    notes = [n for n in to_solfa(raw, do_pitch_class=0)["notes"] if n["start"] < 36]
    reference = MARY_VERSE * 3
    syllables = ["do", "di", "re", "ri", "mi", "fa", "fi", "so", "si", "la", "li", "ti"]
    exact = [syllables[(n["exact_pitch_midi"] - 60) % 12] for n in notes]
    cleaned = [n["syllable"] for n in notes]
    exact_accuracy = 1 - edit_distance(reference, exact) / len(reference)
    cleaned_accuracy = 1 - edit_distance(reference, cleaned) / len(reference)
    assert cleaned_accuracy > exact_accuracy
    assert cleaned_accuracy >= 0.83  # measured 0.833 (exact: 0.756)
    assert "ri" not in cleaned


def test_long_centred_chromatic_note_is_kept():
    # A held, squarely sung F# in C major is deliberate, not a slide.
    notes = [RawNote(0.0, 0.4, 64), RawNote(0.4, 1.4, 66.05), RawNote(1.4, 1.8, 67)]
    result = to_solfa(notes, do_pitch_class=0)
    assert result["notes"][1]["syllable"] == "fi"


def test_short_slide_between_do_and_mi_becomes_re():
    notes = [RawNote(0.0, 0.3, 60.0), RawNote(0.3, 0.6, 62.95), RawNote(0.6, 0.9, 64.0)]
    result = to_solfa(notes * 1, do_pitch_class=0, min_duration=0.07)
    assert [n["syllable"] for n in result["notes"]] == ["do", "re", "mi"]
    assert result["notes"][1]["exact_pitch_midi"] == 63


def test_minor_melody_is_la_based():
    # A natural minor: do should be C, flagged minor.
    notes = snap_to_keys(scale(57, steps=(0, 2, 3, 5, 7, 8, 10, 12, 0, 7, 0)), 0.0)
    best = estimate_do(notes)[0]
    assert best.do_pitch_class == 0
    assert best.minor


def test_to_solfa_labels_with_octave_marks_and_key_names():
    result = to_solfa(scale(67))
    assert result["do"] == "G"
    syllables = [n["syllable"] + n["octave_mark"] for n in result["notes"]]
    assert syllables == ["do", "re", "mi", "fa", "so", "la", "ti", "do'"]
    assert result["notes"][0]["key_name"] == "G4"


def test_user_chosen_do_overrides_estimate():
    result = to_solfa(scale(67), do_pitch_class=2)
    assert result["do"] == "D"
    assert result["do_source"] == "user"
    assert result["notes"][0]["syllable"] == "fa"


def test_no_notes_raises():
    with pytest.raises(ValueError):
        to_solfa([RawNote(0.0, 0.01, 60.0)])
