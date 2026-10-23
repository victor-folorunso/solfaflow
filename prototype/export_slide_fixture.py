"""Write the fixture that checks the frontend's cleanSlides against keyboard.clean_slides.

The player re-cleans slides in the browser when the user changes do, so the
TypeScript copy (frontend/src/lib/solfa.ts) must agree with the Python one.
This exports both real-song fixtures with Python's answer for every possible do;
frontend/src/lib/slides.test.ts replays them, and tests/test_slide_fixture.py
fails if this file is stale.

Usage: python export_slide_fixture.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from keyboard import RawNote, to_solfa

HERE = Path(__file__).resolve().parent
SONGS = {
    "la_cucaracha": HERE / "tests" / "fixtures" / "la_cucaracha_game_notes.csv",
    "mary_had_a_little_lamb": HERE / "tests" / "fixtures" / "mary_had_a_little_lamb_game_notes.csv",
}
FIXTURE = HERE / "frontend" / "src" / "lib" / "slides.fixture.json"


def build() -> dict:
    songs = {}
    for name, path in SONGS.items():
        with open(path, newline="") as f:
            raw = [RawNote(float(r["onset"]), float(r["offset"]), float(r["pitch"])) for r in csv.DictReader(f)]
        by_do = [to_solfa(raw, do_pitch_class=pc) for pc in range(12)]
        songs[name] = {
            "notes": [{"start": n["start"], "end": n["end"], "pitch_midi": n["exact_pitch_midi"],
                       "exact_pitch_midi": n["exact_pitch_midi"], "tuned_pitch": n["tuned_pitch"]}
                      for n in by_do[0]["notes"]],
            "minor_by_do": by_do[0]["minor_by_do"],
            "cleaned_by_do": [[n["pitch_midi"] for n in result["notes"]] for result in by_do],
        }
    return songs


def render() -> str:
    return json.dumps(build(), separators=(",", ":")) + "\n"


if __name__ == "__main__":
    FIXTURE.write_text(render(), encoding="utf-8")
    print(f"wrote {FIXTURE}")
