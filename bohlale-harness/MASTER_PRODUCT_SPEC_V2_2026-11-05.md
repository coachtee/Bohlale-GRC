# BOHLALE HARNESS — AUTHORITATIVE MASTER SPECIFICATION
Version: 2.0 | Approved product direction: 5 November 2026
Status: Development handoff. Not a claim of production readiness.
Project: BOHLALE HARNESS
Tagline: Scan to Secure.
Organisational positioning: Scan to Govern.
AI analyst: BOHLALE ANALYST — Your AI Cybersecurity Analyst.

> Guiding principle: SIMPLE OUTSIDE. POWERFUL INSIDE.

## 0. Instructions for DeepSeek / engineering team
This document **supersedes conflicting older chat prompts**. Inspect the EXISTING local codebase and this repo before modifying anything. Continue implementation, do not start from scratch. Preserve existing working scanning, authentication, history, security controls, code scanning, and reports. Document exactly which capabilities are verified working, partial, missing, or disabled.

IMPORTANT: The local app shown to the owner may contain work not yet pushed to GitHub. Identify the actual working directory, branch, uncommitted files, and source-of-truth before changing code. Never overwrite local work based on an older remote branch.

The existing Bohlale-GRC application is a separate asset: do not disrupt or migrate it without an approved plan. Implement Harness independently and integrate GRC via an authenticated, documented interface. Do not merge the development branch to main or deploy publicly without owner approval.

Implement the smallest safe, testable increments. **No mock success responses in real user flows.** A button is not complete until its backend action and authz are exercised and tested.

## 1. LOCKED VISUAL IDENTITY — DO NOT REDESIGN
- Original Bohlale mark and wordmark only; asset source: https://github.com/coachtee/bohlale-cloud-health/tree/master/apps/web/public/brand (bohlale-logo.png and bohlale-mark.png). Never recreate or approximate the mark.
- Google-inspired MINIMAL UX; not a copy of Google branding. White #FFFFFF, accessible blue primary actions (#1A73E8), charcoal #202124, secondary gray #5F6368, light border #DADCE0.
- No dark dashboard, amber branding, decorative gradients, stock imagery, inflated AI terms, huge marketing blocks or unnecessarily complex front page.
- On **home page only**, show ONE centred original Bohlale logo above BOHLALE HARNESS and "Scan to Secure." Do NOT also show the logo/name in top-left navigation. Keep small top nav (Scan, History, Governance where appropriate, Sign in, Create account).
- On all **internal pages** (results, signed-in workspace, history, governance, admin) show compact original Bohlale logo/name in header.
- Home centre: one rounded URL entry input and blue Scan button; mode options URL | CODE | AI | FILE, accurately labelled and disabled where unavailable.
- No long disclaimer paragraphs interrupting scanning. Display a concise truthful passive-scan notice near input; fuller explanation on Product/How It Works and within results scope.
- Google-style unobtrusive bottom footer with "South Africa" in location row and working links: About, Product, How it works, Pricing, Security, Privacy, Terms; Settings only if operational.
- The approved Bohlale Analyst introductory HTML should be integrated as a separate **Product** page. Analyst execution is not a separate complicated customer dashboard. Product page explains what is AVAILABLE versus COMING LATER.
- Responsive and accessible: WCAG-oriented contrast/focus, screen-reader labels, mobile layout, keyboard interaction.

## 2. USERS, WORKSPACES AND JOURNEY
There are THREE experiences with one identity system:
1. Anonymous visitor: fast, genuine and strictly passive public URL preview; no login to try.
2. Registered developer / organisation workspace: authorised source scan, saved assets, history, verified findings, AI assistance when opted in, reports, share links, rescan, governance entry.
3. Internal platform administration: restricted /admin console, operational monitoring, users, costs, engine controls, audit logs.

Required journey:
Home -> URL scan -> clear scan status -> compact results table -> expand finding -> register/sign in -> securely save or offer one-click rescan of prior anonymous preview -> workspace -> connect READ-ONLY GitHub -> authorise deeper source scan -> findings -> report download -> secure sharing -> revoke access -> remediation -> rescan comparison.

Signing up must never imply that an anonymous passive URL scan became a code or AI vulnerability assessment. Retain an anonymous result only by securely bound short-lived handoff; otherwise offer simple rescan. Keep data scoped to correct user/org.

## 3. RESULTS UI AND SECURITY SEMANTICS
- Present compact truthful counts, e.g. checks completed / attention / passed / informational / not tested / not applicable. Prioritise items needing attention.
- Simple table: Check | Status | Severity | Finding | Action. Search, sort and filters: All, Needs Attention, Passed, Information, Not Applicable, Not Tested.
- Normal users see actionable rows first, with collapsed groups for passed and informational items. Expand a row for: WHAT CHECKED; OBSERVED; WHY IT MATTERS; SEVERITY/CONFIDENCE; EVIDENCE; RECOMMENDED ACTION; VERIFICATION PROCEDURE; COVERAGE/SCANNER VERSION.
- **Internal safety checks** (target URL accepted, DNS allowance, response bounded) must not count as evidence that website security passed. Label correctly as scanner diagnostics.
- Absence of cookies is NOT "Secure cookie attributes passed." Mark Not Observed / N/A.
- Missing optional headers and records may be hardening suggestions, not proven exploitable vulnerabilities. For CSP, explain it is configuration observation; do not infer exploit; suggest staged Report-Only testing before enforcement to avoid breaking legitimate functionality.
- Enforce separate labels: technical check status (Passed / Needs Attention / Informational / Not Applicable / Not Tested / Error) and vulnerability validation status (Confirmed / Needs Validation / Rejected / Configuration Observation). Do not overload "Passed" and "Confirmed".
- No fake security scores, official certificates, guaranteed safety, invented CVEs or statements about untested properties.
- Every finding stores scan ID, scope, relevant engine and version, timestamps, source/evidence, location, severity, confidence, affected user or asset, remediation, and validated/not-validated status. Redact secrets.

## 4. APPLICATION ENGINE — STRONG BACKEND, SIMPLE FRONTEND
Use maintainable modules with typed interfaces and reliable API-to-worker handoff; do not require eight separate servers.

A. Public Web Security engine:
Read-only HTTP/HTTPS observations, redirection, security headers, DNS, cookie attributes when present, document-level observations. Max time and response size, SSRF/rebinding hardening. Anonymous public scans do NOT become active pen tests.

B. TLS & Certificate engine:
Observed HTTPS, certificate issuer, subject/host match, trust chain where actually validated, valid-from/valid-until dates and days remaining, TLS version/negotiated cipher, HSTS, optional CAA. Support Let's Encrypt AND any supported CA. Clearly separate not-checked and incomplete from passed. Certificate issuance/renewal NOT part of v1.

C. Code Security engine:
Customer-authorised read-only GitHub link; repo/branch/commit provenance; isolated static source scanning, dependency CVEs, potential secrets (redact), insecure configuration and contextual triage, file:line evidence, sensible repository/scan limits. Only claim engines actually executed. No untrusted repo scripts on app host.

D. AI Security engine:
Future controlled assessment of verified owned chatbot/agent apps: prompt-injection boundary risks, MCP/tool authorisation, RAG/memory isolation, data leakage and excessive agency. Authorised test scenarios only; **feature flag as unavailable until validated**.

E. Verification and remediation:
Independent reviewer processes to challenge findings, structured evidence, safe test validation where authorised; suggestions and patch proposals reviewed by human. No automatic merge, deploy, exploit, credential use or irreversible changes.

F. Report engine:
Evidence-backed private PDF + JSON; accurate scope, engine versions, coverage and non-coverage, findings, suggested actions and verification history. Accurate report lifecycle and download authorisation.

G. Governance integration:
Reuse existing Bohlale GRC for policy/risk/evidence workflow using secure API; don't claim automatic ISO/POPIA certification. Future AI inventory, named risk owners, mapping to ISO/IEC 27001, ISO/IEC 42001, NIST AI RMF / CSF, OWASP and POPIA.

H. Bohlale Certificate Watch (LATER):
Opt-in monitoring for VERIFIED customer-owned domains; expirations, unexpected certificate change, HTTPS availability, optional CT monitoring, notices and retention. ACME/Certbot issuance or renewal only later with explicit domain control and server permission. Do not issue arbitrary website certs.

## 5. BOHLALE ANALYST — BACKGROUND AI CYBERSECURITY ANALYST
Bohlale Analyst is the orchestration and assistance layer behind authenticated deeper assessments. Not a permanent AI process, not a homepage bot, and not a requirement for basic no-token URL checks.
- Launch only on authorised request or approved schedule; persistent DB-backed stages: Recon -> Investigation/Hunt -> Independent Validation -> Findings/Explanation -> Human-reviewed remediation -> Verify/Rescan.
- Reference Cloudflare: https://github.com/cloudflare/security-audit-skill and https://blog.cloudflare.com/build-your-own-vulnerability-harness. Review licence and retain notices when adapting substantial code. Do not copy Cloudflare's whole internal fleet system; start with minimal bounded pipeline.
- Source code, tool output, websites and MCP manifests are UNTRUSTED DATA. Prompt text alone is not permission enforcement.
- Verify evidence and paths mechanically; independent validator should try to disprove the discovery agent, not rubber-stamp it. Separate confirmed observations from unconfirmed hypotheses.
- Preserve task state, progress, logs, failures and recovery. No endless agent loops, no context explosion. Route to chosen models through provider abstraction (DeepSeek initial; alternative providers possible), with request-level quotas, retries, model version and audit.
- AI explanation / fix suggestion are opt-in. Private customer code must not go to external models without documented consent, appropriate processor terms and redaction.
- Each run records exact metered model/provider input, output and cached tokens, provider cost and estimates clearly distinguished. AI is optional when service is unavailable.
- **Avoid high-cost default reasoning on a R79 plan**. Offer advanced Analyst assessments separately.

## 6. REPORTS, SHARING, COMMERCIAL POLICY
- Free: anonymous bounded passive website URL preview.
- Proposed R79: ONE bounded deeper assessment of an authorised repository with evidence-backed private report and one limited targeted rescan. Payment not live until working functionality, unit economics and approvals are verified.
- Standard pilot target AI spend R2/report; configurable pilot AI ceiling R5/report. These are COST TARGETS, not guarantees; overage should produce an honest partial outcome or require a separate consented upgrade. Do not silently bill extra or drop essential safety verification.
- Payment processing sandbox ONLY until owner authorises production. Entitlement assigned server-side after verified signed/idempotent webhook and reconciliation. Never label sandbox transactions as actual revenue. VAT registration not established: no unsupported VAT wording.
- Secure share workflow: private by default, authenticated recipients or expiring scoped token, link revocation, access audit, limited public summary redacted; cross-tenant report access forbidden.
- Show customer report state, download, share, revoke, fix, rescan; actually verify complete path.

## 7. RESTRICTED ADMIN CONSOLE (/admin)
Use the SAME approved white/blue Bohlale brand with compact inner-page logo and Google Admin-style utility-first navigation; meaningful tables and controls, no fake metrics.
- Secure platform owner bootstrap, backend-enforced RBAC with MFA for privileged staff.
- Roles: Platform Owner, Platform Administrator, Security Analyst, Customer Support, Finance Administrator, Governance Administrator. Least privilege and object-level checks; do not reveal sensitive customer evidence to general support.
- Modules:
  * Overview: measured users, orgs, scans, running/failed jobs, findings, report status, AI spend, alerts, sandbox/live billing distinction.
  * Users & Organisations: memberships, lifecycle, quotas, suspensions, appropriate support actions.
  * Scan Operations: target and verified scope, job states, started/ended, retries, errors, cancellation, scanner versions, execution quotas.
  * Engine Health: API, DB, Redis/queue, workers, URL, TLS, code scanners, optional AI scanners, report engine, provider configuration; real probing states Healthy/Degraded/Unavailable/Not Configured.
  * Analyst Operations: active/completed investigations, stage, model, cost, failures, safe pause/cancel/retry, sanitized logs.
  * Findings & Reports: provenance, verification, owner/tenant, reports and sharing events, careful access audits.
  * Billing & Revenue: sandbox transactions vs verified real revenue, R79 assessments, entitlements, refunds, failed payments.
  * AI Usage & Cost Ledger: per task, user, organisation, model, cache, provider, input/output tokens, ZAR cost, budgets and alerts.
  * Governance: risk/policy records via authenticated bridge to Bohlale GRC.
  * Audit Log: immutable/tamper-evident administrative and sensitive actions with proper retention.
  * Settings: feature flags, budgets, limits, notifications, retention, data provider config; secrets never readable by UI.
- Every action needs an audited, permission-checked backend operation. No user self-elevation. No privileged read of private customer data without specific authorised reason and auditable workflow.

## 8. OPERATIONS, SELF-CHECKING AND RECOVERY
- Startup readiness diagnostics validate required environment, DB connectivity/migrations, queue and workers, storage, auth, scanner installation/versions, PDF service, payment sandbox config, optional AI configuration. No secret leakage. Optional outages show degraded; required outages block the affected operation.
- Separate liveness and readiness health probes; monitored metrics, queue length, worker heartbeats, scan errors, billing discrepancies, token spend and alert escalation.
- Safe retry with bounded exponential backoff, idempotent tasks and webhook processing, cancellation, durable resumability; orchestrator / supervisor may restart isolated workers. No destructive "self repair", unbounded scans, automatic modifications to customer production or silent budget overruns.
- **Demo Readiness Check** button and CLI: real smoke tests for visitor scan, authenticated workflows, private reports, role access, engine health and sandbox payments. Status READY / DEGRADED / NOT READY with timestamp and precise measured evidence.
- Production staged deployment plan: dedicated app/API infrastructure vs isolated scan workers, private storage/DB/queue, TLS, firewall egress rules, backup-and-restore test, rollback, monitoring, secure configuration, vulnerability review, POPIA/privacy policy, abuse handling.

## 9. SECURITY NON-NEGOTIABLES
- Strict SSRF, IP and DNS rebinding protections on URL scanner and every redirect. Disallow local/private/link-local/reserved/cloud metadata access, validate destination at connection and prevent bypass.
- Anonymous scanning is passive and limited. No arbitrary active probes. Intrusive testing demands verified ownership and explicit authorisation/scope.
- Untrusted source code cannot execute in app server. Any sandbox testing requires OS-enforced isolation, no unnecessary external network, read-only source, allow-listed environment and bounded resources.
- Secret redaction, encrypted transport/storage, least privilege, scoped GitHub auth, secure session and MFA, rate limits, tenant isolation, secure report access, retention/deletion requirements.
- Never expose AI keys or customer source in logs. Do not send to public VirusTotal or third-party services without appropriate contract, consent and licensing.
- Verify cross-tenant controls, admin privilege escalation, reporting leaks, webhook replay, compromised scanner output, prompt injection and malicious URLs with tests.
- No model alone can authorise tools, override rules, approve patches or change settings. Human approval for deployment and irreversible operations.
- Don't remove sandbox protections to make a scanner work; unsupported environment is a blocker.

## 10. TESTS, DELIVERY ORDER AND RELEASE GATES
Do not attempt to build every future feature at once. First audit existing implementation and preserve functional milestones.

M1: Fix user journey and semantics: correct statuses, clear table, anonymous-to-account save/rescan, report download/share/revoke; lock homepage single-logo design, Product page, footer.
M2: Deepen verified URL and TLS/CA certificate analysis with safe network controls.
M3: Secure /admin RBAC + MFA + real overview, users, scanning ops, engine health and audits.
M4: Reliable isolated code scanning, findings provenance, persistent background queues and reports.
M5: Bounded optional Bohlale Analyst, verification, usage ledger and R79 payment SANDBOX.
M6: Governance bridge, advanced AI assessments, Certificate Watch and monitoring only after core validation.

Implement test layers:
- unit tests for parsers, findings, severity/classification and boundaries;
- integration tests for DB, queue, scan engines, GitHub auth and reporting;
- negative security tests for SSRF/rebinding/redirect, access-control bypass, tenant/report leakage, rate limits, token/cost ceilings, admin privilege, webhook replay and unsafe files;
- Playwright end-to-end for visitor, developer, admin, sharing/revocation and mobile view;
- demonstrate genuine real scanner results on owned/authorised fixtures, no production attacks;
- performance/load and backup/restore testing with explicit measured limits;
- check scanner versions, report accuracy, incomplete status, and credential redaction.

Status stages are DEVELOPMENT -> DEMONSTRATION READY -> STAGING READY -> PRODUCTION CANDIDATE -> PRODUCTION APPROVED. Never promote to PRODUCTION APPROVED without explicit owner approval, security review and operational evidence.

### Definition of done for each feature
A feature is DONE only with actual functional endpoint/UI, permissions, working data, executed tests, failure handling, documentation and non-fabricated evidence. Otherwise mark PARTIAL / BLOCKED / COMING LATER.

### Required engineer outputs
1. Actual workspace path, repo and git branch, local uncommitted changes.
2. Table of existing features: WORKING / PARTIAL / MISSING / DISABLED.
3. Architecture and priority gaps with security implications.
4. Real changes on the designated development branch only; not production.
5. Passing/failing tests with exact commands and evidence, no invented pass counts.
6. Real browser desktop and mobile screenshots.
7. Admin health and end-to-end demo readiness outcomes.
8. AI spend and scan-cost measurements where usage is implemented.
9. Updated BUILD_STATUS.md, limitations and next actions.
10. Commit/push only validated changes, avoid conflicts with unrelated source work.

**Begin by inspecting the current local application and implementing the highest-priority safe missing capability. Do not merely write plans; do not redesign the homepage; do not pretend unfinished features work.**
