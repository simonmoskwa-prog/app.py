import base64
import datetime
import hashlib
import json
import os
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
import yfinance as yf

# ---------------------------------------------------------
# 1. PAGE CONFIG (Muss ganz oben stehen)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Stage-Analysis RS Dashboard | Pulse Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# 2. HASHING & SICHERHEIT
# ---------------------------------------------------------
USERS_FILE = "users.json"


def get_salt() -> str:
    """Holt einen optionalen Salt aus den Streamlit Secrets."""
    if "SECRET_SALT" in st.secrets:
        return str(st.secrets["SECRET_SALT"])
    return ""


def hash_password(password: str) -> str:
    """Erstellt einen salted SHA-256 Hash für ein Passwort."""
    salted_pwd = password + get_salt()
    return hashlib.sha256(salted_pwd.encode("utf-8")).hexdigest()


# ---------------------------------------------------------
# 3. BENUTZER-VERWALTUNG
# ---------------------------------------------------------
def load_users():
    """Lädt Benutzer aus Secrets und optional aus der lokalen users.json."""
    users_db = {}

    # 1. Aus Streamlit Secrets laden (Empfohlen)
    if "users" in st.secrets and "passwords" in st.secrets:
        for u_key, info in st.secrets["users"].items():
            u_key_clean = str(u_key).strip().lower()
            raw_pwd = st.secrets["passwords"].get(u_key, "")

            users_db[u_key_clean] = {
                "password": hash_password(str(raw_pwd)),
                "display_name": info.get("display_name", u_key_clean.capitalize()),
                "welcome_msg": info.get(
                    "welcome_msg", f"Willkommen {u_key_clean.capitalize()}"
                ),
                "role": info.get("role", "user"),
            }

    # 2. Ergänzend aus lokaler JSON-Datei laden (falls manuell Benutzer angelegt wurden)
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                json_users = json.load(f)
                users_db.update(json_users)
        except Exception:
            pass

    # 3. Falls noch keine Datenbank existiert, Fallback über Secrets prüfen
    if not users_db and "ADMIN_PASSWORD" in st.secrets:
        users_db["admin"] = {
            "password": hash_password(str(st.secrets["ADMIN_PASSWORD"])),
            "display_name": "Admin",
            "welcome_msg": "Willkommen Admin",
            "role": "admin",
        }

    return users_db


def save_users(users_dict):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_dict, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.warning(
            f"Benutzerdaten konnten nicht lokal gespeichert werden (z. B. Read-Only Cloud): {e}"
        )


if "users_db" not in st.session_state:
    st.session_state["users_db"] = load_users()

# ---------------------------------------------------------
# 4. AUTHENTICATION & LOGIN SCREEN
# ---------------------------------------------------------
for key, default in [
    ("authenticated", False),
    ("username", ""),
    ("user_key", ""),
    ("role", "user"),
    ("welcome_msg", ""),
    ("selected_stock", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def render_login_screen():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.write("")
        st.write("")
        with st.container(border=True):
            st.markdown("### 🔐 Pulse Trading Login")
            st.caption(
                "Bitte Zugangsdaten eingeben, um auf das Dashboard zuzugreifen."
            )

            with st.form("login_form"):
                user_input = (
                    st.text_input("Benutzername", key="login_user")
                    .strip()
                    .lower()
                )
                pwd_input = st.text_input(
                    "Passwort", type="password", key="login_pwd"
                )
                login_btn = st.form_submit_button(
                    "Anmelden", use_container_width=True
                )

                if login_btn:
                    users = st.session_state["users_db"]
                    if (
                        user_input in users
                        and users[user_input]["password"]
                        == hash_password(pwd_input)
                    ):
                        st.session_state["authenticated"] = True
                        st.session_state["user_key"] = user_input
                        st.session_state["username"] = users[user_input][
                            "display_name"
                        ]
                        st.session_state["role"] = users[user_input].get(
                            "role", "user"
                        )
                        st.session_state["welcome_msg"] = users[user_input][
                            "welcome_msg"
                        ]
                        st.success(
                            f"Anmeldung erfolgreich: {st.session_state['welcome_msg']}!"
                        )
                        st.rerun()
                    else:
                        st.error("Ungültiger Benutzername oder Passwort.")


if not st.session_state["authenticated"]:
    render_login_screen()
    st.stop()


# ---------------------------------------------------------
# 5. HELPER & TRADING LOGIK
# ---------------------------------------------------------
def is_market_open(ticker: str) -> bool:
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    berlin_tz = ZoneInfo("Europe/Berlin")
    ny_tz = ZoneInfo("America/New_York")

    now_berlin = now_utc.astimezone(berlin_tz)
    now_ny = now_utc.astimezone(ny_tz)

    eu_identifiers = ["GDAXI", "STOXX", "DE", "STX", "WA", "PA", "F"]
    is_european = any(identifier in ticker for identifier in eu_identifiers)

    if is_european:
        core_open = (
            now_berlin.weekday() < 5
            and datetime.time(9, 0)
            <= now_berlin.time()
            <= datetime.time(17, 30)
        )
    else:
        core_open = (
            now_ny.weekday() < 5
            and datetime.time(9, 30) <= now_ny.time() <= datetime.time(16, 0)
        )

    extended_open = (
        now_berlin.weekday() < 5
        and datetime.time(8, 0) <= now_berlin.time() <= datetime.time(22, 0)
    )

    return core_open or extended_open


def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def get_ticker_from_name(query):
    query = query.strip()
    if not query:
        return None

    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=5"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        quotes = data.get("quotes", [])
        if quotes:
            for q in quotes:
                if q.get("quoteType") == "EQUITY":
                    return q.get("symbol")
            return quotes[0].get("symbol")
    except Exception:
        pass

    return query.upper()


@st.cache_data(ttl=300)
def get_data_with_info(ticker):
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=4 * 365)

    yticker = yf.Ticker(ticker)
    df = yticker.history(
        start=start_date,
        end=today + datetime.timedelta(days=2),
        interval="1wk",
        auto_adjust=True,
    )
    if df.empty:
        df = yf.download(
            ticker,
            start=start_date,
            end=today + datetime.timedelta(days=2),
            interval="1wk",
            auto_adjust=True,
            progress=False,
        )
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(ticker, level=1, axis=1)

    if "Volume" not in df.columns:
        df["Volume"] = 0

    df = df[["Close", "Volume"]].dropna()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()

    df["SMA30"] = df["Close"].rolling(window=30).mean()
    df["SMA30_Slope_4W"] = (
        (df["SMA30"] - df["SMA30"].shift(4)) / df["SMA30"].shift(4)
    ) * 100
    df["Vol_Avg_10W"] = df["Volume"].rolling(window=10).mean()

    currency, exchange, company_name = "USD", "N/A", ticker
    try:
        info = yticker.info
        currency = info.get("currency", "USD")
        exchange = info.get("exchange", "N/A")
        company_name = info.get("longName") or info.get("shortName") or ticker
    except Exception:
        pass

    is_open = is_market_open(ticker)
    return df, currency, exchange, is_open, company_name


@st.cache_data(ttl=300)
def get_batch_stock_data(tickers):
    if not tickers:
        return {}

    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=4 * 365)

    data = yf.download(
        tickers,
        start=start_date,
        end=today + datetime.timedelta(days=2),
        interval="1wk",
        auto_adjust=True,
        progress=False,
    )
    results = {}

    for t in tickers:
        try:
            if isinstance(data.columns, pd.MultiIndex):
                df_t = data.xs(t, level=1, axis=1)[["Close", "Volume"]].dropna()
            else:
                df_t = data[["Close", "Volume"]].dropna()

            df_t.index = pd.to_datetime(df_t.index).tz_localize(None).normalize()
            df_t["SMA30"] = df_t["Close"].rolling(window=30).mean()
            df_t["SMA30_Slope_4W"] = (
                (df_t["SMA30"] - df_t["SMA30"].shift(4))
                / df_t["SMA30"].shift(4)
            ) * 100
            df_t["Vol_Avg_10W"] = df_t["Volume"].rolling(window=10).mean()
            results[t] = df_t
        except Exception:
            continue

    return results


def calculate_mansfield_rs(asset_df, benchmark_df):
    if asset_df.empty or benchmark_df.empty:
        return pd.Series(0.0, index=asset_df.index)

    s_asset = asset_df["Close"].copy()
    s_bench = benchmark_df["Close"].copy()

    s_asset.index = pd.to_datetime(s_asset.index).tz_localize(None).normalize()
    s_bench.index = pd.to_datetime(s_bench.index).tz_localize(None).normalize()

    combined = pd.DataFrame({"Asset": s_asset, "Bench": s_bench}).sort_index().ffill().bfill()
    base_rs = combined["Asset"] / combined["Bench"]
    rs_sma52 = base_rs.rolling(window=52, min_periods=10).mean()

    mansfield = ((base_rs / rs_sma52) - 1.0) * 100.0
    return mansfield.reindex(s_asset.index).ffill().bfill().fillna(0.0)


def determine_stage(price, sma30, slope):
    if price > sma30 and slope > 0.5:
        return (
            "Stage 2 (Aufstiegsphase)",
            "background-color: rgba(40, 167, 69, 0.2); color: #2ecc71; border:"
            " 1px solid rgba(40, 167, 69, 0.5);",
        )
    elif price < sma30 and slope < -0.5:
        return (
            "Stage 4 (Abstiegsphase)",
            "background-color: rgba(220, 53, 69, 0.2); color: #e74c3c; border:"
            " 1px solid rgba(220, 53, 69, 0.5);",
        )
    elif price > sma30 and slope <= 0.5:
        return (
            "Stage 3 (Topbildungsphase)",
            "background-color: rgba(255, 193, 7, 0.2); color: #f1c40f; border:"
            " 1px solid rgba(255, 193, 7, 0.5);",
        )
    else:
        return (
            "Stage 1 (Bodenbildungsphase)",
            "background-color: rgba(108, 117, 125, 0.2); color: #95a5a6; border:"
            " 1px solid rgba(108, 117, 125, 0.5);",
        )


def check_stan_weinstein_top_candidate(
    price, sma30, slope, mansfield_rs, volume=None, vol_avg_10w=None
):
    c1 = price > sma30
    c2 = slope > 0.5
    c3 = mansfield_rs > 0.0
    c4 = True
    if volume is not None and vol_avg_10w is not None and vol_avg_10w > 0:
        c4 = volume >= (vol_avg_10w * 1.2)
    return c1 and c2 and c3 and c4


# ---------------------------------------------------------
# 6. DIALOGE
# ---------------------------------------------------------
@st.dialog("📖 Hilfeseite & Screening-Logik (Glossar)", width="large")
def show_glossary_dialog():
    st.markdown("## 📊 Regelwerk & Filter-Logik")
    st.write(
        "Hier findest du genaue Details darüber, wie Aktien gefiltert und als"
        " TOP KANDIDAT ausgezeichnet werden:"
    )
    st.markdown("---")
    st.markdown("### 🔍 1. Erstfilter: Wann erscheint eine Aktie?")
    st.markdown("""
    * **1. Kurs über dem 30W-SMA (`Preis > 30W-SMA`)**
    * **2. Positiver Trend (`Steigung (4W) > 0.0%`)**
    """)
    st.markdown("---")
    st.markdown("### ⭐ 2. Wann wird eine Aktie zum ⭐ TOP KANDIDATEN?")
    st.markdown("""
    1. **Kurs über 30W-SMA:** Der Kurs notiert klar oberhalb der Trendlinie.
    2. **Starke Steigung (`> +0.5%`):** Die 4-Wochen-Steigung des 30W-SMA muss kraftvoll sein.
    3. **Outperformance (`Mansfield RS > 0.0`):** Stärker als der S&P 500 Benchmark.
    4. **Volumen-Bestätigung (`Volumen >= 120% des 10W-Schnitts`)**
    """)


@st.dialog("📩 Kontakt & Private Community")
def show_contact_dialog():
    st.markdown("### Kontakt")
    st.write(
        "Bei Fragen erreichst du mich unter"
        " **[simon.moskwa@outlook.de](mailto:simon.moskwa@outlook.de)**."
    )


@st.dialog("📄 Impressum")
def show_impressum():
    st.markdown(
        "### Impressum\n**Angaben gemäß § 5 DDG:**\nSimon Moskwa\nAm"
        " Kohlenmeiler 81, 42389 Wuppertal, Deutschland\nE-Mail:"
        " [simon.moskwa@outlook.de](mailto:simon.moskwa@outlook.de)"
    )


@st.dialog("🔒 Datenschutzerklärung")
def show_datenschutz():
    st.markdown(
        "### Datenschutzerklärung\nDer Schutz Ihrer persönlichen Daten ist"
        " ein wichtiges Anliegen. Verantwortlich: Simon Moskwa."
    )


# ---------------------------------------------------------
# 7. SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 👤 Benutzer-Session")
    st.markdown(f"**{st.session_state['welcome_msg']}**")
    st.caption(
        f"Konto: {st.session_state['username']}"
        f" (`{st.session_state['role']}`)"
    )

    if st.button(
        "🔄 Charts aktualisieren",
        use_container_width=True,
        help="Leert den Daten-Cache.",
    ):
        st.cache_data.clear()
        st.success("Daten-Cache geleert!")
        st.rerun()

    if st.button("🔒 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["selected_stock"] = None
        st.rerun()

    if st.session_state["role"] == "admin":
        st.markdown("---")
        st.markdown("### ⚙️ Admin-Verwaltung")
        with st.expander("👥 Benutzer-Verwaltung", expanded=False):
            tab_add, tab_edit, tab_del = st.tabs(
                ["➕ Neu", "✏️ Ändern", "❌ Löschen"]
            )

            with tab_add:
                new_key = (
                    st.text_input("Benutzername", key="add_key").strip().lower()
                )
                new_pass = st.text_input(
                    "Passwort", key="add_pass", type="password"
                ).strip()
                new_name = st.text_input(
                    "Anzeigename", key="add_name"
                ).strip()
                new_role = st.selectbox(
                    "Rolle", ["user", "admin"], key="add_role"
                )

                if st.button("User Anlegen", use_container_width=True):
                    if not new_key or not new_pass or not new_name:
                        st.warning("Bitte alle Felder ausfüllen.")
                    elif new_key in st.session_state["users_db"]:
                        st.error("Benutzername existiert bereits.")
                    else:
                        st.session_state["users_db"][new_key] = {
                            "password": hash_password(new_pass),
                            "display_name": new_name,
                            "welcome_msg": f"Willkommen {new_name}",
                            "role": new_role,
                        }
                        save_users(st.session_state["users_db"])
                        st.success(f"User '{new_key}' angelegt!")
                        st.rerun()

            with tab_edit:
                user_list = list(st.session_state["users_db"].keys())
                if user_list:
                    edit_user = st.selectbox(
                        "User auswählen", user_list, key="edit_select"
                    )
                    curr_data = st.session_state["users_db"][edit_user]
                    edit_pass = st.text_input(
                        "Neues Passwort",
                        type="password",
                        key=f"edit_pass_{edit_user}",
                    ).strip()
                    edit_name = st.text_input(
                        "Anzeigename",
                        value=curr_data.get("display_name", ""),
                        key=f"edit_name_{edit_user}",
                    )
                    role_idx = 0 if curr_data.get("role") == "user" else 1
                    edit_role = st.selectbox(
                        "Rolle",
                        ["user", "admin"],
                        index=role_idx,
                        key=f"edit_role_{edit_user}",
                    )

                    if st.button(
                        "Änderungen Speichern",
                        key=f"btn_save_{edit_user}",
                        use_container_width=True,
                    ):
                        final_pass = (
                            hash_password(edit_pass)
                            if edit_pass
                            else curr_data.get("password")
                        )
                        st.session_state["users_db"][edit_user] = {
                            "password": final_pass,
                            "display_name": edit_name,
                            "welcome_msg": f"Willkommen {edit_name}",
                            "role": edit_role,
                        }
                        save_users(st.session_state["users_db"])
                        st.success(f"Daten für '{edit_user}' aktualisiert!")
                        st.rerun()

            with tab_del:
                del_user = st.selectbox(
                    "User zum Löschen",
                    [
                        u
                        for u in st.session_state["users_db"].keys()
                        if u != st.session_state["user_key"]
                    ],
                    key="del_select",
                )
                if del_user and st.button(
                    f"❌ '{del_user}' löschen",
                    use_container_width=True,
                    type="primary",
                ):
                    del st.session_state["users_db"][del_user]
                    save_users(st.session_state["users_db"])
                    st.success(f"User '{del_user}' wurde gelöscht.")
                    st.rerun()

# ---------------------------------------------------------
# 8. STYLES & CSS
# ---------------------------------------------------------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { padding-top: 1rem; }
    .stApp {
        background: radial-gradient(circle at 15% 0%, rgba(56, 189, 248, 0.07) 0%, transparent 45%),
                    radial-gradient(circle at 85% 20%, rgba(129, 140, 248, 0.06) 0%, transparent 45%), #0b0e14;
    }
    div[data-testid="stContainer"] {
        border-radius: 16px; background: rgba(22, 27, 34, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.08); backdrop-filter: blur(10px); padding: 4px;
    }
    .dashboard-title {
        font-size: 2.35rem; font-weight: 800; background: linear-gradient(90deg, #ffffff 10%, #7dd3fc 60%, #a5b4fc 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .top-candidate-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff;
        font-weight: 800; font-size: 0.85rem; padding: 6px 14px; border-radius: 20px; display: inline-block;
    }
    .status-badge-open { color: #4ade80; background: rgba(74, 222, 128, 0.12); padding: 3px 10px; border-radius: 12px; font-size: 0.78rem; font-weight: 600; }
    .status-badge-closed { color: #f87171; background: rgba(248, 113, 113, 0.12); padding: 3px 10px; border-radius: 12px; font-size: 0.78rem; font-weight: 600; }
    .disclaimer-box { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 15px 20px; font-size: 0.82rem; color: #94a3b8; }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 9. CHART RENDERING
# ---------------------------------------------------------
def apply_current_period_view(fig, plot_df):
    if plot_df.empty:
        return fig
    first_date, last_date = plot_df.index.min(), plot_df.index.max()
    fig.update_xaxes(
        type="date",
        tickformat="%b %Y",
        dtick="M1",
        range=[first_date, last_date + pd.Timedelta(days=14)],
        showgrid=True,
        gridcolor="rgba(255,255,255,0.04)",
    )
    fig.add_vline(
        x=last_date.timestamp() * 1000,
        line_width=1,
        line_dash="dot",
        line_color="rgba(255,255,255,0.35)",
    )
    fig.add_annotation(
        x=last_date,
        y=0.97,
        xref="x",
        yref="y domain",
        text="Aktuell ●",
        showarrow=False,
        xanchor="right",
        font=dict(color="#38bdf8", size=10),
    )
    return fig


def render_chart(fig, height=450):
    fig.update_layout(
        height=height,
        autosize=True,
        margin=dict(l=55, r=20, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": True, "displaylogo": False},
    )


# ---------------------------------------------------------
# 10. DETAIL SEITE & MAIN APPS
# ---------------------------------------------------------
BENCHMARK = "^GSPC"
bench_df, _, _, _, _ = get_data_with_info(BENCHMARK)


def render_stock_detail_page(ticker):
    if st.button("⬅ Zurück zum Dashboard"):
        st.session_state["selected_stock"] = None
        st.rerun()

    try:
        with st.spinner(f"Lade Detailanalyse für '{ticker}'..."):
            d_df, d_curr, d_exchange, d_open, d_name = get_data_with_info(ticker)
            d_df["Mansfield_RS"] = calculate_mansfield_rs(d_df, bench_df)

            d_price, d_sma = d_df["Close"].iloc[-1], d_df["SMA30"].iloc[-1]
            d_slope, d_mrs = (
                d_df["SMA30_Slope_4W"].iloc[-1],
                d_df["Mansfield_RS"].iloc[-1],
            )
            d_vol, d_vol_avg = (
                d_df["Volume"].iloc[-1],
                d_df["Vol_Avg_10W"].iloc[-1],
            )
            d_stage, d_css = determine_stage(d_price, d_sma, d_slope)
            d_is_top = check_stan_weinstein_top_candidate(
                d_price, d_sma, d_slope, d_mrs, d_vol, d_vol_avg
            )

            d_status_badge = (
                "<span class='status-badge-open'>🟢 Börse Geöffnet</span>"
                if d_open
                else "<span class='status-badge-closed'>🔴 Börse Geschlossen</span>"
            )
            d_top_badge = (
                "<span class='top-candidate-badge'>⭐ TOP KANDIDAT (Stage"
                " 2)</span> &nbsp;"
                if d_is_top
                else ""
            )

            st.markdown(f"## {d_name} (`{ticker}`)")
            st.markdown(
                f"<div>{d_top_badge}<span"
                f" style='padding:6px;{d_css}'>{d_stage}</span> &nbsp;"
                f" {d_status_badge}</div>",
                unsafe_allow_html=True,
            )

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Aktueller Kurs", f"{d_price:.2f} {d_curr}")
            m2.metric("30W-SMA", f"{d_sma:.2f} {d_curr}")
            m3.metric("SMA Steigung (4W)", f"{d_slope:+.2f}%")
            m4.metric("Mansfield RS", f"{d_mrs:+.2f}")

            plot_df_d = d_df.tail(104)
            fig_d = make_subplots(
                rows=3,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.55, 0.20, 0.25],
            )
            fig_d.add_trace(
                go.Scatter(
                    x=plot_df_d.index,
                    y=plot_df_d["Close"],
                    name="Kurs",
                    line=dict(color="#38bdf8", width=2.5),
                ),
                row=1,
                col=1,
            )
            fig_d.add_trace(
                go.Scatter(
                    x=plot_df_d.index,
                    y=plot_df_d["SMA30"],
                    name="30W-SMA",
                    line=dict(color="#fbbf24", dash="dash"),
                ),
                row=1,
                col=1,
            )
            fig_d.add_trace(
                go.Bar(
                    x=plot_df_d.index,
                    y=plot_df_d["Volume"],
                    name="Volumen",
                    opacity=0.7,
                ),
                row=2,
                col=1,
            )
            fig_d.add_trace(
                go.Bar(
                    x=plot_df_d.index,
                    y=plot_df_d["Mansfield_RS"],
                    name="Mansfield RS",
                ),
                row=3,
                col=1,
            )

            apply_current_period_view(fig_d, plot_df_d)
            render_chart(fig_d, height=520)
    except Exception:
        st.error(f"Daten für '{ticker}' konnten nicht geladen werden.")


if st.session_state.get("selected_stock"):
    render_stock_detail_page(st.session_state["selected_stock"])
    st.stop()

# ---------------------------------------------------------
# 11. DASHBOARD MAIN VIEW
# ---------------------------------------------------------
logo_b64 = get_image_base64("logo.png")
h1, h2, h3 = st.columns([1, 4.2, 2.2])
with h1:
    if logo_b64:
        st.markdown(
            f"<img src='data:image/png;base64,{logo_b64}' style='width: 95px;'>",
            unsafe_allow_html=True,
        )
with h2:
    st.markdown(
        "<div class='dashboard-title'>Stage-Analysis RS-Dashboard</div>",
        unsafe_allow_html=True,
    )
with h3:
    b1, b2 = st.columns(2)
    if b1.button("❓ Hilfeseite"):
        show_glossary_dialog()
    if b2.button("📩 Contact Us"):
        show_contact_dialog()

# Aktiensuche Section
st.markdown("---")
st.subheader("🔍 Aktiensuche & Phasen-Analyse")
with st.container(border=True):
    s_col1, s_col2 = st.columns([3, 1])
    search_query = s_col1.text_input(
        "Aktienname oder Ticker eingeben:",
        value="Dino Polska",
        key="search_ticker_input",
    ).strip()

    if search_query:
        resolved_ticker = get_ticker_from_name(search_query)
        try:
            with st.spinner("Lade Chartdaten..."):
                stock_df, stock_curr, _, stock_open, comp_name = (
                    get_data_with_info(resolved_ticker)
                )
                stock_df["Mansfield_RS"] = calculate_mansfield_rs(
                    stock_df, bench_df
                )

                s_price, s_sma = (
                    stock_df["Close"].iloc[-1],
                    stock_df["SMA30"].iloc[-1],
                )
                s_slope, s_mrs = (
                    stock_df["SMA30_Slope_4W"].iloc[-1],
                    stock_df["Mansfield_RS"].iloc[-1],
                )
                s_stage, s_css = determine_stage(s_price, s_sma, s_slope)

                st.markdown(f"### {comp_name} (`{resolved_ticker}`)")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Kurs", f"{s_price:.2f} {stock_curr}")
                m2.metric("30W-SMA", f"{s_sma:.2f} {stock_curr}")
                m3.metric("Steigung (4W)", f"{s_slope:+.2f}%")
                m4.metric("Mansfield RS", f"{s_mrs:+.2f}")
        except Exception:
            st.error(f"Fehler beim Laden von '{search_query}'.")

# Sektoren Dashboard
SECTOR_COMPONENTS = {
    "Technology (XLK)": {
        "ticker": "XLK",
        "stocks": {
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "NVDA": "NVIDIA",
            "AVGO": "Broadcom",
        },
    },
    "Energy (XLE)": {
        "ticker": "XLE",
        "stocks": {
            "XOM": "Exxon Mobil",
            "CVX": "Chevron",
            "COP": "ConocoPhillips",
        },
    },
    "Financials (XLF)": {
        "ticker": "XLF",
        "stocks": {
            "JPM": "JPMorgan",
            "BAC": "Bank of America",
            "WFC": "Wells Fargo",
        },
    },
}

st.markdown("---")
st.subheader("📊 Sektoren & Top-Performer")

all_sector_results = []
for sec_name, sec_info in SECTOR_COMPONENTS.items():
    try:
        sec_df, curr, exchange, market_open, _ = get_data_with_info(
            sec_info["ticker"]
        )
        sec_df["Mansfield_RS"] = calculate_mansfield_rs(sec_df, bench_df)
        p, sma = sec_df["Close"].iloc[-1], sec_df["SMA30"].iloc[-1]
        slope, m_rs = (
            sec_df["SMA30_Slope_4W"].iloc[-1],
            sec_df["Mansfield_RS"].iloc[-1],
        )
        stage, css = determine_stage(p, sma, slope)

        all_sector_results.append({
            "name": sec_name,
            "ticker": sec_info["ticker"],
            "stocks": sec_info["stocks"],
            "price": p,
            "sma": sma,
            "slope": slope,
            "m_rs": m_rs,
            "stage": stage,
            "css": css,
            "currency": curr,
            "df": sec_df,
        })
    except Exception:
        pass

cols = st.columns(2)
for idx, item in enumerate(all_sector_results):
    with cols[idx % 2]:
        with st.container(border=True):
            st.markdown(f"### {item['name']}")
            st.caption(
                f"RS: **{item['m_rs']:+.2f}** | Steigung:"
                f" **{item['slope']:+.2f}%**"
            )

            exp = st.expander("🔎 Einzelaktien anzeigen")
            with exp:
                sec_stock_tickers = list(item["stocks"].keys())
                batch_dfs = get_batch_stock_data(sec_stock_tickers)

                stock_data = []
                for stk_ticker, stk_name in item["stocks"].items():
                    if stk_ticker in batch_dfs:
                        stk_df = batch_dfs[stk_ticker]
                        if not stk_df.empty:
                            stk_df["Mansfield_RS"] = calculate_mansfield_rs(
                                stk_df, bench_df
                            )
                            stock_data.append({
                                "Handelszeichen": stk_ticker,
                                "Name": stk_name,
                                "Kurs": f"{stk_df['Close'].iloc[-1]:.2f}",
                                "Mansfield-RS": round(
                                    stk_df["Mansfield_RS"].iloc[-1], 2
                                ),
                            })

                if stock_data:
                    sdf = pd.DataFrame(stock_data)
                    event = st.dataframe(
                        sdf,
                        hide_index=True,
                        use_container_width=True,
                        on_select="rerun",
                        selection_mode="single-row",
                        key=f"df_{item['ticker']}_{idx}",
                    )
                    if event and event.get("selection", {}).get("rows"):
                        r_idx = event["selection"]["rows"][0]
                        st.session_state["selected_stock"] = sdf.iloc[r_idx][
                            "Handelszeichen"
                        ]
                        st.rerun()

# Footer
st.markdown("---")
f1, f2, f3 = st.columns([2, 1, 1])
f1.caption("© Pulse Trading • Private & Rein Informative Webseite")
if f2.button("Impressum"):
    show_impressum()
if f3.button("Datenschutz"):
    show_datenschutz()
