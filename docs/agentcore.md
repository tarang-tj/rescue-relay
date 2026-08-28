# Deploying RescueRelay to Amazon Bedrock AgentCore

RescueRelay includes a native `BedrockAgentCoreApp` entrypoint at `src/rescue_relay/agentcore_app.py`. Deployment is intentionally documented but is not represented as completed without an authenticated AWS account.

## Prerequisites

- AWS account with access to the selected Amazon Bedrock model
- AWS credentials configured through the AWS CLI, environment variables, or a profile
- IAM permission to deploy AgentCore and assume the CDK bootstrap roles
- Python 3.12, Node.js 20 or later, and npm

AWS now recommends the Node-based AgentCore CLI; the retired Python starter toolkit should not be installed. RescueRelay's bootstrap script pins `@aws/agentcore` 0.28.1, disables its anonymous telemetry for the command, selects Python 3.12, and configures AWS IAM authorization.

## Prepare and validate the deployment project

From the repository root:

```bash
./scripts/prepare-agentcore.sh
cd .agentcore-build/RescueRelay
```

The generated deployment project is intentionally ignored by Git because it contains account-specific targets and deployment state. The script refuses to overwrite an existing project. Set `RESCUERELAY_AGENTCORE_OUTPUT` to generate it elsewhere, or `AGENTCORE_CLI_VERSION` to test a newer CLI release deliberately.

Inspect the proposed infrastructure before creating resources:

```bash
npx --yes @aws/agentcore@0.28.1 validate
npx --yes @aws/agentcore@0.28.1 deploy --dry-run
```

Then deploy and inspect status:

```bash
npx --yes @aws/agentcore@0.28.1 deploy
npx --yes @aws/agentcore@0.28.1 status
```

## Invoke the runtime

The current AgentCore CLI wraps its argument under `prompt`. RescueRelay accepts that envelope as a JSON object encoded as text, while retaining direct Runtime payload compatibility:

```bash
npx --yes @aws/agentcore@0.28.1 invoke --runtime RescueRelay \
  --prompt '{"action":"scan","mode":"live"}'

npx --yes @aws/agentcore@0.28.1 invoke --runtime RescueRelay \
  --prompt '{"action":"dashboard"}'
```

Approval and explicit resolution use the same form:

```bash
npx --yes @aws/agentcore@0.28.1 invoke --runtime RescueRelay \
  --prompt '{"action":"approve","decision_id":"DECISION_ID"}'

npx --yes @aws/agentcore@0.28.1 invoke --runtime RescueRelay \
  --prompt '{"action":"resolve","decision_id":"DECISION_ID","state":"rejected","note":"Donor changed the pickup window"}'
```

Malformed prompt envelopes return an error instead of silently triggering a live scan.

## Production boundary

Before enabling real traffic or a background schedule:

1. Replace fixture intake with an authenticated, cursor-based inbox adapter.
2. Replace runtime-local SQLite with a shared durable store and concurrency controls.
3. Add idempotency keys derived from the source message identifier.
4. Route failures to an operator alarm and a dead-letter path.
5. Keep outbound delivery in a separate, approval-gated component.

For observability, enable AgentCore traces and CloudWatch logs; attach `run_id`, tool name, result status, and approval state; alarm on failed runs and stalled decisions; and keep raw donor content out of broad logs.

Current AWS references: [AgentCore CLI guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-get-started-cli.html) and [official CLI repository](https://github.com/aws/agentcore-cli).
