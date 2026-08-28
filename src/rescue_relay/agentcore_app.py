"""Amazon Bedrock AgentCore Runtime entrypoint."""

import json

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from .agent import run_agent
from .domain import DecisionState
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

    action = payload.get("action", "scan")
    if action == "scan":
        mode = payload.get("mode", "live")
        summary = run_agent(service, mode=mode)
        return {"summary": summary, "dashboard": service.store.get().model_dump(mode="json")}
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
