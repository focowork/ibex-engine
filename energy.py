"""
energy.py
=========
Analitza si un moviment intradia encara te "energia" (probablement
continuara) o s'esta esgotant, a partir de les barres recents de preu i volum.
"""

from typing import List

from config import (
    ENERGY_STATE_STRONG_CONTINUATION,
    ENERGY_STATE_MODERATE_CONTINUATION,
    ENERGY_STATE_WEAKENING,
    ENERGY_STATE_EXHAUSTED,
    ENERGY_STATE_DECREASING_VOLUME,
    ENERGY_SCORE_MAP,
)
from models import PriceSnapshot, EnergyAnalysis

# Marges utilitzats per decidir si el preu fa "nous maxims" o "perd terreny".
# Es defineixen aqui (i no dins de les funcions) perque son constants propies
# d'aquest modul, seguint la norma de no usar numeros magics inline.
NEW_HIGH_TOLERANCE_RATIO: float = 0.999   # 99.9% del maxim recent compta com "als maxims"
PULLBACK_THRESHOLD_PCT: float = 0.3       # % de retrocés des del maxim per considerar "perd forca"
VOLUME_TREND_RATIO: float = 1.1           # 2a meitat > 1a meitat * 1.1 => volum creixent
VOLUME_DECLINE_RATIO: float = 0.9         # 2a meitat < 1a meitat * 0.9 => volum decreixent
MIN_BARS_FOR_TREND: int = 4               # minim de barres per calcular tendencies


def _is_making_new_highs(closes: List[float]) -> bool:
    """Comprova si l'ultim tancament esta als (o a prop dels) maxims recents."""
    if not closes:
        return False
    return closes[-1] >= max(closes) * NEW_HIGH_TOLERANCE_RATIO


def _volume_trend_increasing(volumes: List[float]) -> bool:
    """Comprova si el volum per barra recent creix (2a meitat vs 1a meitat)."""
    if len(volumes) < MIN_BARS_FOR_TREND:
        return False
    mid = len(volumes) // 2
    first_half_avg = sum(volumes[:mid]) / mid
    second_half_avg = sum(volumes[mid:]) / (len(volumes) - mid)
    return second_half_avg > first_half_avg * VOLUME_TREND_RATIO


def _volume_trend_decreasing(volumes: List[float]) -> bool:
    """Comprova si el volum per barra recent decreix."""
    if len(volumes) < MIN_BARS_FOR_TREND:
        return False
    mid = len(volumes) // 2
    first_half_avg = sum(volumes[:mid]) / mid
    second_half_avg = sum(volumes[mid:]) / (len(volumes) - mid)
    return second_half_avg < first_half_avg * VOLUME_DECLINE_RATIO


def _price_losing_ground(closes: List[float]) -> bool:
    """Comprova si el preu ha retrocedit significativament des del seu maxim recent."""
    if len(closes) < 3:
        return False
    peak = max(closes)
    last = closes[-1]
    if peak <= 0:
        return False
    pullback_pct = (peak - last) / peak * 100.0
    return pullback_pct > PULLBACK_THRESHOLD_PCT


def classify_energy_state(closes: List[float], volumes: List[float]) -> str:
    """Classifica l'estat de moment actual a partir de les barres recents.

    Args:
        closes: preus de tancament intradia recents (ordre cronologic).
        volumes: volum per barra intradia recent (ordre cronologic).

    Returns:
        Un dels ENERGY_STATE_* de config.py.
    """
    if len(closes) < 3 or len(volumes) < 3:
        # Encara no hi ha prou dades (p.ex. molt a l'inici de la sessio).
        return ENERGY_STATE_MODERATE_CONTINUATION

    making_highs = _is_making_new_highs(closes)
    vol_up = _volume_trend_increasing(volumes)
    vol_down = _volume_trend_decreasing(volumes)
    losing_ground = _price_losing_ground(closes)

    if making_highs and vol_up:
        return ENERGY_STATE_STRONG_CONTINUATION
    if losing_ground and vol_down:
        return ENERGY_STATE_EXHAUSTED
    if losing_ground:
        return ENERGY_STATE_WEAKENING
    if vol_down:
        return ENERGY_STATE_DECREASING_VOLUME
    return ENERGY_STATE_MODERATE_CONTINUATION


def _detail_for_state(state: str) -> str:
    """Explicacio curta i llegible per cada estat d'energia."""
    details = {
        ENERGY_STATE_STRONG_CONTINUATION: "El preu fa nous maxims recents amb volum creixent.",
        ENERGY_STATE_MODERATE_CONTINUATION: "El moviment es mante sense senyals clars de canvi.",
        ENERGY_STATE_DECREASING_VOLUME: "El volum disminueix, el moviment perd suport.",
        ENERGY_STATE_WEAKENING: "El preu s'allunya dels maxims recents.",
        ENERGY_STATE_EXHAUSTED: "El preu retrocedeix i el volum cau: moviment esgotat.",
    }
    return details.get(state, "")


def analyze_energy(price: PriceSnapshot) -> EnergyAnalysis:
    """Analisi d'energia/moment complet per una accio.

    Args:
        price: PriceSnapshot amb recent_closes i recent_volumes.

    Returns:
        EnergyAnalysis amb l'estat, el score i un detall curt.
    """
    state = classify_energy_state(price.recent_closes, price.recent_volumes)
    score = ENERGY_SCORE_MAP.get(state, 50.0)
    detail = _detail_for_state(state)
    return EnergyAnalysis(state=state, score=score, detail=detail)
