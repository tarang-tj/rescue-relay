#!/usr/bin/env bash
set -euo pipefail

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
output_root=${RESCUERELAY_AGENTCORE_OUTPUT:-"$project_dir/.agentcore-build"}
project_path="$output_root/RescueRelay"
cli_version=${AGENTCORE_CLI_VERSION:-0.28.1}

if [[ -e "$project_path" ]]; then
  printf 'Refusing to overwrite existing AgentCore project: %s\n' "$project_path" >&2
  printf 'Move it aside or choose RESCUERELAY_AGENTCORE_OUTPUT.\n' >&2
  exit 2
fi

export AGENTCORE_TELEMETRY_DISABLED=${AGENTCORE_TELEMETRY_DISABLED:-1}

npx --yes "@aws/agentcore@$cli_version" create \
  --name RescueRelay \
  --project-name RescueRelay \
  --no-agent \
  --output-dir "$output_root" \
  --skip-git \
  --skip-install \
  --skip-python-setup \
  --json

(
  cd "$project_path"
  npx --yes "@aws/agentcore@$cli_version" add agent \
    --name RescueRelay \
    --type byo \
    --build CodeZip \
    --language Python \
    --framework Strands \
    --model-provider Bedrock \
    --code-location "$project_dir" \
    --entrypoint src/rescue_relay/agentcore_app.py \
    --authorizer-type AWS_IAM \
    --json
)

node - "$project_path/agentcore/agentcore.json" <<'NODE'
const fs = require("node:fs");
const configPath = process.argv[2];
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
const runtime = config.runtimes.find((item) => item.name === "RescueRelay");
if (!runtime) throw new Error("Generated RescueRelay runtime is missing");
runtime.runtimeVersion = "PYTHON_3_12";
fs.writeFileSync(configPath, `${JSON.stringify(config, null, 2)}\n`);
NODE

(
  cd "$project_path"
  npx --yes "@aws/agentcore@$cli_version" validate --json
)

printf 'Prepared and validated AgentCore project: %s\n' "$project_path"
printf 'Next: configure AWS credentials, cd there, then run:\n'
printf '  npx --yes @aws/agentcore@%s deploy --dry-run\n' "$cli_version"
