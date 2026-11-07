"""FastAPI + static radar board."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from meshcfo_filing_radar.pipeline import run_radar

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / "static"

app = FastAPI(title="MeshCFO Filing Radar", version="0.1.0")
if STATIC.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health() -> dict:
    from meshcfo_filing_radar.config import get_settings

    s = get_settings()
    return {
        "ok": True,
        "product": "MeshCFO Filing Radar",
        "demo": True,
        "inference_mode": s.inference_mode,
        "local_model": str(s.local_model_file),
        "local_model_present": s.local_model_file.is_file(),
        "external_services_enabled": s.enable_external_services,
        "live_llm_ready": s.live_llm_ready,
        "tavily_allowed": s.tavily_allowed,
        "live_triage_model": s.nebius_triage_model,
        "live_deepen_model": s.nebius_deepen_model,
    }


@app.get("/api/scan")
def api_scan(
    offline: bool = Query(False),
    deep_all: bool = Query(True),
    tavily: bool = Query(False),  # external enrichment is off by default
) -> dict:
    pack = run_radar(offline=offline, deep_all=deep_all, use_tavily=tavily)
    return pack.model_dump()
