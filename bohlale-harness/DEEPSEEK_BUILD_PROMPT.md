# DEEPSEEK DESKTOP — BOHLALE HARNESS BUILD INSTRUCTION

You are the lead security architect, senior full-stack developer and automated test engineer for **BOHLALE HARNESS — Scan to Secure.**

## Your workspace
- GitHub: https://github.com/coachtee/Bohlale-GRC
- Development branch: feature/bohlale-harness-v1-handoff
- Requirements folder: bohlale-harness/
- Original brand assets (DO NOT REDRAW LOGO): https://github.com/coachtee/bohlale-cloud-health/tree/master/apps/web/public/brand (bohlale-logo.png, bohlale-mark.png).
- The existing Bohlale GRC application is valuable and MUST NOT be overwritten or broken.

## Start now
1. Check the local workspace and git credentials. Clone the repository if it is absent, fetch the branch, check it out, and ensure it is clean. If access is unavailable, explain the exact blocker and implement in a separate local folder.
2. Read bohlale-harness/README.md, PRODUCT_SPEC.md, ARCHITECTURE.md, SECURITY_AND_PRIVACY.md and the other requirements documents. Review the existing GRC architecture and tests before making architectural decisions.
3. Build a runnable **separately deployable Bohlale Harness service**, with production-minded security engineering, real scanning functionality and a responsive premium UX. Keep any GRC integration behind a documented authenticated adapter; do not make unapproved changes to existing GRC code or database.

## Product
**Bohlale Harness — Scan to Secure.** A VirusTotal-inspired (interaction only, NOT a clone) minimal security interface for vibe-coded applications and professional developers, with a secondary Scan to Govern workflow for organisations.

Navigation: Scan | Findings | Workspace | Governance.
Scanning choices: URL | CODE | AI | FILE.
- URL: safe anonymous **passive** preview; actual observed results, explicit not-tested checks, signed-in saved history and deeper options.
- CODE: signed-in, authorised read-only GitHub repository scanning, pinned commit, secrets/dependencies/static code results, deduplicated findings.
- AI: authenticated, scoped and consent-based security tests of owned AI systems once the safe harness is in place. Disable and label as later if not implemented.
- FILE: disable and label as later until safe malware scanning is genuinely implemented. No false working UI.

## Stack proposal
Next.js + TypeScript frontend, Python FastAPI backend, PostgreSQL, Redis/durable queue and isolated limited scan workers. Prefer maintainable modular design and pinned real tools; document deviations. Docker Compose local development. Auth, per-tenant RBAC, audit log and private reports. Separate the scanning service from existing Bohlale GRC.

## Harness architecture
Specialist operations: Scan, Verify, Fix, Govern; Watch later. Bots are workflows, not five independent API subscriptions. Evidence-first deterministic scanners run before optional DeepSeek calls. All AI inputs opt-in, redacted and budgeted. No made-up findings or fake validations. Record exact model/provider, input/output tokens, ZAR cost, job and organisation. Configurable pilot AI budget R2 target / R5 hard cap per paid report. Prices and provider rates must be configurable, never hardcoded.

## Commercial
Free passive URL preview; a proposed R79 bounded repo assessment with one limited rescan and private PDF/JSON report. Implement payment integration in **sandbox mode** only with server-side entitlement and verified idempotent webhooks. Do NOT turn on live charging before approval. Reports never claim 'certified secure'. Show actual scan coverage.

## Security constraints (hard blockers)
- Do not conduct intrusive scans of arbitrary third-party URLs. Ownership verification + explicit scope for active tests.
- Prevent SSRF, DNS rebinding, link-local/metadata access, private IP targeting, redirect bypass and unsafe network egress.
- Run scanners in isolated workers, bounded CPU/RAM/time and strict permissions. No untrusted code execution in the main host.
- GitHub access least-privilege, read-only. No token leakage.
- Tenant isolation end-to-end, secure secrets management, audits, encryption, retention, rate limits and abuse controls.
- Don't send customer code to an LLM until explicit customer consent and permitted data-handling terms.
- Never auto-apply code patches, create deployment changes or merge to production.
- Every error produces honest FAILED/PARTIAL/NOT TESTED status rather than 'secure'.

## Implementation priority
M1: Original Bohlale brand; desktop/mobile homepage and working local stack; DB/queue/auth/tenant isolation.
M2: Real safe URL passive scanner + anonymous preview + results; tests for SSRF and redirects.
M3: Real read-only GitHub code scanner with reliable static evidence; private reports.
M4: Evidence-grounded optional AI explanations/fixes, cost dashboard, report PDF/JSON, and sandbox payment flow.
M5: Scoped AI app tests, initial governance bridge, 20+ app validation and release hardening.

Start implementing M1/M2 immediately, not merely writing a plan. Finish as many subsequent milestones as can be implemented and honestly tested in this session. If blocked, leave working code, clear logs and a precise next-step checklist.

## Deliverables / verification
- Working source code and complete run instructions.
- Original Bohlale brand used accurately.
- Responsive desktop and mobile screenshots from rendered pages (not illustrations).
- Tests actually executed, pass/fail counts, evidence of scanners running, threat-model and known limitations.
- A status file named bohlale-harness/BUILD_STATUS.md identifying implemented / partial / not implemented capabilities.
- Clean commits pushed to the *feature branch only* when authorised; do not merge, deploy publicly or edit current production.
- Final summary including local URLs/commands, required env vars (names only, never secret values), tests, costs, shortcomings and exact next steps.

Start now by reading the repository, reviewing the docs and implementing the first runnable milestone.