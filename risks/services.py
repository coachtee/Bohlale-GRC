from .models import Risk, RiskMatrixConfig


def risk_overview(organisation):
    """Counts of open risks per band, for the dashboard Risk Overview
    donut (spec §34)."""
    matrix, _ = RiskMatrixConfig.objects.get_or_create(organisation=organisation)
    risks = Risk.objects.filter(organisation=organisation).exclude(status="closed")
    counts = {"very_low": 0, "low": 0, "medium": 0, "high": 0}
    for risk in risks:
        band_key, _ = matrix.band_for_score(risk.inherent_risk_score)
        counts[band_key] += 1
    return {
        "counts": counts,
        "total": sum(counts.values()),
    }
