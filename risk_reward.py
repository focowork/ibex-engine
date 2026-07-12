"""
risk_reward.py
==============
Combina el stop suggerit (entry_signal.py) amb l'objectiu de sortida
mes proper (fibonacci.py, extensio 127.2%) per calcular un ratio
Risc:Recompensa (R:R) explicit.

Molts traders professionals nomes es plantegen una entrada si el R:R
es >= 2:1 (es a dir, el guany potencial es almenys el doble de la
perdua potencial). Aixo permet descartar entrades que, tot i tenir un
score alt, tinguin un marge de guany petit comparat amb el risc.

IMPORTANT: aixo NO prediu si el preu arribara a l'objectiu ni si
saltara el stop. Nomes fa una divisio de distancies de preu.
"""

from config import (
    RISK_REWARD_EXCELLENT_THRESHOLD,
    RISK_REWARD_GOOD_THRESHOLD,
    RISK_REWARD_ACCEPTABLE_THRESHOLD,
)
from models import PriceSnapshot, EntrySignal, FibonacciLevels, RiskRewardAnalysis


def analyze_risk_reward(
    price: PriceSnapshot,
    entry: EntrySignal,
    fibonacci: FibonacciLevels,
) -> RiskRewardAnalysis:
    """Calcula el ratio Risc:Recompensa combinant el stop d'EntrySignal
    amb l'extensio de Fibonacci mes propera com a objectiu.

    Args:
        price: PriceSnapshot (preu actual).
        entry: EntrySignal ja calculat (dona el stop suggerit).
        fibonacci: FibonacciLevels ja calculat (dona l'objectiu de sortida).

    Returns:
        RiskRewardAnalysis amb el ratio i la seva classificacio.
    """
    if (
        price.last_price == 0.0
        or entry.suggested_stop_reference == 0.0
        or fibonacci.direction == "SENSE_DADES"
    ):
        return RiskRewardAnalysis(
            stop_price=0.0,
            target_price=0.0,
            risk=0.0,
            reward=0.0,
            ratio=0.0,
            quality="SENSE_DADES",
            notes="Sense dades suficients per calcular el Risc:Recompensa.",
        )

    stop_price = entry.suggested_stop_reference
    # L'objectiu es l'extensio 127.2%, la mes propera i per tant la mes
    # realista de les tres extensions calculades.
    target_price = fibonacci.extension_levels.get("127.2%", price.last_price)

    risk = abs(price.last_price - stop_price)
    reward = abs(target_price - price.last_price)

    if risk == 0:
        return RiskRewardAnalysis(
            stop_price=stop_price,
            target_price=target_price,
            risk=0.0,
            reward=reward,
            ratio=0.0,
            quality="SENSE_DADES",
            notes="El stop suggerit coincideix amb el preu actual: no es pot calcular un ratio fiable.",
        )

    ratio = reward / risk

    if ratio >= RISK_REWARD_EXCELLENT_THRESHOLD:
        quality = "EXCEL·LENT"
    elif ratio >= RISK_REWARD_GOOD_THRESHOLD:
        quality = "BO"
    elif ratio >= RISK_REWARD_ACCEPTABLE_THRESHOLD:
        quality = "ACCEPTABLE"
    else:
        quality = "DOLENT"

    notes = (
        f"Risc de {risk:.2f} (fins al stop a {stop_price:.2f}) vs. recompensa de {reward:.2f} "
        f"(fins a l'objectiu a {target_price:.2f}) → ratio {ratio:.2f}:1 ({quality}). "
        "Molts traders nomes entren si el ratio es >= 2:1."
    )

    return RiskRewardAnalysis(
        stop_price=stop_price,
        target_price=target_price,
        risk=risk,
        reward=reward,
        ratio=ratio,
        quality=quality,
        notes=notes,
    )
