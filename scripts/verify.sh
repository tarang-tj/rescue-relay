#!/usr/bin/env bash
set -euo pipefail

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"
bash -n scripts/prepare-agentcore.sh
bash -n scripts/verify-agentcore-package.sh

if (( $# > 1 )) || { (( $# == 1 )) && [[ "$1" != "--with-docker" ]]; }; then
  printf 'Usage: %s [--with-docker]\n' "$0" >&2
  exit 2
fi

uv sync --extra dev --locked
uv run ruff check .
uv run pytest --cov=rescue_relay --cov-report=term-missing --cov-fail-under=95
uv run python evals/run_evals.py
uv build
./scripts/verify-agentcore-package.sh

cd "$project_dir/frontend"
npm ci
npm run lint
npm run build
npm run test:e2e

if [[ "${1:-}" == "--with-docker" ]]; then
  docker build -t rescue-relay "$project_dir"
fi
