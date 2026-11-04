# Release plan — acceptance criteria
1. Functional local dev: docker compose services, public responsive scanner, real status states, original branding, documented setup, no fake telemetry.
2. URL scanner: real passive observations; rate limit + SSRF prevention tests covering localhost, private ranges, redirects, DNS rebinding and cloud metadata; network sandbox. Anonymous preview truthful, and login only gates private/deep features.
3. GitHub scanner: read-only authorisation, actual pinned source commit, real Semgrep/dependency/secrets outputs, evidence redaction and findings normalisation; no executing repository code.
4. Private reports: scoped access, PDF and JSON, accurate tests run/not-run, exact finding IDs, validated severity/confidence, response errors and engine provenance.
5. Controlled AI: optional consent, truncated relevant code, deepseek actual usage and cost ledger, budget exhaustion graceful; proposed fixes subject to review.
6. Payments: sandbox R79 purchase, cryptographically verified webhook, replay protection, idempotent scan entitlement, partial failure/refund design, no live charges.
7. Governance: adapter to existing GRC with no direct shared database writes, policy approval and risk mapping (ISO/IEC 27001, ISO/IEC 42001, NIST AI RMF, OWASP, POPIA).
8. Release security: RBAC, tenant isolation, rate limits, retention, backups restore, secure service credentials, worker isolation, logging, CI, accessibility and mobile cross-browser tests.
9. Validate on >=20 owned/authorised test apps including intentionally vulnerable samples and clean controls; measure false positives and per-scan infrastructure + token cost.
10. **No production-ready claim** without verified security, operational and functional checks, staging UAT and explicit owner go-live approval.
