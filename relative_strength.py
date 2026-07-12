"""
relative_strength.py
=====================
Compara el comportament d'una accio amb el de l'index de referencia
(p.ex. IBEX +0,30% vs INDRA +2,10% -> forca relativa = +1,80 p.p.).
"""

from config import (
    RS_EXCELLENT_DIFF,
    RS_GOOD_DIFF,
    RS_NEUTRAL_DIFF,
    RS_NEGATIVE_DIFF,
    SCORE_MAX,
    SCORE_MIN,
)
from models import PriceSnapshot, IndexSnapshot, RelativeStrengthAnalysis


def compute_relative_strength(stock_change_pct: float, index_change_pct: float) -> float:
    """Calcula la forca relativa d'una accio respecte l'index.

    Args:
        stock_change_pct: variacio % de l'accio avui.
        index_change_pct: variacio % de l'index avui.

    Returns:
        Diferencia en punts percentuals (accio - index).
    """
    return stock_change_pct - index_change_pct


def score_relative_strength(diff: float) -> float:
    """Mapeja la diferencia de forca relativa a un score 0-100.

    Args:
        diff: diferencia en punts percentuals (accio - index).

    Returns:
        Score entre SCORE_MIN i SCORE_MAX.
    """
    if diff >= RS_EXCELLENT_DIFF:
        return SCORE_MAX
    if diff >= RS_GOOD_DIFF:
        span = RS_EXCELLENT_DIFF - RS_GOOD_DIFF
        progress = (diff - RS_GOOD_DIFF) / span
        return 75.0 + progress * 25.0
    if diff >= RS_NEUTRAL_DIFF:
        span = RS_GOOD_DIFF - RS_NEUTRAL_DIFF
        progress = (diff - RS_NEUTRAL_DIFF) / span
        return 50.0 + progress * 25.0
    if diff >= RS_NEGATIVE_DIFF:
        span = RS_NEUTRAL_DIFF - RS_NEGATIVE_DIFF
        progress = (diff - RS_NEGATIVE_DIFF) / span
        return 25.0 + progress * 25.0
    return max(SCORE_MIN, 25.0 + diff * 10.0)


def analyze_relative_strength(price: PriceSnapshot, index: IndexSnapshot) -> RelativeStrengthAnalysis:
    """Analisi de forca relativa completa per una accio.

    Args:
        price: PriceSnapshot de l'accio.
        index: IndexSnapshot de l'index de referencia.

    Returns:
        RelativeStrengthAnalysis amb la diferencia i el score.
    """
    diff = compute_relative_strength(price.change_pct, index.change_pct)
    score = score_relative_strength(diff)
    return RelativeStrengthAnalysis(
        stock_change_pct=price.change_pct,
        index_change_pct=index.change_pct,
        relative_strength_pct=diff,
        score=score,
    )
