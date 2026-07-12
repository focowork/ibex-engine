"""
orb.py
======
Opening Range Breakout (ORB): una de les estrategies intradia mes
estudiades. Es marca el maxim i el minim dels primers minuts de sessio
(el "rang d'obertura") i es comprova si el preu actual l'ha trencat
per dalt o per baix.

Un breakout del rang d'obertura amb volum es sovint interpretat com el
senyal de quina sera la direccio dominant de la sessio. NO es una
garantia — nomes una referencia estructural mes que altres traders
tambe vigilen.
"""

from models import PriceSnapshot, ORBAnalysis


def analyze_orb(price: PriceSnapshot) -> ORBAnalysis:
    """Compara el preu actual amb el rang d'obertura (ORB) del dia.

    Args:
        price: PriceSnapshot amb orb_high, orb_low i bars_since_open
            ja calculats.

    Returns:
        ORBAnalysis amb l'estat (ruptura alcista/baixista, dins de rang,
        o encara formant-se si tot just ha comencat la sessio).
    """
    if price.last_price == 0.0 or price.orb_high == 0.0:
        return ORBAnalysis(
            orb_high=0.0,
            orb_low=0.0,
            status="SENSE_DADES",
            notes="Sense dades suficients per calcular el rang d'obertura.",
        )

    # Si encara no han passat prou barres com per haver format l'ORB complet
    # (p.ex. estem als primers minuts de la sessio), avisa'n en lloc de
    # comparar un rang a mig formar.
    from config import ORB_BARS
    if price.bars_since_open <= ORB_BARS:
        return ORBAnalysis(
            orb_high=price.orb_high,
            orb_low=price.orb_low,
            status="ENCARA_FORMANT_SE",
            notes=(
                f"El rang d'obertura encara s'esta formant "
                f"({price.bars_since_open}/{ORB_BARS} barres). Torna-ho a provar mes tard."
            ),
        )

    if price.last_price > price.orb_high:
        breakout_pct = ((price.last_price - price.orb_high) / price.orb_high) * 100.0
        status = "RUPTURA_ALCISTA"
        notes = (
            f"Preu {breakout_pct:.2f}% per sobre del maxim del rang d'obertura "
            f"({price.orb_high:.2f}). Possible ruptura alcista si ve amb volum."
        )
    elif price.last_price < price.orb_low:
        breakout_pct = ((price.orb_low - price.last_price) / price.orb_low) * 100.0
        status = "RUPTURA_BAIXISTA"
        notes = (
            f"Preu {breakout_pct:.2f}% per sota del minim del rang d'obertura "
            f"({price.orb_low:.2f}). Possible ruptura baixista si ve amb volum."
        )
    else:
        breakout_pct = 0.0
        status = "DINS_RANG"
        notes = (
            f"Preu encara dins el rang d'obertura ({price.orb_low:.2f} - {price.orb_high:.2f}). "
            "Sense ruptura confirmada."
        )

    return ORBAnalysis(
        orb_high=price.orb_high,
        orb_low=price.orb_low,
        status=status,
        breakout_pct=breakout_pct,
        notes=notes,
    )
