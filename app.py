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

from datetime import date

import streamlit as st

import main
import closing_report as closing_report_module
import app_storage
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

    .eng-note {
        padding: 12px 14px; background: var(--surface); border: 1px solid var(--border);
        border-left: 3px solid var(--amber); border-radius: 8px; font-size: 11.5px; color: var(--text-dim);
        line-height: 1.5; margin-top: 16px;
    }
    .eng-note.green-accent { border-left-color: var(--green); }
    .eng-note b { color: var(--text); }

    .eng-total-row { display: flex; justify-content: space-between; margin-top: 14px; font-family: var(--mono); font-size: 12px; color: var(--text-dim); }
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
    stripe = _stripe_class_for_bias(r.bias.bias)
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
            </div>{note_html}
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


def screen_quick_view():
    render_header("VISTA RÀPIDA", "Què val la pena mirar ara", "Descarta automàticament EVITAR i biaix mixt/baixista")

    with st.spinner("Analitzant IBEX35..."):
        reports = _cached_analyze_market(ACTIVE_MARKET)

    candidates = [
        r for r in reports
        if r.scores.recommendation != "EVITAR"
        and r.bias.bias not in ("MIXT", "BAIXISTA_CLAR", "BAIXISTA_LLEU")
    ]
    candidates.sort(key=lambda r: r.scores.final_score, reverse=True)
    top = candidates[:8]

    if not top:
        st.info("Cap valor destaca prou ara mateix.")
        return

    for r in top:
        st.markdown(render_stock_card(r), unsafe_allow_html=True)


def screen_closing():
    render_header("TANCAMENT DE SESSIÓ", "On invertir demà", "Candidats seleccionats de les 35 empreses de l'IBEX35")

    col1, col2 = st.columns(2)
    with col1:
        capital = st.number_input("Capital a repartir (€)", min_value=0.0, value=float(EOD_DEFAULT_CAPITAL), step=500.0)
    with col2:
        n = st.number_input("Nombre de candidats", min_value=1, max_value=10, value=EOD_NUM_PICKS)

    if st.button("🔍 Analitzar tancament", use_container_width=True):
        with st.spinner("Analitzant les 35 empreses..."):
            reports = main.analyze_market(market=ACTIVE_MARKET)
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
            index_snapshot = main.data_loader.get_index_snapshot(ACTIVE_MARKET)
            fresh_reports = []
            for row in latest:
                try:
                    fresh_reports.append(main.analyze_stock(row["nom"], row["ticker"], index_snapshot))
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
    render_header("ANÀLISI COMPLETA", "Les 35 empreses de l'IBEX35", "Ordenades per potencial (Final Score)")

    with st.spinner("Analitzant IBEX35..."):
        reports = _cached_analyze_market(ACTIVE_MARKET)

    long_only = [r for r in reports if r.bias.bias not in ("BAIXISTA_CLAR", "BAIXISTA_LLEU")]
    long_only.sort(key=lambda r: r.scores.final_score, reverse=True)

    for r in long_only:
        st.markdown(render_stock_card(r), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# NAVEGACIO
# ---------------------------------------------------------------------------

PAGES = {
    "⚡ Vista ràpida": screen_quick_view,
    "🌙 Tancament": screen_closing,
    "☀️ Confirmació matí": screen_morning,
    "📊 Anàlisi completa": screen_full,
    "📈 Historial": screen_history,
}

page = st.radio("", list(PAGES.keys()), horizontal=True, label_visibility="collapsed")
st.divider()
PAGES[page]()
