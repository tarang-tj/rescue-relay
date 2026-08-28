import json
from pathlib import Path

from fastapi.testclient import TestClient

import rescue_relay.api as api_module
from rescue_relay.api import create_app
from rescue_relay.fixtures import demo_offers, demo_pantries


def _event_inputs(*, pounds: int = 48) -> dict:
    offer = demo_offers()[1].model_copy(update={"pounds": pounds})
    pantry = next(item for item in demo_pantries() if item.id == "pantry-riverside")
    return {
        "offers": [offer.model_dump(mode="json")],
        "partners": [pantry.model_dump(mode="json")],
    }


def test_api_core_workflow(tmp_path):
    app = create_app(tmp_path / "api.db")
    client = TestClient(app)

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["outbound_send_capability"] is False

    result = client.post("/api/runs", json={"mode": "demo"})
    assert result.status_code == 200
    assert result.json()["impact"]["pounds_matched"] == 412

    decision_id = result.json()["decisions"][0]["id"]
    approved = client.post(f"/api/decisions/{decision_id}/approve")
    assert approved.status_code == 200
    assert approved.json()["decisions"][0]["state"] == "approved"

    audit = client.get("/api/audit")
    assert audit.status_code == 200
    assert audit.json()["schema_version"] == "1.0"
    assert audit.json()["safety_assertions"]["outbound_send_capability"] is False
    assert audit.json()["safety_assertions"]["event_receipts_expose_raw_payload"] is False


def test_decision_can_be_rejected_but_not_reversed(tmp_path):
    client = TestClient(create_app(tmp_path / "api.db"))
    run = client.post("/api/runs", json={"mode": "demo"}).json()
    decision_id = run["decisions"][0]["id"]

    rejected = client.post(
        f"/api/decisions/{decision_id}/resolve",
        json={"state": "rejected", "note": "Partner unavailable"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["decisions"][0]["state"] == "rejected"

    reversed_decision = client.post(
        f"/api/decisions/{decision_id}/resolve", json={"state": "approved"}
    )
    assert reversed_decision.status_code == 409


def test_invalid_mode_fails_loudly(tmp_path):
    client = TestClient(create_app(tmp_path / "api.db"))
    response = client.post("/api/runs", json={"mode": "pretend-live"})
    assert response.status_code == 422


def test_api_missing_decisions_and_reset(tmp_path):
    client = TestClient(create_app(tmp_path / "api.db"))
    assert client.get("/api/dashboard").json()["active_run"] is None
    assert client.post("/api/decisions/missing/approve").status_code == 404
    assert (
        client.post(
            "/api/decisions/missing/resolve",
            json={"state": "approved", "note": "No such decision"},
        ).status_code
        == 404
    )

    client.post("/api/runs", json={"mode": "demo"})
    reset = client.post("/api/reset")
    assert reset.status_code == 200
    assert reset.json()["active_run"] is None


def test_agent_runtime_failure_returns_service_unavailable(monkeypatch, tmp_path):
    def fail_agent(_service, _mode):
        raise RuntimeError("Bedrock unavailable")

    monkeypatch.setattr(api_module, "run_agent", fail_agent)
    client = TestClient(create_app(tmp_path / "api.db"))

    response = client.post("/api/runs", json={"mode": "demo"})

    assert response.status_code == 503
    assert response.json()["detail"] == "Agent run failed loudly: Bedrock unavailable"


def test_offer_event_runs_agent_in_background_and_deduplicates(tmp_path):
    client = TestClient(create_app(tmp_path / "events.db"))
    payload = {"event_id": "demo-message-batch-001", "source": "demo_inbox", "mode": "demo"}

    accepted = client.post("/api/events/offers", json=payload)
    assert accepted.status_code == 202
    assert accepted.json()["accepted"] is True

    event = client.get("/api/events/demo-message-batch-001")
    assert event.status_code == 200
    assert event.json()["status"] == "completed"
    assert event.json()["run_id"] is not None
    assert event.json()["offer_count"] == 4
    assert event.json()["partner_count"] == 4
    assert len(event.json()["payload_sha256"]) == 64
    first_run_id = event.json()["run_id"]

    duplicate = client.post("/api/events/offers", json=payload)
    assert duplicate.status_code == 200
    assert duplicate.json()["accepted"] is False
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["event"]["run_id"] == first_run_id

    dashboard = client.get("/api/dashboard").json()
    assert dashboard["impact"]["pounds_matched"] == 412
    assert len(dashboard["intake_events"]) == 1
    assert dashboard["run_history"] == []


def test_offer_event_failure_is_visible_without_false_success(monkeypatch, tmp_path):
    def fail_agent(_service, _mode):
        raise RuntimeError("Inbox adapter unavailable")

    monkeypatch.setattr(api_module, "run_agent", fail_agent)
    client = TestClient(create_app(tmp_path / "failed-event.db"))

    response = client.post(
        "/api/events/offers",
        json={"event_id": "demo-message-batch-002", "mode": "demo"},
    )

    assert response.status_code == 202
    event = client.get("/api/events/demo-message-batch-002").json()
    assert event["status"] == "failed"
    assert event["error"] == "RuntimeError: Inbox adapter unavailable"
    assert client.get("/api/dashboard").json()["active_run"] is None


def test_live_offer_events_fail_closed_without_valid_authorization(monkeypatch, tmp_path):
    client = TestClient(create_app(tmp_path / "live-events.db"))
    payload = {
        "event_id": "live-message-batch-001",
        "source": "ses",
        "mode": "live",
        **_event_inputs(),
    }

    assert client.post("/api/events/offers", json=payload).status_code == 503

    monkeypatch.setenv("RESCUERELAY_EVENT_TOKEN", "test-event-secret")
    assert client.post("/api/events/offers", json=payload).status_code == 401

    monkeypatch.setattr(api_module, "run_agent", lambda _service, _mode: "completed")
    accepted = client.post(
        "/api/events/offers",
        json=payload,
        headers={"Authorization": "Bearer test-event-secret"},
    )
    assert accepted.status_code == 202
    assert client.get("/api/events/live-message-batch-001").json()["status"] == "completed"


def test_custom_event_payload_drives_tools_and_conflicting_retry_is_rejected(tmp_path):
    client = TestClient(create_app(tmp_path / "custom-event.db"))
    payload = {
        "event_id": "webhook-offer-0001",
        "source": "partner_webhook",
        "mode": "demo",
        **_event_inputs(pounds=30),
    }

    accepted = client.post("/api/events/offers", json=payload)

    assert accepted.status_code == 202
    receipt = client.get("/api/events/webhook-offer-0001").json()
    assert receipt["status"] == "completed"
    assert receipt["offer_count"] == 1
    assert receipt["partner_count"] == 1
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["impact"]["pounds_matched"] == 30
    assert dashboard["dispatches"][0]["donor"] == "Sunny Bakes"
    assert "four messages" not in dashboard["active_run"]["summary"].lower()
    assert "event source 'partner_webhook'" in dashboard["active_run"]["steps"][0]["detail"]

    conflicting = {**payload, **_event_inputs(pounds=31)}
    response = client.post("/api/events/offers", json=conflicting)
    assert response.status_code == 409
    assert "different normalized payload" in response.json()["detail"]
    assert client.get("/api/dashboard").json()["impact"]["pounds_matched"] == 30


def test_checked_in_offer_event_example_is_executable(tmp_path):
    client = TestClient(create_app(tmp_path / "example-event.db"))
    example = json.loads(
        (Path(__file__).parents[1] / "examples" / "offer-event.json").read_text()
    )

    response = client.post("/api/events/offers", json=example)

    assert response.status_code == 202
    assert response.json()["event"]["offer_count"] == 1
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["impact"]["pounds_matched"] == 36
    assert dashboard["dispatches"][0]["donor"] == "Sample Neighborhood Bakery"


def test_event_payload_and_receipt_survive_store_restart(tmp_path):
    database = tmp_path / "restart-event.db"
    app = create_app(database)
    client = TestClient(app)
    payload = {
        "event_id": "restart-event-0001",
        "source": "partner_webhook",
        "mode": "demo",
        **_event_inputs(pounds=25),
    }
    assert client.post("/api/events/offers", json=payload).status_code == 202
    run_id = client.get("/api/events/restart-event-0001").json()["run_id"]
    app.state.store.close()

    restarted = create_app(database)
    restarted_client = TestClient(restarted)
    duplicate = restarted_client.post("/api/events/offers", json=payload)

    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["event"]["run_id"] == run_id
    persisted = restarted.state.store.load_event_payload("restart-event-0001")
    assert persisted.offers[0].pounds == 25
    assert persisted.partners[0].id == "pantry-riverside"


def test_offer_event_contract_rejects_bad_ids_and_missing_events(tmp_path):
    client = TestClient(create_app(tmp_path / "event-contract.db"))

    assert client.post("/api/events/offers", json={"event_id": "bad id"}).status_code == 422
    assert (
        client.post(
            "/api/events/offers",
            json={
                "event_id": "live-missing-inputs",
                "source": "ses",
                "mode": "live",
            },
        ).status_code
        == 422
    )
    one_sided = {
        "event_id": "one-sided-inputs",
        "mode": "demo",
        "offers": _event_inputs()["offers"],
    }
    assert client.post("/api/events/offers", json=one_sided).status_code == 422
    invalid_window = _event_inputs()
    invalid_window["offers"][0]["pickup_end"] = invalid_window["offers"][0]["pickup_start"]
    assert (
        client.post(
            "/api/events/offers",
            json={"event_id": "invalid-window-0001", "mode": "demo", **invalid_window},
        ).status_code
        == 422
    )
    assert client.get("/api/events/missing-event").status_code == 404
