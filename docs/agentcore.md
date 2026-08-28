# Deploying the agent to Amazon Bedrock AgentCore

RescueRelay includes a native `BedrockAgentCoreApp` entrypoint at `src/rescue_relay/agentcore_app.py`. Deployment is intentionally documented but not represented as completed without an authenticated AWS account.

## Prerequisites

- AWS account with Bedrock model access
- AWS CLI credentials configured for the target account and region
- Python 3.11–3.13
- AgentCore starter toolkit: `uv pip install bedrock-agentcore-starter-toolkit`

## Configure and launch

From the repository root:

```bash
agentcore configure -e src/rescue_relay/agentcore_app.py
agentcore launch
```

Invoke the deployed runtime with the identifier printed by `agentcore launch`:

```bash
agentcore invoke '{"action":"scan","mode":"live"}'
```

The entrypoint also accepts `{"action":"dashboard"}`, `{"action":"approve","decision_id":"…"}`, and an explicit resolution payload:

```json
{"action":"resolve","decision_id":"…","state":"rejected","note":"Donor changed the pickup window"}
```

For a production rollout, replace SQLite with a shared durable store and connect authenticated inbox and messaging adapters; do not add outbound effects without preserving the human approval boundary.

## Background trigger boundary

The repository does not claim that the local demo polls an inbox. A production deployment should invoke the `scan` action from an authenticated event source or scheduled AWS trigger. The trigger owns cadence and retries; RescueRelay owns one idempotent coordination run. Before enabling a schedule:

1. Replace fixture intake with an authenticated, cursor-based inbox adapter.
2. Replace runtime-local SQLite with a shared durable store and concurrency controls.
3. Add idempotency keys derived from the source message identifier.
4. Route failures to an operator alarm and a dead-letter path.
5. Keep outbound delivery in a separate, approval-gated component.

## Observability checklist

- Enable AgentCore observability and inspect Strands model/tool spans in CloudWatch.
- Add `run_id`, tool name, result status, and approval state as span attributes.
- Alarm on failed runs and stalled pending decisions.
- Keep raw donor content out of broad logs; retain it only in the access-controlled evidence store.
