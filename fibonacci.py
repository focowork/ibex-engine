"""
fibonacci.py
============
Projecta nivells de Fibonacci a partir del rang de preu del dia (maxim i
minim), per identificar:

- RETROCESSOS (23.6% / 38.2% / 50% / 61.8% / 78.6%): possibles zones on
  el preu podria "descansar" abans de continuar el moviment. La zona
  entre el 50% i el 61.8% es la mes vigilada pels traders tecnics i es
  marca com a "zona d'entrada suggerida".
- EXTENSIONS (127.2% / 161.8% / 200%): possibles objectius de sortida
  si el moviment continua mes enlla del rang actual.

La direccio (ALCISTA/BAIXISTA) es determina a partir de si el preu
actual esta mes a prop del maxim o del minim del dia (és a dir, si el
moviment dominant d'avui ha estat de pujada o de baixada).

IMPORTANT: aixo es una tecnica d'analisi tecnica estandard basada en
proporcions matematiques (la seqüencia de Fibonacci), NO una prediccio.
Els nivells son referencies que molts altres traders tambe vigilen,
cosa que els dona relleváncia estadistica, pero no garanteixen res.
"""

from typing import Dict

from models import PriceSnapshot, FibonacciLevels


# Percentatges estandard de Fibonacci (com a fraccio, no %).
RETRACEMENT_RATIOS: Dict[str, float] = {
    "23.6%": 0.236,
    "38.2%": 0.382,
    "50.0%": 0.500,
    "61.8%": 0.618,
    "78.6%": 0.786,
}

EXTENSION_RATIOS: Dict[str, float] = {
    "127.2%": 1.272,
    "161.8%": 1.618,
    "200.0%": 2.000,
}


def analyze_fibonacci(price: PriceSnapshot) -> FibonacciLevels:
    """Calcula els nivells de Fibonacci (retrocessos + extensions) a partir
    del rang de preu del dia d'una accio.

    Args:
        price: PriceSnapshot amb day_high, day_low i last_price ja calculats.

    Returns:
        FibonacciLevels amb els nivells de retroces (possibles entrades),
        els nivells d'extensio (possibles objectius de sortida) i la
        zona d'entrada suggerida (banda 50%-61.8%).
    """
    swing_high = price.day_high
    swing_low = price.day_low

    if swing_high <= 0 or swing_low <= 0 or swing_high == swing_low:
        return FibonacciLevels(
            direction="SENSE_DADES",
            swing_low=swing_low,
            swing_high=swing_high,
            notes="Sense prou rang de preu avui per calcular nivells de Fibonacci.",
        )

    rang = swing_high - swing_low

    # Direccio: si el preu actual esta mes a prop del maxim, el moviment
    # dominant d'avui ha estat alcista (i viceversa).
    dist_to_high = swing_high - price.last_price
    dist_to_low = price.last_price - swing_low
    direction = "ALCISTA" if dist_to_high <= dist_to_low else "BAIXISTA"

    retracement_levels: Dict[str, float] = {}
    extension_levels: Dict[str, float] = {}

    if direction == "ALCISTA":
        # Retrocessos: des del maxim cap avall (possibles zones de suport
        # on el preu podria descansar abans de seguir pujant).
        for label, ratio in RETRACEMENT_RATIOS.items():
            retracement_levels[label] = swing_high - (rang * ratio)
        # Extensions: per sobre del maxim (possibles objectius de sortida
        # si el moviment alcista continua).
        for label, ratio in EXTENSION_RATIOS.items():
            extension_levels[label] = swing_low + (rang * ratio)
        suggested_entry_zone = (retracement_levels["61.8%"], retracement_levels["50.0%"])
        notes = (
            "Moviment dominant d'avui a l'alça. Els retrocessos son possibles zones on "
            "el preu podria descansar abans de continuar pujant; les extensions son "
            "possibles objectius de sortida si segueix la pujada."
        )
    else:
        # Retrocessos: des del minim cap amunt (possibles zones de resistencia
        # on el preu podria descansar abans de seguir baixant).
        for label, ratio in RETRACEMENT_RATIOS.items():
            retracement_levels[label] = swing_low + (rang * ratio)
        # Extensions: per sota del minim (possibles objectius si la baixada continua).
        for label, ratio in EXTENSION_RATIOS.items():
            extension_levels[label] = swing_high - (rang * ratio)
        suggested_entry_zone = (retracement_levels["50.0%"], retracement_levels["61.8%"])
        notes = (
            "Moviment dominant d'avui a la baixa. Els retrocessos son possibles zones on "
            "el preu podria descansar abans de continuar baixant; les extensions son "
            "possibles objectius de sortida si segueix la baixada."
        )

    return FibonacciLevels(
        direction=direction,
        swing_low=swing_low,
        swing_high=swing_high,
        retracement_levels=retracement_levels,
        extension_levels=extension_levels,
        suggested_entry_zone=suggested_entry_zone,
        notes=notes,
    )
