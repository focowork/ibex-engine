"""
compare.py
==========
Permet capturar "fotografies" (snapshots) de l'analisi en diferents
moments de la sessio (p.ex. a les 09:45 i despres a les 09:55, deu
minuts mes tard) i comparar-les per veure com evoluciona el score, el
preu i la recomanacio de cada accio. Util per decidir un punt d'entrada:
no nomes mirar una foto fixa, sino veure la tendencia entre dues.

Us a Colab:

    from compare import take_snapshot, compare_latest

    snap1 = take_snapshot()      # primera foto (p.ex. 09:45)
    # ... espera 10 minuts ...
    snap2 = take_snapshot()      # segona foto (p.ex. 09:55)

    print(compare_latest())      # taula de diferencies, llesta per llegir
                                  # o enganxar a un altre assistent (ChatGPT...)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from config import MARKETS_TO_RUN
from models import StockReport
import main


@dataclass
class Snapshot:
    """Una fotografia completa de tots els mercats analitzats en un instant."""
    label: str                                   # p.ex. "09:45:12"
    markets: Dict[str, List[StockReport]] = field(default_factory=dict)


# Historial de snapshots preses durant la sessio de Colab (en memoria,
# es perd si reinicies el runtime).
SNAPSHOTS: List[Snapshot] = []


def take_snapshot(markets: Optional[List[str]] = None, label: Optional[str] = None) -> Snapshot:
    """Executa l'analisi ara mateix per un o mes mercats i guarda el resultat
    com a nova entrada a SNAPSHOTS.

    Args:
        markets: llista de mercats a analitzar (per defecte, config.MARKETS_TO_RUN).
        label: etiqueta opcional per identificar la foto (per defecte, l'hora actual).

    Returns:
        El Snapshot acabat de crear (tambe queda guardat a SNAPSHOTS).
    """
    markets = markets or MARKETS_TO_RUN
    label = label or datetime.now().strftime("%H:%M:%S")

    snap = Snapshot(label=label)
    for market in markets:
        print(f"[compare] Capturant {market} a les {label} ...")
        snap.markets[market] = main.analyze_market(market=market)

    SNAPSHOTS.append(snap)
    print(f"[compare] Snapshot '{label}' guardat ({len(SNAPSHOTS)} en total aquesta sessio).\n")
    return snap


def _index_by_ticker(reports: List[StockReport]) -> Dict[str, StockReport]:
    return {r.ticker: r for r in reports}


def compare_snapshots(older: Snapshot, newer: Snapshot, only_changed: bool = False) -> str:
    """Compara dues snapshots i genera un text amb els canvis de cada accio:
    delta de score, delta de preu, delta de volum relatiu i si ha canviat
    la recomanacio (p.ex. de VIGILAR a COMPRAR).

    Args:
        older: snapshot mes antiga.
        newer: snapshot mes recent.
        only_changed: si True, nomes mostra accions on el score s'ha mogut
            almenys 1 punt (per centrar-se en el que realment es mou).

    Returns:
        Text formatat, llest per llegir a Colab o enganxar a un altre
        assistent (ChatGPT, etc.) per demanar una segona opinio.
    """
    lines: List[str] = []
    lines.append("=" * 42)
    lines.append(f"COMPARATIVA  {older.label}  ->  {newer.label}")
    lines.append("=" * 42)

    common_markets = [m for m in older.markets if m in newer.markets]
    if not common_markets:
        return "No hi ha mercats en comu entre les dues snapshots."

    for market in common_markets:
        old_by_ticker = _index_by_ticker(older.markets[market])
        new_by_ticker = _index_by_ticker(newer.markets[market])
        common_tickers = [t for t in new_by_ticker if t in old_by_ticker]

        rows = []
        for ticker in common_tickers:
            old_r = old_by_ticker[ticker]
            new_r = new_by_ticker[ticker]

            delta_score = new_r.scores.final_score - old_r.scores.final_score
            delta_price_pct = new_r.price.change_pct - old_r.price.change_pct
            delta_rel_vol = new_r.volume.relative_volume - old_r.volume.relative_volume
            rec_changed = old_r.scores.recommendation != new_r.scores.recommendation
            entry_changed = old_r.entry.quality != new_r.entry.quality
            regime_changed = old_r.regime.regime != new_r.regime.regime

            if only_changed and abs(delta_score) < 1 and not rec_changed and not entry_changed and not regime_changed:
                continue

            rows.append({
                "ticker": ticker,
                "name": new_r.display_name,
                "old_score": old_r.scores.final_score,
                "new_score": new_r.scores.final_score,
                "delta_score": delta_score,
                "old_rec": old_r.scores.recommendation,
                "new_rec": new_r.scores.recommendation,
                "rec_changed": rec_changed,
                "old_entry": old_r.entry.quality,
                "new_entry": new_r.entry.quality,
                "entry_changed": entry_changed,
                "old_regime": old_r.regime.regime,
                "new_regime": new_r.regime.regime,
                "regime_changed": regime_changed,
                "delta_price_pct": delta_price_pct,
                "delta_rel_vol": delta_rel_vol,
            })

        rows.sort(key=lambda r: r["delta_score"], reverse=True)

        lines.append("")
        lines.append(f"--- {market} ---")
        if not rows:
            lines.append("  (cap canvi rellevant)")
            continue

        for r in rows:
            arrow = "->" if r["rec_changed"] else "  "
            flag = " *** CANVI DE RECOMANACIO ***" if r["rec_changed"] else ""
            entry_flag = f"   entrada: {r['old_entry']} -> {r['new_entry']}" if r["entry_changed"] else f"   entrada: {r['new_entry']}"
            regime_flag = f"   regim: {r['old_regime']} -> {r['new_regime']}" if r["regime_changed"] else f"   regim: {r['new_regime']}"
            lines.append(
                f"  {r['name']:<10} score {r['old_score']:.0f} {arrow} {r['new_score']:.0f} "
                f"({r['delta_score']:+.0f})   "
                f"preu {r['delta_price_pct']:+.2f} p.p.   "
                f"vol.rel {r['delta_rel_vol']:+.2f}x   "
                f"[{r['old_rec']} {arrow} {r['new_rec']}]{flag}"
                f"{entry_flag}"
                f"{regime_flag}"
            )

    lines.append("")
    lines.append("=" * 42)
    return "\n".join(lines)


def compare_latest(only_changed: bool = False) -> str:
    """Compara automaticament les DUES ultimes snapshots preses aquesta sessio.

    Args:
        only_changed: veure compare_snapshots().

    Returns:
        Text de la comparativa, o un avis si encara no hi ha 2 snapshots.
    """
    if len(SNAPSHOTS) < 2:
        return (
            f"Nomes hi ha {len(SNAPSHOTS)} snapshot(s) guardada(es) aquesta sessio. "
            "Cal fer take_snapshot() almenys dues vegades abans de comparar."
        )
    rendered = compare_snapshots(SNAPSHOTS[-2], SNAPSHOTS[-1], only_changed=only_changed)
    print(rendered)
    return rendered


def _classify_trajectory(scores: List[float]) -> str:
    """Classifica una sequencia de scores al llarg de tota la sessio.

    Args:
        scores: llista de scores en ordre cronologic (una captura = un valor).

    Returns:
        "PUJADA_CONSISTENT" si puja sense cap retrocés, "BAIXADA_CONSISTENT"
        si baixa sense cap repunt, "ERRATIC" si oscil·la amunt i avall,
        o "PLANA" si els canvis son insignificants.
    """
    if len(scores) < 2:
        return "POQUES_DADES"

    diffs = [scores[i] - scores[i - 1] for i in range(1, len(scores))]
    net = scores[-1] - scores[0]

    reversals = 0
    for i in range(1, len(diffs)):
        if diffs[i] == 0 or diffs[i - 1] == 0:
            continue
        if (diffs[i] > 0) != (diffs[i - 1] > 0):
            reversals += 1

    if abs(net) <= 1 and reversals <= 1:
        return "PLANA"
    if reversals == 0 and net > 1:
        return "PUJADA_CONSISTENT"
    if reversals == 0 and net < -1:
        return "BAIXADA_CONSISTENT"
    return "ERRATIC"


_TRAJECTORY_LABELS = {
    "PUJADA_CONSISTENT": "📈 PUJADA CONSISTENT — cada captura mes mes alta que l'anterior",
    "BAIXADA_CONSISTENT": "📉 BAIXADA CONSISTENT — cada captura es mes baixa que l'anterior",
    "ERRATIC": "🔀 ERRATIC — puja i baixa entre captures, sense direccio neta",
    "PLANA": "➖ PLANA — sense canvis significatius",
    "POQUES_DADES": "— nomes 1 captura, cal esperar mes per veure tendencia",
}


def session_trajectory(market: Optional[str] = None, min_snapshots: int = 2) -> str:
    """Analitza TOTES les snapshots preses aquesta sessio (no nomes les
    dues ultimes) per veure si el score de cada accio puja/baixa de forma
    CONSISTENT al llarg del dia, o si nomes oscil·la sense direccio neta.

    Un score que puja consistentment en 4-5 captures seguides es una
    senyal molt mes fiable que un que puja i baixa (aixo ultim sol ser
    soroll, no una tendencia real).

    Args:
        market: si es dona, nomes analitza aquest mercat. Per defecte,
            tots els mercats presents a les snapshots.
        min_snapshots: nombre minim de captures necessaries per generar
            l'informe (per defecte, 2).

    Returns:
        Text amb la trajectoria de cada accio al llarg de la sessio.
    """
    if len(SNAPSHOTS) < min_snapshots:
        msg = (
            f"Nomes hi ha {len(SNAPSHOTS)} snapshot(s) guardada(es) aquesta sessio. "
            f"Cal fer take_snapshot() almenys {min_snapshots} vegades per veure la trajectoria."
        )
        print(msg)
        return msg

    markets = [market] if market else sorted({m for snap in SNAPSHOTS for m in snap.markets})

    lines: List[str] = []
    lines.append("=" * 42)
    lines.append(f"TRAJECTORIA DE LA SESSIO  ({len(SNAPSHOTS)} captures)")
    lines.append("=" * 42)

    for mkt in markets:
        snaps_with_market = [s for s in SNAPSHOTS if mkt in s.markets]
        if not snaps_with_market:
            continue

        # Recull, per cada ticker, la sequencia de scores i l'etiqueta de
        # cada captura en que apareix.
        ticker_names: Dict[str, str] = {}
        ticker_scores: Dict[str, List[float]] = {}
        ticker_labels: Dict[str, List[str]] = {}

        for snap in snaps_with_market:
            for r in snap.markets[mkt]:
                ticker_names[r.ticker] = r.display_name
                ticker_scores.setdefault(r.ticker, []).append(r.scores.final_score)
                ticker_labels.setdefault(r.ticker, []).append(snap.label)

        rows = []
        for ticker, scores in ticker_scores.items():
            trend = _classify_trajectory(scores)
            rows.append({
                "name": ticker_names[ticker],
                "scores": scores,
                "trend": trend,
                "net_change": scores[-1] - scores[0] if len(scores) >= 2 else 0.0,
            })

        # Prioritza les tendencies consistents (les mes accionables) i,
        # dins de cada tipus, la magnitud del canvi net.
        trend_priority = {"PUJADA_CONSISTENT": 0, "BAIXADA_CONSISTENT": 1, "ERRATIC": 2, "PLANA": 3, "POQUES_DADES": 4}
        rows.sort(key=lambda r: (trend_priority.get(r["trend"], 9), -abs(r["net_change"])))

        lines.append("")
        lines.append(f"--- {mkt} ---")
        for r in rows:
            seq_str = " -> ".join(f"{s:.0f}" for s in r["scores"])
            trend_label = _TRAJECTORY_LABELS.get(r["trend"], r["trend"])
            lines.append(f"  {r['name']:<10} {seq_str}   {trend_label}")

    lines.append("")
    lines.append("=" * 42)
    rendered = "\n".join(lines)
    print(rendered)
    return rendered
