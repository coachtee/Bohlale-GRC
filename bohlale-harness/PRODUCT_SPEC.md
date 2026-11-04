# Product specification — Bohlale Harness v1

## 1. Who we serve
**First:** vibe coders and independent developers deploying apps built with Claude, Cursor, Lovable, Bolt, DeepSeek, etc. They may know how to prompt an app into existence but need a clear, evidence-backed security review.

**Second:** software companies and agencies reviewing client code.

**Third:** organisations, Information Officers, SMEs and enterprises adopting AI who need policies, AI inventories, assigned risks and audits.

## 2. Brand and design
- Official product name: **BOHLALE HARNESS**.
- Header/main tagline: **Scan to Secure.** Business section: **Scan to Govern.**
- Use *original* Bohlale mark from existing GitHub asset, not a generated replacement.
- Dark navy professional aesthetic; restrained accent colour, no neon sci-fi slop or fictional security scores.
- VirusTotal is the **interaction reference** only: precise, minimal, fast; do not copy its copyrighted branding or exact screen design.
- Fully responsive desktop and mobile; accessible contrast, focus, semantic labels, keyboard support, understandable errors.
- Top-level navigation: **Scan**, **Findings**, **Workspace**, and **Governance** (governance entry may be secondary for individual users).

## 3. Homepage
- Single clear input and **Scan** button. Tabs: **URL | CODE | AI | FILE**.
- URL: eligible for safe anonymous *passive* preview. No login required for basic public observations; enforce rate limiting.
- CODE: invite login and read-only GitHub connection; no claims of deep code coverage from a URL.
- AI: login, target ownership verification and explicit scope approval before any active probing.
- FILE: mark **Coming later** until safe malware isolation, retention and permissions are genuinely implemented. Do not create fake scan buttons.
- Plain statement of scan limitations and privacy.

## 4. Anonymous preview and login
- After anonymous URL scan show **real**, limited observations only (e.g., redirect, TLS certificate validity, HTTP security headers). Show checks actually run; distinguish **Not tested** from **Passed**.
- Preview may say e.g. '3 observations' only if measured. Avoid hiding immediate actionable safety notices solely for conversion.
- CTA: **Create a free account to save this scan and access deeper analysis.**
- Signing up does not retroactively turn a passive scan into a source-code or AI scan.
- Private reports, repository connection and history require sign-in.

## 5. Vibe-coder workflow
1. Enter public website URL → passive assessment preview.
2. Sign in → private workspace and saved history.
3. Link read-only GitHub repo and select branch / commit.
4. Receive scope summary (allowed tests, data sent to services, cost / quota / privacy).
5. Authorise deeper scan; job executes asynchronously.
6. Inspect Findings: severity, confidence, impacted file / path, evidence, reproduction context (sanitised), remediation and coverage.
7. Ask Bohlale for a concise explanation / proposed patch (opt-in and quota-controlled).
8. Developer reviews suggested change; it is **never auto-merged or auto-deployed**.
9. Re-scan; compare findings by fingerprint / commit.
10. Export signed-in PDF/JSON summary with limitations and checks performed.

## 6. Organisation workflow
- Organisation membership, roles and isolated private workspace.
- Register AI tools / models / application owners / data categories.
- AI usage policy template and approval workflow.
- POPIA awareness questions and safeguards inventory, not automatic POPIA certification.
- Map applicable controls to ISO/IEC 27001, ISO/IEC 42001, NIST AI RMF, NIST CSF and OWASP, with careful status (Mapped / Evidence available / Gap / Not assessed).
- Send verified scan findings into governance risk/action tracking via an authorised service integration with existing Bohlale GRC.
- Distinguish **company policy draft** from approved policy; no AI can publish an official policy unattended.

## 7. Five behind-the-scenes bots (feature flags)
- **Scan:** selects and coordinates tools; starts read-only.
- **Verify:** confidence review and safe, bounded verification using evidence.
- **Fix:** explains issues and prepares suggested patches for human review.
- **Govern:** suggests risks, policies and mapped actions.
- **Watch:** future integration for monitoring (e.g. Wazuh).
Bots share a harness, not necessarily separate LLM subscriptions. Tool policies are enforced **in code**. No autonomous attack/exploit agents in V1.

## 8. Reporting
Every finding must have: unique ID, target and scan ID, source engine + version, observed evidence, severity + confidence, affected location, remediation, validation status, timestamps and optional recognised CWE/CVE/OWASP mapping. If information is missing, show 'unknown' rather than guessing.

Reports must include: scan type, scope and authorisation, tests run, tests not run, repository commit SHA (if applicable), engine versions, findings, limitations, date, and verification state. **A 'no findings' report is not a security guarantee.**

## 9. Commercial proposition
- Free: limited public URL preview.
- Individual developer: **proposed R79 once-off** bounded deeper repo assessment, evidence-backed report and one limited rescan after changes.
- Subscription / governance and enterprise: later and priced separately; payment and invoice language must not assert VAT registration.
- Do not accept money for a feature that cannot actually be performed.

## 10. Explicitly out of V1
Self-serve full penetration testing, unfettered autonomous exploitation, malware detonation, unrestricted file uploads, unrestricted URL crawling, VirusTotal free API embedded into commercial product, automated ISO certification, SIEM replacement, 24/7 SOC, enterprise private deployment, and guaranteed security certificates.
