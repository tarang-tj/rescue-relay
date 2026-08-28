# Demo video script (4:30 target)

## 0:00–0:35 — The human problem

“A food-bank coordinator’s inbox is full of expiring offers. Every message triggers the same scramble: interpret the food, check which pantry needs it, verify storage and hours, split the load, then chase approval. RescueRelay gives that time back before the food loses shelf life.”

Show the empty rescue desk. Point out **labeled demo data** and the honest **Background schedule off** status.

## 0:35–1:25 — The complete agent loop

Select **Run inbox scan**. The replay uses a deterministic model adapter but executes the real Strands Agent and all four tools.

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

“In production, an inbox event or schedule invokes this run. The local replay stays manual and says so. Once invoked, the agent surfaces only when judgment or a real-world commitment is required. That boundary lives in application state, not a prompt.”

## 3:15–3:55 — Technical implementation

Show the architecture diagram, then briefly show `agent.py`, `matching.py`, and `agentcore_app.py`.

“The same workflow can swap the replay adapter for Amazon Bedrock and run through the included AgentCore entrypoint. AgentCore adds a production runtime and observability path without coupling the core logic to deployment.”

## 3:55–4:30 — Impact and close

Return to the impact card: 412 lb, 286 estimated meals, 38 estimated coordinator minutes saved.

“Those are transparent demo estimates derived from allocations, not field-validated claims or model prose. Our pilot plan measures the real baseline. RescueRelay turns an inbox into an accountable community handoff—and lets the coordinator spend their time on people, not message triage.”
