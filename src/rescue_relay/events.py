"""Durable, idempotent intake-event orchestration shared by HTTP and AgentCore."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from .domain import IntakeEvent, IntakeEventStatus
from .service import DispatchService
from .store import StateStore

AgentRunner = Callable[[DispatchService, str], str]


def claim_offer_event(
    store: StateStore,
    *,
    event_id: str,
    source: str,
    mode: str,
) -> tuple[IntakeEvent, bool]:
    return store.claim_event(
        IntakeEvent(
            id=event_id,
            source=source,
            mode=mode,
            received_at=datetime.now(UTC),
        )
    )


def process_offer_event(
    store: StateStore,
    service: DispatchService,
    *,
    event_id: str,
    mode: str,
    runner: AgentRunner,
) -> IntakeEvent:
    """Run a claimed event and persist either a completed receipt or its exact failure."""

    store.update_event(event_id, IntakeEventStatus.PROCESSING)
    try:
        runner(service, mode)
        active_run = store.get().active_run
        return store.update_event(
            event_id,
            IntakeEventStatus.COMPLETED,
            completed_at=datetime.now(UTC),
            run_id=active_run.id if active_run else None,
        )
    except Exception as exc:
        return store.update_event(
            event_id,
            IntakeEventStatus.FAILED,
            completed_at=datetime.now(UTC),
            error=f"{type(exc).__name__}: {exc}",
        )
