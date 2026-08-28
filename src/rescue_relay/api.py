"""FastAPI surface for the operations console."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .agent import run_agent
from .domain import DecisionState
from .service import DispatchService
from .store import StateStore


class RunRequest(BaseModel):
    mode: str = "demo"


class ResolutionRequest(BaseModel):
    state: DecisionState
    note: str | None = None


def create_app(database_path: str | Path | None = None) -> FastAPI:
    path = database_path or os.getenv("RESCUERELAY_DB", "data/rescue_relay.db")
    store = StateStore(path)
    service = DispatchService(store)
    app = FastAPI(title="RescueRelay API", version="0.1.0")
    app.state.store = store
    app.state.service = service
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("RESCUERELAY_ORIGINS", "http://localhost:5173").split(","),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/api/health")
    def health():
        dashboard = store.get()
        return {
            "status": "ok",
            "storage": "sqlite",
            "agent_state": dashboard.active_run.status if dashboard.active_run else "idle",
            "outbound_send_capability": False,
        }

    @app.get("/api/dashboard")
    def dashboard():
        return store.get()

    @app.post("/api/runs")
    def start_run(request: RunRequest):
        if request.mode not in {"demo", "live"}:
            raise HTTPException(status_code=422, detail="mode must be demo or live")
        try:
            run_agent(service, request.mode)
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Agent run failed loudly: {exc}") from exc
        return store.get()

    @app.post("/api/decisions/{decision_id}/approve")
    def approve(decision_id: str):
        try:
            return service.approve(decision_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Decision not found") from exc

    @app.post("/api/decisions/{decision_id}/resolve")
    def resolve(decision_id: str, request: ResolutionRequest):
        try:
            return service.resolve(decision_id, request.state, request.note)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Decision not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/audit")
    def audit():
        return {
            "schema_version": "1.0",
            "generated_at": datetime.now(UTC),
            "safety_assertions": {
                "outbound_send_capability": False,
                "commitments_require_persisted_approval": True,
                "demo_data_labeled": True,
            },
            "dashboard": store.get(),
        }

    @app.post("/api/reset")
    def reset():
        return store.reset()

    frontend = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")

    return app


app = create_app()
