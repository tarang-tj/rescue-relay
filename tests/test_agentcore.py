from __future__ import annotations

import rescue_relay.agentcore_app as agentcore
from rescue_relay.service import DispatchService
from rescue_relay.store import StateStore


def _isolated_service(monkeypatch, tmp_path) -> DispatchService:
    service = DispatchService(StateStore(tmp_path / "agentcore.db"))
    monkeypatch.setattr(agentcore, "service", service)
    return service


def test_agentcore_scan_dashboard_and_approval(monkeypatch, tmp_path):
    service = _isolated_service(monkeypatch, tmp_path)

    scanned = agentcore.invoke({"action": "scan", "mode": "demo"})
    assert scanned["dashboard"]["active_run"]["status"] == "completed"
    assert scanned["dashboard"]["impact"]["pounds_matched"] == 412

    decision_ids = [item["id"] for item in scanned["dashboard"]["decisions"]]
    first = agentcore.invoke({"action": "approve", "decision_id": decision_ids[0]})
    assert first["decisions"][0]["state"] == "approved"

    second = agentcore.invoke(
        {
            "action": "resolve",
            "decision_id": decision_ids[1],
            "state": "approved",
            "note": "Coordinator confirmed with donor",
        }
    )
    harbor = next(item for item in second["dispatches"] if item["offer_id"] == "offer-harbor")
    assert harbor["state"] == "scheduled"
    assert agentcore.invoke({"action": "dashboard"})["active_run"]["id"] == scanned["dashboard"][
        "active_run"
    ]["id"]
    service.store.close()


def test_agentcore_rejection_and_invalid_payloads(monkeypatch, tmp_path):
    service = _isolated_service(monkeypatch, tmp_path)
    scanned = agentcore.invoke({"action": "scan", "mode": "demo"})
    decision_id = scanned["dashboard"]["decisions"][0]["id"]

    rejected = agentcore.invoke(
        {
            "action": "resolve",
            "decision_id": decision_id,
            "state": "rejected",
            "note": "Partner unavailable",
        }
    )
    assert all(item["state"] == "rejected" for item in rejected["decisions"])
    assert next(item for item in rejected["dispatches"] if item["offer_id"] == "offer-harbor")[
        "state"
    ] == "declined"

    assert agentcore.invoke({"action": "resolve"}) == {"error": "decision_id is required"}
    invalid = agentcore.invoke(
        {"action": "resolve", "decision_id": decision_id, "state": "pending"}
    )
    assert "only be approved or rejected" in invalid["error"]
    missing = agentcore.invoke(
        {"action": "resolve", "decision_id": "decision-missing", "state": "approved"}
    )
    assert "decision-missing" in missing["error"]
    assert agentcore.invoke({"action": "delete_everything"}) == {
        "error": "unsupported action: delete_everything"
    }
    service.store.close()


def test_agentcore_cli_prompt_envelope(monkeypatch, tmp_path):
    service = _isolated_service(monkeypatch, tmp_path)

    scanned = agentcore.invoke({"prompt": '{"action":"scan","mode":"demo"}'})
    assert scanned["dashboard"]["impact"]["pounds_matched"] == 412
    assert agentcore.invoke({"prompt": '{"action":"dashboard"}'})["active_run"]["status"] == (
        "completed"
    )
    error = {"error": "prompt must be a JSON object encoded as text"}
    assert agentcore.invoke({"prompt": "scan the inbox"}) == error
    assert agentcore.invoke({"prompt": "[]"}) == error
    assert agentcore.invoke({"prompt": {"action": "dashboard"}}) == error
    service.store.close()


def test_agentcore_event_is_durable_and_idempotent(monkeypatch, tmp_path):
    service = _isolated_service(monkeypatch, tmp_path)
    payload = {
        "action": "event",
        "event_id": "ses-message-0001",
        "source": "ses",
        "mode": "demo",
    }

    first = agentcore.invoke(payload)
    assert first["accepted"] is True
    assert first["event"]["status"] == "completed"
    assert first["event"]["run_id"] == first["dashboard"]["active_run"]["id"]

    duplicate = agentcore.invoke(payload)
    assert duplicate["accepted"] is False
    assert duplicate["duplicate"] is True
    assert duplicate["event"]["run_id"] == first["event"]["run_id"]
    assert duplicate["dashboard"]["run_history"] == []

    assert agentcore.invoke({"action": "event", "event_id": "short"}) == {
        "error": "event_id must be 8-128 URL-safe identifier characters"
    }
    assert agentcore.invoke({"action": "event", "event_id": "invalid event id"}) == {
        "error": "event_id must be 8-128 URL-safe identifier characters"
    }
    assert agentcore.invoke(
        {"action": "event", "event_id": "ses-message-0002", "mode": "pretend"}
    ) == {"error": "mode must be demo or live"}
    assert agentcore.invoke({}) == {"error": "action is required"}
    service.store.close()
