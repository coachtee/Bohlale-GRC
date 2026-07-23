"""
Assembles the data for the main organisation dashboard (spec §34).
Kept as a plain function (not baked into the view) so other places —
e.g. an executive summary report — can reuse the same aggregation.

NOTE: this is intentionally built out incrementally as each dependent
module (journeys, frameworks, risks, documents, actions, activity...)
comes online. See BUILD_STATUS.md for current coverage.
"""


def build_dashboard_context(request):
    org = request.organisation
    context = {
        "organisation": org,
    }
    return context
