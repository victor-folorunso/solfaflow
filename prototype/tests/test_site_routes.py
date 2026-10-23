import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from server import SiteFiles  # noqa: E402


@pytest.fixture
def client(tmp_path):
    (tmp_path / "index.html").write_text("home")
    (tmp_path / "200.html").write_text("app shell")
    (tmp_path / "audio-to-tonic-solfa.html").write_text("guide")
    (tmp_path / "robots.txt").write_text("robots")
    app = FastAPI()
    app.mount("/", SiteFiles(directory=tmp_path, html=True))
    return TestClient(app)


def test_home_page(client):
    assert client.get("/").text == "home"


def test_prerendered_page_without_extension(client):
    assert client.get("/audio-to-tonic-solfa").text == "guide"


def test_private_song_page_gets_app_shell(client):
    assert client.get("/songs/abc123").text == "app shell"


def test_missing_asset_is_still_404(client):
    assert client.get("/_app/missing.js").status_code == 404
    assert client.get("/robots.txt").text == "robots"
