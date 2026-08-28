# Submission checklist

- [x] Push this repository to a public GitHub URL: https://github.com/tarang-tj/rescue-relay
- [x] Confirm GitHub detects the root license as MIT in the About panel.
- [ ] Add the public repository URL to Devpost.
- [ ] Upload the ready `docs/architecture.png` diagram.
- [ ] Record the working demo using `docs/demo-script.md` (maximum 5 minutes).
- [ ] Confirm the video covers problem, audience, and why it matters.
- [ ] Add AWS Builder ID to the submission.
- [ ] Optional: deploy the AgentCore entrypoint and add the live URL.
- [ ] Before AgentCore deployment, run `scripts/prepare-agentcore.sh`, inspect the pinned CLI's `deploy --dry-run` output, and confirm AWS IAM authorization.
- [ ] Optional: publish `docs/builder-post.md` on builder.aws.com with “Agents for Humans” in the title.
- [x] Run the full verification suite locally and on a clean GitHub-hosted runner.
- [x] Build the Docker image on a clean Docker-enabled GitHub-hosted runner.
- [x] Validate the checked-in custom offer payload and prove it drives the Strands tools instead of fixtures.
- [ ] Launch the Docker image in the final hosting environment, if a live demo is deployed.
- [x] Replace screenshots with the final build and verify no private data or credentials are visible.
- [ ] Download and inspect the JSON audit bundle during the recorded demo.
- [x] Cross-check every Devpost claim against `docs/requirements-matrix.md`.
- [ ] If deployed, verify the live URL, authenticated trigger, durable store, alarms, and explicit **live** labeling.
