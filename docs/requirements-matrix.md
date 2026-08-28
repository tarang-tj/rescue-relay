# Hackathon requirements and judging evidence

This matrix separates implemented evidence from deployment and submission work that requires external accounts.

## Required submission artifacts

| Requirement | Status | Evidence / owner action |
|---|---|---|
| New AI agent built with Strands Agents SDK | Implemented | `src/rescue_relay/agent.py`, four typed tools, real Strands tool loop, default-deny hook |
| Handles a real repetitive task end to end | Implemented in event-driven replay and custom-input path | Validated offer + partner event → durable normalized inputs → constraints → deterministic matching → persisted outreach drafts → human decision; `examples/offer-event.json` is executable |
| Text description | Ready | `docs/devpost-submission.md` |
| Public code repository URL | Complete | [github.com/tarang-tj/rescue-relay](https://github.com/tarang-tj/rescue-relay); paste this URL into Devpost |
| All source, assets, and setup instructions | Ready locally | `src/`, `frontend/`, `docs/`, `README.md`, lockfiles, Dockerfile |
| MIT or Apache license visible in repository About | Complete | GitHub detects the root `LICENSE` as MIT and exposes it in the public repository About panel |
| README | Ready | `README.md` |
| Architecture diagram | Ready | `docs/architecture.png`, `docs/architecture.svg`, `docs/architecture.md` |
| Demo video, maximum five minutes | Rendered and inspected locally; public upload external | Reproducible 2:40 caption-led MP4 demonstrates the working end-to-end run, audit export, approval boundary, architecture, and impact; `scripts/record-demo.sh` regenerates it |
| Problem, audience, and importance in pitch | Ready | Demo script sections 0:00–0:35 and 3:55–4:30 |
| AWS Builder ID | External action | Add the entrant's Builder ID in Devpost |
| Optional live demo | Not claimed | AgentCore entrypoint, current stable-CLI bootstrap, explicit target config, minimal CodeZip audit, AWS IAM config, and deployment guide are ready; authenticated deployment remains external |
| Optional builder.aws.com post | Draft ready; publishing external | `docs/builder-post.md`; title already contains “Agents for Humans” |

## Judging evidence

| Criterion | Strongest evidence | Demo moment |
|---|---|---|
| Technological implementation | Strands tool loop; structural hook; deterministic matcher; durable normalized event inputs; ID-and-content idempotency across store instances and restarts; authenticated live HTTP intake; persisted state machine; directly tested AgentCore entrypoint and CLI envelope; backend suite above the enforced 95% coverage floor; 5 deterministic evals; desktop/mobile browser flows | 0:35–1:25 and 3:15–3:55 |
| Design | Responsive rescue desk; evidence timeline; pickup table; persisted draft previews; decision rail; portable audit export | 0:35–3:15 |
| Potential impact | Specific food-rescue coordinator workflow; 412 lb scenario; transparent demo estimates; field-validation plan | 0:00–0:35 and 3:55–4:30 |
| Creativity and originality | Quiet coordination agent rather than chat; reversible work automated while commitments remain human-owned | 2:20–3:15 |
| Presentation | Inspected 2:40 caption-led cut demonstrates the complete loop, evidence, decision transition, architecture, and impact boundary; synchronized narration tooling is included | Entire video |

## Claim boundaries

- **Verified locally and in clean CI:** the event-driven scripted replay executes the real Strands agent and tools; caller-supplied offers and partners drive those tools; normalized payloads survive a store restart; exact duplicates cannot rerun the event while same-ID content changes are rejected; backend tests above the enforced coverage floor, 5 evals, production builds, isolated-wheel smoke, browser flows, decision transitions, audit download, compiled static serving, Docker build, AgentCore project validation, and minimal CodeZip inspection pass. See `docs/verification.md` and the public [GitHub Actions workflow](https://github.com/tarang-tj/rescue-relay/actions/workflows/ci.yml).
- **Implemented but credential-dependent:** Bedrock live-model mode and the AgentCore runtime entrypoint.
- **Not yet claimed:** a deployed live URL, a production inbox connector, outbound message delivery, background polling, or field-validated impact.
- **Experiment to run:** the pilot in `docs/pilot-plan.md` determines whether the product actually reduces coordinator handling time without raising correction or missed-window rates.
