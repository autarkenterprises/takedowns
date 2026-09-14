"""
FastAPI web instance for GrokBot: scan controls, run history, published audit.
"""

from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER

from takedowns_grokbot.grok_client import GrokClient
from takedowns_grokbot.queue_store import CandidateQueue
from takedowns_grokbot.scanner import run_scan

# Package layout: grokbot/ is the project root (templates/, data/, src/).
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

CATALOG_PATH = Path(os.environ.get("GROKBOT_CATALOG", str(ROOT.parent / "instances.txt")))
README_PATH = Path(os.environ.get("GROKBOT_README", str(ROOT.parent / "README.md")))
QUEUE_DIR = Path(os.environ.get("GROKBOT_QUEUE", str(ROOT / "data" / "candidates")))
RUNS_DIR = Path(os.environ.get("GROKBOT_RUNS", str(ROOT / "data" / "runs")))
TEMPLATES = Jinja2Templates(directory=str(ROOT / "templates"))

INTERVAL_HOURS = float(os.environ.get("GROKBOT_INTERVAL_HOURS", "24"))
ADMIN_TOKEN = os.environ.get("GROKBOT_ADMIN_TOKEN", "")

_scheduler: BackgroundScheduler | None = None
_last_error: str = ""
_last_report: str = ""


def _check_form_token(token: str | None) -> None:
    """Shared-secret gate for mutating actions when GROKBOT_ADMIN_TOKEN is set."""
    if not ADMIN_TOKEN:
        return
    if not token or not secrets.compare_digest(token, ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="invalid admin token")


def _do_scan() -> None:
    """Shared scan path for scheduler and manual trigger."""
    global _last_error, _last_report
    try:
        client = GrokClient()
        report = run_scan(
            catalog_path=CATALOG_PATH,
            readme_path=README_PATH,
            queue_dir=QUEUE_DIR,
            runs_dir=RUNS_DIR,
            client=client,
        )
        _last_error = ""
        _last_report = (
            f"{report.run_id}: discovered={report.discovered} "
            f"accepted={report.accepted} rejected={report.rejected} — {report.notes}"
        )
    except Exception as exc:  # noqa: BLE001 - surface to UI
        _last_error = str(exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    _scheduler = BackgroundScheduler()
    if os.environ.get("GROKBOT_ENABLE_SCHEDULER", "1") not in ("0", "false", "False"):
        _scheduler.add_job(
            _do_scan,
            "interval",
            hours=INTERVAL_HOURS,
            id="grokbot_scan",
            replace_existing=True,
        )
        _scheduler.start()
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)


app = FastAPI(title="Takedowns GrokBot", lifespan=lifespan)


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
            "interval_hours": INTERVAL_HOURS,
            "last_error": _last_error,
            "last_report": _last_report,
            "catalog_path": str(CATALOG_PATH),
            "readme_path": str(README_PATH),
            "token_required": bool(ADMIN_TOKEN),
            "has_api_key": bool(os.environ.get("XAI_API_KEY")),
        },
    )


@app.post("/scan")
def trigger_scan(token: str | None = Form(default=None)):
    _check_form_token(token)
    _do_scan()
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
    """Factory for uvicorn: ``uvicorn takedowns_grokbot.web:app``."""
    return app
