import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from compare_notes import match  # noqa: E402


def test_identical_lists_score_perfectly():
    notes = [(0.0, 0.5, 60), (0.5, 1.0, 62)]
    assert match(notes, notes)["f1"] == 1.0


def test_onset_tolerance_and_pitch_both_required():
    reference = [(0.0, 0.5, 60), (1.0, 1.5, 62), (2.0, 2.5, 64)]
    estimate = [(0.03, 0.5, 60), (1.2, 1.5, 62), (2.0, 2.5, 65)]
    result = match(reference, estimate)
    assert result["matched"] == 1
    assert result["precision"] == round(1 / 3, 3)


def test_each_reference_note_matches_once():
    reference = [(0.0, 0.5, 60)]
    estimate = [(0.0, 0.2, 60), (0.01, 0.5, 60)]
    result = match(reference, estimate)
    assert result["matched"] == 1
    assert result["recall"] == 1.0
    assert result["precision"] == 0.5
