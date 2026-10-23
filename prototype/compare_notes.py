"""Compare two note lists: note-level precision / recall / F1 on onset + pitch.

Uses the usual music-transcription convention (as in mir_eval's onset-only
note metric): a note matches if its onset is within 50 ms and its keyboard key
is the same; each reference note matches at most one estimated note.

Inputs are solfa.json files (keyboard notes) or GAME CSVs (raw notes, pitch
rounded to the nearest key).

Usage:
  python compare_notes.py REFERENCE ESTIMATE [--onset-tolerance 0.05]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def load(path: Path) -> list[tuple[float, float, int]]:
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return [(n["start"], n["end"], n["pitch_midi"]) for n in data["notes"]]
    with open(path, newline="") as f:
        return [(float(r["onset"]), float(r["offset"]), round(float(r["pitch"]))) for r in csv.DictReader(f)]


def match(reference: list, estimate: list, onset_tolerance: float = 0.05) -> dict:
    used = set()
    matched = 0
    for ref_start, _, ref_pitch in reference:
        best = None
        for i, (est_start, _, est_pitch) in enumerate(estimate):
            if i in used or est_pitch != ref_pitch:
                continue
            gap = abs(est_start - ref_start)
            if gap <= onset_tolerance and (best is None or gap < best[0]):
                best = (gap, i)
        if best:
            used.add(best[1])
            matched += 1
    precision = matched / len(estimate) if estimate else 0.0
    recall = matched / len(reference) if reference else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"reference_notes": len(reference), "estimated_notes": len(estimate), "matched": matched,
            "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("reference", type=Path)
    parser.add_argument("estimate", type=Path)
    parser.add_argument("--onset-tolerance", type=float, default=0.05)
    args = parser.parse_args()
    print(json.dumps(match(load(args.reference), load(args.estimate), args.onset_tolerance), indent=2))


if __name__ == "__main__":
    main()
