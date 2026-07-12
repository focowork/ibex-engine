"""
regime.py
=========
Detecta el "regim" de mercat d'una accio durant la sessio: si es mou amb
tendencia neta, si esta lateral pero tranquil·la, o si esta en un LATERAL
ERRATIC (whipsaw) — el cas classic de "puja, baixa de cop, torna a pujar,
salta el stop, i despres puja de veritat sense tu". Grifols en son un
exemple habitual.

Fa servir dues metriques estandard d'analisi tecnica:

- Efficiency Ratio (Kaufman): distancia recorreguda EN NET / distancia
  recorreguda EN TOTAL (suma de tots els moviments barra a barra). Prop
  d'1 vol dir que gairebe tot el moviment ha anat en la mateixa direccio
  (tendencia neta). Prop de 0 vol dir que l'accio ha anat amunt i avall
  molt pero sense arribar enlloc (soroll pur).
- Nombre de reversions: quantes vegades canvia de direccio barra a barra
  dins la finestra analitzada. Moltes reversions + Efficiency Ratio baix
  = exactament el patro de "whipsaw" que fa saltar stops ajustats.

A mes, calcula un ATR (rang mitja per barra) per suggerir una distancia
de stop mes ampla que tingui en compte el soroll real de l'accio, en
lloc d'un nivell fix que quedi dins del rang de soroll normal.
"""

from typing import List

from models import PriceSnapshot, RegimeAnalysis


# Llindars de classificacio (ajustables aqui mateix).
EFFICIENCY_TREND_THRESHOLD: float = 0.45   # per sobre, es considera tendencia neta
REVERSALS_CHAOTIC_RATIO: float = 0.45      # % de barres amb canvi de direccio per considerar "caotic"
ATR_STOP_MULTIPLIER: float = 1.5           # distancia de stop suggerida = ATR * aixo


def _efficiency_ratio(closes: List[float]) -> float:
    """Kaufman Efficiency Ratio: |moviment net| / suma(|moviments barra a barra|).

    Args:
        closes: llista de preus de tancament, en ordre cronologic.

    Returns:
        Valor entre 0 i 1 (0 si no hi ha prou dades o no hi ha moviment).
    """
    if len(closes) < 3:
        return 0.0
    net_move = abs(closes[-1] - closes[0])
    total_move = sum(abs(closes[i] - closes[i - 1]) for i in range(1, len(closes)))
    if total_move == 0:
        return 0.0
    return net_move / total_move


def _count_reversals(closes: List[float]) -> int:
    """Compta quantes vegades canvia de signe la direccio barra a barra.

    Args:
        closes: llista de preus de tancament, en ordre cronologic.

    Returns:
        Nombre de reversions de direccio.
    """
    if len(closes) < 3:
        return 0
    diffs = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    reversals = 0
    for i in range(1, len(diffs)):
        if diffs[i] == 0 or diffs[i - 1] == 0:
            continue
        if (diffs[i] > 0) != (diffs[i - 1] > 0):
            reversals += 1
    return reversals


def _average_true_range_simple(highs: List[float], lows: List[float]) -> float:
    """ATR simplificat: mitjana del rang (High - Low) de cada barra.

    No inclou el gap respecte al tancament anterior (ATR "complet"), pero
    es suficient per tenir una mesura de la volatilitat absoluta recent
    sense haver de descarregar dades addicionals.

    Args:
        highs: maxims de cada barra.
        lows: minims de cada barra.

    Returns:
        Rang mitja per barra, en unitats de preu. 0.0 si no hi ha dades.
    """
    if not highs or not lows or len(highs) != len(lows):
        return 0.0
    ranges = [h - l for h, l in zip(highs, lows)]
    return sum(ranges) / len(ranges) if ranges else 0.0


def analyze_regime(price: PriceSnapshot) -> RegimeAnalysis:
    """Classifica el regim de mercat actual d'una accio.

    Args:
        price: PriceSnapshot amb les finestres regime_closes/highs/lows ja
            carregades (finestra mes llarga que la de l'analisi d'energia).

    Returns:
        RegimeAnalysis amb l'Efficiency Ratio, el nombre de reversions,
        l'ATR i la classificacio final del regim.
    """
    closes = price.regime_closes
    highs = price.regime_highs
    lows = price.regime_lows

    if len(closes) < 5:
        return RegimeAnalysis(
            efficiency_ratio=0.0,
            reversals_count=0,
            atr=0.0,
            regime="SENSE_DADES",
            suggested_stop_distance=0.0,
            notes="Encara no hi ha prou barres per avaluar el regim (torna-ho a provar mes tard a la sessio).",
        )

    er = _efficiency_ratio(closes)
    reversals = _count_reversals(closes)
    atr = _average_true_range_simple(highs, lows)
    suggested_stop_distance = atr * ATR_STOP_MULTIPLIER

    reversal_ratio = reversals / max(len(closes) - 2, 1)

    if er >= EFFICIENCY_TREND_THRESHOLD:
        regime = "TENDENCIA"
        notes = (
            f"Moviment net i eficient (ER {er:.2f}): la majoria del recorregut "
            "ha anat en la mateixa direccio, no es soroll pur."
        )
    elif reversal_ratio >= REVERSALS_CHAOTIC_RATIO:
        regime = "LATERAL_CAOTIC"
        notes = (
            f"ALT RISC DE WHIPSAW: {reversals} canvis de direccio en les ultimes "
            f"{len(closes)} barres i nomes {er:.2f} d'eficiencia. L'accio esta "
            "oscil·lant sense arribar enlloc — els stops ajustats tendeixen a saltar aqui."
        )
    else:
        regime = "LATERAL_TRANQUIL"
        notes = (
            f"Lateral pero sense soroll excessiu (ER {er:.2f}, {reversals} reversions). "
            "Menys risc de whipsaw que un lateral caotic, tot i no ser tendencia clara."
        )

    return RegimeAnalysis(
        efficiency_ratio=er,
        reversals_count=reversals,
        atr=atr,
        regime=regime,
        suggested_stop_distance=suggested_stop_distance,
        notes=notes,
    )
