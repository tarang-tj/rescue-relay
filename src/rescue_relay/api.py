"""FastAPI surface for the operations console."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from hmac import compare_digest
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .agent import run_agent
from .domain import DecisionState, IntakeEvent
from .events import claim_offer_event, process_offer_event
from .service import DispatchService
from .store import StateStore


class RunRequest(BaseModel):
    mode: str = "demo"


class ResolutionRequest(BaseModel):
    state: DecisionState
    note: str | None = None


class OfferEventRequest(BaseModel):
    event_id: str = Field(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]+$")
    source: str = Field(default="demo_inbox", min_length=3, max_length=64)
    mode: Literal["demo", "live"] = "demo"


class OfferEventResponse(BaseModel):
    accepted: bool
    duplicate: bool
    event: IntakeEvent


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
        allow_headers=["Authorization", "Content-Type"],
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

    @app.post(
        "/api/events/offers",
        response_model=OfferEventResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def receive_offer_event(
        request: OfferEventRequest,
        background_tasks: BackgroundTasks,
        response: Response,
        authorization: str | None = Header(default=None),
    ):
        if request.mode == "live":
            expected = os.getenv("RESCUERELAY_EVENT_TOKEN")
            if not expected:
                raise HTTPException(status_code=503, detail="Live event intake is not configured")
            supplied = authorization.removeprefix("Bearer ") if authorization else ""
            if not compare_digest(supplied, expected):
                raise HTTPException(status_code=401, detail="Invalid event authorization")

        event, accepted = claim_offer_event(
            store,
            event_id=request.event_id,
            source=request.source,
            mode=request.mode,
        )
        if accepted:
            background_tasks.add_task(
                process_offer_event,
                store,
                service,
                event_id=event.id,
                mode=request.mode,
                runner=run_agent,
            )
        else:
            response.status_code = status.HTTP_200_OK
        return OfferEventResponse(accepted=accepted, duplicate=not accepted, event=event)

    @app.get("/api/events/{event_id}", response_model=IntakeEvent)
    def event_status(event_id: str):
        try:
            return store.get_event(event_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Event not found") from exc

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
                "offer_events_are_idempotent": True,
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
