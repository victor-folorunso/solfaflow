import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server  # noqa: E402


@pytest.mark.parametrize("stem, expected", [
    ("Frozen_-_Let_It_Go_Malay_(mp3.pm)", "Frozen Let It Go Malay"),
    ("Singing-Bell-feat.-Sonia-Ter-Hovanessian-Mary-Had-a-Little-Lamb",
     "Singing Bell feat. Sonia Ter Hovanessian Mary Had a Little Lamb"),
    ("Amazing Grace - Live", "Amazing Grace - Live"),  # already readable: hyphen kept
    ("la_cucaracha", "la cucaracha"),
    ("Song [example.com]", "Song"),
])
def test_pretty_name(stem, expected):
    assert server.pretty_name(stem) == expected


def test_song_name_survives_restart_via_job_file(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "OUTPUT", tmp_path)
    server.save_job_metadata({"id": "abc123", "name": "Let It Go", "created": 1.0,
                              "seconds": None, "do": None, "skip_separation": False})
    assert server.song_name(tmp_path / "abc123") == "Let It Go"


def test_song_name_falls_back_to_player_title(tmp_path):
    (tmp_path / "player.html").write_text("<title>la_cucaracha · SolfaFlow</title>", encoding="utf-8")
    assert server.song_name(tmp_path) == "la cucaracha"


def test_unfinished_result_is_marked_after_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "OUTPUT", tmp_path)
    monkeypatch.setattr(server, "jobs", {})
    out = tmp_path / "job1"
    out.mkdir()
    (out / "solfa.json").write_text(json.dumps({"do": "A", "notes": [], "duration": 60.0,
                                                "complete": False, "processed_seconds": 33.4}))
    server.register_existing_results()
    job = server.jobs["job1"]
    assert job["status"] == "error"
    assert job["player_ready"]
    assert "33s" in job["error"]
