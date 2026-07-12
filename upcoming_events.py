"""
upcoming_events.py
==================
Calendari d'esdeveniments corporatius (principalment la propera data de
publicacio de resultats) per avisar-te ABANS que passi, no nomes quan ja
esta passant. Aixo complementa news.py: news.py busca titulars d'ARA
MATEIX; aquest modul mira el calendari per saber que hi ha programat.

Fa servir l'atribut `.calendar` de yfinance, que en la majoria de casos
inclou la propera data estimada de resultats ("Earnings Date"). La
cobertura d'aquesta dada sol ser molt bona per valors de NASDAQ i mes
irregular per valors mes petits de l'IBEX35 — si no hi ha dades, l'accio
simplement es marca com "SENSE_DADES" en lloc de fallar.
"""

from datetime import date, datetime
from typing import Optional

from config import EVENT_WARNING_WINDOW_DAYS
from models import UpcomingEventsAnalysis


def _extract_earnings_date(calendar) -> Optional[date]:
    """Extreu la propera data de resultats de l'objecte 'calendar' de
    yfinance, sigui quin sigui el format en que el retorni la versio de
    la llibreria instal·lada (dict amb llista de dates, o DataFrame antic).

    Args:
        calendar: objecte retornat per yfinance.Ticker(ticker).calendar.

    Returns:
        La data (date) de la propera publicacio de resultats, o None si
        no s'ha pogut extreure de cap format conegut.
    """
    if calendar is None:
        return None

    raw = None

    # Format modern (yfinance >= ~0.2.x): dict amb clau "Earnings Date"
    # que conte una llista de dates (a vegades un rang [inici, fi]).
    if isinstance(calendar, dict):
        raw = calendar.get("Earnings Date")
        if isinstance(raw, list) and raw:
            raw = raw[0]

    # Format antic: DataFrame amb "Earnings Date" com a index de fila.
    elif hasattr(calendar, "loc"):
        try:
            val = calendar.loc["Earnings Date"]
            raw = val.iloc[0] if hasattr(val, "iloc") else val
        except Exception:
            raw = None

    if raw is None:
        return None

    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw
    if isinstance(raw, datetime):
        return raw.date()

    # Alguns formats retornen strings ("2026-07-15").
    try:
        return datetime.strptime(str(raw)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def analyze_upcoming_events(ticker: str) -> UpcomingEventsAnalysis:
    """Consulta el calendari corporatiu d'un ticker i marca si hi ha un
    esdeveniment (principalment resultats) dins la finestra d'avis.

    Args:
        ticker: simbol de yfinance (p.ex. "GRF.MC", "AAPL").

    Returns:
        UpcomingEventsAnalysis amb la data trobada (si n'hi ha) i si cau
        dins la finestra d'avis (config.EVENT_WARNING_WINDOW_DAYS).
    """
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        calendar = stock.calendar
        earnings_date = _extract_earnings_date(calendar)
    except Exception:
        earnings_date = None

    if earnings_date is None:
        return UpcomingEventsAnalysis(
            has_upcoming_event=False,
            event_type="SENSE_DADES",
            event_date="",
            days_until=0,
            is_imminent=False,
            notes="Sense dades de calendari disponibles per aquest valor.",
        )

    today = date.today()
    days_until = (earnings_date - today).days
    is_imminent = 0 <= days_until <= EVENT_WARNING_WINDOW_DAYS

    if days_until < 0:
        notes = f"L'ultima data de resultats coneguda ({earnings_date.isoformat()}) ja ha passat."
    elif is_imminent:
        dia_paraula = "dema" if days_until == 1 else f"en {days_until} dies"
        notes = (
            f"📅 RESULTATS PROGRAMATS {dia_paraula} ({earnings_date.isoformat()}). "
            "Moviments grans i imprevisibles son habituals al voltant d'aquesta data."
        )
    else:
        notes = f"Propers resultats previstos el {earnings_date.isoformat()} ({days_until} dies)."

    return UpcomingEventsAnalysis(
        has_upcoming_event=True,
        event_type="RESULTATS",
        event_date=earnings_date.isoformat(),
        days_until=days_until,
        is_imminent=is_imminent,
        notes=notes,
    )
