# IBEX Intraday Decision Engine — V1

Assistent de decisió intradia **centrat exclusivament en l'IBEX35** (analisi de NASDAQ desactivada). **No és un bot**: no prediu res abans de l'obertura, només analitza la situació real en el moment exacte en què l'executes (09:45, 11:30, 16:00...).

Cada execució analitza **sempre les 35 empreses de l'índex**, ordenades de més a menys potencial (score més alt primer) — no només un TOP 5.

**Idioma de les notícies**: es cerquen en castellà (l'idioma real de la premsa financera espanyola: Expansión, Cinco Días, El Economista...), per tenir la millor cobertura possible de titulars. Tota la resta de text que genera el motor (recomanacions, explicacions, avisos) és sempre en català, independentment de l'idioma de la notícia trobada.

## 📌 Puja-ho a GitHub (recomanat — evita pujar 23 fitxers cada sessió)

Fins ara calia arrossegar els 23 `.py` cada vegada que Colab reiniciava l'entorn. Amb el codi a GitHub, nomes cal `git clone` un cop per sessio — molt mes rapid i sense errors d'oblidar cap fitxer.

**Passos des del mòbil (sense fer servir cap comandament `git`):**

1. Ves a **github.com**, crea un compte gratuit si no en tens (o inicia sessió).
2. Toca el **+** de dalt a la dreta → **New repository**.
3. Posa-li un nom (p.ex. `ibex-engine`), marca'l com a **Private** si vols que sigui nomes teu, i crea'l.
4. Dins el repositori nou, toca **Add file → Upload files**.
5. Selecciona i puja **tots** els fitxers d'aquesta carpeta (els `.py`, el `.ipynb`, el `.gitignore`, el `requirements.txt` i els `.md`) — es pot fer amb el gestor de fitxers del mòbil igual que feies amb Colab.
6. Toca **Commit changes** (pots deixar el missatge per defecte).

Un cop pujat, copia la URL del repositori (botó verd **Code** → copia l'enllaç `https://github.com/EL_TEU_USUARI/ibex-engine.git`).

**A Colab**, la primera cel·la del notebook (secció "2. Carrega els mòduls") ja porta preparada la comanda:
```python
!git clone https://github.com/EL_TEU_USUARI/EL_TEU_REPO.git
%cd EL_TEU_REPO
```
Substitueix la URL per la teva i ja està — cada sessió nova, només cal tornar a executar aquesta cel·la (una línia, en lloc de pujar 23 fitxers).

**Si el repositori és privat**, `git clone` et demanarà autenticar-te. La manera més senzilla és crear un **Personal Access Token** a GitHub (Settings → Developer settings → Personal access tokens) i fer servir la URL amb el token:
```python
!git clone https://EL_TEU_TOKEN@github.com/EL_TEU_USUARI/EL_TEU_REPO.git
```

**Quan actualitzi codi nou**, només cal repetir el pas 4-6 (pujar els fitxers canviats a GitHub) i a Colab fer `!git pull` en lloc de tornar a pujar-ho tot manualment.

## 🌐 App web (sense Colab, des del mòbil com qualsevol pàgina)

En lloc de fer servir Colab, tot el motor esta disponible com una app web amb botons (`app.py`), amb 5 pantalles: Vista ràpida, Tancament, Confirmació matí, Anàlisi completa i Historial.

### Desplegament gratuït (uns 10 minuts, un cop)

1. **Puja el codi a GitHub** (segueix la secció "Puja-ho a GitHub" de mes amunt si encara no ho has fet).
2. Ves a **streamlit.io/cloud** i inicia sessió amb el teu compte de GitHub.
3. **New app** → selecciona el teu repositori → indica `app.py` com a fitxer principal → **Deploy**.
4. Al cap d'un parell de minuts, tindras una URL fixa (tipus `https://el-teu-nom.streamlit.app`) — obre-la des del mòbil i guarda-la a la pantalla d'inici com si fos una app.

### Historial persistent (opcional pero recomanat)

Perque l'historial de picks (`track_record`) es guardi de manera permanent (i no nomes durant la sessio del navegador), cal donar-li a l'app permis per actualitzar el teu repositori de GitHub:

1. A GitHub: **Settings (del teu perfil) → Developer settings → Personal access tokens → Tokens (classic) → Generate new token**. Marca el permis `repo` i genera'l. Copia el token (nomes es mostra un cop).
2. A la teva app de Streamlit Cloud: **Settings → Secrets**, i afegeix:
   ```toml
   GITHUB_TOKEN = "el_teu_token"
   GITHUB_REPO = "el_teu_usuari/el_teu_repo"
   ```
3. Guarda. L'app ja pot registrar i llegir l'historial fent "commits" automatics al mateix repositori.

Sense aquest pas, l'app funciona igualment (analisi, tancament, confirmacio del mati), pero l'historial nomes dura mentre tinguis la pestanya oberta.

### Actualitzar l'app quan hi hagi codi nou

Puja els fitxers canviats a GitHub (com sempre) — Streamlit Cloud detecta el canvi i redesplega l'app automaticament en uns segons, sense haver de fer res mes.

## Estructura del projecte

```
config.py             -> Constants i pesos (l'únic lloc amb "números màgics")
models.py              -> Dataclasses compartides (PriceSnapshot, ScoreBreakdown, StockReport...)
data_loader.py          -> Descàrrega de dades via yfinance (preu, volum, index)
volume.py               -> Volum relatiu + score (0-100)
relative_strength.py    -> Força relativa vs IBEX + score
news.py                 -> Notícies via Google News RSS (gratuït) + classificació
energy.py               -> Energia del moviment (continua / s'esgota) + score
regime.py               -> Deteccio de regim (tendencia / lateral tranquil / lateral caotic-whipsaw)
entry_signal.py         -> Qualitat del punt d'entrada (VWAP, rang del dia)
fibonacci.py            -> Retrocessos i extensions de Fibonacci
orb.py                  -> Opening Range Breakout
volume_profile.py       -> Point of Control (nivell amb mes volum negociat)
risk_reward.py          -> Ratio Risc:Recompensa explicit
bias.py                 -> Biaix direccional amb codi de colors (NO es una prediccio)
upcoming_events.py      -> Calendari de resultats i altres esdeveniments
scoring.py              -> Score final ponderat + recomanació (COMPRAR/VIGILAR/EVITAR)
report.py               -> Explicacions i informe final (mobile-friendly)
main.py                 -> Orquestrador: run() / run_multi_market() / watch_ticker()
compare.py              -> Snapshots, comparativa temporal i trajectoria de sessio
app.py                  -> App web (Streamlit), 5 pantalles amb botons
app_storage.py          -> Persistencia de l'historial via GitHub (per app.py)
IBEX_Intraday_Engine.ipynb -> Notebook de Colab llest per fer servir
```

## Ús a Google Colab

1. Puja els 19 fitxers `.py` a la carpeta de l'entorn de Colab (o al teu Drive).
2. Obre `IBEX_Intraday_Engine.ipynb`, executa la cel·la d'instal·lació.
3. Executa:
   ```python
   from main import run_multi_market
   run_multi_market()          # analitza IBEX35 + NASDAQ alhora (config.MARKETS_TO_RUN)
   ```
   O si nomes vols un mercat concret:
   ```python
   from main import run
   run(market="NASDAQ")        # o market="IBEX35"
   ```
4. Torna a executar la cel·la cada vegada que vulguis una foto nova de la sessió (09:45, 11:30, 16:00...).

### Projeccio de nivells de Fibonacci (`fibonacci.py`)

Cada accio de l'informe inclou ara els nivells de Fibonacci calculats sobre el rang de preu d'avui (maxim/minim):

- **Retrocessos** (23.6% / 38.2% / 50% / 61.8% / 78.6%): possibles zones on el preu podria "descansar" abans de continuar el moviment — es a dir, possibles nivells d'entrada.
- **Extensions** (127.2% / 161.8% / 200%): possibles objectius de sortida si el moviment continua mes enlla del rang actual.
- **Zona d'entrada suggerida**: la banda entre el 50% i el 61.8%, que es la mes vigilada pels traders tecnics.

La direccio (ALCISTA/BAIXISTA) es determina segons si el preu esta mes a prop del maxim o del minim del dia. Com sempre, aixo es una tecnica estandard d'analisi tecnica basada en proporcions matematiques, NO una prediccio — els nivells son referencies, no garanties.

### Filtres de qualitat afegits

**Notícies "roundup" (falsos positius):** articles generics del tipus "ofertes del 4 de juliol: descomptes fins al 60% de Hanes, Ninja, Apple, Shark..." ja NO es classifiquen com a notícia rellevant de l'empresa, encara que continguin paraules clau com "deal". El filtre (`config.NEWS_ROUNDUP_BLOCKLIST`) descarta titulars amb frases promocionals genèriques ("% off", "deals up to", "black friday"...) o amb massa marques en llista (3+ comes).

**Avís de moviment extrem:** quan una acció ja s'ha mogut molt avui (per defecte, ±4% o mes — configurable a `config.EXTREME_MOVE_WARNING_PCT`), s'afegeix un avís explícit de risc de correcció tècnica als propers dies, independentment de si el score diu COMPRAR. No canvia la recomanació ni prediu res, només avisa de no perseguir cegament un moviment ja molt gran.

### Calendari d'esdeveniments corporatius (`upcoming_events.py`)

A diferencia de `news.py` (que busca titulars d'ARA MATEIX), aquest modul consulta el **calendari** de yfinance per avisar-te ABANS que passi un esdeveniment rellevant — principalment la propera data de publicacio de resultats.

Si un valor te resultats programats dins dels propers **5 dies** (configurable a `config.EVENT_WARNING_WINDOW_DAYS`), apareix una seccio destacada ben visible **al capdamunt de tot l'informe**, abans fins i tot del rànquing:

```
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
📅 PROPERS EVENTS RELLEVANTS — COMPTE ABANS D'ENTRAR-HI
🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔🔔
  ⚠️ BBVA: 📅 RESULTATS PROGRAMATS en 2 dies (2026-07-07). Moviments grans i imprevisibles son habituals al voltant d'aquesta data.
```

**Important**: aquesta secció escaneja **tots** els valors de l'univers, no només el TOP 5 — així no se't escapa un avís de resultats només perquè aquell valor no surti al rànquing en aquell moment.

**Limitacions a tenir en compte**: la cobertura d'aquesta dada de calendari sol ser molt bona per valors de NASDAQ i mes irregular per valors mes petits de l'IBEX35. Si no hi ha dades disponibles per un valor, simplement no apareix cap avís (no falla l'execucio).

### Biaix direccional amb codi de colors (`bias.py`)

**Important primer de tot: aixo NO prediu si un valor pujara o baixara.** Cap eina ho pot fer de forma fiable. El que fa aquest modul es combinar 4 senyals tecnics que ja calculem (VWAP, ORB, direccio del moviment dominant d'avui i forca relativa vs index) en un sol indicador de color que mostra cap a on apunten *ara mateix*:

- 🟢 **TENDEIX A PUJAR** (clar/lleu segons quants senyals coincideixen)
- 🔴 **TENDEIX A BAIXAR** (clar/lleu)
- 🟡 **SENYALS CONTRADICTORIS** (els indicadors no es posen d'acord)

Es mostra ben visible al resum de cada accio:
```
1. 🟢 ENTRA ARA  —  BBVA  (88/100)
   🟢 TENDEIX A PUJAR (clar)   (4 senyals amunt / 0 avall / 0 neutres)
```

Al detall complet, es desglossen els 4 senyals individuals (VWAP, ORB, moviment dominant, forca relativa) perque puguis veure exactament d'on surt el veredicte. Si el regim es LATERAL_CAOTIC (whipsaw), s'afegeix un avis que el biaix pot invertir-se molt rapid.

### 4 mòduls d'avantatge afegits

**Risc:Recompensa explicit (`risk_reward.py`):** combina el stop suggerit amb l'objectiu de sortida (extensio Fibonacci 127.2%) en un sol ratio. Es mostra al resum ("R:R 1.2:1 (ACCEPTABLE)") i al detall. Classificacio: EXCEL·LENT (≥3:1), BO (≥2:1), ACCEPTABLE (≥1:1), DOLENT (<1:1). Molts traders nomes entren si el R:R es ≥2:1.

**Opening Range Breakout (`orb.py`):** marca el rang (maxim/minim) dels primers 30 minuts de sessio i indica si el preu l'ha trencat per dalt o per baix. Una de les estrategies intradia mes estudiades.

**Volume Profile / Point of Control (`volume_profile.py`):** calcula a quin preu concret s'ha negociat mes volum avui (POC), un nivell que sol actuar de suport/resistencia mes fiable que un nivell arbitrari.

**Trajectoria de sessio (`compare.session_trajectory()`):** a diferencia de `compare_latest()` (que nomes mira les dues ultimes captures), aquesta funcio analitza TOTES les captures fetes durant el dia i classifica cada accio com a PUJADA CONSISTENT, BAIXADA CONSISTENT, ERRATIC o PLANA. Una pujada consistent en 4-5 captures seguides es una senyal molt mes fiable que un moviment erratic.

```python
from compare import take_snapshot, session_trajectory

take_snapshot()   # repeteix diverses vegades al llarg del dia
# ...
session_trajectory()   # veu la tendencia de tota la sessio, no nomes de les dues ultimes captures
```

### Vista rapida per decidir en pocs segons (`quick_view()`)

Pensada especificament per fer servir des del mobil quan vols un cop d'ull rapid, sense haver de fer scroll per 35 valors amb detall complet:

```python
from main import quick_view
quick_view()
```

Nomes mostra 1 linia per valor, i nomes els valors que realment val la pena mirar (descarta automaticament EVITAR i biaix mixt/baixista):
```
⚡ IBEX35 — Vista rapida (2 de 35)

1. 🟢 ENTRA ARA BBVA 88  🟢 R:R 3.0:1
2. 🟢 ENTRA ARA SANTANDER 76  🟢 R:R 2.1:1
```

Si algun valor destaca, fes `watch_ticker("NOM", "TICKER.MC")` per veure el detall complet abans de decidir.

### Mode "nomes llarg" (compra)

`config.LONG_ONLY_MODE = True` (activat per defecte): els valors amb biaix tecnic baixista es filtren automaticament fora del rànquing principal, ja que no son operatius per algu que nomes opera a l'alça. Apareixen nomes com a nota de transparencia al peu de l'informe, no s'amaguen del tot.

### Historial de resultats persistent (`track_record.py`)

**Problema que resol**: fins ara, no hi havia manera de saber si el sistema encerta o no al llarg del temps. Aquest modul guarda un CSV a Google Drive amb cada tanda de picks i, mes tard, avalua automaticament com els ha anat.

**Nomes cal muntar Drive un cop per sessio** (et demanara autoritzar amb el teu compte de Google):
```python
from track_record import mount_drive
mount_drive()
```

A partir d'aqui, `closing_scan()` ja registra automaticament els picks (`log_to_drive=True` per defecte). Per consultar l'historial acumulat:
```python
from track_record import evaluate_pending, summary_stats
evaluate_pending()   # actualitza els resultats dels picks de dies anteriors (compara amb el preu actual)
summary_stats()      # win rate, retorn mitja, etc.
```

Com que es guarda a Drive (no al disc temporal de Colab), **persisteix entre sessions** — no cal tornar a pujar-lo cada vegada com els fitxers `.py`.

### Repartiment de capital ajustat per risc (`EOD_ALLOCATION_METHOD`)

Per defecte (`config.EOD_ALLOCATION_METHOD = "RISK_ADJUSTED"`), el repartiment de capital entre els candidats de `closing_scan()` ja no es fa nomes proporcional al Final Score, sino a **Final Score / risc en % del preu**. Aixo vol dir que, entre dos candidats amb el mateix score, el que tingui un stop mes ajustat (menys risc) rep MES capital — l'objectiu es que el risc EN EUROS assumit sigui similar a cada posicio, no nomes repartir "qui te el score mes alt" (filosofia risc parity). Es pot tornar al metode antic amb `EOD_ALLOCATION_METHOD = "SCORE"`.

### Confirmació del matí (`morning_confirmation`)

**Important**: Colab no recorda res d'una sessió a l'altra (es reinicia cada nit), així que `closing_scan()` no es converteix sol en picks de demà al matí. La solució és aquesta funció, que revalida en un sol pas els candidats d'ahir amb dades FRESQUES d'avui:

```python
from main import morning_confirmation
morning_confirmation(
    tickers=["BBVA.MC", "IBE.MC", "ITX.MC"],
    names=["BBVA", "IBERDROLA", "INDITEX"],
    capital=10000
)
```

`closing_scan()` ja et dona aquesta línia feta a punt per copiar, al final del seu informe.

**Què fa**: torna a analitzar només aquests 3 tickers (ràpid, no torna a escanejar les 35 empreses) amb el VWAP i l'ORB ja formats a l'hora que ho executis (p.ex. 9:30). Si algun ha girat baixista durant la nit (gap advers, notícia negativa...) el descarta automàticament i explica per què, i **reparteix el capital de nou només entre els que encara compleixen** els criteris.

### Analisi de tancament amb repartiment de capital (`closing_report.py`)

Al tancament de sessio, `closing_scan()` analitza totes les accions i proposa un nombre reduit de candidats (per defecte 3) per considerar l'obertura de dema, amb un repartiment de capital entre ells:

```python
from main import closing_scan
closing_scan(n=3, capital=10000.0)
```

**Criteris d'elegibilitat** (tots han de complir-se): biaix NO baixista, sense resultats programats de forma imminent, regim NO lateral caotic, recomanacio COMPRAR o VIGILAR.

**Repartiment de capital**: proporcional al Final Score de cada candidat, amb un pes minim del 15% i maxim del 50% per candidat (evita que un sol valor s'enduguin gairebe tot el capital, i evita assignacions simboliques).

**⚠️ Avisos importants**:
- Aixo NO es un consell financer ni una prediccio: es un calcul mecanic basat unicament en el scoring del motor.
- Els nivells d'avui (VWAP, ORB, stop/objectiu) **NO son valids dema** — el mercat obrira a un preu nou. Cal recalcular-los amb `run()` o `take_snapshot()` a l'obertura, no reutilitzar els d'avui.
- Prioritza senyals amb mes continuitat d'un dia a l'altre (Momentum Score, tancament a prop dels maxims) per sobre de l'Entry Score, que es especific de la sessio d'avui.

### Sistema de doble score: Momentum + Entry (V2)

A petició de l'usuari, el sistema de scoring s'ha reestructurat per separar dues coses que abans es barrejaven:

- **Momentum Score** (60% del Final Score): la probabilitat que el moviment CONTINUÏ. Combina VWAP, ORB, força relativa, règim de mercat, estructura (energia) i notícies.
- **Entry Score** (40% del Final Score): si el PUNT D'ENTRADA actual és bo. Parteix d'una base neutra (50) i hi aplica ajustos:
  - **Risc:Recompensa**: <1:1 → -15, 1-2:1 → -5, 2-3:1 → +5, 3-5:1 → +10, >5:1 → +15
  - **Stretch** (com d'estesa està l'entrada: distància VWAP + distància POC + % del rang diari recorregut): si és molt elevat → -10
  - **Volum**: >2x → +10, 1-2x → +5, <0.6x → -5
  - **Potencial restant** (distància a l'objectiu en múltiples d'ATR): <0.5 ATR → -10 (entrada tardana), 1-2 ATR → +5 (correcte), >2 ATR → +10 (molt recorregut)

Això soluciona el problema classic on dues accions amb el mateix "momentum" (mateixa força/tendència) rebien pràcticament el mateix score encara que una tingués una entrada molt millor que l'altra. Ara es mostren els dos scores per separat a cada acció:
```
1. 🟡 VIGILA'L DE PROP  —  INDITEX  (61/100)
   Momentum 81/100   Entry 30/100
```

### Punt d'entrada (`entry_signal.py`)

A partir d'ara, cada accio de l'informe inclou tambe una linia de **"Punt d'entrada"** que et diu si el moment actual es un bon punt per entrar-hi, no nomes si l'accio esta "forta":

- **RUPTURA**: preu a prop del maxim del dia amb energia accelerant. Pot ser un bon punt d'entrada si ve acompanyat de volum alt.
- **MARGE_RECORREGUT**: preu ja per sobre del VWAP pero encara lluny del maxim del dia — encara hi ha recorregut abans de topar amb el sostre d'avui.
- **SOBREESTES**: preu molt allunyat del VWAP i/o a prop del maxim amb l'energia esgotant-se. Entrar aqui vol dir pagar car i sense impuls fresc.
- **LATERAL**: sense senyal clar en cap sentit.

Tambe es mostra la distancia del preu al VWAP (preu mitja ponderat per volum del dia) i al maxim/minim del dia, mes una **referencia de risc** (VWAP o minim del dia) — no es un consell, nomes un nivell objectiu per situar-te.

Quan fas servir `compare.py` per comparar dues fotos, la taula tambe mostra si la qualitat d'entrada ha canviat entre les dues captures (p.ex. de MARGE_RECORREGUT a SOBREESTES vol dir que ja has perdut el millor moment).

**Important**: aixo no prediu res ni es un consell d'inversio. Nomes descriu, amb dades objectives (VWAP i rang del dia), la posicio del preu en aquest instant.

### Detectar lateral erratic / whipsaw (`regime.py`)

Per casos com Grifols, on l'accio puja, baixa de cop, torna a pujar i et fa saltar el stop abans de fer el moviment de veritat, cada accio ara s'analitza tambe pel seu **regim de mercat**:

- **TENDENCIA**: la majoria del moviment ha anat en la mateixa direccio (Efficiency Ratio alt).
- **LATERAL_TRANQUIL**: sense tendencia clara, pero tampoc soroll excessiu.
- **LATERAL_CAOTIC (whipsaw)**: moltes reversions de direccio i Efficiency Ratio molt baix — exactament el patro que fa saltar stops ajustats sense que la tesi d'entrada fos incorrecta.

Quan una accio esta en `LATERAL_CAOTIC`, el punt d'entrada es marca com **"ALT RISC DE WHIPSAW"** (⚠️) independentment de si el score era alt, i la referencia de risc suggerida s'eixampla automaticament fent servir l'ATR (rang mitja per barra) en lloc d'un nivell ajustat al VWAP o al minim del dia.

### Seguiment dedicat d'un valor concret (`watch_ticker`)

Si vols vigilar de prop un valor concret (p.ex. Grifols) amb tot el detall, encara que no surti al TOP 5 general perque el seu score no sigui prou alt:

```python
from main import watch_ticker
watch_ticker("GRIFOLS", "GRF.MC", market="IBEX35")
```

Aixo et dona el detall complet nomes d'aquest valor: recomanacio, punt d'entrada, VWAP, rang del dia, Efficiency Ratio, nombre de reversions, ATR i la referencia de risc suggerida — sense dependre de si guanya o no el rànquing general d'aquell moment.

### Analitzar diversos mercats alhora

`config.MARKETS_TO_RUN` defineix quins mercats s'analitzen quan crides `run_multi_market()` sense arguments (per defecte `["IBEX35", "NASDAQ"]`). Cada mercat fa servir el seu propi univers d'accions (`config.MARKET_STOCK_UNIVERSES`) i la seva moneda (`config.MARKET_CURRENCY`), de manera que l'informe final mostra els dos blocs seguits, cadascun amb el seu rànquing de COMPRAR/VIGILAR/EVITAR.

### Comparar dues captures en el temps (`compare.py`)

Per no dependre nomes d'una foto fixa, pots capturar l'analisi en dos moments (p.ex. amb 10 minuts de diferencia) i veure com evoluciona cada accio:

```python
from compare import take_snapshot, compare_latest

take_snapshot()      # 1a captura, ara
# ... espera 10 minuts ...
take_snapshot()      # 2a captura
compare_latest()      # taula amb delta de score, preu, volum i canvis de recomanacio
```

`compare_latest(only_changed=True)` nomes mostra les accions on el score s'ha mogut o la recomanacio ha canviat, per centrar-se en el que realment es mou. El text de sortida es net i es pot copiar tal qual a ChatGPT o un altre assistent per demanar una segona opinio. Les snapshots es guarden en memoria durant la sessio de Colab (a `compare.SNAPSHOTS`) i es perden si reinicies el runtime.

## Com funciona el score

Score final = 30% Volum + 30% Força relativa + 20% Notícies + 20% Energia (pesos definits a `config.SCORE_WEIGHTS`, fàcilment ajustables).

- **≥ 75** → COMPRAR
- **55–74** → VIGILAR
- **< 55** → EVITAR

Cada recomanació sempre porta els 4 motius que la justifiquen (mai un score sense explicació).

## Ampliar l'univers o el mercat

- Més accions de l'IBEX: afegeix entrades a `config.STOCK_UNIVERSE`.
- Nou mercat (NASDAQ, SP500, DAX...): afegeix una entrada a `config.MARKET_INDEX_TICKERS` i canvia `ACTIVE_MARKET`.

## Preparat per la Fase 2

L'arquitectura modular (cada peça = un mòdul amb dataclasses d'entrada/sortida clares) permet afegir sense reescriure res:
- Backtesting (nou mòdul que reutilitza `data_loader` + `scoring` sobre dades històriques)
- Estadística / Machine Learning (nou mòdul que consumeix `PriceSnapshot`/`StockReport`)
- Probabilitat de continuació, objectiu de preu, stop-loss, gestió monetària (nous camps a `ScoreBreakdown`/`StockReport`)
- Altres mercats (ja contemplat a `config.py`)

## Notes importants

- Totes les fonts són gratuïtes (yfinance + Google News RSS). Cap API de pagament.
- Si el mercat és tancat o yfinance no retorna dades, els mòduls es degraden amb gràcia (scores neutres) en lloc de trencar el programa.
- Aquesta és una eina de suport a la decisió, no prediu el futur ni executa ordres.
