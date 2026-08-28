#!/usr/bin/env bash
set -euo pipefail

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
scratch_root=$(mktemp -d "${TMPDIR:-/tmp}/rescue-relay-agentcore-check.XXXXXX")

cleanup() {
  case "$scratch_root" in
    */rescue-relay-agentcore-check.*) rm -rf -- "$scratch_root" ;;
    *) printf 'Refusing to remove unexpected scratch path: %s\n' "$scratch_root" >&2 ;;
  esac
}
trap cleanup EXIT

RESCUERELAY_AGENTCORE_OUTPUT="$scratch_root" "$project_dir/scripts/prepare-agentcore.sh"
generated_project="$scratch_root/RescueRelay"
archive="$generated_project/agentcore/RescueRelay.zip"

(
  cd "$generated_project"
  npx --yes "@aws/agentcore@${AGENTCORE_CLI_VERSION:-0.28.1}" package --runtime RescueRelay
)

if [[ ! -f "$archive" ]]; then
  printf 'AgentCore package was not created: %s\n' "$archive" >&2
  exit 1
fi

archive_entries=$(unzip -Z1 "$archive")
for required in \
  src/rescue_relay/agentcore_app.py \
  src/rescue_relay/agent.py \
  pyproject.toml \
  uv.lock; do
  if ! grep -Fxq "$required" <<<"$archive_entries"; then
    printf 'AgentCore package is missing required runtime file: %s\n' "$required" >&2
    exit 1
  fi
done

for forbidden_prefix in \
  .git/ \
  .github/ \
  data/ \
  docs/ \
  examples/ \
  frontend/ \
  tests/; do
  if awk -v prefix="$forbidden_prefix" 'index($0, prefix) == 1 { found = 1 } END { exit !found }' \
    <<<"$archive_entries"; then
    printf 'AgentCore package contains forbidden development path: %s\n' "$forbidden_prefix" >&2
    exit 1
  fi
done

archive_bytes=$(wc -c <"$archive" | tr -d ' ')
printf 'Verified minimal AgentCore package: %s bytes\n' "$archive_bytes"
