import pytest

import rescue_relay.agent as agent_module
from rescue_relay.agent import TOOL_ORDER, build_tools, run_agent
from rescue_relay.fixtures import demo_offers, demo_pantries
from rescue_relay.service import DispatchService
from rescue_relay.store import StateStore


def test_demo_runs_real_strands_tool_loop_end_to_end(tmp_path):
    store = StateStore(tmp_path / "state.db")
    service = DispatchService(store)

    summary = run_agent(service, mode="demo")
    dashboard = store.get()

    assert "two Harbor Market decisions require approval" in summary
    assert dashboard.active_run is not None
    assert dashboard.active_run.status == "completed"
    assert [step.tool for step in dashboard.active_run.steps] == TOOL_ORDER
    assert dashboard.impact.pounds_matched == 412
    assert dashboard.impact.meals_estimated == 286
    assert len(dashboard.decisions) == 2
    assert len(dashboard.message_drafts) == 4
    assert all("not a confirmed pickup" in item.body for item in dashboard.message_drafts)
    assert all(item.state == "pending" for item in dashboard.decisions)


def test_agent_tool_surface_has_no_send_or_calendar_capability(tmp_path):
    service = DispatchService(StateStore(tmp_path / "state.db"))
    names = {item.tool_name for item in build_tools(service)}

    assert names == set(TOOL_ORDER)
    assert not any("send" in name or "calendar" in name or "schedule" in name for name in names)


def test_human_approval_is_idempotent_and_required_for_schedule(tmp_path):
    store = StateStore(tmp_path / "state.db")
    service = DispatchService(store)
    run_agent(service, mode="demo")
    harbor = next(item for item in store.get().dispatches if item.offer_id == "offer-harbor")

    decision_ids = {item.kind: item.id for item in store.get().decisions}
    service.approve(decision_ids["allocation_split"])
    assert next(item for item in store.get().dispatches if item.id == harbor.id).state == "awaiting_approval"

    service.approve(decision_ids["pickup_commitment"])
    service.approve(decision_ids["pickup_commitment"])
    dashboard = store.get()
    assert next(item for item in dashboard.dispatches if item.id == harbor.id).state == "scheduled"
    assert all(item.state == "approved" for item in dashboard.decisions)


def test_rejection_closes_related_commitment_and_declines_dispatch(tmp_path):
    store = StateStore(tmp_path / "state.db")
    service = DispatchService(store)
    run_agent(service, mode="demo")
    split = next(item for item in store.get().decisions if item.kind == "allocation_split")

    dashboard = service.resolve(split.id, "rejected", "Capacity changed")
    harbor = next(item for item in dashboard.dispatches if item.offer_id == "offer-harbor")

    assert harbor.state == "declined"
    assert all(item.state == "rejected" for item in dashboard.decisions)
    resolved = next(item for item in dashboard.decisions if item.id == split.id)
    assert resolved.resolution_note == "Capacity changed"


def test_previous_completed_run_moves_into_bounded_history(tmp_path):
    store = StateStore(tmp_path / "state.db")
    service = DispatchService(store)
    run_agent(service, mode="demo")
    first_id = store.get().active_run.id

    run_agent(service, mode="demo")
    dashboard = store.get()

    assert dashboard.active_run.id != first_id
    assert dashboard.run_history[0].id == first_id


def test_live_mode_uses_configured_bedrock_model_without_network(monkeypatch, tmp_path):
    captured: dict = {}

    def fake_bedrock_model(**kwargs):
        captured.update(kwargs)
        return object()

    class FakeAgent:
        def __init__(self, **kwargs):
            captured["agent_model"] = kwargs["model"]

        def __call__(self, _prompt, *, invocation_state):
            captured["invocation_state"] = invocation_state
            return "Live orchestration completed"

    monkeypatch.setenv("RESCUERELAY_MODEL_ID", "test.bedrock-model-v1")
    monkeypatch.setenv("AWS_REGION", "us-east-2")
    monkeypatch.setattr(agent_module, "BedrockModel", fake_bedrock_model)
    monkeypatch.setattr(agent_module, "Agent", FakeAgent)
    service = DispatchService(StateStore(tmp_path / "live.db"))

    summary = run_agent(service, mode="live")

    assert summary == "Live orchestration completed"
    assert captured["model_id"] == "test.bedrock-model-v1"
    assert captured["region_name"] == "us-east-2"
    assert captured["invocation_state"]["mode"] == "live"
    assert service.store.get().active_run.status == "completed"


def test_agent_failure_is_persisted_and_reraised(monkeypatch, tmp_path):
    class FailingAgent:
        def __init__(self, **_kwargs):
            pass

        def __call__(self, *_args, **_kwargs):
            raise RuntimeError("model unavailable")

    monkeypatch.setattr(agent_module, "Agent", FailingAgent)
    service = DispatchService(StateStore(tmp_path / "failed.db"))

    with pytest.raises(RuntimeError, match="model unavailable"):
        run_agent(service, mode="demo")

    run = service.store.get().active_run
    assert run.status == "failed"
    assert run.error == "RuntimeError: model unavailable"


def test_partial_single_destination_match_requires_low_confidence_decision(tmp_path):
    service = DispatchService(StateStore(tmp_path / "partial.db"))
    service._offers = [
        next(item for item in demo_offers() if item.id == "offer-sunny").model_copy(
            update={"pounds": 100}
        )
    ]
    service._pantries = demo_pantries()
    service.begin_run("demo", "deterministic-tool-loop")

    result = service.optimize_dispatches()
    dashboard = service.store.get()

    assert result["pounds_matched"] == 60
    assert dashboard.dispatches[0].unallocated_pounds == 40
    assert dashboard.dispatches[0].state == "awaiting_approval"
    assert dashboard.decisions[0].kind == "low_confidence"
