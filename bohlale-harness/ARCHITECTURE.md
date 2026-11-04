# Technical architecture and engineering contracts

## Proposed boundaries
Bohlale Harness should be its own deployable scanning application, with existing Bohlale GRC as a separate governance service. This folder is a handoff: DeepSeek may implement a new standalone service *inside this folder on the feature branch* and later split to a dedicated repository.

### Suggested stack
- Frontend: Next.js + TypeScript + accessible, mobile-first React UI.
- Backend: Python FastAPI orchestration endpoints, with typed Pydantic schemas.
- DB: PostgreSQL (users, organisations, scan jobs, findings, payments, cost ledger).
- Queue: Redis + durable worker system (Celery/RQ equivalent with defined retries).
- Workers: separate sandboxed containers / processes; non-root, read-only FS as applicable, outbound restrictions, CPU/RAM/time limits.
- Artefacts: private object storage, encrypted, TTL and audit.
- Identity: robust session/auth integration with secure cookies; no homemade OAuth or password hashing.
- Compliance integration: **explicit authenticated REST API** to Bohlale GRC. Never write directly to GRC tables from scanner service.

## Scanner adapters
- URL v1: DNS / TLS / redirects / HTTP header checks, strictly *passive* and SSRF-hardened. No intrusive tests pre-ownership verification.
- Code v1: GitHub read-only clone or archive of approved ref, static analysis via properly licensed scanners (evaluate Semgrep, Trivy, Gitleaks), structured JSON output, pinned versions and tool runtime limits.
- AI app v1.1: controlled Promptfoo / equivalent evaluation of authorised chatbot endpoint with tenant-approved scope, synthetic prompts/test data, no unsafe actions, budgets and explicit customer approval.
- File: hide until safe sandbox / antivirus / quarantine pipeline is built.
- External reputation: never make confidential public uploads. Evaluate licensing separately.

## Bohlale harness agent runtime
- Orchestrator owns state; model never directly executes tools.
- Typed tool requests validated against schema, user/org permissions and scope.
- Default read-only, denied tools by default, no shell access unless explicitly isolated and allow-listed.
- ReAct-like loop with step, wallclock, token, monetary, concurrency and retry budgets.
- Tool observations treated as untrusted input.
- Ground finding explanations in evidence; store model and prompt versions, request ID and real usage / costs.
- Can run LLM-free scanners; AI explanations/fixes are optional and metered.
- Human approval required for PR writes and any impact on customer systems.
- Use existing provider SDK or OpenAI-compatible API contract with robust secret storage; never assume paid consumer chat subscription covers API.

## Scan state machine
CREATED → SCOPE_PENDING → AUTHORIZED → QUEUED → RUNNING → COMPLETED
                                   ↘ CANCELED / EXPIRED
RUNNING → PARTIAL / FAILED / TIMED_OUT
COMPLETED → REMEDIATION_REQUESTED → REVIEW_PENDING → RESCAN_QUEUED → VERIFIED or STILL_OPEN
Persist every transition with timestamp, actor, scope and reason. An engine failure yields PARTIAL or FAILED, never success.

## Authz + identity
User, Organisation, Membership(role), Asset(Target), CredentialReference, Scan, ScanEngineRun, Finding, Evidence, PolicyMapping, RemediationTask, Payment, UsageLedger, AuditEvent. Every customer-owned record has tenant association and enforced object-level permissions.

## Runtime dependencies
Real scanners must be installed and version pinned in isolated workers; placeholder mock engines are only allowed for local demo/CI with explicit DEMO label. Production must fail closed if no scanner is available.

## Deployment
Use docker-compose for local dev, make production manifests separately; PostgreSQL backups, rotation, managed secrets, health probes, migrations, HTTPS, error handling, slow-job monitoring, audit and staged deploy. Include a healthcheck that validates DB/queue readiness and separate worker health.

## Status
These are **engineering requirements / proposed architecture**, not claims of implementation.
