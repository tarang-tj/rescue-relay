"""Durable, idempotent intake-event orchestration shared by HTTP and AgentCore."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from hashlib import sha256

from .domain import EventPayload, IntakeEvent, IntakeEventStatus, Offer, Pantry
from .fixtures import demo_offers, demo_pantries
from .service import DispatchService
from .store import StateStore

AgentRunner = Callable[[DispatchService, str], str]


def claim_offer_event(
    store: StateStore,
    *,
    event_id: str,
    source: str,
    mode: str,
    offers: list[Offer] | None = None,
    partners: list[Pantry] | None = None,
) -> tuple[IntakeEvent, bool, bool]:
    """Validate and atomically claim the exact normalized inputs for one source event."""

    if mode == "demo" and offers is None and partners is None:
        offers = demo_offers()
        partners = demo_pantries()
    elif offers is None or partners is None:
        raise ValueError("offers and partners are both required for non-fixture events")

    payload = EventPayload(offers=offers, partners=partners)
    canonical_claim = json.dumps(
        {"mode": mode, "source": source, "payload": payload.model_dump(mode="json")},
        sort_keys=True,
        separators=(",", ":"),
    )
    payload_digest = sha256(canonical_claim.encode()).hexdigest()
    return store.claim_event(
        IntakeEvent(
            id=event_id,
            source=source,
            mode=mode,
            received_at=datetime.now(UTC),
            payload_sha256=payload_digest,
            offer_count=len(payload.offers),
            partner_count=len(payload.partners),
        ),
        payload,
    )


def process_offer_event(
    store: StateStore,
    *,
    event_id: str,
    mode: str,
    runner: AgentRunner,
) -> IntakeEvent:
    """Run a claimed event and persist either a completed receipt or its exact failure."""

    with store.agent_run_slot():
        store.update_event(event_id, IntakeEventStatus.PROCESSING)
        try:
            event = store.get_event(event_id)
            payload = store.load_event_payload(event_id)
            service = DispatchService(
                store,
                offers=payload.offers,
                pantries=payload.partners,
                source_label=f"event source '{event.source}'",
            )
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
