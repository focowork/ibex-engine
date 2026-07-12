"""
models.py
=========
Dataclasses compartides per tots els moduls de l'IBEX Intraday Decision
Engine. Centralitzar el model de dades permet que cada modul rebi i
retorni aquests tipus en lloc de diccionaris solts, la qual cosa fa el
projecte molt mes facil de mantenir i ampliar (Fase 2: backtesting,
estadistica, ML, altres mercats...).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PriceSnapshot:
    """Dades cru de preu/volum intradia d'una accio en el moment de l'analisi."""
    ticker: str
    display_name: str
    last_price: float
    open_price: float
    change_pct: float                    # % variacio vs tancament anterior
    current_volume: float                # volum acumulat avui fins ara
    average_volume_at_this_time: float   # mitjana historica de volum a aquesta hora
    day_high: float = 0.0                # maxim intradia fins ara
    day_low: float = 0.0                 # minim intradia fins ara
    vwap: float = 0.0                    # preu mitja ponderat per volum del dia
    orb_high: float = 0.0                # maxim del rang d'obertura (primers N minuts)
    orb_low: float = 0.0                 # minim del rang d'obertura (primers N minuts)
    bars_since_open: int = 0             # nombre de barres descarregades avui (per saber si l'ORB ja s'ha format)
    poc_price: float = 0.0               # Point of Control: preu amb mes volum negociat avui
    recent_closes: List[float] = field(default_factory=list)   # ultimes N barres (energia)
    recent_volumes: List[float] = field(default_factory=list)  # ultimes N barres (energia)
    recent_highs: List[float] = field(default_factory=list)    # ultimes N barres (energia, per ATR)
    recent_lows: List[float] = field(default_factory=list)     # ultimes N barres (energia, per ATR)
    regime_closes: List[float] = field(default_factory=list)   # finestra mes llarga (regim/whipsaw)
    regime_highs: List[float] = field(default_factory=list)    # finestra mes llarga (regim/whipsaw)
    regime_lows: List[float] = field(default_factory=list)     # finestra mes llarga (regim/whipsaw)


@dataclass
class IndexSnapshot:
    """Dades intradia de l'index de referencia (p.ex. IBEX 35)."""
    ticker: str
    change_pct: float


@dataclass
class NewsItem:
    """Un titular de noticia ja classificat."""
    headline: str
    source: str
    category: str
    link: Optional[str] = None


@dataclass
class NewsAnalysis:
    """Resultat agregat de l'analisi de noticies d'una accio."""
    items: List[NewsItem]
    best_category: str
    summary: str
    score: float


@dataclass
class VolumeAnalysis:
    """Resultat de l'analisi de volum."""
    relative_volume: float
    score: float


@dataclass
class RelativeStrengthAnalysis:
    """Resultat de l'analisi de forca relativa vs l'index."""
    stock_change_pct: float
    index_change_pct: float
    relative_strength_pct: float
    score: float


@dataclass
class EnergyAnalysis:
    """Resultat de l'analisi d'energia del moviment."""
    state: str
    score: float
    detail: str


@dataclass
class ScoreBreakdown:
    """Desglossament complet del score final d'una accio.

    A partir de la V2, el Final Score separa el Momentum Score (probabilitat
    que el moviment continui) de l'Entry Score (qualitat del punt d'entrada
    actual), perque una accio amb bon momentum pero una entrada ja molt
    cara no rebi la mateixa puntuacio que una amb una entrada millor.
    """
    volume_score: float
    relative_strength_score: float
    news_score: float
    energy_score: float
    momentum_score: float
    entry_score: float
    final_score: float
    recommendation: str


@dataclass
class EntrySignal:
    """Analisi de QUALITAT DEL PUNT D'ENTRADA (no nomes si l'accio esta forta,
    sino si ARA es un bon moment o si ja s'ha perdut el millor moment).

    Aixo NO es un consell d'inversio: nomes descriu, amb dades objectives,
    la posicio del preu actual respecte al VWAP i al rang del dia.
    """
    position_vs_vwap_pct: float   # % de distancia del preu actual al VWAP (+ = per sobre)
    distance_to_high_pct: float   # % de distancia al maxim del dia (0 = som al maxim)
    distance_to_low_pct: float    # % de distancia al minim del dia
    quality: str                  # "RUPTURA", "MARGE_RECORREGUT", "SOBREESTES", "LATERAL", "SENSE_DADES"
    suggested_stop_reference: float  # nivell de referencia (VWAP o minim del dia)
    extreme_move_warning: bool = False  # True si el moviment d'avui es tan gran que hi ha risc de correccio
    notes: str = ""                    # explicacio curta en llenguatge natural


@dataclass
class RegimeAnalysis:
    """Analisi del 'regim' de mercat d'una accio: si es mou amb tendencia
    neta o si nomes esta oscil·lant sense rumb (lateral erratic / whipsaw).

    Aixo es clau per decidir si val la pena operar-la ara mateix: en un
    regim lateral caotic, els stops ajustats salten sovint per soroll
    (falses ruptures amunt i avall), no perque la tesi d'entrada fos
    incorrecta.
    """
    efficiency_ratio: float   # 0-1. Prop d'1 = tendencia neta. Prop de 0 = soroll pur.
    reversals_count: int      # nombre de canvis de direccio en les ultimes barres
    atr: float                # rang mitja per barra (volatilitat absoluta)
    regime: str                # "TENDENCIA", "LATERAL_TRANQUIL", "LATERAL_CAOTIC", "SENSE_DADES"
    suggested_stop_distance: float  # distancia de stop suggerida (en unitats de preu) basada en ATR
    notes: str


@dataclass
class FibonacciLevels:
    """Projeccio de nivells de Fibonacci a partir del rang del dia (maxim/minim),
    per identificar possibles zones d'entrada (retrocessos) i possibles
    objectius de sortida (extensions).

    IMPORTANT: aixo NO prediu res ni es un consell d'inversio. Nomes
    aplica una formula matematica estandard (proporcions de Fibonacci)
    sobre el rang de preus d'avui, perque la persona tingui referencies
    objectives de nivells.
    """
    direction: str                        # "ALCISTA" o "BAIXISTA" (segons el moviment del dia)
    swing_low: float                      # minim de referencia (normalment el minim del dia)
    swing_high: float                     # maxim de referencia (normalment el maxim del dia)
    retracement_levels: Dict[str, float] = field(default_factory=dict)   # possibles zones d'entrada
    extension_levels: Dict[str, float] = field(default_factory=dict)     # possibles objectius de sortida
    suggested_entry_zone: tuple = (0.0, 0.0)   # rang de preu (50%-61.8%) mes vigilat pels traders
    notes: str = ""


@dataclass
class ORBAnalysis:
    """Opening Range Breakout: rang format pels primers minuts de sessio.
    Trencar aquest rang amb volum es una de les estrategies intradia mes
    estudiades. NO prediu res, nomes descriu si el preu actual esta dins
    o fora del rang inicial.
    """
    orb_high: float
    orb_low: float
    status: str    # "RUPTURA_ALCISTA", "RUPTURA_BAIXISTA", "DINS_RANG", "ENCARA_FORMANT_SE", "SENSE_DADES"
    breakout_pct: float = 0.0   # % de distancia mes enlla del rang (0 si esta dins)
    notes: str = ""


@dataclass
class VolumeProfileAnalysis:
    """Analisi del Point of Control (POC): el nivell de preu on s'ha
    negociat mes volum avui. Sol actuar com un iman/suport-resistencia
    mes fiable que un nivell arbitrari, perque reflecteix on hi ha hagut
    mes activitat real.
    """
    poc_price: float
    position_vs_poc_pct: float   # % de distancia del preu actual al POC (+ = per sobre)
    notes: str = ""


@dataclass
class RiskRewardAnalysis:
    """Calcul explicit del ratio Risc:Recompensa combinant el stop
    suggerit (EntrySignal) amb l'objectiu de sortida mes proper
    (FibonacciLevels). Molts traders nomes entren si el R:R es >= 2:1.
    """
    stop_price: float
    target_price: float
    risk: float           # distancia en preu fins al stop
    reward: float         # distancia en preu fins a l'objectiu
    ratio: float          # reward / risk
    quality: str          # "EXCEL·LENT", "BO", "ACCEPTABLE", "DOLENT", "SENSE_DADES"
    notes: str = ""


@dataclass
class BiasAnalysis:
    """Sintetitza en UN sol indicador de color cap a on apunten *ara mateix*
    els senyals tecnics ja calculats (VWAP, ORB, regim/Fibonacci, forca
    relativa). NO ES UNA PREDICCIO: nomes compta quants dels senyals
    disponibles apunten amunt vs avall en aquest instant. El mercat pot
    girar en qualsevol moment; aixo es una fotografia, no una garantia.
    """
    bullish_count: int
    bearish_count: int
    neutral_count: int
    bias: str      # "ALCISTA_CLAR", "ALCISTA_LLEU", "BAIXISTA_CLAR", "BAIXISTA_LLEU", "MIXT"
    color: str      # emoji de color (🟢/🔴/🟡)
    signals: List[str] = field(default_factory=list)   # detall de cada senyal individual
    notes: str = ""


@dataclass
class UpcomingEventsAnalysis:
    """Calendari d'esdeveniments corporatius rellevants (data de resultats,
    juntes d'accionistes...) que podrien causar volatilitat inesperada.

    Aixo ve d'una font DIFERENT de news.py: en lloc de buscar titulars
    d'ARA MATEIX, mira dades de calendari (quan es publicaran els propers
    resultats) per avisar-te ABANS que passi, no despres.
    """
    has_upcoming_event: bool
    event_type: str          # "RESULTATS", "SENSE_DADES"
    event_date: str          # data en format YYYY-MM-DD, o "" si no n'hi ha
    days_until: int           # dies fins a l'esdeveniment (pot ser negatiu si ja ha passat)
    is_imminent: bool         # True si cau dins la finestra d'avis (config.EVENT_WARNING_WINDOW_DAYS)
    notes: str = ""


@dataclass
class StretchAnalysis:
    """Mesura com d'estesa (allunyada del seu 'centre de gravetat') esta
    ja una accio, combinant la distancia al VWAP, la distancia al POC i
    quin % del rang del dia ja s'ha recorregut. Una entrada molt estesa
    es mes cara i te menys marge, encara que el momentum sigui excel·lent.
    """
    vwap_distance_pct: float
    poc_distance_pct: float
    pct_of_day_range_covered: float
    stretch_level: str    # "BAIX", "MITJA", "ALT"
    penalty: float         # ajust aplicat a l'Entry Score (0 o negatiu)
    notes: str = ""


@dataclass
class RemainingPotentialAnalysis:
    """Quant recorregut (en multiples d'ATR) li queda al preu fins a
    l'objectiu de sortida. Una entrada amb molt poc marge fins a l'objectiu
    es una entrada tardana, encara que la resta de senyals siguin bons.
    """
    atr_multiple: float
    category: str    # "ENTRADA_TARDANA", "LIMITAT", "CORRECTE", "MOLT_RECORREGUT", "SENSE_DADES"
    adjustment: float   # ajust aplicat a l'Entry Score
    notes: str = ""


@dataclass
class StockReport:
    """Informe complet d'una accio, llest per ser renderitzat."""
    display_name: str
    ticker: str
    price: PriceSnapshot
    volume: VolumeAnalysis
    relative_strength: RelativeStrengthAnalysis
    news: NewsAnalysis
    energy: EnergyAnalysis
    scores: ScoreBreakdown
    entry: "EntrySignal"
    regime: "RegimeAnalysis"
    fibonacci: "FibonacciLevels"
    orb: "ORBAnalysis"
    volume_profile: "VolumeProfileAnalysis"
    risk_reward: "RiskRewardAnalysis"
    bias: "BiasAnalysis"
    upcoming_events: "UpcomingEventsAnalysis"
    stretch: "StretchAnalysis"
    remaining_potential: "RemainingPotentialAnalysis"
    explanation: str
