"""
scoring.py
==========
Sistema de doble score (V2): separa el Momentum Score (probabilitat que
el moviment continui) de l'Entry Score (qualitat del punt d'entrada
actual), i els combina en un Final Score unic.

Aixo evita que una accio amb bon momentum pero una entrada ja molt cara
(p.ex. Risc:Recompensa d'1:1 perque ja ha pujat molt) rebi la mateixa
puntuacio que una amb el mateix momentum pero una entrada millor.

    Final Score = MOMENTUM_SCORE_WEIGHT * Momentum Score
                + ENTRY_SCORE_WEIGHT   * Entry Score
"""

from config import (
    MOMENTUM_SCORE_WEIGHT,
    ENTRY_SCORE_WEIGHT,
    MOMENTUM_WEIGHT_VWAP,
    MOMENTUM_WEIGHT_ORB,
    MOMENTUM_WEIGHT_RELATIVE_STRENGTH,
    MOMENTUM_WEIGHT_REGIME,
    MOMENTUM_WEIGHT_STRUCTURE,
    MOMENTUM_WEIGHT_NEWS,
    REGIME_MOMENTUM_POINTS,
    ENTRY_SCORE_BASELINE,
    RR_ADJUSTMENT_BELOW_1,
    RR_ADJUSTMENT_1_TO_2,
    RR_ADJUSTMENT_2_TO_3,
    RR_ADJUSTMENT_3_TO_5,
    RR_ADJUSTMENT_ABOVE_5,
    VOLUME_ADJUSTMENT_HIGH,
    VOLUME_ADJUSTMENT_MED,
    VOLUME_ADJUSTMENT_LOW,
    SCORE_MIN,
    SCORE_MAX,
    THRESHOLD_BUY,
    THRESHOLD_WATCH,
    RECOMMENDATION_BUY,
    RECOMMENDATION_WATCH,
    RECOMMENDATION_AVOID,
)
from models import (
    VolumeAnalysis,
    RelativeStrengthAnalysis,
    NewsAnalysis,
    EnergyAnalysis,
    EntrySignal,
    RegimeAnalysis,
    ORBAnalysis,
    RiskRewardAnalysis,
    StretchAnalysis,
    RemainingPotentialAnalysis,
    ScoreBreakdown,
)


def _vwap_points(entry: EntrySignal) -> float:
    """Punts de Momentum segons la posicio del preu respecte al VWAP.

    Args:
        entry: EntrySignal ja calculat.

    Returns:
        100 si el preu esta per sobre del VWAP (alcista), 0 si per sota,
        50 si es pràcticament neutre.
    """
    if entry.position_vs_vwap_pct > 0.05:
        return 100.0
    if entry.position_vs_vwap_pct < -0.05:
        return 0.0
    return 50.0


def _orb_points(orb: ORBAnalysis) -> float:
    """Punts de Momentum segons l'estat de l'Opening Range Breakout."""
    if orb.status == "RUPTURA_ALCISTA":
        return 100.0
    if orb.status == "RUPTURA_BAIXISTA":
        return 0.0
    return 50.0


def _regime_points(regime: RegimeAnalysis) -> float:
    """Punts de Momentum segons el regim de mercat (tendencia/lateral)."""
    return REGIME_MOMENTUM_POINTS.get(regime.regime, 50.0)


def compute_momentum_score(
    entry: EntrySignal,
    orb: ORBAnalysis,
    relative_strength: RelativeStrengthAnalysis,
    regime: RegimeAnalysis,
    energy: EnergyAnalysis,
    news: NewsAnalysis,
) -> float:
    """Calcula el Momentum Score: la probabilitat que el moviment actual
    continui, SENSE tenir en compte si el punt d'entrada es car o barat.

    Components (pesos a config.py):
        - VWAP (direccio respecte al preu mitja ponderat per volum)
        - ORB (ruptura del rang d'obertura)
        - Forca relativa vs index
        - Regim de mercat (tendencia / lateral)
        - Estructura del moviment (energia: accelera o s'esgota)
        - Noticies rellevants

    Returns:
        Score 0-100.
    """
    return (
        _vwap_points(entry) * MOMENTUM_WEIGHT_VWAP
        + _orb_points(orb) * MOMENTUM_WEIGHT_ORB
        + relative_strength.score * MOMENTUM_WEIGHT_RELATIVE_STRENGTH
        + _regime_points(regime) * MOMENTUM_WEIGHT_REGIME
        + energy.score * MOMENTUM_WEIGHT_STRUCTURE
        + news.score * MOMENTUM_WEIGHT_NEWS
    )


def _risk_reward_adjustment(risk_reward: RiskRewardAnalysis) -> float:
    """Ajust de punts de l'Entry Score segons el ratio Risc:Recompensa."""
    if risk_reward.quality == "SENSE_DADES":
        return 0.0
    ratio = risk_reward.ratio
    if ratio < 1.0:
        return RR_ADJUSTMENT_BELOW_1
    if ratio < 2.0:
        return RR_ADJUSTMENT_1_TO_2
    if ratio < 3.0:
        return RR_ADJUSTMENT_2_TO_3
    if ratio <= 5.0:
        return RR_ADJUSTMENT_3_TO_5
    return RR_ADJUSTMENT_ABOVE_5


def _volume_adjustment(volume: VolumeAnalysis) -> float:
    """Ajust de punts de l'Entry Score segons el volum relatiu."""
    if volume.relative_volume > 2.0:
        return VOLUME_ADJUSTMENT_HIGH
    if volume.relative_volume >= 1.0:
        return VOLUME_ADJUSTMENT_MED
    if volume.relative_volume < 0.6:
        return VOLUME_ADJUSTMENT_LOW
    return 0.0


def compute_entry_score(
    risk_reward: RiskRewardAnalysis,
    stretch: StretchAnalysis,
    volume: VolumeAnalysis,
    remaining_potential: RemainingPotentialAnalysis,
) -> float:
    """Calcula l'Entry Score: si el punt d'entrada ACTUAL es bo, independentment
    de si el momentum de fons es fort o feble.

    Parteix d'una base neutra (config.ENTRY_SCORE_BASELINE) i hi aplica
    ajustos additius segons Risc:Recompensa, com d'estesa esta l'entrada
    (stretch), el volum de confirmacio i el potencial restant fins a
    l'objectiu (en multiples d'ATR). El resultat es limita a [0, 100].

    Returns:
        Score 0-100.
    """
    score = (
        ENTRY_SCORE_BASELINE
        + _risk_reward_adjustment(risk_reward)
        + stretch.penalty
        + _volume_adjustment(volume)
        + remaining_potential.adjustment
    )
    return max(SCORE_MIN, min(SCORE_MAX, score))


def determine_recommendation(final_score: float) -> str:
    """Mapeja el score final a una etiqueta de recomanacio.

    Args:
        final_score: 0-100.

    Returns:
        RECOMMENDATION_BUY / RECOMMENDATION_WATCH / RECOMMENDATION_AVOID.
    """
    if final_score >= THRESHOLD_BUY:
        return RECOMMENDATION_BUY
    if final_score >= THRESHOLD_WATCH:
        return RECOMMENDATION_WATCH
    return RECOMMENDATION_AVOID


def build_score_breakdown(
    volume: VolumeAnalysis,
    relative_strength: RelativeStrengthAnalysis,
    news: NewsAnalysis,
    energy: EnergyAnalysis,
    entry: EntrySignal,
    regime: RegimeAnalysis,
    orb: ORBAnalysis,
    risk_reward: RiskRewardAnalysis,
    stretch: StretchAnalysis,
    remaining_potential: RemainingPotentialAnalysis,
) -> ScoreBreakdown:
    """Construeix el ScoreBreakdown complet d'una accio: Momentum Score +
    Entry Score -> Final Score ponderat + recomanacio.

    Args:
        volume: VolumeAnalysis.
        relative_strength: RelativeStrengthAnalysis.
        news: NewsAnalysis.
        energy: EnergyAnalysis.
        entry: EntrySignal.
        regime: RegimeAnalysis.
        orb: ORBAnalysis.
        risk_reward: RiskRewardAnalysis.
        stretch: StretchAnalysis.
        remaining_potential: RemainingPotentialAnalysis.

    Returns:
        ScoreBreakdown amb momentum_score, entry_score, final_score i
        la recomanacio.
    """
    momentum_score = compute_momentum_score(
        entry=entry,
        orb=orb,
        relative_strength=relative_strength,
        regime=regime,
        energy=energy,
        news=news,
    )
    entry_score = compute_entry_score(
        risk_reward=risk_reward,
        stretch=stretch,
        volume=volume,
        remaining_potential=remaining_potential,
    )
    final_score = momentum_score * MOMENTUM_SCORE_WEIGHT + entry_score * ENTRY_SCORE_WEIGHT
    recommendation = determine_recommendation(final_score)

    return ScoreBreakdown(
        volume_score=volume.score,
        relative_strength_score=relative_strength.score,
        news_score=news.score,
        energy_score=energy.score,
        momentum_score=momentum_score,
        entry_score=entry_score,
        final_score=final_score,
        recommendation=recommendation,
    )
