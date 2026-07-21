"""
config.py
=========
Constants i configuracio central de l'IBEX Intraday Decision Engine.

REGLA D'OR: cap altre modul ha de contenir "numeros magics". Tot valor
ajustable (pesos, llindars, finestres temporals...) viu aqui, perque es
pugui afinar el sistema sense tocar la logica de negoci.
"""

from typing import Dict, List

# ---------------------------------------------------------------------------
# MERCATS
# ---------------------------------------------------------------------------
# Ticker de yfinance que representa l'index de referencia de cada mercat.
MARKET_INDEX_TICKERS: Dict[str, str] = {
    "IBEX35": "^IBEX",
    "SPCX": "^IXIC",  # SpaceX cotitza al Nasdaq; fem servir el Nasdaq Composite com a referencia
    # NASDAQ (mercat sencer) desactivat a peticio de l'usuari:
    # "NASDAQ": "^IXIC",
}

# Mercat actiu per aquesta execucio. Per canviar de mercat nomes cal
# modificar aquesta linia.
ACTIVE_MARKET: str = "IBEX35"

# ---------------------------------------------------------------------------
# UNIVERS D'ACCIONS
# ---------------------------------------------------------------------------
# Mapeja un nom llegible al seu ticker de yfinance.
# Les 35 empreses de l'IBEX35 (composicio de referencia; el comite tecnic
# la revisa dues vegades l'any, al juny i al desembre, aixi que pot caldre
# actualitzar algun ticker de tant en tant).
IBEX_STOCK_UNIVERSE: Dict[str, str] = {
    "ACS": "ACS.MC",
    "ACERINOX": "ACX.MC",
    "AENA": "AENA.MC",
    "AMADEUS": "AMS.MC",
    "ACCIONA": "ANA.MC",
    "ACCIONA ENERGIA": "ANE.MC",
    "BBVA": "BBVA.MC",
    "BANKINTER": "BKT.MC",
    "CAIXABANK": "CABK.MC",
    "CELLNEX": "CLNX.MC",
    "COLONIAL": "COL.MC",
    "ENDESA": "ELE.MC",
    "ENAGAS": "ENG.MC",
    "FLUIDRA": "FDR.MC",
    "FERROVIAL": "FER.MC",
    "GRIFOLS": "GRF.MC",
    "IAG": "IAG.MC",
    "IBERDROLA": "IBE.MC",
    "INDRA": "IDR.MC",
    "INDITEX": "ITX.MC",
    "LOGISTA": "LOG.MC",
    "MAPFRE": "MAP.MC",
    "MERLIN PROPERTIES": "MRL.MC",
    "ARCELORMITTAL": "MTS.MC",
    "NATURGY": "NTGY.MC",
    "PUIG": "PUIG.MC",
    "REDEIA": "RED.MC",
    "REPSOL": "REP.MC",
    "ROVI": "ROVI.MC",
    "SABADELL": "SAB.MC",
    "SANTANDER": "SAN.MC",
    "SACYR": "SCYR.MC",
    "SOLARIA": "SLR.MC",
    "TELEFONICA": "TEF.MC",
    "UNICAJA": "UNI.MC",
}

# Univers d'una sola accio dins l'IBEX35: nomes GRIFOLS (a peticio de l'usuari,
# que vol l'app centrada nomes en Grifols + SpaceX, ignorant la resta de l'IBEX).
IBEX_FOCUSED_UNIVERSE: Dict[str, str] = {
    "GRIFOLS": "GRF.MC",
}

# Univers d'una sola accio per SpaceX (Nasdaq: SPCX), IPO del 12 de juny de 2026.
SPCX_STOCK_UNIVERSE: Dict[str, str] = {
    "SPACEX": "SPCX",
}

# Univers actiu que fara servir main.py quan nomes s'analitza UN mercat.
STOCK_UNIVERSE: Dict[str, str] = IBEX_FOCUSED_UNIVERSE

# Mapeig mercat -> univers d'accions.
MARKET_STOCK_UNIVERSES: Dict[str, Dict[str, str]] = {
    "IBEX35": IBEX_FOCUSED_UNIVERSE,
    "SPCX": SPCX_STOCK_UNIVERSE,
}

# Moneda de cotitzacio de cada mercat, nomes per mostrar-la correctament
# a l'informe.
MARKET_CURRENCY: Dict[str, str] = {
    "IBEX35": "EUR",
    "SPCX": "USD",
}

# Mercats que s'analitzaran quan es fa servir run_multi_market() sense
# arguments.
MARKETS_TO_RUN: List[str] = ["IBEX35", "SPCX"]

# ---------------------------------------------------------------------------
# DADES / TEMPS
# ---------------------------------------------------------------------------
INTRADAY_INTERVAL: str = "5m"              # granularitat intradia de yfinance
INTRADAY_PERIOD: str = "1d"                # historial a descarregar per "avui"
HISTORICAL_PERIOD_FOR_AVG_VOLUME: str = "20d"     # finestra per calcular volum mitja
HISTORICAL_INTERVAL_FOR_AVG_VOLUME: str = "5m"

# ---------------------------------------------------------------------------
# SISTEMA DE DOBLE SCORE: MOMENTUM + ENTRY
# ---------------------------------------------------------------------------
# A peticio de l'usuari (document "Propostes de millora del sistema de
# scoring"), el score final separa DUES coses que abans es barrejaven:
#   - Momentum Score: la probabilitat que el moviment CONTINUI (direccio,
#     tendencia, forca relativa...).
#   - Entry Score: si el PUNT D'ENTRADA actual es bo (Risc:Recompensa,
#     com d'estesa esta ja l'accio, quant recorregut li queda...).
# Aixi, una accio amb molt bon momentum pero una entrada ja molt cara
# (p.ex. R:R d'1:1 perque ja ha pujat molt) no reb la mateixa puntuacio
# que una amb el mateix momentum pero una entrada molt millor.

# Pes de cada score dins el Final Score (han de sumar 1.0).
MOMENTUM_SCORE_WEIGHT: float = 0.60
ENTRY_SCORE_WEIGHT: float = 0.40

# Pesos interns del Momentum Score (han de sumar 1.0).
MOMENTUM_WEIGHT_VWAP: float = 0.18
MOMENTUM_WEIGHT_ORB: float = 0.18
MOMENTUM_WEIGHT_RELATIVE_STRENGTH: float = 0.18
MOMENTUM_WEIGHT_REGIME: float = 0.18
MOMENTUM_WEIGHT_STRUCTURE: float = 0.18   # "estructura" = energia del moviment
MOMENTUM_WEIGHT_NEWS: float = 0.10        # noticies rellevants (no forma part de la proposta original, pero es manté amb pes reduït per no perdre senyal)

# Punts de regim (dins del Momentum Score).
REGIME_MOMENTUM_POINTS: Dict[str, float] = {
    "TENDENCIA": 100.0,
    "LATERAL_TRANQUIL": 50.0,
    "LATERAL_CAOTIC": 0.0,
    "SENSE_DADES": 50.0,
}

# --- Entry Score: baseline + ajustos additius, despres es fa clamp 0-100 ---
ENTRY_SCORE_BASELINE: float = 50.0

# Ajustos de Risc:Recompensa (proposta #2).
RR_ADJUSTMENT_BELOW_1: float = -15.0     # R:R < 1:1
RR_ADJUSTMENT_1_TO_2: float = -5.0       # 1:1 <= R:R < 2:1
RR_ADJUSTMENT_2_TO_3: float = 5.0        # 2:1 <= R:R < 3:1
RR_ADJUSTMENT_3_TO_5: float = 10.0       # 3:1 <= R:R <= 5:1
RR_ADJUSTMENT_ABOVE_5: float = 15.0      # R:R > 5:1

# Penalitzacio per "stretch" (entrada massa estesa, proposta #3).
STRETCH_PENALTY: float = -10.0
STRETCH_VWAP_THRESHOLD_PCT: float = 2.0        # % de distancia al VWAP considerat "molt"
STRETCH_POC_THRESHOLD_PCT: float = 3.0         # % de distancia al POC considerat "molt"
STRETCH_DAY_RANGE_THRESHOLD_PCT: float = 85.0  # % del rang diari recorregut considerat "molt"

# Ajustos de volum (proposta #5).
VOLUME_ADJUSTMENT_HIGH: float = 10.0   # volum > 2x
VOLUME_ADJUSTMENT_MED: float = 5.0     # volum 1x-2x
VOLUME_ADJUSTMENT_LOW: float = -5.0    # volum < 0.6x

# Potencial restant, en multiples d'ATR (proposta #6).
REMAINING_POTENTIAL_LATE_THRESHOLD: float = 0.5    # < aixo = entrada tardana
REMAINING_POTENTIAL_GOOD_MIN: float = 1.0
REMAINING_POTENTIAL_GOOD_MAX: float = 2.0          # > aixo = molt recorregut
REMAINING_POTENTIAL_LATE_ADJUSTMENT: float = -10.0
REMAINING_POTENTIAL_CORRECT_ADJUSTMENT: float = 5.0
REMAINING_POTENTIAL_HIGH_ADJUSTMENT: float = 10.0

# ---------------------------------------------------------------------------
# ESCALA DE SCORE
# ---------------------------------------------------------------------------
SCORE_MIN: float = 0.0
SCORE_MAX: float = 100.0

# ---------------------------------------------------------------------------
# LLINDARS DE RECOMANACIO
# ---------------------------------------------------------------------------
THRESHOLD_BUY: float = 75.0
THRESHOLD_WATCH: float = 55.0
# Per sota de THRESHOLD_WATCH => evitar / sense oportunitat clara

RECOMMENDATION_BUY: str = "COMPRAR"
RECOMMENDATION_WATCH: str = "VIGILAR"
RECOMMENDATION_AVOID: str = "EVITAR"

# ---------------------------------------------------------------------------
# SCORE DE VOLUM
# ---------------------------------------------------------------------------
# Volum relatiu = volum acumulat avui / volum mitja historic a la mateixa hora.
RELATIVE_VOLUME_EXCELLENT: float = 2.0   # >= 2x la mitjana => score maxim
RELATIVE_VOLUME_HIGH: float = 1.5
RELATIVE_VOLUME_NORMAL: float = 1.0
RELATIVE_VOLUME_LOW: float = 0.5

# ---------------------------------------------------------------------------
# SCORE DE FORCA RELATIVA
# ---------------------------------------------------------------------------
# Diferencia en punts percentuals entre la variacio de l'accio i la de l'index.
RS_EXCELLENT_DIFF: float = 2.0
RS_GOOD_DIFF: float = 1.0
RS_NEUTRAL_DIFF: float = 0.0
RS_NEGATIVE_DIFF: float = -1.0

# ---------------------------------------------------------------------------
# NOTICIES
# ---------------------------------------------------------------------------
NEWS_MAX_HEADLINES: int = 8
# Noticies en castella: es l'idioma real en que es publica la premsa
# financera sobre empreses de l'IBEX (Expansion, Cinco Dias, El
# Economista...), aixi que dona la millor cobertura de titulars. Nomes
# el text que GENERA el motor (recomanacions, explicacions, avisos) es
# sempre en catala, independentment de l'idioma de la noticia trobada.
NEWS_LANGUAGE: str = "es"
NEWS_REGION: str = "ES"

# Categories de noticia i la seva puntuacio base d'impacte (0-100).
NEWS_CATEGORY_SCORES: Dict[str, float] = {
    "OPA": 100.0,
    "Resultats": 90.0,
    "Contracte": 85.0,
    "Recomanacio": 70.0,
    "Canvi de previsio": 65.0,
    "Rumor": 50.0,
    "Sectorial": 40.0,
    "Sense noticia": 0.0,
}

# Paraules clau (en minuscules) per classificar cada titular en una categoria.
# Inclou termes en castella (IBEX) i en angles (NASDAQ) perque el motor
# funcioni amb qualsevol dels dos mercats sense tocar mes codi.
NEWS_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "OPA": [
        "opa", "oferta publica de adquisicion", "takeover bid",
        "acquisition", "acquires", "merger", "buyout", "tender offer",
        "oferta publica d'adquisicio", "fusio", "compra d'accions",
    ],
    "Resultats": [
        "resultados", "beneficio", "beneficios", "ebitda", "ingresos", "cuentas",
        "earnings", "quarterly results", "revenue", "profit", "eps beat", "eps miss",
        "resultats", "beneficis", "ingressos", "comptes",
    ],
    "Contracte": [
        "contrato", "adjudicacion", "acuerdo", "alianza",
        "contract", "deal", "partnership", "agreement",
        "contracte", "adjudicacio", "acord", "alianca",
    ],
    "Recomanacio": [
        "recomienda", "sobreponderar", "infraponderar", "precio objetivo", "eleva", "rebaja",
        "upgrades", "downgrades", "price target", "overweight", "underweight", "outperform",
        "recomana", "preu objectiu", "eleva la previsio", "rebaixa",
    ],
    "Canvi de previsio": [
        "revisa", "prevision", "guidance", "actualiza objetivo",
        "raises guidance", "cuts guidance", "forecast",
        "previsio", "actualitza objectiu",
    ],
    "Rumor": [
        "rumor", "fuentes", "podria", "negocia",
        "sources say", "reportedly", "in talks",
        "rumors", "fonts", "podria", "negocia",
    ],
    "Sectorial": ["sector", "industry", "industria"],
}

# Frases que indiquen un article de tipus "roundup" promocional (llistat
# d'ofertes/descomptes que esmenta moltes marques de passada), NO una
# noticia real sobre l'empresa. Si el titular en conte alguna, es forca
# a "Sense noticia" independentment de si tambe conte alguna paraula clau
# de les categories normals (p.ex. "deal").
NEWS_ROUNDUP_BLOCKLIST: List[str] = [
    "% off", "off from", "deals up to", "shop deals", "shop the best deals",
    "best deals", "top deals", "gift guide", "black friday", "cyber monday",
    "prime day", "prime day deals", "holiday deals", "deals of the day",
    "rebajas", "chollos", "ofertas de",
]

# Si un titular te moltes comes seguides (llista de marques/productes),
# es un indici mes de "roundup" generic i no de noticia especifica de
# l'empresa. A partir d'aquest nombre de comes, es tracta com a roundup.
NEWS_ROUNDUP_COMMA_THRESHOLD: int = 3

# ---------------------------------------------------------------------------
# ENERGIA DEL MOVIMENT (continuitat del momentum)
# ---------------------------------------------------------------------------
ENERGY_LOOKBACK_BARS: int = 6  # barres intradia recents a analitzar

# Finestra mes llarga que ENERGY_LOOKBACK_BARS, nomes per detectar si l'accio
# esta en tendencia neta o en regim lateral erratic (whipsaw). Amb interval
# de 5 min, 20 barres = ~100 minuts de sessio.
REGIME_LOOKBACK_BARS: int = 20

# A partir d'aquest % de variacio intradia (en valor absolut), s'afegeix un
# avis de "moviment extrem": un moviment tan gran en una sola sessio te mes
# risc estadistic de correccio tecnica els dies seguents, independentment
# de si l'score diu COMPRAR. No es una prediccio, nomes un avis de prudencia.
EXTREME_MOVE_WARNING_PCT: float = 4.0

# ---------------------------------------------------------------------------
# OPENING RANGE BREAKOUT (ORB)
# ---------------------------------------------------------------------------
# Nombre de barres inicials de la sessio que formen el "rang d'obertura".
# Amb interval de 5 min, 6 barres = primers 30 minuts de sessio.
ORB_BARS: int = 6

# ---------------------------------------------------------------------------
# VOLUME PROFILE (Point of Control)
# ---------------------------------------------------------------------------
# Nombre de "caixes" de preu en que es divideix el rang del dia per trobar
# el nivell amb mes volum negociat (POC). Mes caixes = mes precisio pero
# mes soroll amb poques dades.
VOLUME_PROFILE_BINS: int = 20

# ---------------------------------------------------------------------------
# RISC:RECOMPENSA (R:R)
# ---------------------------------------------------------------------------
# Llindars per classificar la qualitat del R:R d'una possible entrada.
RISK_REWARD_EXCELLENT_THRESHOLD: float = 3.0   # R:R >= 3:1
RISK_REWARD_GOOD_THRESHOLD: float = 2.0        # R:R >= 2:1
RISK_REWARD_ACCEPTABLE_THRESHOLD: float = 1.0  # R:R >= 1:1 (per sota, es considera dolent)

# ---------------------------------------------------------------------------
# CALENDARI D'ESDEVENIMENTS CORPORATIUS (resultats, juntes...)
# ---------------------------------------------------------------------------
# Si la propera data de resultats (o un altre esdeveniment rellevant) cau
# dins d'aquest nombre de dies, es destaca com a avis a l'informe.
EVENT_WARNING_WINDOW_DAYS: int = 5

ENERGY_STATE_STRONG_CONTINUATION: str = "Mante maxims / entra volum"
ENERGY_STATE_MODERATE_CONTINUATION: str = "Mante forca"
ENERGY_STATE_WEAKENING: str = "Perd forca"
ENERGY_STATE_EXHAUSTED: str = "Esgota moviment"
ENERGY_STATE_DECREASING_VOLUME: str = "Disminueix volum"

ENERGY_SCORE_MAP: Dict[str, float] = {
    ENERGY_STATE_STRONG_CONTINUATION: 95.0,
    ENERGY_STATE_MODERATE_CONTINUATION: 75.0,
    ENERGY_STATE_DECREASING_VOLUME: 50.0,
    ENERGY_STATE_WEAKENING: 30.0,
    ENERGY_STATE_EXHAUSTED: 10.0,
}

# ---------------------------------------------------------------------------
# INFORME
# ---------------------------------------------------------------------------
TOP_N_RESULTS: int = 35  # les 35 empreses de l'IBEX35, sempre totes, ordenades per score

# ---------------------------------------------------------------------------
# MODE OPERATIU: NOMES LLARG (COMPRA)
# ---------------------------------------------------------------------------
# L'usuari nomes opera a l'alça (compra i despres ven, mai posicions curtes).
# Quan es True, els valors amb biaix tecnic BAIXISTA_CLAR o BAIXISTA_LLEU
# es filtren fora del rànquing principal (no son operatius per aquest
# usuari) i nomes apareixen en una nota al peu, per transparencia.
LONG_ONLY_MODE: bool = True

# ---------------------------------------------------------------------------
# TANCAMENT DE SESSIO: PICKS PER L'ENDEMA
# ---------------------------------------------------------------------------
# Nombre de candidats que es proposen a l'analisi de tancament (closing_report.py).
EOD_NUM_PICKS: int = 3

# Capital total per defecte a repartir entre els EOD_NUM_PICKS candidats.
EOD_DEFAULT_CAPITAL: float = 10000.0

# Repartiment de capital: pes minim i maxim per candidat (evita que un sol
# valor s'enduguin gairebe tot el capital nomes per tenir el score mes alt,
# i evita tambe assignar quantitats simbolicament petites).
EOD_ALLOCATION_MIN_PCT: float = 0.15
EOD_ALLOCATION_MAX_PCT: float = 0.50

# Metode de repartiment de capital entre els candidats:
#   "SCORE"          -> proporcional nomes al Final Score
#   "RISK_ADJUSTED"  -> proporcional a Final Score / risc en % del preu
#                       (posicions amb stop mes ajustat en % reben mes pes,
#                       per igualar el risc en euros entre posicions -
#                       filosofia "risk parity")
EOD_ALLOCATION_METHOD: str = "RISK_ADJUSTED"

# ---------------------------------------------------------------------------
# TRACK RECORD (historial persistent a Google Drive)
# ---------------------------------------------------------------------------
# Carpeta a Google Drive on es guarda l'historial de picks i resultats.
# Persisteix entre sessions de Colab (a diferencia dels fitxers .py, que
# cal tornar a pujar cada vegada).
TRACK_RECORD_DRIVE_PATH: str = "/content/drive/MyDrive/ibex_engine_track_record"
TRACK_RECORD_FILENAME: str = "picks_historial.csv"
