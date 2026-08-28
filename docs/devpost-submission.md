# Devpost submission draft

## Source code

Public MIT-licensed repository: https://github.com/tarang-tj/rescue-relay

## Tagline

RescueRelay turns messy surplus-food offers into safe, evidence-backed pantry pickups—and only interrupts a coordinator when human judgment is truly required.

## Inspiration

Food rescue is a race against time, yet community coordinators lose hours to small coordination tasks: reading donor messages, checking pantry capacity, splitting loads, confirming pickup windows, and drafting the same outreach. Each task is minor. Together they are the reason usable food can sit while people need it.

## What it does

RescueRelay turns a donation-inbox event into a complete coordination run. It normalizes the offer, checks pantry needs and constraints, runs a deterministic allocator, and persists complete outreach drafts. The coordinator sees one evidence-backed workspace and is surfaced only for ambiguous allocations or real pickup commitments. The local judge replay is manually invoked and labeled; an AgentCore deployment can be invoked by a production inbox event or schedule.

The demo coordinates four offers totaling 412 lb across four community pantries, preserves Today/Tomorrow pickup dates, produces four persisted drafts, and surfaces two precise human decisions. Approval schedules the handoff; rejection safely declines it. It never pretends a draft was sent or a pickup was scheduled.

## How we built it

- **Strands Agents SDK:** a genuine tool-calling agent orchestrates inbox reading, constraint loading, optimization, and message staging.
- **Safety hooks:** `BeforeToolCallEvent` enforces a default-deny tool boundary.
- **Deterministic allocation:** capacity, need, receiving hours, and distance are calculated in tested code rather than improvised by a model.
- **Evidence ledger:** SQLite persists runs, history, tool timings, source records, message drafts, decisions, and transparent impact estimates; the UI exports a portable audit bundle.
- **Product experience:** React and FastAPI provide a coherent operations desk instead of a chat transcript.
- **AWS path:** live mode uses Strands `BedrockModel`, and a `BedrockAgentCoreApp` entrypoint is ready for AgentCore Runtime.

## Challenges

The difficult part was choosing where autonomy should stop. Giving an agent a send button makes a flashy demo but a brittle community tool. We moved the boundary into the system design: tools can read, calculate, and draft; only a persisted human decision can create a commitment.

We also separated repeatability from model claims. The judge demo uses a labeled scripted Strands model adapter, ensuring the complete tool loop can be replayed without credentials. Live mode swaps in Amazon Bedrock without changing any business logic.

## Accomplishments

- A complete, non-trivial Strands tool loop—not a prompt wrapper
- A human approval boundary enforced outside the model
- Evidence-linked decisions and fail-loud execution
- Reproducible evals covering capacity, dates, grounding, partial allocation, and ambiguous splits
- A responsive product UI tested end to end at desktop and mobile sizes
- An AgentCore-ready runtime entrypoint with explicit approval and rejection actions

## What we learned

The most useful agent is not the one that talks the most. It is the one that quietly handles the reversible work, can show its evidence, and knows exactly when a human decision becomes valuable.

## What’s next

Pilot with one food-bank network using the included measurement plan; replace fixture adapters with authenticated inbox and pantry integrations; validate meal and time-saved estimates against field data; move the ledger to a shared store; deploy the live model path on AgentCore with CloudWatch traces, alarms, and an idempotent event trigger.
