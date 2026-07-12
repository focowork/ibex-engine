"""
stretch.py
==========
Mesura com d'"estesa" (allunyada del seu centre de gravetat) esta ja
una accio, combinant tres distancies:

    - Distancia al VWAP (preu mitja ponderat per volum del dia)
    - Distancia al POC (Point of Control, nivell amb mes volum negociat)
    - % del rang del dia ja recorregut en la direccio del moviment

Si dues o mes d'aquestes distancies son "grans", l'entrada es considera
massa estesa: encara que el momentum sigui excel·lent, pagar un preu
molt allunyat del seu centre de gravetat deixa menys marge i mes risc
de "digestio" (correccio tecnica curta abans de continuar, o final del
moviment).
"""

from config import (
    STRETCH_PENALTY,
    STRETCH_VWAP_THRESHOLD_PCT,
    STRETCH_POC_THRESHOLD_PCT,
    STRETCH_DAY_RANGE_THRESHOLD_PCT,
)
from models import PriceSnapshot, EntrySignal, VolumeProfileAnalysis, StretchAnalysis


def analyze_stretch(
    price: PriceSnapshot,
    entry: EntrySignal,
    volume_profile: VolumeProfileAnalysis,
) -> StretchAnalysis:
    """Calcula el nivell de 'stretch' d'una accio a partir de 3 distancies.

    Args:
        price: PriceSnapshot (day_high, day_low, last_price).
        entry: EntrySignal ja calculat (dona la distancia al VWAP).
        volume_profile: VolumeProfileAnalysis ja calculat (dona la
            distancia al POC).

    Returns:
        StretchAnalysis amb el nivell (BAIX/MITJA/ALT) i la penalitzacio
        a aplicar a l'Entry Score.
    """
    vwap_distance_pct = abs(entry.position_vs_vwap_pct)
    poc_distance_pct = abs(volume_profile.position_vs_poc_pct)

    if price.day_high > price.day_low:
        if price.last_price >= price.vwap:
            # Moviment alcista: quant s'ha recorregut des del minim.
            pct_range_covered = (
                (price.last_price - price.day_low) / (price.day_high - price.day_low)
            ) * 100.0
        else:
            # Moviment baixista: quant s'ha recorregut des del maxim.
            pct_range_covered = (
                (price.day_high - price.last_price) / (price.day_high - price.day_low)
            ) * 100.0
    else:
        pct_range_covered = 0.0

    exceed_count = 0
    if vwap_distance_pct >= STRETCH_VWAP_THRESHOLD_PCT:
        exceed_count += 1
    if poc_distance_pct >= STRETCH_POC_THRESHOLD_PCT:
        exceed_count += 1
    if pct_range_covered >= STRETCH_DAY_RANGE_THRESHOLD_PCT:
        exceed_count += 1

    if exceed_count >= 2:
        stretch_level = "ALT"
        penalty = STRETCH_PENALTY
        notes = (
            f"Entrada molt estesa: {vwap_distance_pct:.2f}% del VWAP, "
            f"{poc_distance_pct:.2f}% del POC, {pct_range_covered:.0f}% del rang del dia recorregut. "
            "Menys marge i mes risc de digestio abans de continuar."
        )
    elif exceed_count == 1:
        stretch_level = "MITJA"
        penalty = 0.0
        notes = (
            f"Estesa moderada: {vwap_distance_pct:.2f}% del VWAP, "
            f"{poc_distance_pct:.2f}% del POC, {pct_range_covered:.0f}% del rang del dia recorregut."
        )
    else:
        stretch_level = "BAIX"
        penalty = 0.0
        notes = (
            f"Entrada propera al seu centre de gravetat: {vwap_distance_pct:.2f}% del VWAP, "
            f"{poc_distance_pct:.2f}% del POC, {pct_range_covered:.0f}% del rang del dia recorregut."
        )

    return StretchAnalysis(
        vwap_distance_pct=vwap_distance_pct,
        poc_distance_pct=poc_distance_pct,
        pct_of_day_range_covered=pct_range_covered,
        stretch_level=stretch_level,
        penalty=penalty,
        notes=notes,
    )
