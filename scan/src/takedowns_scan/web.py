"""
FastAPI debug UI: ingest Cloud Agent JSON, inspect queue/run logs.

Discovery is not performed here. Production discovery is the Cursor Cloud
Agent using the account's native model.
"""

from __future__ import annotations

import os
import secrets
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER

from takedowns_scan.queue_store import CandidateQueue
from takedowns_scan.scanner import StaticCandidateSource, run_scan

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

CATALOG_PATH = Path(os.environ.get("SCAN_CATALOG", str(ROOT.parent / "instances.txt")))
README_PATH = Path(os.environ.get("SCAN_README", str(ROOT.parent / "README.md")))
QUEUE_DIR = Path(os.environ.get("SCAN_QUEUE", str(ROOT / "data" / "candidates")))
RUNS_DIR = Path(os.environ.get("SCAN_RUNS", str(ROOT / "data" / "runs")))
TEMPLATES = Jinja2Templates(directory=str(ROOT / "templates"))
ADMIN_TOKEN = os.environ.get("SCAN_ADMIN_TOKEN", "")

_last_error: str = ""
_last_report: str = ""


def _check_form_token(token: str | None) -> None:
    if not ADMIN_TOKEN:
        return
    if not token or not secrets.compare_digest(token, ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="invalid admin token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Takedowns catalog ingest", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    queue = CandidateQueue(QUEUE_DIR)
    published = queue.list_by_status("published")
    rejected = queue.list_by_status("rejected_auto")
    runs = sorted(RUNS_DIR.glob("*.json"), reverse=True)[:10] if RUNS_DIR.exists() else []
    return TEMPLATES.TemplateResponse(
        request,
        "dashboard.html",
        {
            "published": published[:30],
            "rejected": rejected[:20],
            "runs": [p.name for p in runs],
            "last_error": _last_error,
            "last_report": _last_report,
            "catalog_path": str(CATALOG_PATH),
            "readme_path": str(README_PATH),
            "token_required": bool(ADMIN_TOKEN),
        },
    )


@app.post("/ingest")
async def ingest_json(
    inbox: UploadFile = File(...),
    token: str | None = Form(default=None),
):
    """Debug ingest of Cloud Agent candidate JSON (same gates as production)."""
    global _last_error, _last_report
    _check_form_token(token)
    try:
        raw = await inbox.read()
        with tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False) as tmp:
            tmp.write(raw)
            tmp_path = Path(tmp.name)
        report = run_scan(
            catalog_path=CATALOG_PATH,
            readme_path=README_PATH,
            queue_dir=QUEUE_DIR,
            runs_dir=RUNS_DIR,
            client=StaticCandidateSource.from_json_file(tmp_path),
        )
        tmp_path.unlink(missing_ok=True)
        _last_error = ""
        _last_report = (
            f"{report.run_id}: discovered={report.discovered} "
            f"accepted={report.accepted} rejected={report.rejected} — {report.notes}"
        )
    except Exception as exc:  # noqa: BLE001
        _last_error = str(exc)
    return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)


@app.get("/candidate/{candidate_id}", response_class=HTMLResponse)
def candidate_detail(request: Request, candidate_id: str):
    queue = CandidateQueue(QUEUE_DIR)
    item = queue.get(candidate_id)
    if item is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    return TEMPLATES.TemplateResponse(
        request,
        "candidate.html",
        {"item": item, "token_required": bool(ADMIN_TOKEN)},
    )


def create_app() -> FastAPI:
    return app
