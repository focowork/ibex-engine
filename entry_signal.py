"""
entry_signal.py
================
Analitza si el moment ACTUAL es un bon punt d'entrada, no nomes si
l'accio esta "forta". Una accio pot tenir un score alt (molt volum,
molt mes forta que l'index) i tot i aixi ja estar massa "esgotada"
en el moment exacte que mires la pantalla — comprar-la aleshores sol
sortir car.

Fa servir dues referencies estandard de trading intradia:

- VWAP (preu mitja ponderat per volum del dia): si el preu esta molt
  per sobre del VWAP, la posicio mitjana de qui ha comprat avui ja te
  molt de guany, i entrar ara vol dir pagar un preu allunyat de la
  "mitjana justa" del dia.
- Rang del dia (maxim/minim): si el preu esta MOLT a prop del maxim
  del dia, pot ser una ruptura (bo, si ve amb volum) o pot ser un
  sostre a curt termini (car, si el volum ja s'esta apagant).

IMPORTANT: aixo NO es un consell d'inversio ni prediu res. Nomes
descriu, amb dades objectives, la posicio del preu dins la sessio
d'avui, perque la persona pugui jutjar-ho amb mes context.
"""

from config import EXTREME_MOVE_WARNING_PCT
from models import PriceSnapshot, EnergyAnalysis, RegimeAnalysis, EntrySignal


# Llindars (en %) que separen les diferents categories de qualitat
# d'entrada. Son configurables aqui mateix si es vol ajustar la sensibilitat.
VWAP_EXTENDED_THRESHOLD_PCT = 1.5     # per sobre d'aixo, es considera "allunyat" del VWAP
NEAR_HIGH_THRESHOLD_PCT = 0.5         # per sota d'aixo del maxim, es considera "a prop del maxim"
NEAR_LOW_THRESHOLD_PCT = 0.5          # per sota d'aixo per sobre del minim, "a prop del minim"


def analyze_entry(price: PriceSnapshot, energy: EnergyAnalysis, regime: RegimeAnalysis) -> EntrySignal:
    """Genera un EntrySignal a partir del PriceSnapshot, l'EnergyAnalysis i
    el RegimeAnalysis ja calculats.

    Args:
        price: dades de preu/VWAP/rang del dia d'aquesta accio.
        energy: analisi d'energia del moviment (per saber si accelera
            o s'esgota, i combinar-ho amb la posicio dins el rang).
        regime: analisi de regim (tendencia / lateral tranquil / lateral
            caotic). Si el regim es LATERAL_CAOTIC, es sobreescriu la
            qualitat d'entrada amb un avis de whipsaw i s'eixampla la
            referencia de stop en lloc de fer servir un nivell ajustat.

    Returns:
        EntrySignal.
    """
    if price.last_price == 0.0 or price.day_high == 0.0:
        return EntrySignal(
            position_vs_vwap_pct=0.0,
            distance_to_high_pct=0.0,
            distance_to_low_pct=0.0,
            quality="SENSE_DADES",
            suggested_stop_reference=0.0,
            notes="Sense dades de mercat suficients (mercat tancat o accio sense historial).",
        )

    position_vs_vwap_pct = ((price.last_price - price.vwap) / price.vwap) * 100.0 if price.vwap else 0.0
    distance_to_high_pct = ((price.day_high - price.last_price) / price.day_high) * 100.0 if price.day_high else 0.0
    distance_to_low_pct = ((price.last_price - price.day_low) / price.day_low) * 100.0 if price.day_low else 0.0

    near_high = distance_to_high_pct <= NEAR_HIGH_THRESHOLD_PCT
    near_low = distance_to_low_pct <= NEAR_LOW_THRESHOLD_PCT
    far_above_vwap = position_vs_vwap_pct >= VWAP_EXTENDED_THRESHOLD_PCT
    far_below_vwap = position_vs_vwap_pct <= -VWAP_EXTENDED_THRESHOLD_PCT
    energy_accelerating = energy.state == "ACCELERANT"
    energy_fading = energy.state == "ESGOTANT"

    # --- Prioritat maxima: regim lateral caotic (whipsaw) ---
    # Si l'accio esta oscil·lant sense rumb, qualsevol senyal de "ruptura"
    # o "marge de recorregut" es poc fiable: avisa'n abans que res.
    if regime.regime == "LATERAL_CAOTIC":
        quality = "ALT_RISC_WHIPSAW"
        notes = (
            f"{regime.notes} Si tot i aixi vols entrar-hi, considera un stop MES AMPLE "
            f"(~{regime.suggested_stop_distance:.2f} de distancia en preu, basat en l'ATR) "
            "en lloc d'un stop ajustat al VWAP o al minim del dia, que quedaria dins el "
            "soroll normal i saltaria facilment."
        )
        suggested_stop_reference = (
            price.last_price - regime.suggested_stop_distance
            if price.last_price >= price.vwap
            else price.last_price + regime.suggested_stop_distance
        )
    else:
        # --- Logica de classificacio normal (regim en tendencia o lateral tranquil) ---
        if near_high and far_above_vwap and energy_fading:
            quality = "SOBREESTES"
            notes = (
                f"Preu molt a prop del maxim del dia (a {distance_to_high_pct:.2f}% del maxim) "
                f"i {position_vs_vwap_pct:+.2f}% per sobre del VWAP, amb l'energia esgotant-se. "
                "Entrar ara vol dir pagar lluny de la mitjana del dia i sense impuls fresc darrere."
            )
        elif near_high and energy_accelerating:
            quality = "RUPTURA"
            notes = (
                f"Preu a {distance_to_high_pct:.2f}% del maxim del dia amb energia accelerant. "
                "Pot ser una ruptura valida si ve acompanyada de volum alt (mira l'analisi de volum)."
            )
        elif far_above_vwap and not near_high:
            quality = "MARGE_RECORREGUT"
            notes = (
                f"Preu {position_vs_vwap_pct:+.2f}% per sobre del VWAP pero encara a "
                f"{distance_to_high_pct:.2f}% del maxim del dia: encara hi ha marge abans de xocar amb el sostre d'avui."
            )
        elif far_below_vwap and near_low:
            quality = "SOBREESTES"
            notes = (
                f"Preu {position_vs_vwap_pct:+.2f}% per sota del VWAP i a prop del minim del dia "
                f"({distance_to_low_pct:.2f}% per sobre). Moviment baixista amb poc marge de descans."
            )
        else:
            quality = "LATERAL"
            notes = (
                f"Preu {position_vs_vwap_pct:+.2f}% respecte al VWAP, sense una posicio extrema "
                "dins el rang del dia. Ni clarament sobreestes ni clarament en ruptura."
            )

        # Referencia de risc: si estem per sobre del VWAP, referencia = VWAP (o minim si es mes proper);
        # si estem per sota, referencia = minim del dia.
        if price.last_price >= price.vwap:
            suggested_stop_reference = max(price.vwap, price.day_low)
        else:
            suggested_stop_reference = price.day_low

    # --- Avis de moviment extrem (independent del regim/qualitat anterior) ---
    # Un moviment intradia molt gran te mes risc estadistic de correccio
    # tecnica en properes sessions. No sobreescriu la qualitat d'entrada,
    # nomes hi afegeix una nota de prudencia.
    extreme_move_warning = abs(price.change_pct) >= EXTREME_MOVE_WARNING_PCT
    if extreme_move_warning:
        notes += (
            f" ⚠️ Moviment intradia molt gran avui ({price.change_pct:+.2f}%): "
            "els moviments grans en una sola sessio tenen mes risc estadistic de correccio "
            "tecnica els dies seguents. Aixo no es una prediccio, nomes un avis de prudencia "
            "abans de perseguir el preu."
        )

    return EntrySignal(
        position_vs_vwap_pct=position_vs_vwap_pct,
        distance_to_high_pct=distance_to_high_pct,
        distance_to_low_pct=distance_to_low_pct,
        quality=quality,
        suggested_stop_reference=suggested_stop_reference,
        extreme_move_warning=extreme_move_warning,
        notes=notes,
    )
