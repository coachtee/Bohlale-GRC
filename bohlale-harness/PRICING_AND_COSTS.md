# Bohlale Harness pricing and unit economics (pilot assumptions)
**Proposed R79** per bounded developer code scan plus private report and one limited targeted rescan. Free passive public URL preview. No live charging before product is operational and approved.

Track actual report cost: LLM uncached/cached input and output tokens, model, API charged USD and conversion FX, sandbox CPU-minutes, egress/storage, threat feeds, payment fees, refunds and support. Per-report contribution = R79 - all variable costs; it is not net profit.

Default pilot budget: AI model cost target R2 / scan; hard R5; no AI required for deterministic checks; AI explanations and fixes opt-in with consent. Limit repository size and scanning duration. Price, model IDs, tariffs and fx-rate must be configurable and measured from actual provider usage, not assumed '$2 = 1M tokens'. Enforce quotas before calling models. Record overflow/partial outcomes honestly.

Do not imply the business is VAT-registered. Verify payment-provider pricing at implementation time. Payment sandbox first, only activate production after approval and successful security tests.
