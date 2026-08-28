#!/usr/bin/env bash
set -euo pipefail

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
output_root=${RESCUERELAY_AGENTCORE_OUTPUT:-"$project_dir/.agentcore-build"}
project_path="$output_root/RescueRelay"
runtime_source="$project_path/runtime-source"
cli_version=${AGENTCORE_CLI_VERSION:-0.28.1}
account_id=${RESCUERELAY_AWS_ACCOUNT_ID:-}
aws_region=${RESCUERELAY_AWS_REGION:-}

if [[ -e "$project_path" ]]; then
  printf 'Refusing to overwrite existing AgentCore project: %s\n' "$project_path" >&2
  printf 'Move it aside or choose RESCUERELAY_AGENTCORE_OUTPUT.\n' >&2
  exit 2
fi

export AGENTCORE_TELEMETRY_DISABLED=${AGENTCORE_TELEMETRY_DISABLED:-1}

if [[ -n "$account_id" || -n "$aws_region" ]]; then
  if [[ ! "$account_id" =~ ^[0-9]{12}$ ]]; then
    printf 'RESCUERELAY_AWS_ACCOUNT_ID must be a 12-digit AWS account ID.\n' >&2
    exit 2
  fi
  if [[ ! "$aws_region" =~ ^[a-z]{2}(-[a-z]+)+-[0-9]+$ ]]; then
    printf 'RESCUERELAY_AWS_REGION must be an AWS region such as us-west-2.\n' >&2
    exit 2
  fi
fi

npx --yes "@aws/agentcore@$cli_version" create \
  --name RescueRelay \
  --project-name RescueRelay \
  --no-agent \
  --output-dir "$output_root" \
  --skip-git \
  --skip-install \
  --skip-python-setup \
  --json

# Stage only runtime inputs. Pointing CodeZip at the repository root also packages
# local databases, test output, documentation, and other development artifacts.
mkdir -p "$runtime_source/src"
cp "$project_dir/pyproject.toml" "$project_dir/uv.lock" \
  "$project_dir/README.md" "$project_dir/LICENSE" "$runtime_source/"
cp -R "$project_dir/src/rescue_relay" "$runtime_source/src/"
find "$runtime_source" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$runtime_source" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

(
  cd "$project_path"
  npx --yes "@aws/agentcore@$cli_version" add agent \
    --name RescueRelay \
    --type byo \
    --build CodeZip \
    --language Python \
    --framework Strands \
    --model-provider Bedrock \
    --code-location "$runtime_source" \
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

if [[ -n "$account_id" ]]; then
  node - "$project_path/agentcore/aws-targets.json" "$account_id" "$aws_region" <<'NODE'
const fs = require("node:fs");
const [configPath, account, region] = process.argv.slice(2);
const targets = [{
  name: "default",
  description: `RescueRelay deployment (${region})`,
  account,
  region,
}];
fs.writeFileSync(configPath, `${JSON.stringify(targets, null, 2)}\n`);
NODE
fi

(
  cd "$project_path"
  npx --yes "@aws/agentcore@$cli_version" validate --json
)

printf 'Prepared and validated AgentCore project: %s\n' "$project_path"
if [[ -n "$account_id" ]]; then
  printf 'Configured target: AWS account %s in %s\n' "$account_id" "$aws_region"
  printf 'Next: confirm AWS credentials, cd there, then run:\n'
  printf '  npx --yes @aws/agentcore@%s deploy --dry-run --target default\n' "$cli_version"
else
  printf 'No AWS target was written. Regenerate with both:\n'
  printf '  RESCUERELAY_AWS_ACCOUNT_ID=123456789012 RESCUERELAY_AWS_REGION=us-west-2 ./scripts/prepare-agentcore.sh\n'
fi
