"""
app.py
======
App web (Streamlit) de l'IBEX Intraday Decision Engine. Substitueix la
necessitat de fer servir Google Colab: s'obre com qualsevol pagina web,
amb botons en lloc de cel·les de codi.

Reutilitza TOTA la logica d'analisi ja existent (main.py, closing_report.py,
bias.py, etc.) — aquest fitxer nomes s'encarrega de la interficie visual.

Per executar-ho en local (proves):
    streamlit run app.py

Per desplegar-ho gratis:
    1. Puja aquest repositori a GitHub (ja fet si segueixes el README).
    2. Ves a https://streamlit.io/cloud i connecta el teu compte de GitHub.
    3. Crea una app nova apuntant a aquest repositori i a app.py.
    4. (Opcional, per l'historial persistent) A Settings -> Secrets, afegeix:
           GITHUB_TOKEN = "ghp_xxxxxxxxxxxx"
           GITHUB_REPO = "el_teu_usuari/el_teu_repo"
"""

from datetime import date, datetime

import streamlit as st

import main
import closing_report as closing_report_module
import app_storage
import commentary as commentary_module
import position_manager
from models import Position
from config import EOD_DEFAULT_CAPITAL, EOD_NUM_PICKS, ACTIVE_MARKET


# ---------------------------------------------------------------------------
# CONFIGURACIO DE LA PAGINA I ESTIL VISUAL
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="IBEX Engine",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
    :root {
        --bg: #0B0F14;
        --surface: #141A22;
        --surface-2: #1B232D;
        --border: #232D38;
        --text: #E8ECEF;
        --text-dim: #7C8794;
        --green: #3DDC84;
        --red: #FF5C5C;
        --amber: #FFB84D;
        --mono: ui-monospace, "SF Mono", "Cascadia Code", "Consolas", monospace;
    }
    .stApp { background-color: var(--bg); }
    #MainMenu, footer, header { visibility: hidden; }

    .eng-eyebrow {
        font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase;
        color: var(--text-dim); font-family: var(--mono); margin-bottom: 4px;
    }
    .eng-title { font-size: 22px; font-weight: 650; color: var(--text); letter-spacing: -0.01em; }
    .eng-subtitle { font-size: 13px; color: var(--text-dim); margin-top: 4px; margin-bottom: 18px; }

    .eng-capital-block {
        background: linear-gradient(180deg, #17202B 0%, #131A22 100%);
        border: 1px solid var(--border); border-radius: 14px; padding: 18px 20px; margin-bottom: 18px;
    }
    .eng-capital-label { font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px; }
    .eng-capital-amount { font-family: var(--mono); font-size: 32px; font-weight: 600; color: var(--text); letter-spacing: -0.01em; }
    .eng-capital-sub { font-size: 12px; color: var(--text-dim); margin-top: 6px; }

    .eng-card {
        background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
        overflow: hidden; display: flex; margin-bottom: 12px;
    }
    .eng-stripe { width: 5px; flex-shrink: 0; }
    .eng-stripe.green { background: var(--green); }
    .eng-stripe.red { background: var(--red); }
    .eng-stripe.amber { background: var(--amber); }
    .eng-card-body { flex: 1; padding: 14px 16px 16px 16px; }
    .eng-card-top { display: flex; justify-content: space-between; align-items: flex-start; }
    .eng-stock-name { font-size: 16px; font-weight: 650; color: var(--text); }
    .eng-stock-ticker { font-family: var(--mono); font-size: 11px; color: var(--text-dim); margin-top: 2px; }
    .eng-pct-badge { font-family: var(--mono); font-size: 20px; font-weight: 650; text-align: right; }
    .eng-pct-badge.green { color: var(--green); }
    .eng-pct-badge.amber { color: var(--amber); }
    .eng-pct-badge.red { color: var(--red); }
    .eng-euro-amount { font-family: var(--mono); font-size: 13px; color: var(--text-dim); text-align: right; margin-top: 2px; }

    .eng-status-tag { font-family: var(--mono); font-size: 10.5px; font-weight: 650; letter-spacing: 0.04em; padding: 4px 8px; border-radius: 6px; }
    .eng-status-tag.ok { background: rgba(61,220,132,0.14); color: var(--green); }
    .eng-status-tag.out { background: rgba(255,92,92,0.14); color: var(--red); }

    .eng-bar-track { height: 6px; background: var(--surface-2); border-radius: 3px; margin-top: 12px; overflow: hidden; }
    .eng-bar-fill { height: 100%; border-radius: 3px; }
    .eng-bar-fill.green { background: var(--green); }
    .eng-bar-fill.amber { background: var(--amber); }
    .eng-bar-fill.red { background: var(--red); }

    .eng-metrics-row { display: flex; gap: 14px; margin-top: 13px; }
    .eng-metric { flex: 1; }
    .eng-metric-label { font-size: 10px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.06em; }
    .eng-metric-value { font-family: var(--mono); font-size: 14px; margin-top: 2px; font-weight: 600; color: var(--text); }

    .eng-dial-row { display: flex; align-items: center; gap: 8px; margin-top: 13px; padding-top: 12px; border-top: 1px solid var(--border); }
    .eng-dial { width: 34px; height: 18px; position: relative; flex-shrink: 0; }
    .eng-dial-track { width: 34px; height: 4px; background: var(--surface-2); border-radius: 2px; position: absolute; top: 7px; }
    .eng-dial-needle { width: 3px; height: 14px; border-radius: 2px; position: absolute; top: 2px; }
    .eng-dial-needle.green { background: var(--green); left: 26px; }
    .eng-dial-needle.amber { background: var(--amber); left: 15px; }
    .eng-dial-needle.red { background: var(--red); left: 4px; }
    .eng-bias-text { font-size: 12px; color: var(--text-dim); }
    .eng-bias-text b { color: var(--text); }

    .eng-compare-row { display: flex; align-items: center; gap: 10px; margin-top: 12px; font-family: var(--mono); }
    .eng-compare-val { font-size: 13px; color: var(--text-dim); }
    .eng-compare-val.now { font-size: 15px; font-weight: 650; color: var(--text); }
    .eng-compare-val.now.red { color: var(--red); }

    .eng-exclude-reason { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border); font-size: 12px; color: var(--red); }
    .eng-commentary { margin-top: 10px; padding: 10px 12px; border-radius: 8px; background: rgba(255,255,255,0.04); font-size: 13px; line-height: 1.4; color: var(--text); }
    .eng-commentary-time { display: block; margin-top: 6px; font-size: 10px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.04em; }
    .eng-target-line { margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--border); font-size: 12px; color: var(--text-dim); }
    .eng-target-line b { color: var(--text); font-family: var(--mono); }

    .eng-note {
        padding: 12px 14px; background: var(--surface); border: 1px solid var(--border);
        border-left: 3px solid var(--amber); border-radius: 8px; font-size: 11.5px; color: var(--text-dim);
        line-height: 1.5; margin-top: 16px;
    }
    .eng-note.green-accent { border-left-color: var(--green); }
    .eng-note b { color: var(--text); }

    .eng-total-row { display: flex; justify-content: space-between; margin-top: 14px; font-family: var(--mono); font-size: 12px; color: var(--text-dim); }

    .eng-pos-action { margin-top: 10px; padding: 10px 12px; border-radius: 8px; font-size: 13px; line-height: 1.4; }
    .eng-pos-action.green { background: rgba(61,220,132,0.10); color: var(--text); border: 1px solid rgba(61,220,132,0.35); }
    .eng-pos-action.amber { background: rgba(255,184,77,0.10); color: var(--text); border: 1px solid rgba(255,184,77,0.35); }
    .eng-pos-action.red { background: rgba(255,92,92,0.10); color: var(--text); border: 1px solid rgba(255,92,92,0.35); }
    .eng-pos-sub { font-size: 11px; color: var(--text-dim); margin-top: 8px; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# FUNCIONS AUXILIARS DE RENDERITZAT (HTML coherent amb els mockups)
# ---------------------------------------------------------------------------

BIAS_DIAL_CLASS = {
    "ALCISTA_CLAR": "green", "ALCISTA_LLEU": "green",
    "BAIXISTA_CLAR": "red", "BAIXISTA_LLEU": "red",
    "MIXT": "amber",
}
BIAS_LABEL = {
    "ALCISTA_CLAR": "Alcista clar", "ALCISTA_LLEU": "Alcista lleu",
    "BAIXISTA_CLAR": "Baixista clar", "BAIXISTA_LLEU": "Baixista lleu",
    "MIXT": "Senyals contradictoris",
}


def _stripe_class_for_bias(bias_label: str) -> str:
    return BIAS_DIAL_CLASS.get(bias_label, "amber")


_COLOR_TO_CSS_CLASS = {"verd": "green", "vermell": "red", "groc": "amber"}


def _stripe_class_for_report(r) -> str:
    """Color de la targeta basat en la categoria matisada de commentary.py
    (verd nomes si es alcista AMB marge real; groc si esta massa estirat,
    encara que la tendencia de fons sigui alcista)."""
    color = commentary_module.get_color(r)
    return _COLOR_TO_CSS_CLASS.get(color, "amber")


def render_stock_card(r, allocation_eur=None, capital=None, extra_note=None) -> str:
    """Genera l'HTML d'una targeta d'accio, coherent amb el mockup.

    Args:
        r: StockReport.
        allocation_eur: import assignat (opcional, per pantalles amb repartiment).
        capital: capital total (per calcular el %).
        extra_note: text addicional opcional (p.ex. motiu d'exclusio).

    Returns:
        Fragment HTML.
    """
    stripe = _stripe_class_for_report(r)
    dial_class = stripe

    pct_html = ""
    if allocation_eur is not None and capital:
        pct = (allocation_eur / capital) * 100.0
        pct_html = (
            f'<div class="eng-pct-badge {stripe}">{pct:.0f}%</div>'
            f'<div class="eng-euro-amount">{allocation_eur:,.0f} €</div>'
        )

    rr_txt = f"{r.risk_reward.ratio:.1f}:1" if r.risk_reward.quality != "SENSE_DADES" else "n/d"
    risk_pct = (r.risk_reward.risk / r.price.last_price * 100.0) if r.price.last_price else 0.0

    bar_html = ""
    if allocation_eur is not None and capital:
        pct = (allocation_eur / capital) * 100.0
        bar_html = (
            f'<div class="eng-bar-track"><div class="eng-bar-fill {stripe}" style="width:{pct:.0f}%"></div></div>'
        )

    bias_label = BIAS_LABEL.get(r.bias.bias, r.bias.bias)

    note_html = f'<div class="eng-exclude-reason">{extra_note}</div>' if extra_note else ""

    comment_text = commentary_module.generate_commentary(r)
    now_str = datetime.now().strftime("%H:%M")

    target_html = ""
    if r.risk_reward.quality != "SENSE_DADES" and r.risk_reward.target_price and r.price.last_price:
        currency_symbol = "$" if r.ticker.upper() == "SPCX" else "€"
        target_price = r.risk_reward.target_price
        target_pct = (target_price - r.price.last_price) / r.price.last_price * 100.0
        target_html = (
            f'<div class="eng-target-line">🎯 Objectiu aprox: '
            f'<b>{target_price:,.2f} {currency_symbol}</b> '
            f'({target_pct:+.1f}% des d\'ara)</div>'
        )

    comment_html = (
        f'<div class="eng-commentary">{comment_text}{target_html}'
        f'<span class="eng-commentary-time">Actualitzat {now_str} · dades amb ~15 min de retard</span>'
        f'</div>'
    )

    return f"""
    <div class="eng-card">
        <div class="eng-stripe {stripe}"></div>
        <div class="eng-card-body">
            <div class="eng-card-top">
                <div>
                    <div class="eng-stock-name">{r.display_name}</div>
                    <div class="eng-stock-ticker">{r.ticker}</div>
                </div>
                <div>{pct_html}</div>
            </div>{bar_html}
            <div class="eng-metrics-row">
                <div class="eng-metric">
                    <div class="eng-metric-label">Score</div>
                    <div class="eng-metric-value">{r.scores.final_score:.0f}</div>
                </div>
                <div class="eng-metric">
                    <div class="eng-metric-label">R:R</div>
                    <div class="eng-metric-value">{rr_txt}</div>
                </div>
                <div class="eng-metric">
                    <div class="eng-metric-label">Risc</div>
                    <div class="eng-metric-value">{risk_pct:.1f}%</div>
                </div>
            </div>
            <div class="eng-dial-row">
                <div class="eng-dial">
                    <div class="eng-dial-track"></div>
                    <div class="eng-dial-needle {dial_class}"></div>
                </div>
                <div class="eng-bias-text"><b>{bias_label}</b> · {r.bias.bullish_count} senyals a favor</div>
            </div>{comment_html}{note_html}
        </div>
    </div>
    """


def render_header(eyebrow: str, title: str, subtitle: str):
    st.markdown(
        f'<div class="eng-eyebrow">{eyebrow}</div>'
        f'<div class="eng-title">{title}</div>'
        f'<div class="eng-subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# PANTALLES
# ---------------------------------------------------------------------------

@st.cache_data(ttl=120, show_spinner=False)
def _cached_analyze_market(market: str):
    """Cacheja l'analisi 2 minuts perque canviar de pantalla no torni a
    descarregar dades cada vegada."""
    return main.analyze_market(market=market)


@st.cache_data(ttl=120, show_spinner=False)
def _cached_analyze_focused():
    """Cacheja l'analisi combinada de GRIFOLS + SPCX (els unics valors
    que l'usuari vol seguir)."""
    return main.analyze_focused()


def screen_quick_view():
    render_header("VISTA RÀPIDA", "Estat actual", "Grifols (IBEX35) i SpaceX (Nasdaq) — es mostren sempre totes dues")

    with st.spinner("Analitzant Grifols i SpaceX..."):
        reports = _cached_analyze_focused()

    order = {"GRF.MC": 0, "SPCX": 1}
    top = sorted(reports, key=lambda r: order.get(r.ticker.upper(), 99))

    if not top:
        st.info("No s'han pogut obtenir dades ara mateix. Torna-ho a provar en uns minuts.")
        return

    for r in top:
        st.markdown(render_stock_card(r), unsafe_allow_html=True)


def screen_closing():
    render_header("TANCAMENT DE SESSIÓ", "On invertir demà", "Candidats seleccionats entre Grifols i SpaceX")

    col1, col2 = st.columns(2)
    with col1:
        capital = st.number_input("Capital a repartir (€)", min_value=0.0, value=float(EOD_DEFAULT_CAPITAL), step=500.0)
    with col2:
        n = st.number_input("Nombre de candidats", min_value=1, max_value=2, value=min(EOD_NUM_PICKS, 2))

    if st.button("🔍 Analitzar tancament", use_container_width=True):
        with st.spinner("Analitzant Grifols i SpaceX..."):
            reports = main.analyze_focused()
            picks, allocations = closing_report_module.select_and_allocate(reports, n=int(n), capital=capital)

        if not picks:
            st.warning("Cap valor compleix els criteris avui. Millor no forçar cap entrada.")
            return

        st.markdown(
            f'<div class="eng-capital-block">'
            f'<div class="eng-capital-label">Capital a repartir</div>'
            f'<div class="eng-capital-amount">{capital:,.0f} €</div>'
            f'<div class="eng-capital-sub">Repartit per risc · cap posició supera el 50%</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        for r, alloc in zip(picks, allocations):
            st.markdown(render_stock_card(r, allocation_eur=alloc, capital=capital), unsafe_allow_html=True)

        st.markdown(
            f'<div class="eng-total-row"><span>TOTAL REPARTIT</span>'
            f'<span>{sum(allocations):,.0f} € / {capital:,.0f} €</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="eng-note">⚠️ No és consell financer. Confirma cada candidat demà a les 9:30 '
            'amb dades fresques abans d\'entrar-hi.</div>',
            unsafe_allow_html=True,
        )

        msg = app_storage.log_picks_to_github(picks, allocations, capital)
        if "✅" in msg:
            st.success(msg)
        else:
            st.info(msg)


def screen_morning():
    render_header("CONFIRMACIÓ DEL MATÍ", "Segueixen sent vàlids?", "Revisió automàtica dels candidats guardats ahir")

    latest = app_storage.read_latest_picks()
    if not latest:
        st.info("Encara no hi ha cap tanda de picks guardada. Fes primer 'Tancament de sessió'.")
        return

    st.markdown(
        f'<div class="eng-note green-accent">🔄 <b>Carregat automàticament</b> — '
        f'{len(latest)} candidats guardats el {latest[0]["data_pick"]}. No cal que els tornis a escriure.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    if st.button("🔄 Confirmar amb dades d'ara", use_container_width=True):
        with st.spinner("Revalidant amb dades fresques..."):
            # Cada ticker pertany a un mercat diferent (Grifols=IBEX35, SPCX=Nasdaq),
            # aixi que cal l'index de referencia correcte per cadascun.
            index_snapshots = {
                "IBEX35": main.data_loader.get_index_snapshot("IBEX35"),
                "SPCX": main.data_loader.get_index_snapshot("SPCX"),
            }
            fresh_reports = []
            for row in latest:
                market = "SPCX" if row["ticker"].upper() == "SPCX" else "IBEX35"
                try:
                    fresh_reports.append(
                        main.analyze_stock(row["nom"], row["ticker"], index_snapshots[market])
                    )
                except Exception as exc:
                    st.warning(f"No s'ha pogut analitzar {row['nom']}: {exc}")

            capital = sum(float(row["capital_assignat_eur"]) for row in latest)
            still_eligible = [r for r in fresh_reports if closing_report_module.is_eligible(r)]
            no_longer = [r for r in fresh_reports if not closing_report_module.is_eligible(r)]
            allocations = closing_report_module.allocate_capital(still_eligible, capital)

        old_pct_by_ticker = {row["ticker"]: float(row["pct_capital"]) for row in latest}

        for idx, r in enumerate(still_eligible):
            new_alloc = allocations[idx]
            new_pct = (new_alloc / capital * 100.0) if capital else 0.0
            old_pct = old_pct_by_ticker.get(r.ticker, 0.0)
            st.markdown(
                f'<div class="eng-compare-row">'
                f'<span class="eng-compare-val">Ahir {old_pct:.0f}%</span>'
                f'<span class="eng-compare-val">→</span>'
                f'<span class="eng-compare-val now">Ara {new_pct:.0f}%</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown(render_stock_card(r, allocation_eur=new_alloc, capital=capital), unsafe_allow_html=True)

        for r in no_longer:
            motiu = []
            if r.bias.bias in ("BAIXISTA_CLAR", "BAIXISTA_LLEU"):
                motiu.append("ara té biaix baixista")
            if r.upcoming_events.is_imminent:
                motiu.append("resultats imminents")
            if r.regime.regime == "LATERAL_CAOTIC":
                motiu.append("règim lateral caòtic (whipsaw)")
            if r.scores.recommendation == "EVITAR":
                motiu.append("recomanació ara és EVITAR")
            reason = ", ".join(motiu) if motiu else "ja no compleix criteris"
            old_pct = old_pct_by_ticker.get(r.ticker, 0.0)
            st.markdown(
                f'<div class="eng-compare-row">'
                f'<span class="eng-compare-val">Ahir {old_pct:.0f}%</span>'
                f'<span class="eng-compare-val">→</span>'
                f'<span class="eng-compare-val now red">Ara 0%</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown(render_stock_card(r, extra_note=f"⚠ {reason}"), unsafe_allow_html=True)


def screen_history():
    render_header("HISTORIAL", "Com ha anat fins ara", "Track record acumulat de tots els picks")

    if not app_storage.is_persistent():
        st.warning(
            "L'historial persistent no està configurat (falten els Secrets GITHUB_TOKEN i GITHUB_REPO). "
            "Sense això, l'historial nomes dura la sessió actual."
        )

    if st.button("📊 Avaluar picks pendents i actualitzar estadístiques", use_container_width=True):
        with st.spinner("Consultant preus actuals..."):
            rows = app_storage.read_all_history()
            if not rows:
                st.info("Encara no hi ha cap historial guardat.")
                return

            import yfinance as yf
            today_str = date.today().isoformat()
            evaluated_count = 0
            for row in rows:
                if row["data_avaluacio"] or row["data_pick"] == today_str:
                    continue
                try:
                    hist = yf.Ticker(row["ticker"]).history(period="1d")
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
                row["data_avaluacio"] = today_str
                row["preu_avaluacio"] = f"{current_price:.4f}"
                row["resultat"] = resultat
                row["retorn_pct"] = f"{((current_price - entry) / entry * 100.0) if entry else 0.0:.2f}"
                evaluated_count += 1

            msg = app_storage.evaluate_and_save(rows)
            st.info(f"Avaluades {evaluated_count} files noves. {msg}")

    rows = [r for r in app_storage.read_all_history() if r["resultat"]]
    if not rows:
        st.info("Encara no hi ha cap pick avaluat.")
        return

    total = len(rows)
    objectius = sum(1 for r in rows if r["resultat"] == "OBJECTIU")
    stops = sum(1 for r in rows if r["resultat"] == "STOP")
    en_curs = sum(1 for r in rows if r["resultat"] == "EN_CURS")
    retorns = [float(r["retorn_pct"]) for r in rows]
    retorn_mitja = sum(retorns) / len(retorns) if retorns else 0.0
    win_rate = (objectius / (objectius + stops) * 100.0) if (objectius + stops) > 0 else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Win rate", f"{win_rate:.0f}%")
    c2.metric("Retorn mitjà", f"{retorn_mitja:+.1f}%")
    c3.metric("Picks avaluats", total)

    st.caption(f"🎯 {objectius} objectiu · 🛑 {stops} stop · ⏳ {en_curs} en curs")
    st.caption("Nota: no és una garantia de resultats futurs.")


def screen_full():
    render_header("ANÀLISI COMPLETA", "Grifols i SpaceX", "Comparativa completa dels dos valors, sense filtrar cap")

    with st.spinner("Analitzant Grifols i SpaceX..."):
        reports = _cached_analyze_focused()

    order = {"GRF.MC": 0, "SPCX": 1}
    long_only = sorted(reports, key=lambda r: order.get(r.ticker.upper(), 99))

    for r in long_only:
        st.markdown(render_stock_card(r), unsafe_allow_html=True)


_ACTION_TO_STRIPE = {
    "MANTENIR": None,          # es decideix segons move_pct (verd si a favor, ambre si en contra)
    "REDUIR": "red",
    "TANCAR_STOP": "red",
    "RECOLLIR_BENEFICI": "green",
    "OBJECTIU_ASSOLIT": "green",
    "TANCADA": "amber",
}


def _position_stripe_class(status) -> str:
    stripe = _ACTION_TO_STRIPE.get(status.action)
    if stripe is not None:
        return stripe
    return "green" if status.move_pct >= 0 else "amber"


def render_position_card(row: dict, status, currency_symbol: str) -> str:
    """Genera l'HTML de la targeta d'una posicio oberta, amb el P&L en
    temps real i la recomanacio d'accio (reduir/mantenir/tancar/recollir).
    """
    stripe = _position_stripe_class(status)
    pnl_class = "green" if status.pnl_eur >= 0 else "red"

    action_html = (
        f'<div class="eng-pos-action {stripe}">{status.recommendation_text}</div>'
    )

    return f"""
    <div class="eng-card">
        <div class="eng-stripe {stripe}"></div>
        <div class="eng-card-body">
            <div class="eng-card-top">
                <div>
                    <div class="eng-stock-name">{row['nom']}</div>
                    <div class="eng-stock-ticker">{row['ticker']} · {status.shares_remaining} accions actives</div>
                </div>
                <div>
                    <div class="eng-pct-badge {pnl_class}">{status.pnl_pct:+.1f}%</div>
                    <div class="eng-euro-amount">{status.pnl_eur:+,.0f} {currency_symbol}</div>
                </div>
            </div>
            <div class="eng-metrics-row">
                <div class="eng-metric">
                    <div class="eng-metric-label">Preu ara</div>
                    <div class="eng-metric-value">{status.current_price:,.2f} {currency_symbol}</div>
                </div>
                <div class="eng-metric">
                    <div class="eng-metric-label">Dist. stop</div>
                    <div class="eng-metric-value">{status.distance_to_stop_pct:.1f}%</div>
                </div>
                <div class="eng-metric">
                    <div class="eng-metric-label">Dist. objectiu</div>
                    <div class="eng-metric-value">{status.distance_to_target_pct:.1f}%</div>
                </div>
            </div>{action_html}
            <div class="eng-pos-sub">Entrada a {float(row['preu_entrada']):,.2f} {currency_symbol} · stop {float(row['stop']):,.2f} · objectiu {float(row['objectiu']):,.2f}</div>
        </div>
    </div>
    """


def _currency_for_ticker(ticker: str) -> str:
    return "$" if ticker.upper() == "SPCX" else "€"


def screen_position():
    render_header("GESTIÓ DE POSICIÓ", "On sóc ara mateix", "Capital ja invertit a Grifols i/o SpaceX: P&L en temps real i quan toca reduir o recollir benefici")

    with st.spinner("Consultant preus actuals..."):
        reports = _cached_analyze_focused()
    reports_by_ticker = {r.ticker.upper(): r for r in reports}

    open_rows = app_storage.read_open_positions()

    if open_rows:
        st.markdown("#### Posicions obertes")
        for row in open_rows:
            ticker = row["ticker"]
            position = Position(
                ticker=ticker,
                display_name=row["nom"],
                entry_price=float(row["preu_entrada"]),
                initial_shares=int(row["accions_inicials"]),
                capital_invested=float(row["capital_invertit_eur"]),
                stop_price=float(row["stop"]),
                target_price=float(row["objectiu"]),
                shares_reduced=int(row["accions_reduides"]),
                opened_at=row["oberta_el"],
            )
            report = reports_by_ticker.get(ticker.upper())
            if report is None:
                st.warning(f"No s'ha pogut obtenir el preu actual de {row['nom']} ara mateix.")
                continue

            status = position_manager.evaluate_position(position, report.price.last_price)
            currency_symbol = _currency_for_ticker(ticker)
            st.markdown(render_position_card(row, status, currency_symbol), unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if status.shares_to_act_now > 0 and st.button(
                    f"✅ Aplicar reducció ({status.shares_to_act_now} accions)", key=f"reduce_{ticker}", use_container_width=True
                ):
                    new_total = position.shares_reduced + status.shares_to_act_now
                    msg = app_storage.update_position_reduction(ticker, new_total)
                    st.success(msg) if "✅" in msg else st.info(msg)
                    st.rerun()
            with col2:
                if st.button("🔒 Tancar posició del tot", key=f"close_{ticker}", use_container_width=True):
                    msg = app_storage.close_position(ticker)
                    st.success(msg) if "✅" in msg else st.info(msg)
                    st.rerun()

            with st.expander(f"✏️ Editar aquesta posició ({row['nom']})"):
                with st.form(f"edit_position_form_{ticker}"):
                    edit_entry = st.number_input(
                        f"Preu de compra ({currency_symbol})", min_value=0.01,
                        value=position.entry_price, step=0.01, format="%.2f", key=f"edit_entry_{ticker}",
                    )
                    edit_shares_initial = st.number_input(
                        "Accions inicials", min_value=1, value=position.initial_shares, step=1, key=f"edit_shares_{ticker}",
                    )
                    edit_shares_reduced = st.number_input(
                        "Accions ja reduides", min_value=0, value=position.shares_reduced, step=1, key=f"edit_reduced_{ticker}",
                    )
                    edit_stop = st.number_input(
                        f"Stop ({currency_symbol})", min_value=0.0, value=position.stop_price, step=0.01, format="%.2f", key=f"edit_stop_{ticker}",
                    )
                    edit_target = st.number_input(
                        f"Objectiu ({currency_symbol})", min_value=0.0, value=position.target_price, step=0.01, format="%.2f", key=f"edit_target_{ticker}",
                    )
                    edit_submitted = st.form_submit_button("💾 Guardar canvis", use_container_width=True)
                    if edit_submitted:
                        if edit_shares_reduced > edit_shares_initial:
                            st.error("Les accions ja reduïdes no poden superar les accions inicials.")
                        elif edit_stop >= edit_entry:
                            st.error("El stop ha de quedar per SOTA del preu de compra (només operes a l'alça).")
                        elif edit_target <= edit_entry:
                            st.error("L'objectiu ha de quedar per SOBRE del preu de compra (només operes a l'alça).")
                        else:
                            msg = app_storage.edit_position(ticker, {
                                "preu_entrada": edit_entry,
                                "accions_inicials": edit_shares_initial,
                                "accions_reduides": edit_shares_reduced,
                                "capital_invertit_eur": edit_entry * edit_shares_initial,
                                "stop": edit_stop,
                                "objectiu": edit_target,
                            })
                            st.success(msg) if "✅" in msg else st.info(msg)
                            st.rerun()

            with st.expander(f"✏️ Editar dades de {row['nom']}"):
                with st.form(f"edit_position_form_{ticker}"):
                    edit_entry = st.number_input(
                        f"Preu de compra ({currency_symbol})", min_value=0.01,
                        value=position.entry_price, step=0.01, format="%.2f", key=f"edit_entry_{ticker}",
                    )
                    edit_stop = st.number_input(
                        f"Stop ({currency_symbol})", min_value=0.0,
                        value=position.stop_price, step=0.01, format="%.2f", key=f"edit_stop_{ticker}",
                    )
                    edit_target = st.number_input(
                        f"Objectiu ({currency_symbol})", min_value=0.0,
                        value=position.target_price, step=0.01, format="%.2f", key=f"edit_target_{ticker}",
                    )
                    edit_capital = st.number_input(
                        f"Capital invertit ({currency_symbol})", min_value=0.0,
                        value=position.capital_invested, step=100.0, key=f"edit_capital_{ticker}",
                    )
                    edit_submitted = st.form_submit_button("💾 Guardar correcció", use_container_width=True)
                    if edit_submitted:
                        if edit_stop >= edit_entry:
                            st.error("El stop ha de quedar per SOTA del preu de compra (només operes a l'alça).")
                        elif edit_target <= edit_entry:
                            st.error("L'objectiu ha de quedar per SOBRE del preu de compra (només operes a l'alça).")
                        else:
                            msg = app_storage.update_position_details(
                                ticker, entry_price=edit_entry, stop=edit_stop,
                                target=edit_target, capital_invested=edit_capital,
                            )
                            st.success(msg) if "✅" in msg else st.info(msg)
                            st.rerun()
        st.divider()
    else:
        st.info("Encara no tens cap posició oberta registrada.")

    open_tickers = {row["ticker"].upper() for row in open_rows}
    available = [r for r in reports if r.ticker.upper() not in open_tickers]

    if available:
        st.markdown("#### Obrir una posició nova")
        options = {f"{r.display_name} ({r.ticker})": r for r in available}
        choice_label = st.selectbox("Valor", list(options.keys()), key="new_pos_ticker")
        chosen = options[choice_label]
        currency_symbol = _currency_for_ticker(chosen.ticker)
        current_price = chosen.price.last_price

        capital = st.number_input(f"Capital invertit ({currency_symbol})", min_value=0.0, step=100.0, key="new_pos_capital")
        entry_price_input = st.number_input(
            f"Preu de compra ({currency_symbol})", min_value=0.01,
            value=float(current_price) if current_price else 1.0,
            step=0.01, format="%.2f", key="new_pos_entry_price",
            help="Per defecte el preu actual de mercat. Canvia'l si la teva compra real va ser a un altre preu.",
        )
        shares = int(capital // entry_price_input) if entry_price_input > 0 else 0
        capital_realment_invertit = shares * entry_price_input
        if capital > 0:
            st.caption(
                f"📐 Accions calculades: **{shares}** ({capital:,.2f} ÷ {entry_price_input:,.2f}, arrodonit a la baixa). "
                f"Capital realment desplegat: {capital_realment_invertit:,.2f} {currency_symbol} "
                f"(sobrant: {capital - capital_realment_invertit:,.2f} {currency_symbol})."
            )

        # Nomes operem a l'alça (LONG_ONLY_MODE): el stop SEMPRE ha de quedar per
        # sota del preu de compra i l'objectiu SEMPRE per sobre, independentment
        # d'on apuntin els nivells tecnics bruts del motor en aquest moment.
        atr_fallback = chosen.regime.atr if chosen.regime.atr > 0 else current_price * 0.015
        engine_stop = chosen.risk_reward.stop_price
        engine_target = chosen.risk_reward.target_price
        stop_from_engine_ok = chosen.risk_reward.quality != "SENSE_DADES" and 0 < engine_stop < current_price
        target_from_engine_ok = chosen.risk_reward.quality != "SENSE_DADES" and engine_target > current_price

        default_stop = engine_stop if stop_from_engine_ok else max(0.01, current_price - atr_fallback)
        default_target = engine_target if target_from_engine_ok else current_price + atr_fallback * 2

        if not target_from_engine_ok:
            st.markdown(
                '<div class="eng-note">⚠️ Ara mateix el biaix tècnic d\'aquest valor apunta a la baixa '
                "(l'objectiu del motor quedaria per sota del preu actual). Com que només operes a l'alça, "
                "s'ha suggerit un objectiu alternatiu basat en l'ATR — revisa'l bé abans de guardar, o "
                "espera que el biaix es giri alcista abans d'entrar-hi.</div>",
                unsafe_allow_html=True,
            )

        with st.form("new_position_form"):
            st.caption("Suggerits pel motor a partir de l'anàlisi tècnica actual — es poden ajustar abans de guardar.")
            stop = st.number_input(f"Stop ({currency_symbol})", min_value=0.0, value=float(default_stop), step=0.01, format="%.2f")
            target = st.number_input(f"Objectiu ({currency_symbol})", min_value=0.0, value=float(default_target), step=0.01, format="%.2f")

            submitted = st.form_submit_button("💾 Guardar posició", use_container_width=True)
            if submitted:
                if capital <= 0 or shares <= 0:
                    st.error("Cal indicar un capital invertit suficient per comprar com a mínim 1 acció al preu de compra indicat.")
                elif stop >= entry_price_input:
                    st.error("El stop ha de quedar per SOTA del preu de compra (només operes a l'alça).")
                elif target <= entry_price_input:
                    st.error("L'objectiu ha de quedar per SOBRE del preu de compra (només operes a l'alça).")
                else:
                    position = Position(
                        ticker=chosen.ticker,
                        display_name=chosen.display_name,
                        entry_price=entry_price_input,
                        initial_shares=int(shares),
                        capital_invested=capital_realment_invertit,
                        stop_price=stop,
                        target_price=target,
                        opened_at=date.today().isoformat(),
                    )
                    msg = app_storage.open_position(position)
                    st.success(msg) if "✅" in msg else st.info(msg)
                    st.rerun()

    st.markdown(
        '<div class="eng-note">⚠️ Els trams de reducció i presa de beneficis (config.py) són regles '
        "mecàniques i transparents, no consell financer ni una predicció. Sempre és l'usuari qui "
        "decideix i executa cada operació al seu broker.</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# NAVEGACIO
# ---------------------------------------------------------------------------

PAGES = {
    "⚡ Vista ràpida": screen_quick_view,
    "🌙 Tancament": screen_closing,
    "☀️ Confirmació matí": screen_morning,
    "📍 Posició": screen_position,
    "📊 Anàlisi completa": screen_full,
    "📈 Historial": screen_history,
}

page = st.radio("", list(PAGES.keys()), horizontal=True, label_visibility="collapsed")
st.divider()
PAGES[page]()
