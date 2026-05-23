"""A domain — market & customer intelligence (Lead Intelligence)."""

from app.services.a_domain.intelligence_score import (
    IntelligenceScoreInput,
    IntelligenceScoreResult,
    compute_intelligence_score,
    infer_market_fit_segments,
)

__all__ = [
    "IntelligenceScoreInput",
    "IntelligenceScoreResult",
    "compute_intelligence_score",
    "infer_market_fit_segments",
]
