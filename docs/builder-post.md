# Agents for Humans: Building an agent that knows when to stop

The common food-rescue bottleneck is not a lack of generosity. It is coordination latency. A coordinator must turn incomplete donor messages into safe, feasible handoffs before perishable food loses its window.

RescueRelay explores a specific architecture for that problem: let an AI agent orchestrate repetitive, reversible work, but keep quantities deterministic and commitments human-owned.

## The four-tool loop

Using the Strands Agents SDK, the coordinator calls four tools: read offers, load pantry constraints, optimize allocations, and stage messages. The tool surface is deliberately narrow. A `BeforeToolCallEvent` hook rejects unknown tools by default, and there is no send tool to accidentally invoke.

## Why the model does not allocate food

An LLM is useful for deciding what to do next and for interpreting varied communication. It is a poor source of truth for arithmetic and inventory constraints. RescueRelay’s allocator is ordinary typed Python, tested against capacity and coverage invariants. The agent receives the result and moves the workflow forward.

## A structural approval boundary

The agent can propose a two-pantry split, but the dispatch remains `awaiting_approval`. Approval is stored in application state, and only the state machine can mark the pickup `scheduled`. A rejection atomically declines the dispatch and closes related decisions. This matters because safety instructions in a system prompt are policy suggestions; application boundaries are guarantees we can test.

## Repeatable locally, production-ready on AWS

The local demo uses a clearly labeled scripted model implementing the Strands model interface. It drives the actual tool loop and makes the demo reproducible. A simulated offer-arrival event is atomically claimed before the asynchronous run begins; each receipt moves through received, processing, completed, or failed, and a repeated event ID cannot trigger duplicate work. Live HTTP intake requires an explicit bearer secret.

Live mode swaps the replay adapter for Amazon Bedrock. The `BedrockAgentCoreApp` entrypoint exposes the same idempotent event action behind AWS IAM, providing the production deployment seam with AgentCore observability as the next operational layer. The demo proves event handling but does not pretend its local fixture is a connected inbox.

## The larger lesson

For background agents, “only surfaces when needed” is not a copywriting claim. It is an architecture: deterministic work, evidence trails, fail-loud runs, and explicit effect boundaries. That combination lets the human spend attention where judgment actually changes the outcome.
