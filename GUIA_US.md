# Guia rapida d'us — quan vulguis operar

## 0. Nomes la primera vegada (o si obres un Colab nou)

1. Ves a https://colab.research.google.com i crea un notebook nou, o obre `IBEX_Intraday_Engine.ipynb`.
2. Puja tots els fitxers `.py` + aquesta guia a l'arrel de l'entorn (icona de carpeta a l'esquerra → arrossega'ls).
3. Executa la primera cel·la (instal·lacio):
   ```python
   !pip install yfinance feedparser pandas --quiet
   ```

Aixo nomes cal fer-ho un cop per cada sessio nova de Colab (si tanques la pestanya o passen moltes hores, el runtime es reinicia i ho hauras de refer).

---

## 1. Quan arribi el moment d'operar (cada dia)

**Pas 1 — Foto general del mercat:**
```python
from main import run_multi_market
run_multi_market()
```
Et dona el TOP 5 d'IBEX35 i de NASDAQ ordenats per score, amb recomanacio COMPRAR/VIGILAR/EVITAR i els 4 motius de cadascuna.

**Pas 2 — Si alguna cosa et crida l'atencio, confirma-ho amb una segona foto:**
```python
from compare import take_snapshot
take_snapshot()
```
Espera entre 5 i 15 minuts (el temps que vulguis) i torna a executar la mateixa cel·la:
```python
take_snapshot()
```

**Pas 3 — Compara les dues fotos:**
```python
from compare import compare_latest
compare_latest()
```
o, per veure nomes el que realment s'ha mogut:
```python
compare_latest(only_changed=True)
```

**Com llegir la comparativa:**
- Score puja + volum relatiu puja + recomanacio passa a COMPRAR → la situacio guanya forca, moment mes solid per entrar.
- Score baixa o recomanacio passa a EVITAR → l'oportunitat s'esta refredant, millor no entrar ara.
- Si vols una segona opinio, copia el text que surt de `compare_latest()` i enganxa'l a ChatGPT o un altre assistent.

**Pas 4 — Repeteix durant la sessio:** torna a fer `take_snapshot()` cada 10-15 min (09:45, 11:30, 16:00...) tantes vegades com vulguis; totes les fotos queden guardades a `compare.SNAPSHOTS` durant la sessio.

---

## 2. Ajustos habituals (nomes si els necessites)

| Vull... | On ho canvio |
|---|---|
| Afegir/treure una accio | `config.py` → `IBEX_STOCK_UNIVERSE` o `NASDAQ_STOCK_UNIVERSE` |
| Analitzar nomes un mercat | `run(market="NASDAQ")` o `run(market="IBEX35")` |
| Canviar quants resultats es mostren | `config.py` → `TOP_N_RESULTS` |
| Ser mes/menys exigent amb el score | `config.py` → `THRESHOLD_BUY` / `THRESHOLD_WATCH` |
| Canviar el pes de cada factor del score | `config.py` → `WEIGHT_VOLUME`, `WEIGHT_RELATIVE_STRENGTH`, `WEIGHT_NEWS`, `WEIGHT_ENERGY` |

---

## 3. Recordatoris importants

- Aquesta eina **no prediu res**: nomes fotografia la situacio real en el moment exacte que l'executes.
- Si el mercat esta tancat o yfinance no respon, els mòduls es degraden amb gracia (score neutre) en lloc de trencar-se.
- No es un bot: no executa ordres ni compra/ven res. Nomes t'ajuda a decidir amb dades.
- Les captures de `compare.py` es perden si reinicies el runtime de Colab; si vols conservar-les entre sessions, hauries de desar-les manualment (per exemple amb `print()` i copiant el text).
