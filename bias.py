"""
bias.py
=======
Sintetitza en UN sol indicador de color cap a on apunten *ara mateix*
els senyals tecnics ja calculats per altres moduls (VWAP, ORB, regim +
direccio de Fibonacci, forca relativa vs index). Nomes compta quants
senyals apunten amunt vs avall, i tradueix aixo en un color:

    🟢 ALCISTA — la majoria de senyals apunten amunt ara mateix
    🔴 BAIXISTA — la majoria de senyals apunten avall ara mateix
    🟡 MIXT — els senyals es contradiuen entre ells

*** AIXO NO ES UNA PREDICCIO ***
No hi ha cap formula que garanteixi si un valor pujara o baixara. Aixo
nomes agrega senyals tecnics objectius (on esta el preu respecte al
VWAP, si ha trencat l'ORB, etc.) que ja existeixen en aquest motor. El
mercat pot girar en qualsevol moment; un biaix "alcista" pot invertir-se
al minut seguent. Es una fotografia del consens tecnic actual, no una
garantia de resultat futur.
"""

from typing import List

from models import (
    PriceSnapshot,
    RelativeStrengthAnalysis,
    RegimeAnalysis,
    FibonacciLevels,
    ORBAnalysis,
    BiasAnalysis,
)


def analyze_bias(
    price: PriceSnapshot,
    relative_strength: RelativeStrengthAnalysis,
    regime: RegimeAnalysis,
    fibonacci: FibonacciLevels,
    orb: ORBAnalysis,
) -> BiasAnalysis:
    """Combina 4 senyals direccionals ja calculats en un sol veredicte de color.

    Els 4 senyals son:
        1. Posicio del preu vs VWAP (per sobre = alcista, per sota = baixista)
        2. Estat de l'ORB (ruptura alcista/baixista, o neutre si esta dins de rang)
        3. Direccio de regim/Fibonacci (calculada a partir de si el preu esta
           mes a prop del maxim o del minim del dia)
        4. Forca relativa vs l'index (si l'accio guanya o perd contra el mercat)

    Args:
        price: PriceSnapshot (per la posicio vs VWAP).
        relative_strength: RelativeStrengthAnalysis.
        regime: RegimeAnalysis (nomes per avisar si el regim es caotic).
        fibonacci: FibonacciLevels (dona la direccio ALCISTA/BAIXISTA).
        orb: ORBAnalysis (estat de la ruptura del rang d'obertura).

    Returns:
        BiasAnalysis amb el recompte de senyals, el veredicte i el color.
    """
    signals: List[str] = []
    bullish = 0
    bearish = 0
    neutral = 0

    # --- Senyal 1: VWAP ---
    if price.vwap:
        vwap_diff_pct = ((price.last_price - price.vwap) / price.vwap) * 100.0
        if vwap_diff_pct > 0.05:
            bullish += 1
            signals.append(f"VWAP: preu per sobre ({vwap_diff_pct:+.2f}%) → alcista")
        elif vwap_diff_pct < -0.05:
            bearish += 1
            signals.append(f"VWAP: preu per sota ({vwap_diff_pct:+.2f}%) → baixista")
        else:
            neutral += 1
            signals.append("VWAP: preu pràcticament al VWAP → neutre")
    else:
        neutral += 1
        signals.append("VWAP: sense dades → neutre")

    # --- Senyal 2: ORB ---
    if orb.status == "RUPTURA_ALCISTA":
        bullish += 1
        signals.append("ORB: ruptura alcista del rang d'obertura → alcista")
    elif orb.status == "RUPTURA_BAIXISTA":
        bearish += 1
        signals.append("ORB: ruptura baixista del rang d'obertura → baixista")
    else:
        neutral += 1
        signals.append("ORB: dins del rang o sense dades → neutre")

    # --- Senyal 3: Regim / Fibonacci (direccio del moviment dominant d'avui) ---
    if fibonacci.direction == "ALCISTA":
        bullish += 1
        signals.append("Moviment dominant d'avui: alcista")
    elif fibonacci.direction == "BAIXISTA":
        bearish += 1
        signals.append("Moviment dominant d'avui: baixista")
    else:
        neutral += 1
        signals.append("Moviment dominant d'avui: sense dades → neutre")

    # --- Senyal 4: Forca relativa vs index ---
    if relative_strength.relative_strength_pct > 0.05:
        bullish += 1
        signals.append(f"Forca relativa: +{relative_strength.relative_strength_pct:.2f} p.p. vs index → alcista")
    elif relative_strength.relative_strength_pct < -0.05:
        bearish += 1
        signals.append(f"Forca relativa: {relative_strength.relative_strength_pct:.2f} p.p. vs index → baixista")
    else:
        neutral += 1
        signals.append("Forca relativa: pràcticament igual que l'index → neutre")

    # --- Veredicte final ---
    if bullish > bearish and bullish >= 3:
        bias_label, color = "ALCISTA_CLAR", "🟢"
    elif bullish > bearish:
        bias_label, color = "ALCISTA_LLEU", "🟢"
    elif bearish > bullish and bearish >= 3:
        bias_label, color = "BAIXISTA_CLAR", "🔴"
    elif bearish > bullish:
        bias_label, color = "BAIXISTA_LLEU", "🔴"
    else:
        bias_label, color = "MIXT", "🟡"

    whipsaw_warning = ""
    if regime.regime == "LATERAL_CAOTIC":
        whipsaw_warning = (
            " ⚠️ Regim lateral erratic (whipsaw): el biaix pot invertir-se molt rapid, "
            "dona-li menys pes del habitual."
        )

    notes = (
        f"{bullish} senyals alcistes, {bearish} baixistes, {neutral} neutres. "
        "AIXO NO ES UNA PREDICCIO: nomes el consens tecnic actual, que pot canviar "
        f"en qualsevol moment.{whipsaw_warning}"
    )

    return BiasAnalysis(
        bullish_count=bullish,
        bearish_count=bearish,
        neutral_count=neutral,
        bias=bias_label,
        color=color,
        signals=signals,
        notes=notes,
    )
