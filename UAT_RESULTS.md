# UAT Results — NIBS Reference Scenario

Executed during the production-readiness review (see `UAT_PLAN.md` for
the plan this reports against). Two passes were performed, as planned:
an automated pass through the real HTTP/view/template stack, and a
manual/visual pass in an actual browser.

## 1. Automated pass — `core/tests_uat.py`

**Command**: `python manage.py test core.tests_uat -v 2`
**Result**: `OK` — the full 22-step journey passes.

Every step in `UAT_PLAN.md` was exercised through Django's test client
(real URL routing → view → form validation → template — not a
shortcut through service functions), with assertions against actual
database state after each step, not just HTTP status codes. Confirmed:

- Organisation, journey, interview session, and knowledge-profile
  creation all persisted correctly with the expected field values.
- The AI-generated ISMS Scope document started in `Draft` status and
  never skipped a workflow stage — reaching `Published` only after a
  real `Signature` record was created with a typed name matching the
  approver's profile, consent ticked, and the document's content hash
  captured.
- **Permission boundaries were actively tested, not assumed**: a
  contributor was confirmed blocked (403) from signing a document and
  from closing an audit; only Executive/Approver/Consultant/Org Admin
  roles could complete those actions.
- Risk scores, SoA entries, evidence uploads (and their tenant-scoped
  download), incident notifications, register entries, audit findings,
  corrective actions, and management review completion all persisted
  with the exact values submitted through the forms.
- The audit readiness report rendered with real, non-trivial data and
  never used the word "certified".
- The risk register report (both HTML and the underlying data) reflected
  the actual risk created earlier in the same walkthrough.

### A real bug found and fixed during this pass

The UAT walkthrough's realistic three-persona setup (Consultant,
Executive, Contributor — no separate "Org Admin" account, mirroring how
a small NIBS-sized organisation would actually be staffed) surfaced a
genuine production bug that isolated unit tests had not caught:
**`IncidentCreateView` only notified `org_admin`/`consultant`-role
members, excluding the reporter. If the only consultant/org_admin in the
organisation was also the one reporting the incident, the notification
loop had nobody left to notify — the incident was recorded but silently
notified no one.** Fixed by broadening the notified role set to
`APPROVER_ROLES` (adds Executive), matching how approval-type
escalations are already handled elsewhere in the codebase. A regression
test (`incidents/tests.py::test_reporting_incident_also_notifies_executives`)
locks this in. This is exactly the kind of gap a realistic end-to-end
walkthrough catches that isolated per-feature unit tests, each set up
with a convenient admin account, do not.

Two issues were also found and fixed in the *test* itself during
development (not application bugs): an incorrect assumption about which
persona should be blocked from closing an audit (the Consultant is
themselves an approver — the boundary check needed the Contributor
persona instead), and an invalid Django ORM filter against a
`GenericForeignKey` field. Both are noted here for transparency, not
because they indicate a product defect.

## 2. Manual / visual pass (Playwright, real browser)

**Setup**: fresh SQLite dev database, `seed_frameworks` +
`seed_journey_templates` + `seed_nibs_demo` (idempotent, fictional NIBS
data only), `manage.py runserver`, Chromium via Playwright.

**Coverage**: 18 pages (dashboard, journey, frameworks, documents, risks,
controls/SoA, evidence, incidents, registers, audits, actions, reviews,
reports hub, audit readiness report, notifications, activity feed,
organisation members, profile) at two viewports (desktop 1440px, mobile
390px) = 36 page loads.

**Result**:
- **36/36 pages returned HTTP 200.**
- **Zero real console errors or JS exceptions.** The only console
  message logged across the entire pass was a single `favicon.ico`
  404 (Chromium's automatic favicon request — cosmetic, pre-existing,
  unrelated to any code in this repository, not fixed).
- Screenshots were taken for every page/viewport combination and
  reviewed directly (not just captured) — see §3 below for what was
  specifically checked.
- Mobile sidebar: the hamburger menu correctly opens a full-height
  slide-in navigation drawer with a backdrop; confirmed via computed
  class-state assertion (`#sidebar.open` toggled by the click), not
  just a screenshot.
- The new organisation member-management page (added during this
  review — see `SECURITY_AUDIT.md`) renders correctly with live data:
  5 members, per-row role dropdowns, Remove buttons, and the
  logged-in user's own row correctly showing a static badge instead of
  self-service controls (a user cannot demote/remove themselves).
- The Statement of Applicability table is wide (6 columns); on mobile
  it scrolls horizontally within its container (`.table-wrap {
  overflow-x: auto }`) rather than trying to compress every column into
  a 390px viewport — this is the deliberate, standard responsive
  pattern for dense data tables, not a bug.

## 3. What was specifically checked in the reviewed screenshots

- Dashboard (both viewports): stat cards, donut charts, implementation
  journey stepper, quick actions, task/review/activity panels all
  render with real NIBS data and correct proportions; no layout
  overflow or clipped content.
- Journey page (mobile): PDCA stepper and "what you need to do"
  guidance card readable and correctly stacked single-column.
- Documents list (mobile): filter pills, reference codes, and the two
  real published documents (ISMS Scope, Information Security Policy)
  render correctly.
- Organisation Settings / members (desktop): the newly-added
  member-management feature (§SECURITY_AUDIT.md RBAC section) confirmed
  visually correct with live seeded data.

## 4. Conclusion

The full NIBS reference journey (spec §47) works end-to-end through the
real application — not just individually-passing unit tests, but a
single continuous walkthrough that persists correct data, advances
workflow state correctly at each stage, and enforces the intended
permission boundaries. One real production bug was found and fixed as a
direct result of running this walkthrough with a realistic role
configuration; see §1 above and `SECURITY_AUDIT.md`.
