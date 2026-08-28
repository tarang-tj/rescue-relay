# Security and safety model

## Protected outcomes

RescueRelay must not fabricate pantry capacity, silently create a pickup commitment, send outreach without authorization, or present failed work as complete.

## Trust boundaries

- Donor text and future connector payloads are untrusted data.
- The model chooses among a four-tool allowlist; a `BeforeToolCallEvent` hook denies unknown tools.
- Deterministic Python—not the model—owns quantities, capacity, receiving-window compatibility, and confidence.
- Draft creation is internal persistence. No outbound messaging tool exists.
- A persisted decision state machine owns approval and rejection. Rejection declines the dispatch and closes sibling decisions.
- Demo replay and fixture data are labeled. Live AWS execution requires explicit configuration.
- The generated AgentCore deployment config uses AWS IAM authorization; malformed CLI prompt envelopes fail closed instead of defaulting to a live scan.

## Known production gaps

- Runtime-local SQLite is suitable for the replay, not concurrent multi-instance deployment.
- Authentication, authorization, tenant isolation, source-message deduplication, secret management, retention policy, and external connector hardening must be added before handling real donor data.
- Background invocation, retries, and dead-letter handling belong to the deployment trigger and are not active in the local demo.
- No food-safety or regulatory eligibility engine is implemented; a pilot must constrain supported food categories and preserve coordinator review.
- The included image drops root privileges to UID/GID 10001 and exposes an application health check; CI is configured to build the image on a Docker-enabled runner.

## Reporting

Do not include donor personal data, credentials, or exploit details in a public issue. For this hackathon prototype, contact the repository owner privately through the account listed on the public repository.
