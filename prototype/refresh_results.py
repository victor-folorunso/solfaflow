"""Re-label existing results with the current post-processing, without re-transcribing.

Every solfa.json stores each note's raw transcribed pitch, so improvements to
keyboard.py (slide cleanup, key estimation), the synth sound or the player can
be applied to old results in seconds. Notes dropped as too short in the
original run stay dropped.

Usage:
  python refresh_results.py            # every result in output/
  python refresh_results.py ID [ID…]   # specific result folders
"""

from __future__ import annotations

import json
import sys

from chords import Chord
from keyboard import RawNote
from server import OUTPUT, song_name
from solfaflow_proto import publish


def refresh(out_dir) -> str:
    data = json.loads((out_dir / "solfa.json").read_text(encoding="utf-8"))
    if data.get("complete") is False:
        return "skipped (still processing or interrupted)"
    notes = [RawNote(n["start"], n["end"], n["raw_pitch"]) for n in data["notes"]]
    chords = [Chord(c["start"], c["end"], c["root"], c["quality"]) for c in data.get("chords", [])]
    do = data["do"] if data.get("do_source") == "user" else None
    keep = {k: data[k] for k in ("engine", "timings_seconds") if k in data}
    result = publish(notes, out_dir, title=song_name(out_dir), duration=data["duration"],
                     processed=data["duration"], complete=True, version=data.get("version", 0) + 1,
                     do=do, min_duration=0.0, extra=keep, chords=chords)
    changed = sum(n["pitch_midi"] != n["exact_pitch_midi"] for n in result["notes"])
    return f"do = {result['do']}, {len(result['notes'])} notes, {changed} slides cleaned"


def main() -> None:
    dirs = [OUTPUT / name for name in sys.argv[1:]] or sorted(p.parent for p in OUTPUT.glob("*/solfa.json"))
    for out_dir in dirs:
        print(f"{out_dir.name}: {refresh(out_dir)}")


if __name__ == "__main__":
    main()
