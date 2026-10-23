"""Local web UI for the SolfaFlow prototype.

Upload a song in the browser and open the synced solfa player straight away:
the song plays immediately and solfa fills in chunk by chunk as it is transcribed.
Jobs run one at a time on a background thread because each one saturates the CPU.

Run:  .venv/Scripts/python.exe -m uvicorn server:app --port 8765
"""

from __future__ import annotations

import json
import queue
import threading
import time
import traceback
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from keyboard import NOTE_NAMES
from solfaflow_proto import HERE, run

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


def register_existing_results() -> None:
    """Show results from earlier CLI runs so the page is not empty on first launch."""
    for solfa in sorted(OUTPUT.glob("*/solfa.json")):
        data = json.loads(solfa.read_text(encoding="utf-8"))
        job_id = solfa.parent.name
        jobs[job_id] = {
            "id": job_id, "name": job_id, "status": "done", "stage": "done", "player_ready": True,
            "created": solfa.stat().st_mtime, "do": data["do"], "notes": len(data["notes"]),
            "audio_seconds": round(data.get("duration", 0), 1),
        }


@app.on_event("startup")
def startup() -> None:
    OUTPUT.mkdir(exist_ok=True)
    UPLOADS.mkdir(exist_ok=True)
    register_existing_results()
    threading.Thread(target=worker, daemon=True).start()


@app.get("/")
def index() -> FileResponse:
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
        "id": job_id, "name": Path(file.filename).stem[:80], "status": "queued", "stage": "queued",
        "created": time.time(), "upload": str(upload), "seconds": seconds if seconds > 0 else None,
        "do": do or None, "skip_separation": skip_separation,
    }
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


app.mount("/results", NoCacheStaticFiles(directory=OUTPUT, check_dir=False), name="results")
