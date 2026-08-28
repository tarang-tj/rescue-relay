# Verification record

Last full local run: **2026-08-28**, using `./scripts/verify.sh` on macOS with Python 3.12 and Node.js 22.

| Gate | Result | Scope |
|---|---|---|
| Locked Python environment | Pass | 65 packages resolved from `uv.lock` |
| Ruff | Pass | All Python source, tests, and eval runner |
| Pytest | **23 passed** | Agent loop, AgentCore actions, API, CLI, matcher, state transitions, persistence, failure paths, and safety hook |
| Python coverage | **98% total** | AgentCore entrypoint 96%, API 100%, CLI 100%, service 99%; enforced floor 95% |
| Deterministic evals | **5/5 passed** | Full allocation, ambiguous split, evidence grounding, Tomorrow date, partial remainder |
| Python distribution | Pass | Source archive and wheel built; wheel separately installed and smoke-tested in an isolated virtual environment |
| Clean frontend install | Pass | `npm ci`; 0 reported vulnerabilities |
| ESLint | Pass | React and TypeScript source/tests/configuration |
| Production frontend build | Pass | TypeScript project build and Vite production bundle |
| Browser tests | **2 passed, 2 intentionally skipped by project routing** | One desktop evidence/rejection/audit/reset flow and one emulated iPhone control/overflow flow |
| Browser flake check | Pass | Complete Playwright suite passed twice consecutively after per-process database isolation |
| Production static serving | Pass | Compiled UI returned over FastAPI and `/api/health` returned HTTP 200 |
| Secret/trailing-whitespace scan | Pass | No recognized credential patterns or trailing whitespace in tracked-source candidates |
| Docker image | Awaiting Docker-enabled runner | Docker is unavailable locally; Dockerfile uses a non-root UID and health check, and CI includes a dedicated `docker build` job |

Two warnings originate in installed dependencies: AgentCore currently uses a Pydantic class-based config, and FastAPI's compatibility `TestClient` re-exports Starlette's deprecated httpx-backed client. Neither warning is emitted by RescueRelay source or causes a failed gate.

This record is reproducible evidence, not a hosted-status claim. After the repository is published, the GitHub Actions test and container jobs should be linked from the submission as external clean-run proof.
