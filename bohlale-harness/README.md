# BOHLALE HARNESS
## Scan to Secure.

**Status: approved product specification and development handoff — not a deployed or production-certified application.**

Bohlale Harness is a security-scanning and governance product with a VirusTotal-inspired *simple workflow*, but with its own design and original Bohlale branding. Its primary users are vibe coders and AI-assisted application developers. SMEs and enterprises use the related **Scan to Govern** workspace.

### The two experiences
- **Scan to Secure** — URL quick check, authorised source-code scan, optional AI application security checks, understandable findings, human-reviewed fix suggestions, rescan and evidence-based report.
- **Scan to Govern** — organisational AI inventory, AI usage policy, risk and control management, assigned actions, evidence and framework mapping, ideally using existing Bohlale GRC functionality through a secure integration.

### The product promise
The home screen has one primary action: **Scan**. The technical engine behind it is a bounded *security harness*, which coordinates scanners and AI only where justified. No fabricated vulnerabilities or fake scan progress. No claims of complete safety or official ISO certification.

### Development documents (read in this order)
1. [DEEPSEEK_BUILD_PROMPT.md](./DEEPSEEK_BUILD_PROMPT.md) — paste to DeepSeek
2. [PRODUCT_SPEC.md](./PRODUCT_SPEC.md) — final user-visible requirements
3. [ARCHITECTURE.md](./ARCHITECTURE.md) — implementation guidance
4. [SECURITY_AND_PRIVACY.md](./SECURITY_AND_PRIVACY.md) — mandatory gates
5. [API_CONTRACT.md](./API_CONTRACT.md) — scan and findings interface
6. [PRICING_AND_COSTS.md](./PRICING_AND_COSTS.md) — R79 proposal and AI budgets
7. [DELIVERY_AND_TESTS.md](./DELIVERY_AND_TESTS.md) — implementation priorities and exit criteria

### Existing Bohlale sources (preserve — do not overwrite)
- **Bohlale GRC:** https://github.com/coachtee/Bohlale-GRC — existing Django risk, policy, evidence and governance platform. Integrate using an explicit API contract, never direct cross-app DB writes.
- **Original Bohlale logo and mark:** https://github.com/coachtee/bohlale-cloud-health/tree/master/apps/web/public/brand — exact filenames: bohlale-logo-source.png, bohlale-logo.png, bohlale-mark.png. Verify brand permissions and image rendering before reuse.
- **CSAHE handbook:** User-provided learning reference for safe harness engineering. Not an endorsement, certification, or production code.
- **Claude Security / VirusTotal / Wazuh:** sources of product workflow inspiration; not a licence to copy UI, embed closed products or use their services without proper agreements.

### Repo handoff
This folder is a **standalone build brief placed on a feature branch in the existing public Bohlale-GRC repo**. It does not modify production app code or imply an existing production deployment. DeepSeek should implement the actual new services in this folder or propose a dedicated private repository when GitHub creation permissions are available.

**Branding:** BOHLALE HARNESS — Scan to Secure. Organisation workflow: Scan to Govern.
