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
export RESCUERELAY_AWS_ACCOUNT_ID=123456789012
export RESCUERELAY_AWS_REGION=us-west-2
./scripts/prepare-agentcore.sh
cd .agentcore-build/RescueRelay
```

Replace the example account ID and region with the actual deployment target. Both variables are required together; the script validates them and writes a named `default` target to `agentcore/aws-targets.json`. If they are omitted, project generation and schema validation still work, but deployment deliberately stops until a target is supplied.

The generated deployment project is intentionally ignored by Git because it contains account-specific targets and deployment state. The script refuses to overwrite an existing project. It also stages a minimal runtime source tree instead of packaging the repository root. Set `RESCUERELAY_AGENTCORE_OUTPUT` to generate it elsewhere, or `AGENTCORE_CLI_VERSION` to test a newer CLI release deliberately.

Verify both the generated configuration and the exact CodeZip contents:

```bash
./scripts/verify-agentcore-package.sh
```

That gate requires the application entrypoint and lockfiles and rejects repository metadata, local databases, documentation, examples, frontend files, and tests from the deployment ZIP. It runs in the full local verifier and GitHub Actions.

Inspect the proposed infrastructure before creating resources:

```bash
npx --yes @aws/agentcore@0.28.1 validate
npx --yes @aws/agentcore@0.28.1 deploy --dry-run --target default
```

Then deploy and inspect status:

```bash
npx --yes @aws/agentcore@0.28.1 deploy --target default
npx --yes @aws/agentcore@0.28.1 status --target default
```

## Invoke the runtime

The current AgentCore CLI wraps its argument under `prompt`. RescueRelay accepts that envelope as a JSON object encoded as text, while retaining direct Runtime payload compatibility:

```bash
npx --yes @aws/agentcore@0.28.1 invoke --runtime RescueRelay \
  --prompt '{"action":"event","event_id":"judge-demo-0001","source":"demo_inbox","mode":"demo"}'

npx --yes @aws/agentcore@0.28.1 invoke --runtime RescueRelay \
  --prompt '{"action":"dashboard"}'
```

For live traffic, the event object must also include non-empty `offers` and `partners` arrays using the contract in `examples/offer-event.json`. The source integration must derive `event_id` from a stable source-message identifier. RescueRelay durably persists the normalized inputs before execution and records their SHA-256 fingerprint on the receipt. Replaying the same ID and content returns `duplicate: true` without another run; changing the source, mode, offers, or partners under that ID fails with a collision error. The lower-level `{"action":"scan","mode":"live"}` action remains available only for an operator-initiated model diagnostic.

Approval and explicit resolution use the same form:

```bash
npx --yes @aws/agentcore@0.28.1 invoke --runtime RescueRelay \
  --prompt '{"action":"approve","decision_id":"DECISION_ID"}'

npx --yes @aws/agentcore@0.28.1 invoke --runtime RescueRelay \
  --prompt '{"action":"resolve","decision_id":"DECISION_ID","state":"rejected","note":"Donor changed the pickup window"}'
```

Missing actions and malformed prompt envelopes return an error instead of silently triggering a live scan.

## Production boundary

Before enabling real traffic or a background schedule:

1. Connect an authenticated inbox transformer that maps source records into the validated event schema.
2. Replace runtime-local SQLite with a shared durable store and concurrency controls.
3. Map the connector's stable source-message identifier to `event_id` and provide a current partner snapshot.
4. Route failures to an operator alarm and a dead-letter path.
5. Keep outbound delivery in a separate, approval-gated component.

For observability, enable AgentCore traces and CloudWatch logs; attach `run_id`, tool name, result status, and approval state; alarm on failed runs and stalled decisions; and keep raw donor content out of broad logs.

Current AWS references: [AgentCore CLI guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-get-started-cli.html) and [official CLI repository](https://github.com/aws/agentcore-cli).
