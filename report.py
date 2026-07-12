"""
report.py
=========
Construeix les explicacions i renderitza l'informe final, net i llegible
des del mobil, amb nomes les cinc millors accions.
"""

from typing import List

from config import TOP_N_RESULTS, LONG_ONLY_MODE
from models import (
    PriceSnapshot,
    VolumeAnalysis,
    RelativeStrengthAnalysis,
    NewsAnalysis,
    EnergyAnalysis,
    ScoreBreakdown,
    EntrySignal,
    RegimeAnalysis,
    FibonacciLevels,
    ORBAnalysis,
    VolumeProfileAnalysis,
    RiskRewardAnalysis,
    BiasAnalysis,
    UpcomingEventsAnalysis,
    StretchAnalysis,
    RemainingPotentialAnalysis,
    StockReport,
)

# Llindars nomes per triar la frase descriptiva (no afecten el score,
# que ja s'ha calculat als moduls corresponents).
VOLUME_PHRASE_HIGH: float = 2.0
VOLUME_PHRASE_MEDIUM: float = 1.5
VOLUME_PHRASE_NORMAL: float = 1.0

STRENGTH_PHRASE_STRONG: float = 1.0
STRENGTH_PHRASE_POSITIVE: float = 0.0


def _volume_phrase(volume: VolumeAnalysis) -> str:
    """Frase curta que descriu el volum relatiu."""
    if volume.relative_volume >= VOLUME_PHRASE_HIGH:
        return "Volum molt alt"
    if volume.relative_volume >= VOLUME_PHRASE_MEDIUM:
        return "Volum alt"
    if volume.relative_volume >= VOLUME_PHRASE_NORMAL:
        return "Volum normal"
    return "Volum baix"


def _strength_phrase(rs: RelativeStrengthAnalysis) -> str:
    """Frase curta que descriu la forca relativa vs l'index."""
    if rs.relative_strength_pct >= STRENGTH_PHRASE_STRONG:
        return "Molt mes forta que l'index"
    if rs.relative_strength_pct >= STRENGTH_PHRASE_POSITIVE:
        return "Mes forta que l'index"
    return "Mes debil que l'index"


def build_explanation(
    volume: VolumeAnalysis,
    relative_strength: RelativeStrengthAnalysis,
    news: NewsAnalysis,
    energy: EnergyAnalysis,
) -> str:
    """Construeix una explicacio curta que justifica el score/recomanacio.

    Cada accio ha d'entendre's SEMPRE: mai es dona una recomanacio sense
    els motius que la sustenten.

    Args:
        volume: VolumeAnalysis.
        relative_strength: RelativeStrengthAnalysis.
        news: NewsAnalysis.
        energy: EnergyAnalysis.

    Returns:
        Text multi-linia amb un motiu per pilar.
    """
    lines = [
        f"- {_volume_phrase(volume)}",
        f"- {_strength_phrase(relative_strength)}",
        f"- {news.summary}",
        f"- {energy.detail}",
    ]
    return "\n".join(lines)


def build_stock_report(
    price: PriceSnapshot,
    volume: VolumeAnalysis,
    relative_strength: RelativeStrengthAnalysis,
    news: NewsAnalysis,
    energy: EnergyAnalysis,
    scores: ScoreBreakdown,
    entry: EntrySignal,
    regime: RegimeAnalysis,
    fibonacci: FibonacciLevels,
    orb: ORBAnalysis,
    volume_profile: VolumeProfileAnalysis,
    risk_reward: RiskRewardAnalysis,
    bias: BiasAnalysis,
    upcoming_events: UpcomingEventsAnalysis,
    stretch: StretchAnalysis,
    remaining_potential: RemainingPotentialAnalysis,
) -> StockReport:
    """Munta l'objecte StockReport complet d'una accio.

    Args:
        price: PriceSnapshot.
        volume: VolumeAnalysis.
        relative_strength: RelativeStrengthAnalysis.
        news: NewsAnalysis.
        energy: EnergyAnalysis.
        scores: ScoreBreakdown (Momentum Score + Entry Score + Final Score).
        entry: EntrySignal (qualitat del punt d'entrada ara mateix).
        regime: RegimeAnalysis (tendencia / lateral tranquil / lateral caotic).
        fibonacci: FibonacciLevels (retrocessos i extensions).
        orb: ORBAnalysis (Opening Range Breakout).
        volume_profile: VolumeProfileAnalysis (Point of Control).
        risk_reward: RiskRewardAnalysis (ratio R:R explicit).
        bias: BiasAnalysis (biaix direccional combinat, NO es una prediccio).
        upcoming_events: UpcomingEventsAnalysis (calendari de resultats).
        stretch: StretchAnalysis (com d'estesa esta l'entrada).
        remaining_potential: RemainingPotentialAnalysis (potencial restant en ATR).

    Returns:
        StockReport llest per renderitzar.
    """
    explanation = build_explanation(volume, relative_strength, news, energy)
    return StockReport(
        display_name=price.display_name,
        ticker=price.ticker,
        price=price,
        volume=volume,
        relative_strength=relative_strength,
        news=news,
        energy=energy,
        scores=scores,
        entry=entry,
        regime=regime,
        fibonacci=fibonacci,
        orb=orb,
        volume_profile=volume_profile,
        risk_reward=risk_reward,
        bias=bias,
        upcoming_events=upcoming_events,
        stretch=stretch,
        remaining_potential=remaining_potential,
        explanation=explanation,
    )


def build_short_reason(
    volume: VolumeAnalysis,
    relative_strength: RelativeStrengthAnalysis,
    news: NewsAnalysis,
) -> str:
    """Construeix UNA sola frase amb el motiu mes rellevant, per un resum
    directe (no una llista de 4 bullets). Prioritza la noticia si n'hi ha
    una de rellevant; si no, combina volum + forca relativa.

    Args:
        volume: VolumeAnalysis.
        relative_strength: RelativeStrengthAnalysis.
        news: NewsAnalysis.

    Returns:
        Frase curta, en minuscules excepte la primera lletra.
    """
    if news.best_category not in ("Sense noticia",) and news.score >= 65:
        return news.summary
    return f"{_volume_phrase(volume).lower()} i {_strength_phrase(relative_strength).lower()}"


# Veredicte directe: combina la recomanacio (COMPRAR/VIGILAR/EVITAR) amb la
# qualitat del punt d'entrada (RUPTURA/MARGE_RECORREGUT/SOBREESTES/LATERAL)
# per donar UNA frase d'accio, en lloc de deixar que la persona hagi de
# creuar dues dades per treure la conclusio ella mateixa.
_VERDICTS = {
    ("COMPRAR", "RUPTURA"):          ("🟢", "ENTRA ARA"),
    ("COMPRAR", "MARGE_RECORREGUT"): ("🟢", "COMPRA — encara hi ha marge"),
    ("COMPRAR", "SOBREESTES"):       ("🟡", "ESPERA UN RECULL — ja ha pujat molt"),
    ("COMPRAR", "LATERAL"):          ("🟢", "COMPRAR"),
    ("COMPRAR", "SENSE_DADES"):      ("🟢", "COMPRAR (verifica dades)"),
    ("COMPRAR", "ALT_RISC_WHIPSAW"): ("⚠️", "COMPTE — whipsaw, no fiquis stop ajustat"),
    ("VIGILAR", "RUPTURA"):          ("🟡", "VIGILA'L DE PROP — pot trencar"),
    ("VIGILAR", "MARGE_RECORREGUT"): ("🟡", "VIGILAR"),
    ("VIGILAR", "SOBREESTES"):       ("🟡", "VIGILAR — sembla esgotat"),
    ("VIGILAR", "LATERAL"):          ("🟡", "VIGILAR"),
    ("VIGILAR", "SENSE_DADES"):      ("🟡", "VIGILAR"),
    ("VIGILAR", "ALT_RISC_WHIPSAW"): ("⚠️", "EVITA ENTRAR ARA — lateral erratic"),
    ("EVITAR", "RUPTURA"):           ("🔴", "EVITAR — encara feble de fons"),
    ("EVITAR", "MARGE_RECORREGUT"):  ("🔴", "EVITAR"),
    ("EVITAR", "SOBREESTES"):        ("🔴", "EVITAR"),
    ("EVITAR", "LATERAL"):           ("🔴", "EVITAR"),
    ("EVITAR", "SENSE_DADES"):       ("🔴", "EVITAR"),
    ("EVITAR", "ALT_RISC_WHIPSAW"):  ("⚠️", "EVITAR — lateral erratic"),
}


def build_verdict(recommendation: str, entry_quality: str) -> str:
    """Retorna un emoji + una frase d'accio directa combinant recomanacio i entrada.

    Args:
        recommendation: "COMPRAR" / "VIGILAR" / "EVITAR".
        entry_quality: qualitat d'entrada de EntrySignal.quality.

    Returns:
        Text tipus "🟢 ENTRA ARA".
    """
    emoji, phrase = _VERDICTS.get((recommendation, entry_quality), ("⚪", recommendation))
    return f"{emoji} {phrase}"


ENTRY_LABELS = {
    "RUPTURA": "RUPTURA (possible entrada, confirma amb volum)",
    "MARGE_RECORREGUT": "MARGE DE RECORREGUT (encara no toca sostre)",
    "SOBREESTES": "SOBREESTES (compte, ja allunyat / esgotant-se)",
    "LATERAL": "LATERAL (sense senyal clar d'entrada)",
    "ALT_RISC_WHIPSAW": "ALT RISC DE WHIPSAW (lateral erratic, veure nota de regim)",
    "SENSE_DADES": "SENSE DADES SUFICIENTS",
}

REGIME_LABELS = {
    "TENDENCIA": "TENDENCIA",
    "LATERAL_TRANQUIL": "LATERAL TRANQUIL",
    "LATERAL_CAOTIC": "LATERAL CAOTIC (whipsaw)",
    "SENSE_DADES": "SENSE DADES",
}


def render_fibonacci_section(fib: FibonacciLevels, currency: str = "EUR") -> List[str]:
    """Renderitza els nivells de Fibonacci (retrocessos i extensions) d'una accio.

    Args:
        fib: FibonacciLevels ja calculats.
        currency: codi de moneda per mostrar els preus.

    Returns:
        Llista de linies de text.
    """
    lines: List[str] = []
    if fib.direction == "SENSE_DADES":
        lines.append(f"   Fibonacci: {fib.notes}")
        return lines

    lines.append(f"   Fibonacci ({fib.direction}, rang {fib.swing_low:.2f}-{fib.swing_high:.2f} {currency}):")
    retro_str = "  ".join(f"{label} {price:.2f}" for label, price in fib.retracement_levels.items())
    lines.append(f"     Retrocessos (possibles entrades): {retro_str}")
    ext_str = "  ".join(f"{label} {price:.2f}" for label, price in fib.extension_levels.items())
    lines.append(f"     Extensions (possibles objectius): {ext_str}")
    lines.append(
        f"     Zona d'entrada suggerida: {fib.suggested_entry_zone[0]:.2f} - "
        f"{fib.suggested_entry_zone[1]:.2f} {currency}"
    )
    return lines


def render_stock_detail(r: StockReport, currency: str = "EUR", label: str = None) -> List[str]:
    """Renderitza el bloc de detall complet d'UNA accio (recomanacio, entrada,
    regim, motiu). Reutilitzat tant pel detall del TOP N com per la 'lupa'
    de seguiment dedicat d'un ticker concret (veure watch_ticker a main.py).

    Args:
        r: StockReport de l'accio.
        currency: codi de moneda per mostrar el preu.
        label: text opcional per la capcalera (per defecte, el nom de l'accio).

    Returns:
        Llista de linies de text (sense fer join, per poder-les combinar
        amb altres blocs).
    """
    entry_label = ENTRY_LABELS.get(r.entry.quality, r.entry.quality)
    regime_label = REGIME_LABELS.get(r.regime.regime, r.regime.regime)
    header = label or r.display_name

    lines: List[str] = []
    lines.append(f"--- {header} ---")
    if r.upcoming_events.is_imminent:
        lines.append(f"   {r.upcoming_events.notes}")
    elif r.upcoming_events.has_upcoming_event:
        lines.append(f"   Calendari: {r.upcoming_events.notes}")
    lines.append(
        f"   Biaix tecnic: {r.bias.color} {r.bias.bias.replace('_', ' ')}   "
        f"({r.bias.bullish_count} amunt / {r.bias.bearish_count} avall / {r.bias.neutral_count} neutres)"
    )
    for s in r.bias.signals:
        lines.append(f"     · {s}")
    lines.append(f"   {r.bias.notes}")
    lines.append(f"   Recomanacio: {r.scores.recommendation}   |   Punt d'entrada: {entry_label}")
    lines.append(f"   Preu: {r.price.last_price:.2f} {currency}  ({r.price.change_pct:+.2f}%)")
    lines.append(f"   Volum relatiu: {r.volume.relative_volume:.2f}x")
    lines.append(f"   Forca relativa vs index: {r.relative_strength.relative_strength_pct:+.2f} p.p.")
    lines.append(f"   vs VWAP: {r.entry.position_vs_vwap_pct:+.2f}%   "
                 f"al maxim del dia: -{r.entry.distance_to_high_pct:.2f}%   "
                 f"al minim del dia: +{r.entry.distance_to_low_pct:.2f}%")
    lines.append(f"   Referencia de risc (no es consell): {r.entry.suggested_stop_reference:.2f} {currency}")
    lines.append(f"   Regim: {regime_label}   |   Efficiency Ratio: {r.regime.efficiency_ratio:.2f}   "
                 f"|   Reversions: {r.regime.reversals_count}   |   ATR: {r.regime.atr:.2f} {currency}")
    lines.append(f"   {r.regime.notes}")
    if r.regime.regime == "LATERAL_CAOTIC":
        lines.append(f"     ⚠️ {r.entry.notes}")
    lines.extend(render_fibonacci_section(r.fibonacci, currency=currency))

    orb_label = {
        "RUPTURA_ALCISTA": "RUPTURA ALCISTA del rang d'obertura",
        "RUPTURA_BAIXISTA": "RUPTURA BAIXISTA del rang d'obertura",
        "DINS_RANG": "dins el rang d'obertura",
        "ENCARA_FORMANT_SE": "rang d'obertura encara formant-se",
        "SENSE_DADES": "sense dades",
    }.get(r.orb.status, r.orb.status)
    lines.append(
        f"   ORB (rang d'obertura {r.orb.orb_low:.2f}-{r.orb.orb_high:.2f} {currency}): {orb_label}"
    )

    lines.append(
        f"   Volume Profile: POC a {r.volume_profile.poc_price:.2f} {currency} "
        f"({r.volume_profile.position_vs_poc_pct:+.2f}% respecte al preu actual)"
    )

    if r.risk_reward.quality != "SENSE_DADES":
        lines.append(
            f"   Risc:Recompensa: {r.risk_reward.ratio:.2f}:1 ({r.risk_reward.quality})   "
            f"stop {r.risk_reward.stop_price:.2f} {currency}   objectiu {r.risk_reward.target_price:.2f} {currency}"
        )
    else:
        lines.append("   Risc:Recompensa: sense dades suficients")

    lines.append(
        f"   Stretch (com d'estesa esta l'entrada): {r.stretch.stretch_level}   "
        f"(VWAP {r.stretch.vwap_distance_pct:.2f}%, POC {r.stretch.poc_distance_pct:.2f}%, "
        f"{r.stretch.pct_of_day_range_covered:.0f}% del rang recorregut)"
    )

    if r.remaining_potential.category != "SENSE_DADES":
        lines.append(
            f"   Potencial restant: {r.remaining_potential.atr_multiple:.2f}x ATR ({r.remaining_potential.category})"
        )
    else:
        lines.append("   Potencial restant: sense dades suficients")

    lines.append(
        f"   Desglossament del score: Momentum {r.scores.momentum_score:.0f}/100   "
        f"Entry {r.scores.entry_score:.0f}/100   →   Final {r.scores.final_score:.0f}/100"
    )

    lines.append(f"   Noticia: {r.news.summary}")
    lines.append("   Motiu complet:")
    for line in r.explanation.split("\n"):
        lines.append(f"     {line}")
    lines.append("-" * 38)
    return lines


def render_quick_view(
    reports: List[StockReport],
    top_n: int = 8,
    market_name: str = "IBEX35",
    currency: str = "EUR",
) -> str:
    """Vista ULTRA-COMPACTA per decidir rapid des del mobil: nomes 1 linia
    per accio, nomes els valors que realment val la pena mirar (descarta
    EVITAR i biaix mixt/contradictori), ordenats pel Final Score.

    Pensada per un primer cop d'ull en pocs segons; per aprofundir en un
    valor concret, fes servir render_report() o watch_ticker().

    Args:
        reports: llista de StockReport (normalment TOTS els de l'univers).
        top_n: quants valors mostrar com a maxim (per defecte, 8).
        market_name: nom del mercat, per la capcalera.
        currency: codi de moneda per mostrar el preu.

    Returns:
        Text curt, llest per fer print() a Colab.
    """
    candidates = [
        r for r in reports
        if r.scores.recommendation != "EVITAR"
        and r.bias.bias != "MIXT"
        and r.bias.bias not in ("BAIXISTA_CLAR", "BAIXISTA_LLEU")
    ]
    candidates.sort(key=lambda r: r.scores.final_score, reverse=True)
    top = candidates[:top_n]

    lines: List[str] = []
    lines.append(f"⚡ {market_name} — Vista rapida ({len(top)} de {len(reports)})")
    lines.append("")

    if not top:
        lines.append("Cap valor destaca prou ara mateix. Millor esperar.")
        return "\n".join(lines)

    for rank, r in enumerate(top, start=1):
        verdict = build_verdict(r.scores.recommendation, r.entry.quality)
        rr_txt = f"R:R {r.risk_reward.ratio:.1f}:1" if r.risk_reward.quality != "SENSE_DADES" else "R:R n/d"
        warn = ""
        if r.entry.quality == "ALT_RISC_WHIPSAW":
            warn = " ⚠️whipsaw"
        elif r.entry.extreme_move_warning:
            warn = " ⚠️extrem"
        elif r.stretch.stretch_level == "ALT":
            warn = " ⚠️estes"
        lines.append(
            f"{rank}. {verdict} {r.display_name} {r.scores.final_score:.0f}  "
            f"{r.bias.color} {rr_txt}{warn}"
        )

    lines.append("")
    lines.append("Per mes detall d'un valor: watch_ticker(\"NOM\", \"TICKER.MC\")")
    return "\n".join(lines)


def render_report(
    reports: List[StockReport],
    top_n: int = TOP_N_RESULTS,
    market_name: str = "IBEX35",
    currency: str = "EUR",
) -> str:
    """Renderitza les top N accions com un bloc de text DIRECTE i clar,
    llegible d'un sol cop d'ull des del mobil.

    Args:
        reports: llista de StockReport, en qualsevol ordre.
        top_n: quantes mostrar (per defecte, config.TOP_N_RESULTS).
        market_name: nom del mercat analitzat, per al titol de l'informe.
        currency: codi de moneda (EUR, USD...) per mostrar el preu correctament.

    Returns:
        Text formatat, llest per fer print() a Colab.
    """
    all_sorted = sorted(reports, key=lambda r: r.scores.final_score, reverse=True)

    excluded_bearish: List[StockReport] = []
    if LONG_ONLY_MODE:
        bearish_bias = {"BAIXISTA_CLAR", "BAIXISTA_LLEU"}
        sorted_reports = [r for r in all_sorted if r.bias.bias not in bearish_bias]
        excluded_bearish = [r for r in all_sorted if r.bias.bias in bearish_bias]
    else:
        sorted_reports = all_sorted

    top = sorted_reports[:top_n]

    lines: List[str] = []

    # --- Seccio destacada: propers esdeveniments (escaneja TOTS els valors, ---
    # --- no nomes el TOP N, perque no se't escapi un valor fora de rànquing) ---
    imminent = [r for r in all_sorted if r.upcoming_events.is_imminent]
    if imminent:
        lines.append("🔔" * 19)
        lines.append("📅 PROPERS EVENTS RELLEVANTS — COMPTE ABANS D'ENTRAR-HI")
        lines.append("🔔" * 19)
        for r in sorted(imminent, key=lambda r: r.upcoming_events.days_until):
            lines.append(f"  ⚠️ {r.display_name}: {r.upcoming_events.notes}")
        lines.append("")

    lines.append("=" * 38)
    lines.append(f"{market_name} — {len(top)} millors oportunitats")
    if LONG_ONLY_MODE:
        lines.append("(nomes operativa llarg/compra — biaix baixista exclos del rànquing)")
    lines.append("=" * 38)
    lines.append("🟢/🔴/🟡 = biaix tecnic actual (NO es una prediccio, pot canviar en qualsevol moment)")
    lines.append("")

    if not top:
        lines.append("No hi ha dades disponibles en aquest moment.")
        return "\n".join(lines)

    BIAS_LABELS = {
        "ALCISTA_CLAR": "TENDEIX A PUJAR (clar)",
        "ALCISTA_LLEU": "TENDEIX A PUJAR (lleu)",
        "BAIXISTA_CLAR": "TENDEIX A BAIXAR (clar)",
        "BAIXISTA_LLEU": "TENDEIX A BAIXAR (lleu)",
        "MIXT": "SENYALS CONTRADICTORIS",
    }

    for rank, r in enumerate(top, start=1):
        verdict = build_verdict(r.scores.recommendation, r.entry.quality)
        reason = build_short_reason(r.volume, r.relative_strength, r.news)
        bias_label = BIAS_LABELS.get(r.bias.bias, r.bias.bias)

        lines.append(f"{rank}. {verdict}  —  {r.display_name}  ({r.scores.final_score:.0f}/100)")
        lines.append(
            f"   Momentum {r.scores.momentum_score:.0f}/100   Entry {r.scores.entry_score:.0f}/100"
        )
        lines.append(
            f"   {r.bias.color} {bias_label}   "
            f"({r.bias.bullish_count} senyals amunt / {r.bias.bearish_count} avall / {r.bias.neutral_count} neutres)"
        )
        lines.append(f"   {reason.capitalize()}.")
        lines.append(
            f"   {r.price.last_price:.2f} {currency} ({r.price.change_pct:+.2f}%)   "
            f"vol {r.volume.relative_volume:.2f}x   vs VWAP {r.entry.position_vs_vwap_pct:+.2f}%"
        )
        if r.risk_reward.quality != "SENSE_DADES":
            lines.append(
                f"   R:R {r.risk_reward.ratio:.1f}:1 ({r.risk_reward.quality})   "
                f"stop {r.risk_reward.stop_price:.2f}   objectiu {r.risk_reward.target_price:.2f}"
            )
        if r.stretch.stretch_level == "ALT":
            lines.append(f"   ⚠️ Entrada molt estesa (stretch ALT) — {r.stretch.notes}")
        if r.entry.extreme_move_warning:
            lines.append(
                f"   ⚠️ Moviment molt gran avui ({r.price.change_pct:+.2f}%) — "
                "mes risc de correccio tecnica els propers dies."
            )
        lines.append("-" * 38)

    lines.append("")
    lines.append("Detall complet de cada accio a sota (motius, VWAP, rang del dia).")
    lines.append("")

    for rank, r in enumerate(top, start=1):
        lines.extend(render_stock_detail(r, currency=currency, label=f"{rank}. {r.display_name}"))

    if excluded_bearish:
        lines.append("")
        lines.append("-" * 38)
        names = ", ".join(r.display_name for r in excluded_bearish)
        lines.append(
            f"({len(excluded_bearish)} valors amb biaix baixista exclosos del rànquing "
            f"per no ser operatius en llarg: {names})"
        )

    return "\n".join(lines)
