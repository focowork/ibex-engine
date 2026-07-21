"""
main.py
=======
Punt d'entrada de l'IBEX Intraday Decision Engine.

Executa aquest modul en qualsevol moment de la sessio (09:45, 11:30, 16:00...)
per obtenir una analisi instantania de l'univers d'accions, ordenada per
oportunitat.

Us a Google Colab:

    !pip install yfinance feedparser --quiet
    # (puja/importa config.py, models.py, data_loader.py, volume.py,
    #  relative_strength.py, news.py, energy.py, scoring.py, report.py, main.py)
    from main import run
    run()

IMPORTANT: aquest programa NO prediu abans de l'obertura. Nomes analitza
la situacio real en el moment exacte en que s'executa.
"""

from typing import Dict, List, Optional

from config import (
    STOCK_UNIVERSE,
    ACTIVE_MARKET,
    MARKET_STOCK_UNIVERSES,
    MARKET_CURRENCY,
    MARKETS_TO_RUN,
    EOD_DEFAULT_CAPITAL,
    EOD_NUM_PICKS,
)
from models import StockReport, IndexSnapshot
import data_loader
import volume as volume_module
import relative_strength as rs_module
import news as news_module
import energy as energy_module
import regime as regime_module
import entry_signal as entry_module
import fibonacci as fibonacci_module
import orb as orb_module
import volume_profile as volume_profile_module
import risk_reward as risk_reward_module
import bias as bias_module
import upcoming_events as upcoming_events_module
import stretch as stretch_module
import remaining_potential as remaining_potential_module
import scoring
import report as report_module
import closing_report as closing_report_module
import track_record as track_record_module


def analyze_stock(display_name: str, ticker: str, index_snapshot: IndexSnapshot) -> StockReport:
    """Executa el pipeline complet d'analisi per una sola accio.

    Args:
        display_name: nom llegible (p.ex. "INDRA").
        ticker: simbol de yfinance (p.ex. "IDR.MC").
        index_snapshot: IndexSnapshot de l'index de referencia, ja descarregat.

    Returns:
        StockReport complet d'aquesta accio.
    """
    price = data_loader.get_price_snapshot(display_name, ticker)

    vol_analysis = volume_module.analyze_volume(price)
    rs_analysis = rs_module.analyze_relative_strength(price, index_snapshot)
    news_analysis = news_module.analyze_news(display_name)
    energy_analysis = energy_module.analyze_energy(price)
    regime_analysis = regime_module.analyze_regime(price)
    entry_analysis = entry_module.analyze_entry(price, energy_analysis, regime_analysis)
    fibonacci_analysis = fibonacci_module.analyze_fibonacci(price)
    orb_analysis = orb_module.analyze_orb(price)
    volume_profile_analysis = volume_profile_module.analyze_volume_profile(price)
    risk_reward_analysis = risk_reward_module.analyze_risk_reward(price, entry_analysis, fibonacci_analysis)
    bias_analysis = bias_module.analyze_bias(price, rs_analysis, regime_analysis, fibonacci_analysis, orb_analysis)
    upcoming_events_analysis = upcoming_events_module.analyze_upcoming_events(ticker)
    stretch_analysis = stretch_module.analyze_stretch(price, entry_analysis, volume_profile_analysis)
    remaining_potential_analysis = remaining_potential_module.analyze_remaining_potential(
        price, risk_reward_analysis, regime_analysis
    )

    score_breakdown = scoring.build_score_breakdown(
        volume=vol_analysis,
        relative_strength=rs_analysis,
        news=news_analysis,
        energy=energy_analysis,
        entry=entry_analysis,
        regime=regime_analysis,
        orb=orb_analysis,
        risk_reward=risk_reward_analysis,
        stretch=stretch_analysis,
        remaining_potential=remaining_potential_analysis,
    )

    return report_module.build_stock_report(
        price=price,
        volume=vol_analysis,
        relative_strength=rs_analysis,
        news=news_analysis,
        energy=energy_analysis,
        scores=score_breakdown,
        entry=entry_analysis,
        regime=regime_analysis,
        fibonacci=fibonacci_analysis,
        orb=orb_analysis,
        volume_profile=volume_profile_analysis,
        risk_reward=risk_reward_analysis,
        bias=bias_analysis,
        upcoming_events=upcoming_events_analysis,
        stretch=stretch_analysis,
        remaining_potential=remaining_potential_analysis,
    )


def analyze_focused() -> List[StockReport]:
    """Analitza NOMES els valors en els que l'usuari s'ha centrat: GRIFOLS
    (dins l'IBEX35) i SPCX (SpaceX, Nasdaq). Combina els dos mercats en una
    sola llista, perque l'app els mostri sempre junts.

    Returns:
        Llista de StockReport amb Grifols i SpaceX (en aquest ordre).
    """
    reports: List[StockReport] = []
    for market in ("IBEX35", "SPCX"):
        try:
            reports.extend(analyze_market(market=market))
        except Exception as exc:
            print(f"[main] Avis: error analitzant el mercat {market}: {exc}")
    return reports


def analyze_market(market: str = ACTIVE_MARKET, universe: Optional[Dict[str, str]] = None) -> List[StockReport]:
    """Executa el pipeline complet per UN mercat i retorna els StockReport crus
    (sense renderitzar), perque altres moduls (com compare.py) els puguin
    reutilitzar per fer snapshots i comparacions.

    Args:
        market: clau de config.MARKET_INDEX_TICKERS (nomes "IBEX35" per defecte).
        universe: mapeig opcional nom_visible -> ticker per sobreescriure
            l'univers per defecte d'aquest mercat.

    Returns:
        Llista de StockReport (un per accio analitzada amb exit).
    """
    universe = universe or MARKET_STOCK_UNIVERSES.get(market, STOCK_UNIVERSE)
    index_snapshot = data_loader.get_index_snapshot(market)

    reports: List[StockReport] = []
    for display_name, ticker in universe.items():
        try:
            reports.append(analyze_stock(display_name, ticker, index_snapshot))
        except Exception as exc:
            print(f"[main] Avis: error analitzant {display_name}: {exc}")
    return reports


def run(market: str = ACTIVE_MARKET, universe: Optional[Dict[str, str]] = None) -> str:
    """Executa el pipeline complet per UN mercat i imprimeix l'informe.

    Args:
        market: clau de config.MARKET_INDEX_TICKERS (nomes "IBEX35" per defecte).
            Per defecte, config.ACTIVE_MARKET.
        universe: mapeig opcional nom_visible -> ticker per sobreescriure
            l'univers per defecte d'aquest mercat (util per testejar amb
            menys accions).

    Returns:
        El text de l'informe renderitzat (tambe s'imprimeix per pantalla).
    """
    currency = MARKET_CURRENCY.get(market, "EUR")
    print(f"Analitzant mercat: {market} ...\n")

    reports = analyze_market(market=market, universe=universe)

    rendered = report_module.render_report(reports, market_name=market, currency=currency)
    print(rendered)
    return rendered


def watch_ticker(display_name: str, ticker: str, market: str = ACTIVE_MARKET) -> str:
    """Fa un seguiment EXHAUSTIU d'UN sol valor (p.ex. Grifols), amb tot el
    detall (VWAP, rang del dia, Efficiency Ratio, reversions, ATR), sense
    filtrar-lo per si surt o no al TOP N del mercat. Util per valors en
    regim lateral erratic que et preocupen especificament, encara que
    el seu score no sigui prou alt per sortir al rànquing general.

    Args:
        display_name: nom llegible (p.ex. "GRIFOLS").
        ticker: simbol de yfinance (p.ex. "GRF.MC").
        market: mercat de referencia per calcular la forca relativa
            (per defecte, config.ACTIVE_MARKET).

    Returns:
        El text del detall renderitzat (tambe s'imprimeix per pantalla).
    """
    currency = MARKET_CURRENCY.get(market, "EUR")
    index_snapshot = data_loader.get_index_snapshot(market)

    try:
        r = analyze_stock(display_name, ticker, index_snapshot)
    except Exception as exc:
        msg = f"[main] Error analitzant {display_name}: {exc}"
        print(msg)
        return msg

    lines = [f"SEGUIMENT DEDICAT — {display_name} ({ticker})"]
    lines.append("=" * 38)
    lines.extend(report_module.render_stock_detail(r, currency=currency, label=display_name))
    rendered = "\n".join(lines)
    print(rendered)
    return rendered


def run_multi_market(markets: Optional[List[str]] = None) -> str:
    """Executa el pipeline per DIVERSOS mercats en la mateixa crida i
    concatena els informes (nomes IBEX35 per defecte, pero preparat per si es reactiven mes mercats).

    Args:
        markets: llista de mercats (claus de config.MARKET_INDEX_TICKERS).
            Per defecte, config.MARKETS_TO_RUN (nomes ["IBEX35"]).

    Returns:
        Text amb tots els informes concatenats, un darrere l'altre.
    """
    markets = markets or MARKETS_TO_RUN
    rendered_reports: List[str] = []

    for market in markets:
        rendered_reports.append(run(market=market))
        print("\n")

    return "\n\n".join(rendered_reports)


def quick_view(market: str = ACTIVE_MARKET, top_n: int = 8) -> str:
    """Vista ULTRA-COMPACTA per decidir rapid des del mobil: nomes 1 linia
    per accio, nomes els valors que realment val la pena mirar.

    Args:
        market: mercat a analitzar (per defecte, config.ACTIVE_MARKET).
        top_n: quants valors mostrar com a maxim (per defecte, 8).

    Returns:
        El text de la vista rapida (tambe s'imprimeix per pantalla).
    """
    currency = MARKET_CURRENCY.get(market, "EUR")
    print(f"Analitzant {market} ...\n")
    reports = analyze_market(market=market)
    rendered = report_module.render_quick_view(reports, top_n=top_n, market_name=market, currency=currency)
    print(rendered)
    return rendered


def closing_scan(
    n: int = EOD_NUM_PICKS,
    capital: float = EOD_DEFAULT_CAPITAL,
    market: str = ACTIVE_MARKET,
    log_to_drive: bool = True,
) -> str:
    """Analisi de TANCAMENT de sessio: analitza totes les accions del mercat
    ara mateix i proposa N candidats per l'endema amb repartiment de capital.

    Pensat per executar-se al tancament (p.ex. cap a les 17:30), quan les
    dades del dia ja son completes. Veure closing_report.py per llegir
    els avisos importants abans de fer-lo servir.

    Args:
        n: nombre de candidats a proposar (per defecte, config.EOD_NUM_PICKS).
        capital: import total a repartir (per defecte, config.EOD_DEFAULT_CAPITAL).
        market: mercat a analitzar (per defecte, config.ACTIVE_MARKET).
        log_to_drive: si True (per defecte), intenta registrar els picks
            a l'historial persistent de Google Drive (track_record.py).
            Si Drive no esta muntat, nomes avisa i continua sense fallar.

    Returns:
        El text de l'informe de tancament (tambe s'imprimeix per pantalla).
    """
    currency = MARKET_CURRENCY.get(market, "EUR")
    print(f"Analitzant tancament de {market} ...\n")
    reports = analyze_market(market=market)

    picks, allocations = closing_report_module.select_and_allocate(reports, n=n, capital=capital)
    rendered = closing_report_module.eod_top_picks(reports, n=n, capital=capital, currency=currency)
    print(rendered)

    if log_to_drive and picks:
        log_msg = track_record_module.log_picks(picks, allocations, capital)
        print(f"\n{log_msg}")

    return rendered


def morning_confirmation(
    tickers: List[str],
    names: Optional[List[str]] = None,
    capital: float = EOD_DEFAULT_CAPITAL,
    market: str = ACTIVE_MARKET,
) -> str:
    """Torna a validar, amb dades FRESQUES d'ara mateix (p.ex. a les 9:30,
    amb el VWAP i l'ORB d'avui ja formats), els candidats triats ahir al
    tancament amb closing_scan(). Nomes analitza els tickers que li
    passis (no torna a escanejar les 35 empreses), aixi que es rapid.

    Copia i enganxa la linia que et dona closing_scan() al final de
    l'informe d'ahir; ja porta els tickers i noms correctes.

    Args:
        tickers: llista de simbols de yfinance dels candidats d'ahir
            (p.ex. ["BBVA.MC", "IBE.MC", "ITX.MC"]).
        names: llista de noms llegibles, en el mateix ordre que tickers
            (p.ex. ["BBVA", "IBERDROLA", "INDITEX"]). Si no es dona,
            es fa servir el ticker tal qual com a nom.
        capital: import total a repartir (per defecte, config.EOD_DEFAULT_CAPITAL).
        market: mercat de referencia per calcular la forca relativa.

    Returns:
        El text de la confirmacio del mati (tambe s'imprimeix per pantalla).
    """
    names = names or tickers
    currency = MARKET_CURRENCY.get(market, "EUR")
    print(f"Confirmant {len(tickers)} candidats amb dades fresques d'avui ...\n")

    index_snapshot = data_loader.get_index_snapshot(market)
    reports: List[StockReport] = []
    for display_name, ticker in zip(names, tickers):
        try:
            reports.append(analyze_stock(display_name, ticker, index_snapshot))
        except Exception as exc:
            print(f"[main] Avis: error analitzant {display_name}: {exc}")

    rendered = closing_report_module.morning_reconfirm(reports, capital=capital, currency=currency)
    print(rendered)
    return rendered


if __name__ == "__main__":
    run_multi_market()
