def active_organisation(request):
    return {
        "active_organisation": getattr(request, "organisation", None),
        "active_membership": getattr(request, "membership", None),
        "accessible_organisations": getattr(request, "accessible_organisations", None),
    }
