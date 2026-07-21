"""
position_manager.py
====================
Gestor d'una posicio REAL ja oberta (capital ja invertit + nombre concret
d'accions), independent del rànquing general de l'accio. Fa de "company
de trading": en cada actualitzacio et diu exactament on ets (P&L, distancia
al stop i a l'objectiu) i si toca reduir accions ara mateix, seguint una
sortida ESGLAONADA per trams (en lloc de nomes "aguanta" o "ven-ho tot").

Filosofia dels trams (config.POSITION_DRAWDOWN_TIERS):
    Quan el preu es mou EN CONTRA, en lloc d'esperar que salti un unic
    stop sencer, es recomana anar reduint la posicio per trams a mesura
    que la caiguda (en %, des del preu d'entrada) avança. Aixo suavitza
    l'impacte: es va retallant risc de mica en mica, i nomes es tanca el
    100% si es toca el stop tecnic o el darrer tram.

    Quan el preu es mou A FAVOR i s'acosta o supera l'objectiu, es
    recomana recollir una part dels guanys (config.POSITION_PARTIAL_
    PROFIT_TAKE_PCT / POSITION_FULL_TARGET_TAKE_PCT) en lloc d'esperar
    a que el moviment es giri i es mengi el benefici acumulat.

IMPORTANT: aixo NO es consell financer ni una prediccio de cap tipus.
Nomes tradueix regles mecaniques i transparents (definides a config.py,
facilment ajustables) sobre el preu actual en aquest instant exacte.
"""

from config import (
    POSITION_DRAWDOWN_TIERS,
    POSITION_CLOSE_AT_STOP,
    POSITION_PARTIAL_PROFIT_AT_PCT_OF_TARGET,
    POSITION_PARTIAL_PROFIT_TAKE_PCT,
    POSITION_FULL_TARGET_TAKE_PCT,
)
from models import Position, PositionStatus


def _recommended_cumulative_fraction(position: Position, current_price: float) -> tuple:
    """Calcula quina fraccio ACUMULADA de les accions INICIALS s'hauria
    d'haver reduit a aquest preu, i una nota curta explicant per que.

    Returns:
        (fraccio 0.0-1.0, nota en catala, "stop_tocat"|"tram_perdua"|
         "objectiu"|"benefici_parcial"|"cap")
    """
    entry = position.entry_price
    if entry <= 0:
        return 0.0, "", "cap"

    # --- Preu tocant o per sota del stop tecnic: prioritat maxima ---
    if POSITION_CLOSE_AT_STOP and position.stop_price and current_price <= position.stop_price:
        return 1.0, f"El preu ha tocat el stop tecnic ({position.stop_price:.2f}).", "stop_tocat"

    # --- Preu en contra (per sota de l'entrada): trams de reduccio ---
    if current_price < entry:
        drop_pct = (entry - current_price) / entry * 100.0
        fraction = 0.0
        note = ""
        for threshold_pct, cumulative_fraction in POSITION_DRAWDOWN_TIERS:
            if drop_pct >= threshold_pct:
                fraction = cumulative_fraction
                note = f"Caiguda de {drop_pct:.1f}% des de l'entrada (tram -{threshold_pct:.0f}%)."
        if fraction > 0:
            return fraction, note, "tram_perdua"
        return 0.0, f"Caiguda de {drop_pct:.1f}% des de l'entrada, encara dins del primer tram.", "cap"

    # --- Preu a favor (per sobre de l'entrada): presa de beneficis ---
    if position.target_price and position.target_price > entry:
        progress = (current_price - entry) / (position.target_price - entry)
        if progress >= 1.0:
            return (
                POSITION_FULL_TARGET_TAKE_PCT,
                f"El preu ha arribat o superat l'objectiu ({position.target_price:.2f}).",
                "objectiu",
            )
        if progress >= POSITION_PARTIAL_PROFIT_AT_PCT_OF_TARGET:
            return (
                POSITION_PARTIAL_PROFIT_TAKE_PCT,
                f"El preu ja ha recorregut el {progress*100:.0f}% del cami cap a l'objectiu.",
                "benefici_parcial",
            )

    return 0.0, "Dins de marge, sense necessitat d'actuar ara mateix.", "cap"


def evaluate_position(position: Position, current_price: float) -> PositionStatus:
    """Avalua l'estat d'una posicio oberta al preu actual i genera la
    recomanacio d'accio (si n'hi ha alguna) en llenguatge natural.

    Args:
        position: Position ja oberta (capital, accions, stop, objectiu).
        current_price: preu actual de mercat.

    Returns:
        PositionStatus amb P&L, distancies i recomanacio.
    """
    shares_remaining = max(0, position.initial_shares - position.shares_reduced)
    entry = position.entry_price

    move_pct = ((current_price - entry) / entry * 100.0) if entry else 0.0
    pnl_eur = (current_price - entry) * shares_remaining
    capital_remaining = entry * shares_remaining
    pnl_pct = (pnl_eur / capital_remaining * 100.0) if capital_remaining else 0.0

    distance_to_stop_pct = (
        (current_price - position.stop_price) / current_price * 100.0
        if position.stop_price and current_price else 0.0
    )
    distance_to_target_pct = (
        (position.target_price - current_price) / current_price * 100.0
        if position.target_price and current_price else 0.0
    )

    if shares_remaining == 0:
        return PositionStatus(
            current_price=current_price,
            move_pct=move_pct,
            shares_remaining=0,
            pnl_eur=0.0,
            pnl_pct=0.0,
            distance_to_stop_pct=distance_to_stop_pct,
            distance_to_target_pct=distance_to_target_pct,
            shares_to_act_now=0,
            action="TANCADA",
            recommendation_text="Posicio ja tancada del tot: no queden accions actives.",
        )

    target_fraction, note, kind = _recommended_cumulative_fraction(position, current_price)
    already_reduced_fraction = position.shares_reduced / position.initial_shares if position.initial_shares else 0.0
    extra_fraction = max(0.0, target_fraction - already_reduced_fraction)
    shares_to_act_now = min(shares_remaining, round(extra_fraction * position.initial_shares))

    if kind == "stop_tocat":
        action = "TANCAR_STOP"
        recommendation_text = (
            f"🛑 {note} Tanca la posicio restant ({shares_remaining} accions) per protegir el capital."
        )
    elif kind == "tram_perdua" and shares_to_act_now > 0:
        action = "REDUIR"
        recommendation_text = (
            f"🔻 {note} Redueix {shares_to_act_now} accions ara mateix "
            f"(et quedarien {shares_remaining - shares_to_act_now} accions actives)."
        )
    elif kind == "objectiu" and shares_to_act_now > 0:
        action = "OBJECTIU_ASSOLIT"
        recommendation_text = (
            f"🎯 {note} Recomanat recollir benefici en {shares_to_act_now} accions "
            f"i pujar el stop al preu d'entrada ({entry:.2f}) per protegir la resta."
        )
    elif kind == "benefici_parcial" and shares_to_act_now > 0:
        action = "RECOLLIR_BENEFICI"
        recommendation_text = (
            f"💰 {note} Es pot valorar recollir benefici parcial en {shares_to_act_now} accions."
        )
    else:
        action = "MANTENIR"
        if move_pct >= 0:
            recommendation_text = f"✅ Preu a favor ({move_pct:+.1f}% des de l'entrada). Sense acció necessària ara mateix."
        else:
            recommendation_text = f"⏳ Preu en contra ({move_pct:+.1f}% des de l'entrada), pero encara dins de marge. Sense acció necessària ara mateix."

    return PositionStatus(
        current_price=current_price,
        move_pct=move_pct,
        shares_remaining=shares_remaining,
        pnl_eur=pnl_eur,
        pnl_pct=pnl_pct,
        distance_to_stop_pct=distance_to_stop_pct,
        distance_to_target_pct=distance_to_target_pct,
        shares_to_act_now=shares_to_act_now,
        action=action,
        recommendation_text=recommendation_text,
        tier_notes=note,
    )
