"""Local web UI for the SolfaFlow prototype.

Upload a song in the browser and open the synced solfa player straight away:
the song plays immediately and solfa fills in chunk by chunk as it is transcribed.
Jobs run one at a time on a background thread because each one saturates the CPU.

Run:  .venv/Scripts/python.exe -m uvicorn server:app --port 8765
"""

from __future__ import annotations

import html
import json
import queue
import re
import threading
import time
import traceback
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from keyboard import NOTE_NAMES
from solfaflow_proto import HERE, pretty_name, run

OUTPUT = HERE / "output"
UPLOADS = HERE / "uploads"
ALLOWED_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".webm", ".mp4"}
MAX_UPLOAD_BYTES = 60 * 1024 * 1024

app = FastAPI(title="SolfaFlow prototype")
jobs: dict[str, dict] = {}
work_queue: queue.Queue[str] = queue.Queue()
lock = threading.Lock()


def update(job_id: str, **fields) -> None:
    with lock:
        jobs[job_id].update(fields)


def worker() -> None:
    while True:
        job_id = work_queue.get()
        job = jobs[job_id]
        update(job_id, status="running", started=time.time())
        try:
            result = run(
                Path(job["upload"]), OUTPUT / job_id,
                do=job["do"], skip_separation=job["skip_separation"], seconds=job["seconds"],
                title=job["name"], on_progress=lambda progress: update(job_id, **progress),
            )
            update(job_id, status="done", stage="done", finished=time.time(),
                   do=result["do"], notes=len(result["notes"]), audio_seconds=round(result["duration"], 1))
        except Exception as exc:  # surfaced to the UI; the prototype has no retry logic
            traceback.print_exc()
            update(job_id, status="error", error=f"{type(exc).__name__}: {exc}", finished=time.time())


JOB_FILE = "job.json"  # per-result metadata, so song names survive a server restart
PLAYER_TITLE = re.compile(r"<title>(.*?) · SolfaFlow</title>")


def save_job_metadata(job: dict) -> None:
    out_dir = OUTPUT / job["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    keep = ("id", "name", "created", "seconds", "do", "skip_separation")
    (out_dir / JOB_FILE).write_text(json.dumps({k: job[k] for k in keep}, indent=2), encoding="utf-8")


def song_name(out_dir: Path) -> str:
    """The uploaded song's name; results from before job.json existed recover it from the player title."""
    meta = out_dir / JOB_FILE
    if meta.exists():
        return pretty_name(json.loads(meta.read_text(encoding="utf-8"))["name"])
    player = out_dir / "player.html"
    if player.exists():
        match = PLAYER_TITLE.search(player.read_text(encoding="utf-8"))
        if match:
            return pretty_name(html.unescape(match.group(1)))
    return pretty_name(out_dir.name)


def register_existing_results() -> None:
    """Show earlier results (from the web UI or the CLI) after a restart."""
    for solfa in sorted(OUTPUT.glob("*/solfa.json")):
        data = json.loads(solfa.read_text(encoding="utf-8"))
        out_dir = solfa.parent
        meta = out_dir / JOB_FILE
        created = json.loads(meta.read_text(encoding="utf-8"))["created"] if meta.exists() else solfa.stat().st_mtime
        job = {
            "id": out_dir.name, "name": song_name(out_dir), "status": "done", "stage": "done", "player_ready": True,
            "created": created, "do": data["do"], "notes": len(data["notes"]),
            "audio_seconds": round(data.get("duration", 0), 1),
        }
        if data.get("complete") is False:  # the server stopped while this song was still being transcribed
            job |= {"status": "error", "error": f"Stopped at {data.get('processed_seconds', 0):.0f}s when the "
                                                  "server restarted. What was finished can still be opened."}
        jobs[job["id"]] = job


@app.on_event("startup")
def startup() -> None:
    OUTPUT.mkdir(exist_ok=True)
    UPLOADS.mkdir(exist_ok=True)
    register_existing_results()
    threading.Thread(target=worker, daemon=True).start()


SITE = HERE / "frontend" / "build"  # `npm run build` in frontend/


if not SITE.exists():
    @app.get("/")
    def index() -> FileResponse:
        """Fallback upload page for when the SvelteKit site has not been built."""
        return FileResponse(HERE / "web" / "index.html")


@app.post("/api/jobs")
async def create_job(
    file: UploadFile = File(...),
    seconds: float = Form(60),
    do: str = Form(""),
    skip_separation: bool = Form(False),
) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(400, f"Unsupported file type '{suffix}'. Use one of: {', '.join(sorted(ALLOWED_SUFFIXES))}")
    if do and do not in NOTE_NAMES:
        raise HTTPException(400, "do must be a note name like C, F# or A")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File is larger than 60 MB")

    job_id = uuid.uuid4().hex[:10]
    upload = UPLOADS / f"{job_id}{suffix}"
    upload.write_bytes(data)
    jobs[job_id] = {
        "id": job_id, "name": pretty_name(Path(file.filename).stem), "status": "queued", "stage": "queued",
        "created": time.time(), "upload": str(upload), "seconds": seconds if seconds > 0 else None,
        "do": do or None, "skip_separation": skip_separation,
    }
    save_job_metadata(jobs[job_id])
    work_queue.put(job_id)
    return public(jobs[job_id])


def public(job: dict) -> dict:
    return {k: v for k, v in job.items() if k != "upload"} | {"queue_position": queue_position(job["id"])}


def queue_position(job_id: str) -> int | None:
    queued = [j["id"] for j in sorted(jobs.values(), key=lambda j: j["created"]) if j["status"] == "queued"]
    return queued.index(job_id) + 1 if job_id in queued else None


@app.get("/api/jobs")
def list_jobs() -> list[dict]:
    with lock:
        return [public(j) for j in sorted(jobs.values(), key=lambda j: j["created"], reverse=True)]


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    if job_id not in jobs:
        raise HTTPException(404, "No such job")
    return public(jobs[job_id])


class NoCacheStaticFiles(StaticFiles):
    """Results change while a job runs, so the browser must always re-fetch them."""

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-store"
        return response


class SiteFiles(StaticFiles):
    """The built SvelteKit site.

    Prerendered pages are written as "<page>.html" (clean URLs without the
    extension), and private song pages are rendered in the browser from the
    200.html shell.
    """

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404 or Path(path).suffix:
                raise
            page = Path(self.directory) / f"{path}.html"
            return FileResponse(page if page.is_file() else Path(self.directory) / "200.html")


app.mount("/results", NoCacheStaticFiles(directory=OUTPUT, check_dir=False), name="results")
if SITE.exists():
    app.mount("/", SiteFiles(directory=SITE, html=True), name="site")  # last: everything not matched above
