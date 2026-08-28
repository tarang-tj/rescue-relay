# Demo video script (4:30 target)

## Reproducible caption-led cut

Run `./scripts/record-demo.sh` from the repository root to create `artifacts/rescue-relay-demo.mp4`. The automated cut is approximately 2:40, covers every section below, validates the audit download while recording, and includes an upload-compatible silent audio track. It is a complete caption-led submission candidate; optional narration may be layered over it for a more personal final presentation.

## 0:00–0:35 — The human problem

“A food-bank coordinator’s inbox is full of expiring offers. Every message triggers the same scramble: interpret the food, check which pantry needs it, verify storage and hours, split the load, then chase approval. RescueRelay gives that time back before the food loses shelf life.”

Show the empty rescue desk. Point out **labeled demo data** and the **Event intake armed** status.

## 0:35–1:25 — The complete agent loop

Select **Simulate offer arrival**. FastAPI durably claims the event ID, returns an asynchronous receipt, and executes the real Strands Agent and all four tools through a deterministic model adapter. Point out the **event completed** receipt: retrying that ID cannot rerun the agent.

Briefly show `examples/offer-event.json`: “The replay button uses labeled fixtures for a stable video, but this checked-in executable payload proves the same tools consume caller-supplied offers and partner constraints. Inputs are validated and durably persisted before the receipt is acknowledged; an ID reused with different content is rejected.”

Click each timeline step:

1. Four donor offers become evidence records.
2. Four pantry capacity snapshots are verified.
3. The deterministic allocator matches all 412 lb.
4. Four complete outreach drafts are persisted, with zero sent.

Say: “The model orchestrates; tested code owns quantities and capacity.”

## 1:25–2:20 — Evidence and safety

Open the **Matched 412 lb** step and show linked donor and pantry evidence. Point out the boundary note.

“A donor message is untrusted data. RescueRelay has a default-deny tool hook and no send capability. Errors are saved as failed runs rather than dressed up as success.”

Show the pickup table, Today/Tomorrow windows, confidence/state columns, and the audit download.

## 2:20–3:15 — Human judgment, not human busywork

Show both actions in the decision rail. Approve the split first; the pickup remains awaiting approval. Approve the pickup commitment; the Harbor row changes to scheduled. Then explain the alternate path: declining either decision atomically declines the dispatch and closes its sibling decision.

“The local button simulates the inbox event; the agent run itself is background work. A production event source invokes the same idempotent action through the AWS-IAM-protected AgentCore runtime. Once invoked, RescueRelay surfaces only when judgment or a real-world commitment is required. That boundary lives in application state, not a prompt.”

## 3:15–3:55 — Technical implementation

Show the architecture diagram, then briefly show `agent.py`, `matching.py`, and `agentcore_app.py`.

“The same validated event contract reaches the included AgentCore entrypoint, where the workflow can swap the replay adapter for Amazon Bedrock. AgentCore adds a production runtime and observability path without coupling the core logic to deployment.”

## 3:55–4:30 — Impact and close

Return to the impact card: 412 lb, 286 estimated meals, 38 estimated coordinator minutes saved.

“Those are transparent demo estimates derived from allocations, not field-validated claims or model prose. Our pilot plan measures the real baseline. RescueRelay turns an inbox into an accountable community handoff—and lets the coordinator spend their time on people, not message triage.”
