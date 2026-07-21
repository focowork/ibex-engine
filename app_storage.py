"""
app_storage.py
===============
Persistencia de l'historial de picks per a l'APP WEB (Streamlit), fent
servir el mateix repositori de GitHub on viu el codi com a "base de
dades" senzilla. Es l'alternativa a track_record.py (que fa servir
Google Drive i nomes funciona dins de Colab).

Com funciona:
    1. Streamlit Cloud clona el repositori de GitHub per executar l'app;
       aixi que el checkout local JA es el repositori git.
    2. Quan es registren picks nous, s'escriu/actualitza el CSV local
       (dins d'aquest checkout) i despres es fa "git commit" + "git push"
       cap al mateix repositori de GitHub, fent servir un token
       d'autenticacio guardat als "Secrets" de Streamlit (mai al codi).

Configuracio necessaria (a Streamlit Cloud -> Settings -> Secrets):

    GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"
    GITHUB_REPO  = "el_teu_usuari/el_teu_repo"

Si aquests secrets no estan configurats, l'app funciona igualment pero
sense guardar res de manera permanent (nomes en memoria de la sessio
actual del navegador).
"""

import csv
import os
import subprocess
from datetime import date
from typing import List, Optional

CSV_FILENAME = "picks_historial.csv"

CSV_FIELDS = [
    "data_pick", "ticker", "nom", "preu_entrada", "stop", "objectiu",
    "capital_assignat_eur", "pct_capital", "final_score", "recomanacio",
    "data_avaluacio", "preu_avaluacio", "resultat", "retorn_pct",
]


def _repo_root() -> str:
    """Retorna la carpeta arrel del repositori (on hi ha aquest fitxer)."""
    return os.path.dirname(os.path.abspath(__file__))


def _csv_path() -> str:
    return os.path.join(_repo_root(), CSV_FILENAME)


def _get_secret(key: str) -> Optional[str]:
    """Llegeix un valor dels Secrets de Streamlit, si estan disponibles.

    Args:
        key: nom del secret (p.ex. "GITHUB_TOKEN").

    Returns:
        El valor, o None si no esta configurat o Streamlit no esta disponible.
    """
    try:
        import streamlit as st
        return st.secrets.get(key)
    except Exception:
        return None


def _git_configured() -> bool:
    """Comprova si tenim les credencials necessaries per fer push a GitHub."""
    return bool(_get_secret("GITHUB_TOKEN") and _get_secret("GITHUB_REPO"))


def _configure_git_remote() -> bool:
    """Configura el remote 'origin' del repositori local amb el token
    d'autenticacio, perque 'git push' funcioni sense demanar contrasenya.

    Returns:
        True si s'ha pogut configurar.
    """
    token = _get_secret("GITHUB_TOKEN")
    repo = _get_secret("GITHUB_REPO")
    if not token or not repo:
        return False

    remote_url = f"https://{token}@github.com/{repo}.git"
    root = _repo_root()
    try:
        subprocess.run(["git", "remote", "set-url", "origin", remote_url], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "app@ibex-engine.local"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "IBEX Engine App"], cwd=root, check=True, capture_output=True)
        return True
    except Exception:
        return False


def _commit_and_push(message: str) -> bool:
    """Fa 'git add' del CSV, 'git commit' i 'git push' cap a GitHub.

    Si no hi ha canvis (el CSV es identic a l'ultim commit), no falla,
    nomes no fa res.

    Args:
        message: missatge del commit.

    Returns:
        True si el push ha anat be (o no calia fer res).
    """
    if not _configure_git_remote():
        return False

    root = _repo_root()
    try:
        subprocess.run(["git", "add", CSV_FILENAME], cwd=root, check=True, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", message], cwd=root, capture_output=True, text=True
        )
        if result.returncode != 0 and "nothing to commit" in (result.stdout + result.stderr):
            return True  # no hi havia res nou a guardar, no es un error
        subprocess.run(
            ["git", "pull", "--rebase", "--autostash"], cwd=root, check=True, capture_output=True
        )
        subprocess.run(["git", "push"], cwd=root, check=True, capture_output=True)
        return True
    except Exception:
        return False


def is_persistent() -> bool:
    """Indica si l'historial es guardara de manera permanent (GitHub
    configurat) o nomes durara la sessio actual del navegador.

    Returns:
        True si GITHUB_TOKEN i GITHUB_REPO estan configurats als Secrets.
    """
    return _git_configured()


def log_picks_to_github(picks: List, allocations: List[float], capital: float) -> str:
    """Registra la tanda de picks d'avui al CSV i el puja a GitHub.

    Args:
        picks: llista de StockReport dels picks triats.
        allocations: import en euros assignat a cada pick (mateix ordre).
        capital: capital total repartit.

    Returns:
        Text de confirmacio (indica si s'ha pogut pujar a GitHub o no).
    """
    if not picks:
        return "Cap pick per registrar."

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

    if _git_configured():
        pushed = _commit_and_push(f"Picks del {date.today().isoformat()}")
        if pushed:
            return f"✅ Registrats {len(picks)} picks i guardats a GitHub."
        return f"⚠️ Registrats {len(picks)} picks localment, pero no s'han pogut pujar a GitHub (revisa els Secrets)."
    return f"Registrats {len(picks)} picks nomes per aquesta sessio (GitHub no configurat als Secrets)."


def read_latest_picks() -> List[dict]:
    """Llegeix la tanda de picks MES RECENT de l'historial (la data mes
    alta present al CSV), per fer servir a la confirmacio del mati sense
    que l'usuari hagi d'introduir res manualment.

    Returns:
        Llista de diccionaris (files del CSV) de la data mes recent, o
        llista buida si no hi ha historial.
    """
    path = _csv_path()
    if not os.path.isfile(path):
        return []

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        return []

    latest_date = max(r["data_pick"] for r in rows)
    return [r for r in rows if r["data_pick"] == latest_date]


def read_all_history() -> List[dict]:
    """Llegeix tot l'historial de picks (totes les dates).

    Returns:
        Llista de diccionaris (totes les files del CSV), o llista buida.
    """
    path = _csv_path()
    if not os.path.isfile(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# POSICIONS OBERTES (position_manager.py)
# ---------------------------------------------------------------------------
POSITIONS_CSV_FILENAME = "positions.csv"

POSITIONS_CSV_FIELDS = [
    "ticker", "nom", "preu_entrada", "accions_inicials", "capital_invertit_eur",
    "stop", "objectiu", "accions_reduides", "oberta_el", "tancada", "tancada_el",
]


def _positions_csv_path() -> str:
    return os.path.join(_repo_root(), POSITIONS_CSV_FILENAME)


def _read_positions_rows() -> List[dict]:
    path = _positions_csv_path()
    if not os.path.isfile(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_positions_rows(rows: List[dict]) -> None:
    path = _positions_csv_path()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=POSITIONS_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def open_position(position) -> str:
    """Guarda una posicio nova al CSV i la puja a GitHub.

    Args:
        position: models.Position ja creada (encara sense reduccions).

    Returns:
        Text de confirmacio.
    """
    rows = _read_positions_rows()
    rows = [r for r in rows if not (r["ticker"] == position.ticker and r["tancada"] != "True")]
    rows.append({
        "ticker": position.ticker,
        "nom": position.display_name,
        "preu_entrada": f"{position.entry_price:.4f}",
        "accions_inicials": str(position.initial_shares),
        "capital_invertit_eur": f"{position.capital_invested:.2f}",
        "stop": f"{position.stop_price:.4f}",
        "objectiu": f"{position.target_price:.4f}",
        "accions_reduides": "0",
        "oberta_el": position.opened_at,
        "tancada": "False",
        "tancada_el": "",
    })
    _write_positions_rows(rows)

    if _git_configured():
        pushed = _commit_and_push(f"Posicio oberta: {position.display_name} el {position.opened_at}")
        if pushed:
            return f"✅ Posicio de {position.display_name} guardada i pujada a GitHub."
        return f"⚠️ Posicio guardada localment, pero no s'ha pogut pujar a GitHub (revisa els Secrets)."
    return f"Posicio de {position.display_name} guardada nomes per aquesta sessio (GitHub no configurat)."


def read_open_positions() -> List[dict]:
    """Retorna nomes les files de posicions encara obertes (no tancades)."""
    return [r for r in _read_positions_rows() if r.get("tancada") != "True"]


def update_position_reduction(ticker: str, new_shares_reduced: int) -> str:
    """Actualitza el nombre d'accions ja reduides d'una posicio oberta.

    Args:
        ticker: identifica la posicio.
        new_shares_reduced: nou total ACUMULAT d'accions reduides.

    Returns:
        Text de confirmacio.
    """
    rows = _read_positions_rows()
    found = False
    for r in rows:
        if r["ticker"] == ticker and r.get("tancada") != "True":
            r["accions_reduides"] = str(new_shares_reduced)
            found = True
    if not found:
        return f"No s'ha trobat cap posicio oberta per {ticker}."
    _write_positions_rows(rows)

    if _git_configured():
        pushed = _commit_and_push(f"Reduccio actualitzada: {ticker} -> {new_shares_reduced} accions")
        if pushed:
            return "✅ Reduccio guardada i pujada a GitHub."
        return "⚠️ Reduccio guardada localment, pero no s'ha pogut pujar a GitHub."
    return "Reduccio guardada nomes per aquesta sessio (GitHub no configurat)."


def close_position(ticker: str) -> str:
    """Marca una posicio com a tancada del tot (venuda o stop executat)."""
    rows = _read_positions_rows()
    found = False
    for r in rows:
        if r["ticker"] == ticker and r.get("tancada") != "True":
            r["tancada"] = "True"
            r["tancada_el"] = date.today().isoformat()
            found = True
    if not found:
        return f"No s'ha trobat cap posicio oberta per {ticker}."
    _write_positions_rows(rows)

    if _git_configured():
        pushed = _commit_and_push(f"Posicio tancada: {ticker} el {date.today().isoformat()}")
        if pushed:
            return "✅ Posicio tancada i guardada a GitHub."
        return "⚠️ Posicio tancada localment, pero no s'ha pogut pujar a GitHub."
    return "Posicio tancada nomes per aquesta sessio (GitHub no configurat)."


def evaluate_and_save(evaluated_rows: List[dict]) -> str:
    """Sobreescriu el CSV amb les files ja avaluades i el puja a GitHub.

    Args:
        evaluated_rows: totes les files (avaluades i pendents), ja
            actualitzades.

    Returns:
        Text de confirmacio.
    """
    path = _csv_path()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(evaluated_rows)

    if _git_configured():
        pushed = _commit_and_push(f"Avaluacio del {date.today().isoformat()}")
        if pushed:
            return "✅ Historial avaluat i guardat a GitHub."
        return "⚠️ Avaluat localment, pero no s'ha pogut pujar a GitHub."
    return "Avaluat nomes per aquesta sessio (GitHub no configurat)."
