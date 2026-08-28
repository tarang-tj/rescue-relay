# Verification record

Last full local run: **2026-08-28**, using `./scripts/verify.sh` on macOS with Python 3.12 and Node.js 22.

| Gate | Result | Scope |
|---|---|---|
| Locked Python environment | Pass | 65 packages resolved from `uv.lock` |
| Ruff | Pass | All Python source, tests, and eval runner |
| Pytest | **29 passed** | Agent loop, idempotent offer events, authenticated live intake, AgentCore actions and current CLI envelope, API, CLI, matcher, state transitions, persistence, failure paths, and safety hook |
| Python coverage | **98.2% total** | Event orchestrator and API 100%, AgentCore entrypoint 98%, CLI 100%, service 99%; enforced floor 95% |
| AgentCore deployment bootstrap | Pass | Pinned `@aws/agentcore` 0.28.1 generated and schema-validated a Python 3.12, AWS-IAM-authorized BYO runtime project |
| Deterministic evals | **5/5 passed** | Full allocation, ambiguous split, evidence grounding, Tomorrow date, partial remainder |
| Python distribution | Pass | Source archive and wheel built; wheel separately installed and smoke-tested in an isolated virtual environment |
| Clean frontend install | Pass | `npm ci`; 0 reported vulnerabilities |
| ESLint | Pass | React and TypeScript source/tests/configuration |
| Production frontend build | Pass | TypeScript project build and Vite production bundle |
| Browser tests | **2 passed, 2 intentionally skipped by project routing** | One desktop evidence/rejection/audit/reset flow and one emulated iPhone control/overflow flow |
| Browser flake check | Pass | Complete Playwright suite passed twice consecutively after per-process database isolation |
| Production static serving | Pass | Compiled UI returned over FastAPI and `/api/health` returned HTTP 200 |
| Secret/trailing-whitespace scan | Pass | No recognized credential patterns or trailing whitespace in tracked-source candidates |
| Docker image | **Pass in GitHub Actions** | A clean Ubuntu runner built the multi-stage image; the runtime uses non-root UID/GID 10001 and includes a health check |

Two warnings originate in installed dependencies: AgentCore currently uses a Pydantic class-based config, and FastAPI's compatibility `TestClient` re-exports Starlette's deprecated httpx-backed client. Neither warning is emitted by RescueRelay source or causes a failed gate.

The public repository's [GitHub Actions workflow](https://github.com/tarang-tj/rescue-relay/actions/workflows/ci.yml) independently reproduces the test and container gates on clean Ubuntu runners. The workflow uses read-only repository permissions and immutable commit pins for third-party actions.
