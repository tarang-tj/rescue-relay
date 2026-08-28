from fastapi.testclient import TestClient

import rescue_relay.api as api_module
from rescue_relay.api import create_app


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
