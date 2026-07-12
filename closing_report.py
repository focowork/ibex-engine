"""
closing_report.py
==================
Analisi de TANCAMENT de sessio: mira com han acabat totes les accions
avui i proposa un nombre reduit de candidats (per defecte 3) per
considerar l'obertura de dema, amb un repartiment de capital entre ells.

*** MOLT IMPORTANT — LLEGIR ABANS D'USAR ***

1. Aixo NO ES UN CONSELL FINANCER ni una prediccio. Es un calcul
   MECANIC basat unicament en el propi scoring del motor (Momentum +
   Entry, biaix, risc:recompensa). No te en compte res que passi
   despres del tancament (notícies nocturnes, futurs, mercats asiatics
   o americans, res). La decisio final, i la responsabilitat, es sempre
   de la persona que opera.

2. Els nivells intradia d'avui (VWAP, ORB, stop/objectiu calculats amb
   el rang d'avui) NOMES SON VALIDS PER AVUI. Dema el mercat obrira a un
   preu nou i es formaran un VWAP i un ORB completament nous. Per aixo
   aquest modul prioritza els SENYALS QUE TENEN MES continuitat d'un dia
   a l'altre (Momentum Score, forca relativa, tancament a prop dels
   maxims del dia) per sobre dels nivells exactes d'avui (que cal
   RECALCULAR dema al mati amb take_snapshot() / run(), no reutilitzar
   els d'avui tal qual).

3. Nomes es consideren candidats amb biaix NO baixista (operativa
   nomes en llarg), sense resultats programats en els propers dies
   (evitar sorpreses de resultats de la nit al dia), i sense regim
   lateral caotic (evitar comprar just abans d'un whipsaw).
"""

from typing import List, Tuple

from config import (
    EOD_NUM_PICKS,
    EOD_DEFAULT_CAPITAL,
    EOD_ALLOCATION_MIN_PCT,
    EOD_ALLOCATION_MAX_PCT,
    EOD_ALLOCATION_METHOD,
)
from models import StockReport


def _is_eligible(r: StockReport) -> bool:
    """Determina si una accio es candidata per l'endema.

    Criteris (tots han de complir-se):
        - Biaix tecnic NO baixista (operativa nomes en llarg).
        - Sense resultats programats de forma imminent.
        - Regim de mercat NO lateral caotic (evitar whipsaw a l'obertura).
        - Recomanacio COMPRAR o VIGILAR (EVITAR queda descartat).

    Args:
        r: StockReport d'una accio.

    Returns:
        True si es candidata.
    """
    if r.bias.bias in ("BAIXISTA_CLAR", "BAIXISTA_LLEU"):
        return False
    if r.upcoming_events.is_imminent:
        return False
    if r.regime.regime == "LATERAL_CAOTIC":
        return False
    if r.scores.recommendation == "EVITAR":
        return False
    return True


def _closing_strength_key(r: StockReport):
    """Clau d'ordenacio que prioritza senyals amb continuitat d'un dia a
    l'altre (Momentum, tancament a prop dels maxims) per sobre de
    l'Entry Score (que es especific de la sessio d'avui i no te validesa
    dema al mati).

    Args:
        r: StockReport d'una accio.

    Returns:
        Tupla per ordenar de major a menor "força de tancament".
    """
    closed_near_high = -r.entry.distance_to_high_pct   # com mes a prop del maxim, millor
    return (r.scores.momentum_score, closed_near_high, r.scores.final_score)


def _risk_pct(r: StockReport) -> float:
    """Risc de la posicio, en % del preu actual (distancia al stop / preu).

    Args:
        r: StockReport amb risk_reward ja calculat.

    Returns:
        % de risc (sempre >= 0.1 per evitar divisions per gairebe 0).
    """
    if not r.price.last_price:
        return 1.0
    pct = (r.risk_reward.risk / r.price.last_price) * 100.0
    return max(pct, 0.1)


def _normalize_with_bounds(raw_weights: List[float], min_w: float, max_w: float) -> List[float]:
    """Normalitza una llista de pesos perque sumin 1.0, respectant un
    minim i un maxim per element de veritat (un simple "clip i
    renormalitza" NO ho garanteix: renormalitzar despres de retallar pot
    tornar a fer pujar un pes per sobre del maxim). Fa servir un
    algorisme iteratiu de "water-filling": fixa els pesos que ja toquen
    un limit i reparteix la resta proporcionalment entre els que encara
    son lliures, repetint fins que no cal fixar-ne cap mes.

    Args:
        raw_weights: pesos sense normalitzar (p.ex. score/risc de cada candidat).
        min_w: pes minim per element (fraccio, p.ex. 0.15).
        max_w: pes maxim per element (fraccio, p.ex. 0.50).

    Returns:
        Llista de pesos normalitzats que sumen 1.0 i respecten [min_w, max_w].
    """
    n = len(raw_weights)
    if n == 0:
        return []
    if n * min_w > 1.0 or n * max_w < 1.0:
        # Els limits son incompatibles amb aquest nombre de candidats
        # (p.ex. 3 candidats amb minim 40% cadascun no pot sumar 1.0).
        # Recorre a repartiment equitatiu com a alternativa segura.
        return [1.0 / n] * n

    weights = list(raw_weights)
    total = sum(weights)
    weights = [w / total if total else 1.0 / n for w in weights]

    fixed = [False] * n
    for _ in range(n):
        changed = False
        for i in range(n):
            if not fixed[i]:
                if weights[i] > max_w:
                    weights[i] = max_w
                    fixed[i] = True
                    changed = True
                elif weights[i] < min_w:
                    weights[i] = min_w
                    fixed[i] = True
                    changed = True
        if not changed:
            break

        free_indices = [i for i in range(n) if not fixed[i]]
        if not free_indices:
            break

        fixed_sum = sum(weights[i] for i in range(n) if fixed[i])
        remaining = 1.0 - fixed_sum
        free_raw_sum = sum(raw_weights[i] for i in free_indices)

        if free_raw_sum <= 0:
            for i in free_indices:
                weights[i] = remaining / len(free_indices)
        else:
            for i in free_indices:
                weights[i] = remaining * (raw_weights[i] / free_raw_sum)

    return weights


def _allocate_capital(picks: List[StockReport], capital: float) -> List[float]:
    """Reparteix el capital entre els candidats triats.

    Dos metodes disponibles (config.EOD_ALLOCATION_METHOD):
        - "SCORE": proporcional nomes al Final Score.
        - "RISK_ADJUSTED" (per defecte): proporcional a Final Score / risc
          en % del preu. Aixo vol dir que, entre dos candidats amb el
          mateix score, el que tingui un stop mes ajustat (menys risc en %)
          rep MES capital -- l'objectiu es que el risc EN EUROS assumit
          sigui similar a cada posicio, en lloc de nomes repartir segons
          "qui te el score mes alt" (filosofia "risk parity").

    En tots dos casos s'aplica un pes minim i maxim per candidat (config
    EOD_ALLOCATION_MIN_PCT / MAX_PCT) perque cap valor s'enduguin gairebe
    tot el capital, i cap quedi amb una quantitat simbolica.

    Args:
        picks: llista de StockReport ja filtrada als candidats finals.
        capital: import total a repartir.

    Returns:
        Llista d'imports en euros, un per candidat, en el mateix ordre.
    """
    if not picks:
        return []
    if len(picks) == 1:
        return [capital]

    if EOD_ALLOCATION_METHOD == "RISK_ADJUSTED":
        raw = [max(r.scores.final_score, 1.0) / _risk_pct(r) for r in picks]
    else:
        raw = [max(r.scores.final_score, 1.0) for r in picks]

    weights = _normalize_with_bounds(raw, EOD_ALLOCATION_MIN_PCT, EOD_ALLOCATION_MAX_PCT)

    return [capital * w for w in weights]


def select_and_allocate(
    reports: List[StockReport],
    n: int = EOD_NUM_PICKS,
    capital: float = EOD_DEFAULT_CAPITAL,
) -> Tuple[List[StockReport], List[float]]:
    """Selecciona els N millors candidats elegibles i calcula el repartiment
    de capital, SENSE renderitzar cap text. Reutilitzat tant per
    eod_top_picks() (que ho renderitza) com per track_record.py / app.py
    (que ho volen fer servir directament).

    Args:
        reports: llista de StockReport de TOTES les accions analitzades.
        n: nombre de candidats a triar.
        capital: import total a repartir.

    Returns:
        Tupla (picks, allocations): llista de StockReport triats i llista
        d'imports en euros, en el mateix ordre.
    """
    eligible = [r for r in reports if _is_eligible(r)]
    eligible.sort(key=_closing_strength_key, reverse=True)
    picks = eligible[:n]
    allocations = _allocate_capital(picks, capital)
    return picks, allocations


# Alies publics (sense guio baix) de les funcions internes, per fer-les
# servir comodament des d'altres moduls com app.py sense dependre de
# noms "privats".
is_eligible = _is_eligible
allocate_capital = _allocate_capital


def eod_top_picks(
    reports: List[StockReport],
    n: int = EOD_NUM_PICKS,
    capital: float = EOD_DEFAULT_CAPITAL,
    currency: str = "EUR",
) -> str:
    """Genera l'informe de tancament: N candidats per l'endema amb
    repartiment de capital.

    Args:
        reports: llista de StockReport de TOTES les accions analitzades
            (normalment, el resultat de main.analyze_market() executat
            al tancament de sessio).
        n: nombre de candidats a proposar (per defecte, config.EOD_NUM_PICKS).
        capital: import total a repartir (per defecte, config.EOD_DEFAULT_CAPITAL).
        currency: codi de moneda per mostrar els imports.

    Returns:
        Text formatat, llest per fer print() a Colab.
    """
    picks, allocations = select_and_allocate(reports, n=n, capital=capital)

    lines: List[str] = []
    lines.append("=" * 42)
    lines.append(f"ANALISI DE TANCAMENT — {n} CANDIDATS PER DEMA")
    lines.append("=" * 42)
    lines.append(
        "⚠️ AIXO NO ES UN CONSELL FINANCER. Es un calcul mecanic basat en "
        "el scoring del motor, sense tenir en compte res que passi despres "
        "del tancament d'avui. Confirma sempre amb una foto nova (take_snapshot) "
        "a l'obertura de dema abans d'entrar-hi — els nivells d'avui (VWAP, ORB) "
        "no son valids dema."
    )
    metode_label = "ajustat per risc (posicions amb stop mes ajustat reben mes pes)" if EOD_ALLOCATION_METHOD == "RISK_ADJUSTED" else "proporcional al score"
    lines.append(f"Metode de repartiment: {metode_label}.")
    lines.append("")

    if not picks:
        lines.append(
            "Cap valor compleix els criteris avui (biaix no baixista, sense "
            "resultats imminents, regim no caotic, recomanacio COMPRAR/VIGILAR). "
            "Millor no forçar cap entrada per dema."
        )
        return "\n".join(lines)

    for i, (r, import_eur) in enumerate(zip(picks, allocations), start=1):
        pct = (import_eur / capital) * 100.0 if capital else 0.0
        lines.append(f"{i}. {r.display_name}  ({r.ticker})")
        lines.append(
            f"   Capital assignat: {import_eur:,.0f} {currency}  ({pct:.0f}% dels {capital:,.0f} {currency})"
        )
        lines.append(
            f"   Momentum {r.scores.momentum_score:.0f}/100   Entry {r.scores.entry_score:.0f}/100   "
            f"Final {r.scores.final_score:.0f}/100   Recomanacio: {r.scores.recommendation}"
        )
        lines.append(
            f"   Tancament: {r.price.last_price:.2f} {currency} ({r.price.change_pct:+.2f}%)   "
            f"a {r.entry.distance_to_high_pct:.2f}% del maxim del dia   "
            f"vol.rel {r.volume.relative_volume:.2f}x"
        )
        lines.append(f"   Biaix: {r.bias.color} {r.bias.bias.replace('_', ' ')}")
        lines.append(
            f"   Regim: {r.regime.regime.replace('_', ' ')}   R:R avui: {r.risk_reward.ratio:.2f}:1   "
            f"risc {_risk_pct(r):.2f}% del preu"
        )
        if r.risk_reward.quality != "SENSE_DADES":
            lines.append(
                f"   Referencia (recalcula-la dema, no es vàlida tal qual): "
                f"stop ~{r.risk_reward.stop_price:.2f} {currency}   objectiu ~{r.risk_reward.target_price:.2f} {currency}"
            )
        lines.append(f"   Motiu: {r.explanation.splitlines()[0] if r.explanation else ''}")
        lines.append("-" * 42)

    lines.append("")
    lines.append(f"Total repartit: {sum(allocations):,.0f} {currency} de {capital:,.0f} {currency}")
    lines.append(
        "Recorda: aquests son els MILLORS candidats segons dades D'AVUI. Abans "
        "d'obrir cap posicio dema, torna a executar l'analisi (run() o "
        "take_snapshot()) amb les dades noves de l'obertura."
    )
    lines.append("")
    tickers_list = ", ".join(f'"{r.ticker}"' for r in picks)
    names_list = ", ".join(f'"{r.display_name}"' for r in picks)
    lines.append("📋 Copia aixo dema al mati per confirmar-los amb dades fresques:")
    lines.append(f"   morning_confirmation(tickers=[{tickers_list}], names=[{names_list}], capital={capital:.0f})")

    return "\n".join(lines)


def morning_reconfirm(
    picks_reports: List[StockReport],
    capital: float = EOD_DEFAULT_CAPITAL,
    currency: str = "EUR",
) -> str:
    """Torna a validar, amb dades FRESQUES del mati (VWAP i ORB ja formats
    a l'hora que ho executis), els candidats triats ahir al tancament.
    Reparteix el capital nomes entre els que ENCARA compleixen els criteris
    ara mateix; els que ja no els compleixen es marquen clarament amb el
    motiu (p.ex. han obert amb gap advers i ara son baixistes).

    Args:
        picks_reports: llista de StockReport, ja recalculats AVUI (amb
            dades fresques) nomes per als tickers triats ahir. Veure
            main.morning_confirmation() per la funcio que ho fa tot junt.
        capital: import total a repartir.
        currency: codi de moneda.

    Returns:
        Text formatat, llest per fer print() a Colab.
    """
    lines: List[str] = []
    lines.append("=" * 42)
    lines.append("CONFIRMACIO DEL MATI — DADES FRESQUES D'AVUI")
    lines.append("=" * 42)
    lines.append(
        "⚠️ AIXO NO ES UN CONSELL FINANCER. Nomes revalida amb dades d'avui "
        "els candidats triats ahir al tancament."
    )
    lines.append("")

    still_eligible = [r for r in picks_reports if _is_eligible(r)]
    no_longer_eligible = [r for r in picks_reports if not _is_eligible(r)]

    if no_longer_eligible:
        lines.append("❌ Ja NO compleixen els criteris avui:")
        for r in no_longer_eligible:
            motiu = []
            if r.bias.bias in ("BAIXISTA_CLAR", "BAIXISTA_LLEU"):
                motiu.append("ara te biaix baixista")
            if r.upcoming_events.is_imminent:
                motiu.append("resultats imminents")
            if r.regime.regime == "LATERAL_CAOTIC":
                motiu.append("regim lateral caotic (whipsaw)")
            if r.scores.recommendation == "EVITAR":
                motiu.append("recomanacio ara es EVITAR")
            lines.append(f"   • {r.display_name}: {', '.join(motiu) if motiu else 'ja no compleix criteris'}")
        lines.append("")

    if not still_eligible:
        lines.append("Cap dels candidats d'ahir es manté valid amb les dades d'avui. Millor no forçar cap entrada.")
        return "\n".join(lines)

    allocations = _allocate_capital(still_eligible, capital)

    lines.append(f"✅ Confirmats amb dades d'avui ({len(still_eligible)} de {len(picks_reports)}):")
    lines.append("")
    for i, (r, import_eur) in enumerate(zip(still_eligible, allocations), start=1):
        pct = (import_eur / capital) * 100.0 if capital else 0.0
        lines.append(f"{i}. {r.display_name}  ({r.ticker})")
        lines.append(f"   Capital assignat: {import_eur:,.0f} {currency}  ({pct:.0f}%)")
        lines.append(
            f"   Preu ara: {r.price.last_price:.2f} {currency} ({r.price.change_pct:+.2f}% avui)   "
            f"vs VWAP {r.entry.position_vs_vwap_pct:+.2f}%   ORB: {r.orb.status.replace('_', ' ')}"
        )
        lines.append(f"   Punt d'entrada: {r.entry.quality.replace('_', ' ')}   R:R avui: {r.risk_reward.ratio:.2f}:1")
        if r.risk_reward.quality != "SENSE_DADES":
            lines.append(
                f"   Stop: {r.risk_reward.stop_price:.2f} {currency}   Objectiu: {r.risk_reward.target_price:.2f} {currency}"
            )
        lines.append("-" * 42)

    lines.append("")
    lines.append(f"Total repartit: {sum(allocations):,.0f} {currency} de {capital:,.0f} {currency}")

    return "\n".join(lines)
