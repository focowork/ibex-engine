"""
remaining_potential.py
======================
Calcula quant recorregut (en multiples d'ATR, la volatilitat mitjana per
barra) li queda al preu fins a l'objectiu de sortida. Una entrada amb
molt poc marge fins a l'objectiu es una entrada tardana: encara que
tots els altres senyals siguin excel·lents, ja queda poc marge de guany
respecte al risc assumit.

    Remaining Potential = |Objectiu - Preu actual| / ATR

    < 0.5 ATR  -> Entrada tardana (ja gairebe no queda recorregut)
    1-2 ATR    -> Correcte
    > 2 ATR    -> Molt recorregut (marge ampli fins a l'objectiu)
"""

from config import (
    REMAINING_POTENTIAL_LATE_THRESHOLD,
    REMAINING_POTENTIAL_GOOD_MIN,
    REMAINING_POTENTIAL_GOOD_MAX,
    REMAINING_POTENTIAL_LATE_ADJUSTMENT,
    REMAINING_POTENTIAL_CORRECT_ADJUSTMENT,
    REMAINING_POTENTIAL_HIGH_ADJUSTMENT,
)
from models import PriceSnapshot, RiskRewardAnalysis, RegimeAnalysis, RemainingPotentialAnalysis


def analyze_remaining_potential(
    price: PriceSnapshot,
    risk_reward: RiskRewardAnalysis,
    regime: RegimeAnalysis,
) -> RemainingPotentialAnalysis:
    """Calcula el potencial restant fins a l'objectiu, en multiples d'ATR.

    Args:
        price: PriceSnapshot (preu actual).
        risk_reward: RiskRewardAnalysis ja calculat (dona l'objectiu).
        regime: RegimeAnalysis ja calculat (dona l'ATR).

    Returns:
        RemainingPotentialAnalysis amb la categoria i l'ajust a aplicar
        a l'Entry Score.
    """
    if regime.atr <= 0 or risk_reward.target_price == 0.0 or price.last_price == 0.0:
        return RemainingPotentialAnalysis(
            atr_multiple=0.0,
            category="SENSE_DADES",
            adjustment=0.0,
            notes="Sense dades suficients (ATR o objectiu no disponibles) per calcular el potencial restant.",
        )

    distance = abs(risk_reward.target_price - price.last_price)
    atr_multiple = distance / regime.atr

    if atr_multiple < REMAINING_POTENTIAL_LATE_THRESHOLD:
        category = "ENTRADA_TARDANA"
        adjustment = REMAINING_POTENTIAL_LATE_ADJUSTMENT
        notes = (
            f"Nomes queden {atr_multiple:.2f}x l'ATR fins a l'objectiu: entrada tardana, "
            "ja gairebe no queda recorregut fins al preu objectiu actual."
        )
    elif atr_multiple > REMAINING_POTENTIAL_GOOD_MAX:
        category = "MOLT_RECORREGUT"
        adjustment = REMAINING_POTENTIAL_HIGH_ADJUSTMENT
        notes = f"Queden {atr_multiple:.2f}x l'ATR fins a l'objectiu: marge ampli."
    elif REMAINING_POTENTIAL_GOOD_MIN <= atr_multiple <= REMAINING_POTENTIAL_GOOD_MAX:
        category = "CORRECTE"
        adjustment = REMAINING_POTENTIAL_CORRECT_ADJUSTMENT
        notes = f"Queden {atr_multiple:.2f}x l'ATR fins a l'objectiu: marge correcte."
    else:
        category = "LIMITAT"
        adjustment = 0.0
        notes = f"Queden {atr_multiple:.2f}x l'ATR fins a l'objectiu: marge limitat pero no critic."

    return RemainingPotentialAnalysis(
        atr_multiple=atr_multiple,
        category=category,
        adjustment=adjustment,
        notes=notes,
    )
