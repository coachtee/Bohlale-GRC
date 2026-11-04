# Bohlale Guard — Hermes Plugin Hackathon (Nov 2026)

**Submission deadline (as announced):** 11 November 2026 at 5 PM EST = 12 November 2026 at 00:00 SAST. Verify the submission form cutoff.

## Entry
**Bohlale Guard — Scan before your agent acts.** Native Hermes plugin with a pre_tool_call hook that blocks selected dangerous shell actions and requests approval for high-impact commands. Provides read-only offline project checks for common secret patterns, plus a command safety preview. No direct LLM API charges for the plugin tools. Optional secure integration with Bohlale Harness later.

## Prototype
ChatGPT-created source ZIP: BOHLALE_GUARD_HERMES_PLUGIN_v0.1.zip (attached in the conversation; not uploaded to GitHub). Passed 16 local Python unit tests and compilation, but it has NOT been tested inside the actual Hermes runtime, catalog-reviewed or deployed. Never advertise it as a complete security boundary.

## Next tasks for DeepSeek desktop
1. Unpack the ZIP and inspect/test source on current Hermes: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
2. Confirm pre_tool_call block/approve directives work on actual Hermes. Improve policy engine and coverage, and test bypasses; do not claim complete protection.
3. Show a safe non-executing test demo: evaluate rm -rf / (block), terraform destroy (approve); scan a locally owned demo project containing a fake secret marker and show file/line without leaking contents.
4. Put plugin source in a standalone **public** repository, or a public monorepo subdirectory. Follow official catalog admission rules and open PR against NousResearch/hermes-agent.
5. Post a REAL <=90 second demo video on X tagging @NousResearch; submit both links at https://form.typeform.com/to/FwJLvOln.

Bohlale Harness (Contabo SaaS, proposed R79 reports) is a distinct workstream. This plugin does not require Contabo, and it must never upload source code or tool arguments without explicit opt-in.
