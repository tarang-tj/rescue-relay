import threading
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from rescue_relay.agent import run_agent
from rescue_relay.domain import EventPayload, Offer, Pantry, RunStep
from rescue_relay.events import claim_offer_event, process_offer_event
from rescue_relay.fixtures import demo_offers, demo_pantries
from rescue_relay.service import DispatchService
from rescue_relay.store import StateStore


def test_event_claim_is_shared_across_store_instances(tmp_path):
    database = tmp_path / "shared-events.db"
    first_store = StateStore(database)
    second_store = StateStore(database)

    first, accepted, matches = claim_offer_event(
        first_store,
        event_id="shared-event-0001",
        source="demo_inbox",
        mode="demo",
    )
    duplicate, accepted_again, matches_again = claim_offer_event(
        second_store,
        event_id="shared-event-0001",
        source="demo_inbox",
        mode="demo",
    )

    assert accepted is True
    assert matches is True
    assert accepted_again is False
    assert matches_again is True
    assert duplicate.payload_sha256 == first.payload_sha256
    assert second_store.load_event_payload(first.id).offers[0].donor == "Harbor Market"
    first_store.close()
    second_store.close()


def test_deduplication_outlives_bounded_dashboard_receipts(tmp_path):
    store = StateStore(tmp_path / "bounded-events.db")
    first_id = "bounded-event-0000"

    for index in range(26):
        _, accepted, matches = claim_offer_event(
            store,
            event_id=f"bounded-event-{index:04d}",
            source="demo_inbox",
            mode="demo",
        )
        assert accepted is True
        assert matches is True

    assert len(store.get().intake_events) == 25
    assert all(item.id != first_id for item in store.get().intake_events)
    assert store.get_event(first_id).id == first_id

    _, accepted_again, matches_again = claim_offer_event(
        store,
        event_id=first_id,
        source="demo_inbox",
        mode="demo",
    )
    assert accepted_again is False
    assert matches_again is True
    store.close()


def test_event_domain_rejects_semantically_unsafe_inputs(tmp_path):
    offer_data = demo_offers()[0].model_dump()
    offer_data["pickup_end"] = offer_data["pickup_start"]
    with pytest.raises(ValidationError, match="pickup_start must be before pickup_end"):
        Offer.model_validate(offer_data)

    pantry_data = demo_pantries()[0].model_dump()
    pantry_data["capacity"] = {"produce": -1}
    with pytest.raises(ValidationError, match="needs and capacity values"):
        Pantry.model_validate(pantry_data)

    closed_pantry_data = demo_pantries()[0].model_dump()
    closed_pantry_data["available_end"] = closed_pantry_data["available_start"]
    with pytest.raises(ValidationError, match="available_start must be before available_end"):
        Pantry.model_validate(closed_pantry_data)

    with pytest.raises(ValidationError, match="offer IDs must be unique"):
        EventPayload(
            offers=[demo_offers()[0], demo_offers()[0]],
            partners=[demo_pantries()[0]],
        )
    with pytest.raises(ValidationError, match="partner IDs must be unique"):
        EventPayload(
            offers=[demo_offers()[0]],
            partners=[demo_pantries()[0], demo_pantries()[0]],
        )

    service = DispatchService(StateStore(tmp_path / "invalid-mode.db"))
    with pytest.raises(ValueError, match="mode must be"):
        run_agent(service, "unsafe")
    service.store.close()


def test_events_are_serialized_within_one_runtime(tmp_path):
    store = StateStore(tmp_path / "serialized-events.db")
    for event_id in ("serialized-event-0001", "serialized-event-0002"):
        claim_offer_event(store, event_id=event_id, source="demo_inbox", mode="demo")

    first_entered = threading.Event()
    second_entered = threading.Event()
    release_first = threading.Event()
    call_lock = threading.Lock()
    call_count = 0

    def controlled_runner(_service, _mode):
        nonlocal call_count
        with call_lock:
            call_count += 1
            current = call_count
        if current == 1:
            first_entered.set()
            assert release_first.wait(timeout=2)
        else:
            second_entered.set()

    first = threading.Thread(
        target=process_offer_event,
        args=(store,),
        kwargs={
            "event_id": "serialized-event-0001",
            "mode": "demo",
            "runner": controlled_runner,
        },
    )
    second = threading.Thread(
        target=process_offer_event,
        args=(store,),
        kwargs={
            "event_id": "serialized-event-0002",
            "mode": "demo",
            "runner": controlled_runner,
        },
    )

    first.start()
    assert first_entered.wait(timeout=2)
    second.start()
    assert second_entered.wait(timeout=0.05) is False
    release_first.set()
    first.join(timeout=2)
    second.join(timeout=2)

    assert not first.is_alive()
    assert not second.is_alive()
    assert second_entered.is_set()
    assert store.get_event("serialized-event-0001").status == "completed"
    assert store.get_event("serialized-event-0002").status == "completed"
    store.close()


def test_store_rejects_overlapping_or_unscoped_run_mutations(tmp_path):
    store = StateStore(tmp_path / "run-guards.db")
    with pytest.raises(RuntimeError, match="No active run"):
        store.append_step(
            RunStep(
                id="step-unscoped",
                tool="test",
                label="Unsafe unscoped step",
                detail="must fail",
                started_at=datetime.now(UTC),
            )
        )

    service = DispatchService(store)
    service.begin_run("demo", "deterministic-tool-loop")
    with pytest.raises(RuntimeError, match="already in progress"):
        service.begin_run("demo", "deterministic-tool-loop")
    store.close()
