"""AudioToText web app: upload audio, pick languages and output format, download the result."""
import os
import threading
import traceback
import uuid
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from engine import diarize, translate
from engine.formats import FORMATS, render
from engine.languages import LANGUAGES
from engine.pipeline import process_audio

BASE = Path(__file__).parent
UPLOADS = BASE / "uploads"
OUTPUTS = BASE / "outputs"
UPLOADS.mkdir(exist_ok=True)
OUTPUTS.mkdir(exist_ok=True)

ALLOWED = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".aac", ".wma",
           ".mp4", ".mkv", ".mov", ".webm", ".avi"}
MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_UPLOAD_MB", "1024")) * 1024 * 1024

jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()


def _update(job_id: str, **fields):
    with jobs_lock:
        jobs[job_id].update(fields)


def _run_job(job_id: str, path: Path, source: str | None, target: str | None,
             fmt: str, model_size: str):
    def progress(stage, fraction):
        _update(job_id, stage=stage, progress=round(fraction * 100))

    try:
        transcript = process_audio(str(path), source_lang=source, target_lang=target,
                                   speakers=(fmt == "meeting"), model_size=model_size,
                                   progress=progress)
        content, ext = render(transcript, fmt)
        suffix = (f".{target}" if target else "") + (".meeting" if fmt == "meeting" else "")
        out_name = f"{Path(jobs[job_id]['filename']).stem}{suffix}{ext}"
        out_path = OUTPUTS / f"{job_id}{ext}"
        out_path.write_text(content, encoding="utf-8")
        _update(job_id, status="done", stage="done", progress=100, output=str(out_path),
                output_name=out_name, preview=content[:5000],
                detected_language=transcript.language)
    except Exception as exc:  # report any failure to the page
        traceback.print_exc()
        _update(job_id, status="error", error=str(exc))
    finally:
        path.unlink(missing_ok=True)


@app.get("/")
def index():
    return render_template("index.html", languages=LANGUAGES, formats=FORMATS,
                           model_sizes=MODEL_SIZES,
                           default_model=os.environ.get("WHISPER_MODEL", "small"),
                           speakers_ready=diarize.is_available(),
                           ollama_ready=translate.is_reachable())


@app.post("/jobs")
def create_job():
    file = request.files.get("audio")
    if not file or not file.filename:
        return jsonify(error="Please choose an audio file."), 400
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED:
        return jsonify(error=f"Unsupported file type {ext}."), 400

    source = request.form.get("source") or None
    target = request.form.get("target") or None
    fmt = request.form.get("format", "text")
    model_size = request.form.get("model") or os.environ.get("WHISPER_MODEL", "small")
    if fmt not in FORMATS or model_size not in MODEL_SIZES:
        return jsonify(error="Invalid option."), 400
    if source and source not in LANGUAGES or target and target not in LANGUAGES:
        return jsonify(error="Unknown language."), 400
    if source and target == source:
        target = None

    job_id = uuid.uuid4().hex
    path = UPLOADS / f"{job_id}{ext}"
    file.save(path)
    with jobs_lock:
        jobs[job_id] = {"status": "running", "stage": "starting", "progress": 0,
                        "filename": secure_filename(file.filename) or "audio"}
    threading.Thread(target=_run_job, args=(job_id, path, source, target, fmt, model_size),
                     daemon=True).start()
    return jsonify(id=job_id)


@app.get("/jobs/<job_id>")
def job_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            abort(404)
        return jsonify({k: v for k, v in job.items() if k != "output"})


@app.get("/jobs/<job_id>/download")
def download(job_id):
    job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        abort(404)
    return send_file(job["output"], as_attachment=True, download_name=job["output_name"])


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")))
