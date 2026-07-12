"""
data_loader.py
==============
Responsable de TOTA la descarrega de dades de mercat (yfinance / Yahoo
Finance). Aquest modul nomes descarrega i dona forma lleugera a les dades
(PriceSnapshot / IndexSnapshot). Cap logica de scoring viu aqui.
"""

import datetime as dt
from typing import Dict, List

import pandas as pd
import yfinance as yf

from config import (
    STOCK_UNIVERSE,
    MARKET_INDEX_TICKERS,
    ACTIVE_MARKET,
    INTRADAY_INTERVAL,
    INTRADAY_PERIOD,
    HISTORICAL_PERIOD_FOR_AVG_VOLUME,
    HISTORICAL_INTERVAL_FOR_AVG_VOLUME,
    ENERGY_LOOKBACK_BARS,
    REGIME_LOOKBACK_BARS,
    ORB_BARS,
    VOLUME_PROFILE_BINS,
)
from models import PriceSnapshot, IndexSnapshot


def _compute_poc(df: pd.DataFrame, bins: int = VOLUME_PROFILE_BINS) -> float:
    """Calcula el Point of Control (POC): el preu amb mes volum negociat.

    Divideix el rang de preu del dia en 'bins' caixes i suma el volum de
    cada barra a la caixa on cau el seu preu tipic ((H+L+C)/3). Retorna
    el punt mig de la caixa amb mes volum acumulat.

    Args:
        df: DataFrame intradia complet (Open, High, Low, Close, Volume).
        bins: nombre de caixes de preu.

    Returns:
        Preu del POC. Si no hi ha prou rang, retorna el preu de tancament.
    """
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3.0
    low, high = float(df["Low"].min()), float(df["High"].max())
    if high <= low:
        return float(df["Close"].iloc[-1])

    bin_edges = [low + (high - low) * i / bins for i in range(bins + 1)]
    bin_volumes = [0.0] * bins

    for price, vol in zip(typical_price.tolist(), df["Volume"].tolist()):
        idx = int((price - low) / (high - low) * bins)
        idx = min(max(idx, 0), bins - 1)
        bin_volumes[idx] += float(vol)

    max_idx = max(range(bins), key=lambda i: bin_volumes[i])
    return (bin_edges[max_idx] + bin_edges[max_idx + 1]) / 2.0


def _download_intraday(ticker: str) -> pd.DataFrame:
    """Descarrega les barres intradia d'avui per un ticker.

    Args:
        ticker: simbol de yfinance.

    Returns:
        DataFrame indexat per datetime amb columnes Open, High, Low, Close,
        Volume. DataFrame buit si no hi ha dades (mercat tancat, festiu...).
    """
    data = yf.download(
        tickers=ticker,
        period=INTRADAY_PERIOD,
        interval=INTRADAY_INTERVAL,
        progress=False,
        auto_adjust=False,
    )
    if isinstance(data.columns, pd.MultiIndex):
        # yfinance a vegades retorna columnes multi-index encara que nomes
        # es demani un ticker.
        data.columns = [c[0] for c in data.columns]
    return data


def _historical_average_volume_at_time(ticker: str, current_time: dt.time) -> float:
    """Estima el volum mitja acumulat fins `current_time` en un dia tipic.

    Aixo dona un "volum relatiu" mes just que comparar amb la mitjana de tot
    el dia, ja que p.ex. les 10:00 tenen naturalment menys volum que les 16:00.

    Args:
        ticker: simbol de yfinance.
        current_time: hora del dia amb la qual comparar l'historic.

    Returns:
        Volum mitja acumulat fins aquesta hora, basat en els ultims
        HISTORICAL_PERIOD_FOR_AVG_VOLUME dies. Retorna 0.0 si no hi ha dades.
    """
    try:
        hist = yf.download(
            tickers=ticker,
            period=HISTORICAL_PERIOD_FOR_AVG_VOLUME,
            interval=HISTORICAL_INTERVAL_FOR_AVG_VOLUME,
            progress=False,
            auto_adjust=False,
        )
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = [c[0] for c in hist.columns]
        if hist.empty:
            return 0.0

        hist = hist.copy()
        hist["date"] = hist.index.date
        hist["time"] = hist.index.time

        daily_cumsum_at_time = []
        for _, day_df in hist.groupby("date"):
            day_df = day_df[day_df["time"] <= current_time]
            if not day_df.empty:
                daily_cumsum_at_time.append(day_df["Volume"].sum())

        if not daily_cumsum_at_time:
            return 0.0
        return float(sum(daily_cumsum_at_time) / len(daily_cumsum_at_time))
    except Exception:
        # Problema puntual de la font de dades: degradem amb gracia,
        # l'score de volum quedara neutre.
        return 0.0


def get_index_snapshot(market: str = ACTIVE_MARKET) -> IndexSnapshot:
    """Descarrega la variacio % actual de l'index de referencia del mercat actiu.

    Args:
        market: clau de MARKET_INDEX_TICKERS.

    Returns:
        IndexSnapshot amb el ticker de l'index i la seva variacio % avui.
    """
    ticker = MARKET_INDEX_TICKERS[market]
    df = _download_intraday(ticker)
    if df.empty:
        return IndexSnapshot(ticker=ticker, change_pct=0.0)

    open_price = float(df["Open"].iloc[0])
    last_price = float(df["Close"].iloc[-1])
    change_pct = ((last_price - open_price) / open_price) * 100.0 if open_price else 0.0
    return IndexSnapshot(ticker=ticker, change_pct=change_pct)


def get_price_snapshot(display_name: str, ticker: str) -> PriceSnapshot:
    """Descarrega les dades intradia actuals d'una accio.

    Args:
        display_name: nom llegible (p.ex. "INDRA").
        ticker: simbol de yfinance (p.ex. "IDR.MC").

    Returns:
        PriceSnapshot amb preu, volum i barres recents per l'analisi d'energia.
    """
    df = _download_intraday(ticker)
    if df.empty:
        # Mercat probablement tancat o encara sense dades: snapshot neutre.
        return PriceSnapshot(
            ticker=ticker,
            display_name=display_name,
            last_price=0.0,
            open_price=0.0,
            change_pct=0.0,
            current_volume=0.0,
            average_volume_at_this_time=0.0,
        )

    open_price = float(df["Open"].iloc[0])
    last_price = float(df["Close"].iloc[-1])
    change_pct = ((last_price - open_price) / open_price) * 100.0 if open_price else 0.0
    current_volume = float(df["Volume"].sum())

    day_high = float(df["High"].max())
    day_low = float(df["Low"].min())

    # VWAP = suma(preu_tipic * volum) / suma(volum), amb preu_tipic = (H+L+C)/3
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3.0
    total_volume = df["Volume"].sum()
    vwap = float((typical_price * df["Volume"]).sum() / total_volume) if total_volume else last_price

    current_time = df.index[-1].time()
    avg_volume = _historical_average_volume_at_time(ticker, current_time)

    recent = df.tail(ENERGY_LOOKBACK_BARS)
    recent_closes = [float(x) for x in recent["Close"].tolist()]
    recent_volumes = [float(x) for x in recent["Volume"].tolist()]
    recent_highs = [float(x) for x in recent["High"].tolist()]
    recent_lows = [float(x) for x in recent["Low"].tolist()]

    regime_window = df.tail(REGIME_LOOKBACK_BARS)
    regime_closes = [float(x) for x in regime_window["Close"].tolist()]
    regime_highs = [float(x) for x in regime_window["High"].tolist()]
    regime_lows = [float(x) for x in regime_window["Low"].tolist()]

    bars_since_open = len(df)
    orb_window = df.head(ORB_BARS)
    orb_high = float(orb_window["High"].max()) if not orb_window.empty else 0.0
    orb_low = float(orb_window["Low"].min()) if not orb_window.empty else 0.0

    poc_price = _compute_poc(df)

    return PriceSnapshot(
        ticker=ticker,
        display_name=display_name,
        last_price=last_price,
        open_price=open_price,
        change_pct=change_pct,
        current_volume=current_volume,
        average_volume_at_this_time=avg_volume,
        day_high=day_high,
        day_low=day_low,
        vwap=vwap,
        orb_high=orb_high,
        orb_low=orb_low,
        bars_since_open=bars_since_open,
        poc_price=poc_price,
        recent_closes=recent_closes,
        recent_volumes=recent_volumes,
        recent_highs=recent_highs,
        recent_lows=recent_lows,
        regime_closes=regime_closes,
        regime_highs=regime_highs,
        regime_lows=regime_lows,
    )


def get_all_price_snapshots(universe: Dict[str, str] = None) -> List[PriceSnapshot]:
    """Descarrega el PriceSnapshot de totes les accions de l'univers.

    Args:
        universe: mapeig nom_visible -> ticker. Per defecte config.STOCK_UNIVERSE.

    Returns:
        Llista de PriceSnapshot, un per accio. Continua encara que una accio falli.
    """
    universe = universe or STOCK_UNIVERSE
    snapshots: List[PriceSnapshot] = []
    for display_name, ticker in universe.items():
        try:
            snapshots.append(get_price_snapshot(display_name, ticker))
        except Exception as exc:
            print(f"[data_loader] Avis: no s'ha pogut carregar {display_name} ({ticker}): {exc}")
    return snapshots
