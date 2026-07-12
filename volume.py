"""
volume.py
=========
Analisi de volum: calcula el volum relatiu i el seu score (0-100).
"""

from config import (
    RELATIVE_VOLUME_EXCELLENT,
    RELATIVE_VOLUME_HIGH,
    RELATIVE_VOLUME_NORMAL,
    RELATIVE_VOLUME_LOW,
    SCORE_MAX,
    SCORE_MIN,
)
from models import PriceSnapshot, VolumeAnalysis


def compute_relative_volume(current_volume: float, average_volume: float) -> float:
    """Calcula com es compara el volum actual amb la mitjana historica.

    Args:
        current_volume: volum acumulat avui fins ara.
        average_volume: mitjana historica de volum a la mateixa hora del dia.

    Returns:
        Ratio actual/mitjana. Retorna 1.0 (neutre) si la mitjana es 0.
    """
    if average_volume <= 0:
        return 1.0
    return current_volume / average_volume


def score_relative_volume(relative_volume: float) -> float:
    """Mapeja un ratio de volum relatiu a un score 0-100.

    Interpolacio lineal entre els llindars definits a config.py:
      < LOW        -> 0-25
      LOW-NORMAL   -> 25-50
      NORMAL-HIGH  -> 50-75
      HIGH-EXCELLENT -> 75-100
      >= EXCELLENT -> 100

    Args:
        relative_volume: ratio volum actual / volum mitja.

    Returns:
        Score entre SCORE_MIN i SCORE_MAX.
    """
    if relative_volume >= RELATIVE_VOLUME_EXCELLENT:
        return SCORE_MAX
    if relative_volume >= RELATIVE_VOLUME_HIGH:
        span = RELATIVE_VOLUME_EXCELLENT - RELATIVE_VOLUME_HIGH
        progress = (relative_volume - RELATIVE_VOLUME_HIGH) / span
        return 75.0 + progress * 25.0
    if relative_volume >= RELATIVE_VOLUME_NORMAL:
        span = RELATIVE_VOLUME_HIGH - RELATIVE_VOLUME_NORMAL
        progress = (relative_volume - RELATIVE_VOLUME_NORMAL) / span
        return 50.0 + progress * 25.0
    if relative_volume >= RELATIVE_VOLUME_LOW:
        span = RELATIVE_VOLUME_NORMAL - RELATIVE_VOLUME_LOW
        progress = (relative_volume - RELATIVE_VOLUME_LOW) / span
        return 25.0 + progress * 25.0
    # Per sota del llindar LOW: volum molt feble.
    return max(SCORE_MIN, relative_volume / RELATIVE_VOLUME_LOW * 25.0)


def analyze_volume(price: PriceSnapshot) -> VolumeAnalysis:
    """Analisi de volum completa per una accio.

    Args:
        price: PriceSnapshot amb volum actual i mitja.

    Returns:
        VolumeAnalysis amb el ratio de volum relatiu i el seu score.
    """
    relative_volume = compute_relative_volume(price.current_volume, price.average_volume_at_this_time)
    score = score_relative_volume(relative_volume)
    return VolumeAnalysis(relative_volume=relative_volume, score=score)
