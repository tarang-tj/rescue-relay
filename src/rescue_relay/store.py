"""Tiny durable state store with atomic SQLite updates."""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .domain import (
    AgentRun,
    Dashboard,
    DecisionState,
    DispatchState,
    EventPayload,
    Evidence,
    Impact,
    IntakeEvent,
    IntakeEventStatus,
    RunStep,
)


def empty_dashboard() -> Dashboard:
    return Dashboard(
        active_run=None,
        dispatches=[],
        decisions=[],
        message_drafts=[],
        evidence=[],
        impact=Impact(pounds_matched=0, meals_estimated=0, minutes_saved=0),
        run_history=[],
        intake_events=[],
    )


class StateStore:
    def __init__(self, path: str | Path = "data/rescue_relay.db") -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._run_lock = threading.Lock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS app_state "
            "(id INTEGER PRIMARY KEY CHECK (id = 1), payload TEXT NOT NULL)"
        )
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS intake_payloads "
            "(event_id TEXT PRIMARY KEY, payload_sha256 TEXT NOT NULL, "
            "payload TEXT NOT NULL, event TEXT NOT NULL)"
        )
        self._connection.commit()
        if self._connection.execute("SELECT COUNT(*) FROM app_state").fetchone()[0] == 0:
            self._write(empty_dashboard())

    def _write(self, dashboard: Dashboard, *, commit: bool = True) -> None:
        payload = dashboard.model_dump_json()
        self._connection.execute(
            "INSERT INTO app_state(id, payload) VALUES(1, ?) "
            "ON CONFLICT(id) DO UPDATE SET payload = excluded.payload",
            (payload,),
        )
        if commit:
            self._connection.commit()

    def get(self) -> Dashboard:
        with self._lock:
            row = self._connection.execute("SELECT payload FROM app_state WHERE id = 1").fetchone()
            return Dashboard.model_validate_json(row[0])

    @contextmanager
    def agent_run_slot(self):
        """Serialize agent runs that share this store while leaving event receipt reads available."""

        with self._run_lock:
            yield

    def update(self, mutate: Callable[[Dashboard], Any]) -> Dashboard:
        with self._lock:
            dashboard = self.get()
            mutate(dashboard)
            self._write(dashboard)
            return dashboard

    def reset(self) -> Dashboard:
        with self._lock:
            dashboard = empty_dashboard()
            self._connection.execute("DELETE FROM intake_payloads")
            self._write(dashboard)
            return dashboard

    def start_run(self, run: AgentRun) -> Dashboard:
        def mutate(dashboard: Dashboard) -> None:
            if dashboard.active_run is not None:
                if dashboard.active_run.status == "running":
                    raise RuntimeError("An agent run is already in progress")
                if all(item.id != dashboard.active_run.id for item in dashboard.run_history):
                    dashboard.run_history.insert(0, dashboard.active_run)
                    dashboard.run_history = dashboard.run_history[:10]
            dashboard.active_run = run

        return self.update(mutate)

    def append_step(self, step: RunStep) -> Dashboard:
        def mutate(dashboard: Dashboard) -> None:
            if dashboard.active_run is None:
                raise RuntimeError("No active run")
            dashboard.active_run.steps.append(step)

        return self.update(mutate)

    def add_evidence(self, evidence: list[Evidence]) -> Dashboard:
        def mutate(dashboard: Dashboard) -> None:
            known = {item.id for item in dashboard.evidence}
            dashboard.evidence.extend(item for item in evidence if item.id not in known)

        return self.update(mutate)

    def claim_event(
        self, event: IntakeEvent, payload: EventPayload
    ) -> tuple[IntakeEvent, bool, bool]:
        """Atomically persist an event payload and report ownership and payload consistency."""

        with self._lock:
            try:
                inserted = self._connection.execute(
                    "INSERT INTO intake_payloads(event_id, payload_sha256, payload, event) "
                    "VALUES(?, ?, ?, ?) "
                    "ON CONFLICT(event_id) DO NOTHING",
                    (
                        event.id,
                        event.payload_sha256,
                        payload.model_dump_json(),
                        event.model_dump_json(),
                    ),
                ).rowcount
                if inserted:
                    dashboard = self.get()
                    dashboard.intake_events.insert(0, event)
                    dashboard.intake_events = dashboard.intake_events[:25]
                    self._write(dashboard)
                    return event, True, True

                row = self._connection.execute(
                    "SELECT payload_sha256, event FROM intake_payloads WHERE event_id = ?", (event.id,)
                ).fetchone()
                if row is None:
                    raise RuntimeError(f"event claim disappeared before lookup: {event.id}")
                persisted = IntakeEvent.model_validate_json(row[1])
                return persisted, False, row[0] == event.payload_sha256
            except Exception:
                self._connection.rollback()
                raise

    def load_event_payload(self, event_id: str) -> EventPayload:
        with self._lock:
            row = self._connection.execute(
                "SELECT payload FROM intake_payloads WHERE event_id = ?", (event_id,)
            ).fetchone()
            if row is None:
                raise KeyError(event_id)
            return EventPayload.model_validate_json(row[0])

    def update_event(
        self,
        event_id: str,
        status: IntakeEventStatus,
        *,
        completed_at: Any = None,
        run_id: str | None = None,
        error: str | None = None,
    ) -> IntakeEvent:
        with self._lock:
            try:
                event = self.get_event(event_id)
                event.status = status
                event.completed_at = completed_at
                event.run_id = run_id
                event.error = error
                dashboard = self.get()
                visible = next(
                    (item for item in dashboard.intake_events if item.id == event_id), None
                )
                if visible is not None:
                    visible.status = status
                    visible.completed_at = completed_at
                    visible.run_id = run_id
                    visible.error = error
                self._write(dashboard, commit=False)
                self._connection.execute(
                    "UPDATE intake_payloads SET event = ? WHERE event_id = ?",
                    (event.model_dump_json(), event_id),
                )
                self._connection.commit()
                return event
            except Exception:
                self._connection.rollback()
                raise

    def get_event(self, event_id: str) -> IntakeEvent:
        with self._lock:
            row = self._connection.execute(
                "SELECT event FROM intake_payloads WHERE event_id = ?", (event_id,)
            ).fetchone()
            if row is None:
                raise KeyError(event_id)
            return IntakeEvent.model_validate_json(row[0])

    def resolve_decision(
        self, decision_id: str, state: DecisionState, resolved_at: Any, note: str | None = None
    ) -> Dashboard:
        def mutate(dashboard: Dashboard) -> None:
            decision = next((item for item in dashboard.decisions if item.id == decision_id), None)
            if decision is None:
                raise KeyError(decision_id)
            if decision.state == state:
                return
            if decision.state != DecisionState.PENDING:
                raise ValueError(f"Decision is already {decision.state}")
            decision.state = state
            decision.resolved_at = resolved_at
            decision.resolution_note = note
            related = [item for item in dashboard.decisions if item.dispatch_id == decision.dispatch_id]
            dispatch = next(item for item in dashboard.dispatches if item.id == decision.dispatch_id)
            if state == DecisionState.REJECTED:
                dispatch.state = DispatchState.DECLINED
                for sibling in related:
                    if sibling.state == DecisionState.PENDING:
                        sibling.state = DecisionState.REJECTED
                        sibling.resolved_at = resolved_at
                        sibling.resolution_note = "Closed because a required decision was declined."
            elif all(item.state == DecisionState.APPROVED for item in related):
                dispatch.state = DispatchState.SCHEDULED

        return self.update(mutate)

    def close(self) -> None:
        self._connection.close()
