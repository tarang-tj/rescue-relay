"""Amazon Bedrock AgentCore Runtime entrypoint."""

import json
import re

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from .agent import run_agent
from .domain import DecisionState
from .events import claim_offer_event, process_offer_event
from .service import DispatchService
from .store import StateStore

app = BedrockAgentCoreApp()
service = DispatchService(StateStore("/tmp/rescue-relay-agentcore.db"))


@app.entrypoint
def invoke(payload: dict):
    # The current AgentCore CLI sends its argument as a string under `prompt`.
    # Keep accepting direct Runtime payloads while decoding that CLI envelope.
    if "action" not in payload and "prompt" in payload:
        prompt = payload["prompt"]
        if not isinstance(prompt, str):
            return {"error": "prompt must be a JSON object encoded as text"}
        try:
            decoded = json.loads(prompt)
        except json.JSONDecodeError:
            return {"error": "prompt must be a JSON object encoded as text"}
        if not isinstance(decoded, dict):
            return {"error": "prompt must be a JSON object encoded as text"}
        payload = decoded

    action = payload.get("action")
    if action is None:
        return {"error": "action is required"}
    if action == "scan":
        mode = payload.get("mode", "live")
        summary = run_agent(service, mode=mode)
        return {"summary": summary, "dashboard": service.store.get().model_dump(mode="json")}
    if action == "event":
        event_id = payload.get("event_id")
        if (
            not isinstance(event_id, str)
            or not (8 <= len(event_id) <= 128)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]+", event_id) is None
        ):
            return {"error": "event_id must be 8-128 URL-safe identifier characters"}
        mode = payload.get("mode", "live")
        if mode not in {"demo", "live"}:
            return {"error": "mode must be demo or live"}
        source = payload.get("source", "agentcore_runtime")
        if (
            not isinstance(source, str)
            or not (3 <= len(source) <= 64)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]+", source) is None
        ):
            return {"error": "source must be 3-64 URL-safe identifier characters"}
        try:
            event, accepted, payload_matches = claim_offer_event(
                service.store,
                event_id=event_id,
                source=source,
                mode=mode,
                offers=payload.get("offers"),
                partners=payload.get("partners"),
            )
        except ValueError as exc:
            return {"error": f"invalid event payload: {exc}"}
        if not payload_matches:
            return {"error": "event ID was already used for a different normalized payload"}
        if accepted:
            event = process_offer_event(
                service.store,
                event_id=event.id,
                mode=mode,
                runner=run_agent,
            )
        return {
            "accepted": accepted,
            "duplicate": not accepted,
            "event": event.model_dump(mode="json"),
            "dashboard": service.store.get().model_dump(mode="json"),
        }
    if action == "dashboard":
        return service.store.get().model_dump(mode="json")
    if action in {"approve", "resolve"}:
        decision_id = payload.get("decision_id")
        if not decision_id:
            return {"error": "decision_id is required"}
        try:
            state = DecisionState(payload.get("state", "approved"))
            return service.resolve(decision_id, state, payload.get("note")).model_dump(mode="json")
        except (KeyError, ValueError) as exc:
            return {"error": str(exc)}
    return {"error": f"unsupported action: {action}"}


if __name__ == "__main__":
    app.run()
