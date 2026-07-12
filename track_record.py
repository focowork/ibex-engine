"""
track_record.py
================
Guarda un historial PERSISTENT (a Google Drive) de cada tanda de picks
generada per closing_scan(), i permet avaluar mes tard com els ha anat
comparant el preu registrat amb el preu actual i els nivells de
stop/objectiu d'aquell dia.

Aixo permet saber, amb dades reals acumulades al llarg de setmanes, si
el sistema te un edge real o no -- en lloc de confiar nomes en l'opinio
d'un sol dia.

*** COM FER-LO SERVIR ***

Nomes cal muntar Google Drive UN COP per sessio de Colab:

    from track_record import mount_drive
    mount_drive()

A partir d'aqui, l'historial es guarda automaticament cada vegada que
fas closing_scan(log_to_drive=True) (per defecte). Per consultar-lo:

    from track_record import evaluate_pending, summary_stats
    evaluate_pending()   # actualitza els resultats dels picks de dies anteriors
    summary_stats()      # mostra les estadistiques acumulades

Els fitxers es guarden a config.TRACK_RECORD_DRIVE_PATH, aixi que
PERSISTEIXEN entre sessions de Colab (a diferencia dels moduls .py, que
cal tornar a pujar cada vegada que es reinicia el runtime).
"""

import csv
import os
from datetime import date
from typing import List

from config import TRACK_RECORD_DRIVE_PATH, TRACK_RECORD_FILENAME
from models import StockReport


CSV_FIELDS = [
    "data_pick", "ticker", "nom", "preu_entrada", "stop", "objectiu",
    "capital_assignat_eur", "pct_capital", "final_score", "recomanacio",
    "data_avaluacio", "preu_avaluacio", "resultat", "retorn_pct",
]


def mount_drive() -> bool:
    """Munta Google Drive a l'entorn de Colab, si encara no ho esta, i
    crea la carpeta de l'historial si no existeix.

    Nomes cal fer-ho un cop per sessio de Colab (et demanara autoritzar
    l'acces amb el teu compte de Google la primera vegada).

    Returns:
        True si s'ha muntat correctament (o ja ho estava), False si
        no es pot muntar (p.ex. no estem realment a Colab).
    """
    try:
        from google.colab import drive
        drive.mount("/content/drive", force_remount=False)
        os.makedirs(TRACK_RECORD_DRIVE_PATH, exist_ok=True)
        print(f"[track_record] Google Drive muntat. Historial a: {TRACK_RECORD_DRIVE_PATH}")
        return True
    except Exception as exc:
        print(
            f"[track_record] No s'ha pogut muntar Google Drive ({exc}). "
            "Nomes funciona dins de Google Colab."
        )
        return False


def _csv_path() -> str:
    return os.path.join(TRACK_RECORD_DRIVE_PATH, TRACK_RECORD_FILENAME)


def _drive_available() -> bool:
    return os.path.isdir(TRACK_RECORD_DRIVE_PATH) or os.path.isdir("/content/drive")


def log_picks(picks: List[StockReport], allocations: List[float], capital: float) -> str:
    """Registra la tanda de picks d'avui al CSV historic (n'afegeix files
    noves; no sobreescriu les anteriors).

    Args:
        picks: llista de StockReport dels picks triats.
        allocations: import en euros assignat a cada pick (mateix ordre).
        capital: capital total repartit.

    Returns:
        Text de confirmacio (o avis si Drive no esta muntat).
    """
    if not picks:
        return "[track_record] Cap pick per registrar."

    try:
        os.makedirs(TRACK_RECORD_DRIVE_PATH, exist_ok=True)
    except Exception as exc:
        return f"[track_record] No s'ha pogut escriure a Drive ({exc}). Fes mount_drive() primer."

    path = _csv_path()
    file_exists = os.path.isfile(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        today = date.today().isoformat()
        for r, alloc in zip(picks, allocations):
            pct = (alloc / capital * 100.0) if capital else 0.0
            writer.writerow({
                "data_pick": today,
                "ticker": r.ticker,
                "nom": r.display_name,
                "preu_entrada": f"{r.price.last_price:.4f}",
                "stop": f"{r.risk_reward.stop_price:.4f}",
                "objectiu": f"{r.risk_reward.target_price:.4f}",
                "capital_assignat_eur": f"{alloc:.2f}",
                "pct_capital": f"{pct:.1f}",
                "final_score": f"{r.scores.final_score:.1f}",
                "recomanacio": r.scores.recommendation,
                "data_avaluacio": "",
                "preu_avaluacio": "",
                "resultat": "",
                "retorn_pct": "",
            })

    return f"[track_record] Registrats {len(picks)} picks de {today} a {path}"


def evaluate_pending() -> str:
    """Recorre el CSV historic i avalua les files pendents (sense
    data_avaluacio, i que no siguin d'avui mateix) comparant el preu
    registrat amb el preu ACTUAL de mercat.

    Marca 'resultat' com OBJECTIU (preu actual >= objectiu), STOP (preu
    actual <= stop), o EN_CURS (encara dins el rang entre tots dos).

    Returns:
        Text amb el resum de l'avaluacio.
    """
    path = _csv_path()
    if not os.path.isfile(path):
        return "[track_record] Encara no hi ha cap historial guardat (fes closing_scan() amb log_to_drive=True primer)."

    import yfinance as yf

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    evaluated_count = 0
    today_str = date.today().isoformat()

    for row in rows:
        if row["data_avaluacio"]:
            continue  # ja avaluada
        if row["data_pick"] == today_str:
            continue  # es d'avui mateix, encara no te sentit avaluar-la

        try:
            ticker_data = yf.Ticker(row["ticker"])
            hist = ticker_data.history(period="1d")
            if hist.empty:
                continue
            current_price = float(hist["Close"].iloc[-1])
        except Exception:
            continue

        entry = float(row["preu_entrada"])
        stop = float(row["stop"])
        target = float(row["objectiu"])

        if current_price >= target:
            resultat = "OBJECTIU"
        elif current_price <= stop:
            resultat = "STOP"
        else:
            resultat = "EN_CURS"

        retorn_pct = ((current_price - entry) / entry) * 100.0 if entry else 0.0

        row["data_avaluacio"] = today_str
        row["preu_avaluacio"] = f"{current_price:.4f}"
        row["resultat"] = resultat
        row["retorn_pct"] = f"{retorn_pct:.2f}"
        evaluated_count += 1

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    msg = f"[track_record] Avaluades {evaluated_count} files noves."
    print(msg)
    return msg


def summary_stats() -> str:
    """Calcula estadistiques agregades de tot l'historial ja avaluat.

    Returns:
        Text amb el resum (nombre de picks, win rate, retorn mitja...).
    """
    path = _csv_path()
    if not os.path.isfile(path):
        msg = "[track_record] Encara no hi ha cap historial guardat."
        print(msg)
        return msg

    with open(path, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["resultat"]]

    if not rows:
        msg = "[track_record] Encara no hi ha cap pick avaluat (fes evaluate_pending() primer)."
        print(msg)
        return msg

    total = len(rows)
    objectius = sum(1 for r in rows if r["resultat"] == "OBJECTIU")
    stops = sum(1 for r in rows if r["resultat"] == "STOP")
    en_curs = sum(1 for r in rows if r["resultat"] == "EN_CURS")
    retorns = [float(r["retorn_pct"]) for r in rows]
    retorn_mitja = sum(retorns) / len(retorns) if retorns else 0.0
    win_rate = (objectius / (objectius + stops) * 100.0) if (objectius + stops) > 0 else 0.0

    lines = []
    lines.append("=" * 42)
    lines.append("HISTORIAL DE RESULTATS (TRACK RECORD)")
    lines.append("=" * 42)
    lines.append(f"Total de picks avaluats: {total}")
    lines.append(f"  Objectiu assolit: {objectius}")
    lines.append(f"  Stop tocat: {stops}")
    lines.append(f"  Encara en curs: {en_curs}")
    lines.append(f"Win rate (objectiu vs stop, sense comptar en curs): {win_rate:.1f}%")
    lines.append(f"Retorn mitja per pick: {retorn_mitja:+.2f}%")
    lines.append("=" * 42)
    lines.append(
        "Nota: aixo NO es una garantia de resultats futurs. Com mes picks "
        "acumulis a l'historial, mes fiable sera aquesta estadistica."
    )

    rendered = "\n".join(lines)
    print(rendered)
    return rendered
