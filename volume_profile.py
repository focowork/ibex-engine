"""
volume_profile.py
==================
Interpreta el Point of Control (POC) ja calculat a data_loader.py: el
nivell de preu on s'ha negociat mes volum avui. Aquest nivell sol
actuar com un "iman" de preu (molta gent hi te posicions obertes des
d'aquell nivell), i tendeix a comportar-se com un suport/resistencia
mes fiable que un nivell triat arbitrariament.
"""

from models import PriceSnapshot, VolumeProfileAnalysis


def analyze_volume_profile(price: PriceSnapshot) -> VolumeProfileAnalysis:
    """Genera la interpretacio del POC per aquesta accio.

    Args:
        price: PriceSnapshot amb poc_price ja calculat.

    Returns:
        VolumeProfileAnalysis amb la posicio del preu actual respecte al POC.
    """
    if price.last_price == 0.0 or price.poc_price == 0.0:
        return VolumeProfileAnalysis(
            poc_price=0.0,
            position_vs_poc_pct=0.0,
            notes="Sense dades suficients per calcular el Volume Profile.",
        )

    position_vs_poc_pct = ((price.last_price - price.poc_price) / price.poc_price) * 100.0

    if abs(position_vs_poc_pct) < 0.2:
        notes = (
            f"Preu pràcticament al POC ({price.poc_price:.2f}), el nivell amb mes volum "
            "negociat avui. Zona d'equilibri, sovint amb mes soroll a curt termini."
        )
    elif position_vs_poc_pct > 0:
        notes = (
            f"Preu {position_vs_poc_pct:+.2f}% per sobre del POC ({price.poc_price:.2f}). "
            "El POC pot actuar de suport si el preu hi torna."
        )
    else:
        notes = (
            f"Preu {position_vs_poc_pct:+.2f}% per sota del POC ({price.poc_price:.2f}). "
            "El POC pot actuar de resistencia si el preu hi torna."
        )

    return VolumeProfileAnalysis(
        poc_price=price.poc_price,
        position_vs_poc_pct=position_vs_poc_pct,
        notes=notes,
    )
