import os
import json
import hashlib
import secrets
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import numpy as np
import plotly.graph_objects as rx
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

# ==============================================================================
# 1. KONFIGURATION & KONSTANTEN
# ==============================================================================
st.set_page_config(
    page_title="Stan Weinstein Stage Analysis & RS",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

USERS_FILE = "users.json"
BENCHMARK_TICKER = "^GSPC"  # S&P 500 als weltweiter Standard-Benchmark

# Sektoren und zugehörige Einzelaktien (Erweiterbar)
SECTORS = {
    "Technologie & Halbleiter": {
        "etf": "XLK",
        "stocks": {
            "NVDA": "NVIDIA Corp.",
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corp.",
            "AMD": "Advanced Micro Devices",
            "AVGO": "Broadcom Inc."
        }
    },
    "Konsumgüter & Einzelhandel": {
        "etf": "XLY",
        "stocks": {
            "AMZN": "Amazon.com Inc.",
            "TSLA": "Tesla Inc.",
            "DNO.WA": "Dino Polska S.A.",
            "BIRK": "Birkenstock Holding"
        }
    },
    "Finanzen": {
        "etf": "XLF",
        "stocks": {
            "JPM": "JPMorgan Chase & Co.",
            "BAC": "Bank of America",
            "MS": "Morgan Stanley"
        }
    },
    "Industrie & Infrastruktur": {
        "etf": "XLI",
        "stocks": {
            "DG.PA": "Vinci S.A.",
            "CAT": "Caterpillar Inc.",
            "GE": "General Electric"
        }
    },
    "Digital Assets & Infrastructure": {
        "etf": "IREN",  # Beispiel-Muster
        "stocks": {
            "IREN": "Iris Energy Ltd.",
            "BTC-USD": "Bitcoin",
            "ETH-USD": "Ethereum"
        }
    }
}

# ==============================================================================
# 2. BENUTZERVERWALTUNG & SICHERHEIT
# ==============================================================================
def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Erstellt einen sicheren SHA-256 Hash mit Salt."""
    if not salt:
        salt = secrets.token_hex(16)
    salted_pwd = salt + password
    pwd_hash = hashlib.sha256(salted_pwd.encode("utf-8")).hexdigest()
    return pwd_hash, salt

def load_users() -> dict:
    """Lädt Benutzerdaten aus users.json oder Streamlit Secrets."""
    users = {}
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
        except Exception:
            users = {}
    
    # Fallback/Integration für Streamlit Secrets
    if "users" in st.secrets:
        for u, p in st.secrets["users"].items():
            if u not in users:
                pwd_hash, salt = hash_password(str(p))
                users[u] = {"hash": pwd_hash, "salt": salt}
    return users

def save_users(users: dict):
    """Speichert die Benutzerstruktur ab."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def verify_credentials(username, password) -> bool:
    """Überprüft Anmeldedaten."""
    users = load_users()
    if username in users:
        user_data = users[username]
        # Abwärtskompatibilität für ältere Hashes ohne Salt
        if isinstance(user_data, str):
            old_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            return user_data == old_hash
        
        stored_hash = user_data.get("hash")
        salt = user_data.get("salt")
        calc_hash, _ = hash_password(password, salt)
        return calc_hash == stored_hash
    return False

def init_session_state():
    """Initialisiert den Sitzungsstatus."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""

# ==============================================================================
# 3. DATENBESCHAFFUNG & MARKTANALYSE (STAGE ANALYSIS & RS)
# ==============================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def get_data_with_info(ticker_symbol: str):
    """Lade Wochenkurse und Zusatzinformationen via yfinance."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="2y", interval="1wk")
        if df.empty or len(df) < 35:
            return None, "USD", "N/A", False, {}
        
        info = ticker.info or {}
        currency = info.get("currency", "USD")
        exchange = info.get("exchange", "N/A")
        
        # Prüfung ob Markt offen / Daten aktuell
        market_open = True
        
        # Indikatoren berechnen
        df["SMA30"] = df["Close"].rolling(window=30).mean()
        df["SMA30_Slope_4W"] = (df["SMA30"] - df["SMA30"].shift(4)) / df["SMA30"].shift(4) * 100
        df["Vol_Avg_10W"] = df["Volume"].rolling(window=10).mean()
        
        return df, currency, exchange, market_open, info
    except Exception:
        return None, "USD", "N/A", False, {}

def calculate_mansfield_rs(stock_df: pd.DataFrame, benchmark_df: pd.DataFrame) -> pd.Series:
    """Berechnet den Mansfield Relative Strength Indikator."""
    aligned = pd.concat([stock_df["Close"], benchmark_df["Close"]], axis=1, keys=["Stock", "Bench"]).dropna()
    base_rs = aligned["Stock"] / aligned["Bench"]
    sma_base_rs = base_rs.rolling(window=30).mean()
    mansfield_rs = ((base_rs / sma_base_rs) - 1) * 100
    return mansfield_rs.reindex(stock_df.index)

def check_stan_weinstein_top_candidate(price, sma, slope, mansfield_rs, vol, vol_avg_10w) -> bool:
    """
    4-Punkte-Validierung für Stage-2 Ausbrüche nach Stan Weinstein:
    1. Preis oberhalb des 30-Wochen-SMA
    2. 30W-SMA Steigung über 4 Wochen positiv (> 0.5%)
    3. Mansfield RS im positiven Bereich (> 0)
    4. Volumen beim Ausbruch überdurchschnittlich (>= 120% des 10W-Schnitts)
    """
    cond_price = price > sma
    cond_slope = slope > 0.5
    cond_rs = mansfield_rs > 0
    cond_vol = vol >= (vol_avg_10w * 1.20) if vol_avg_10w and vol_avg_10w > 0 else True
    
    return cond_price and cond_slope and cond_rs and cond_vol

def fetch_single_stock_data(stk_ticker, stk_name, bench_df):
    """Hilfsfunktion für die parallele Abfrage der Sektor-Einzelaktien."""
    try:
        stk_df, stk_curr, stk_exchange, stk_open, _ = get_data_with_info(stk_ticker)
        if stk_df is None or stk_df.empty:
            return None
        
        stk_df["Mansfield_RS"] = calculate_mansfield_rs(stk_df, bench_df)
        
        stk_p = stk_df["Close"].iloc[-1]
        stk_sma = stk_df["SMA30"].iloc[-1]
        stk_slope = stk_df["SMA30_Slope_4W"].iloc[-1]
        stk_mrs = stk_df["Mansfield_RS"].iloc[-1]
        stk_vol = stk_df["Volume"].iloc[-1]
        stk_vol_avg = stk_df["Vol_Avg_10W"].iloc[-1]

        if pd.isna(stk_sma) or pd.isna(stk_slope):
            return None

        stk_is_top = check_stan_weinstein_top_candidate(stk_p, stk_sma, stk_slope, stk_mrs, stk_vol, stk_vol_avg)

        return {
            "Top": "⭐ TOP KANDIDAT" if stk_is_top else "—",
            "Ticker": stk_ticker,
            "Name": stk_name,
            "Börse": stk_exchange,
            "Kurs": f"{stk_p:.2f} {stk_curr}",
            "30W-SMA": f"{stk_sma:.2f} {stk_curr}",
            "SMA-Steigung (4W)": f"{stk_slope:+.2f}%",
            "Mansfield-RS": f"{stk_mrs:+.2f}",
            "Status": "🟢 Offen" if stk_open else "🔴 Geschlossen"
        }
    except Exception:
        return None

# ==============================================================================
# 4. PLOTLY CHARTING ENGINE
# ==============================================================================
def create_stage_analysis_chart(df: pd.DataFrame, ticker_symbol: str):
    """Erstellt ein interaktives 3-Panel Plotly-Chart."""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f"{ticker_symbol} — Kurs & 30W-SMA", "Volumen & 10W-Durchschnitt", "Mansfield Relative Strength (vs. S&P 500)"),
        row_heights=[0.55, 0.20, 0.25]
    )

    # 1. Candlestick & SMA30
    fig.add_trace(
        rx.Candlestick(
            x=df.index,
            open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            name="Kurs"
        ),
        row=1, col=1
    )
    fig.add_trace(
        rx.Scatter(
            x=df.index, y=df["SMA30"],
            line=dict(color="orange", width=2),
            name="30W-SMA"
        ),
        row=1, col=1
    )

    # 2. Volumen
    colors = ["green" if c >= o else "red" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(
        rx.Bar(x=df.index, y=df["Volume"], marker_color=colors, name="Volumen"),
        row=2, col=1
    )
    fig.add_trace(
        rx.Scatter(x=df.index, y=df["Vol_Avg_10W"], line=dict(color="blue", width=1.5), name="10W-Vol-Ø"),
        row=2, col=1
    )

    # 3. Mansfield RS
    rs_colors = ["green" if val >= 0 else "red" for val in df["Mansfield_RS"]]
    fig.add_trace(
        rx.Bar(x=df.index, y=df["Mansfield_RS"], marker_color=rs_colors, name="Mansfield RS"),
        row=3, col=1
    )
    fig.add_hline(y=0, line_dash="dash", line_color="white", row=3, col=1)

    # Layout Anpassungen
    fig.update_layout(
        height=750,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# ==============================================================================
# 5. USER INTERFACE & COMPONENTEN
# ==============================================================================
def render_login():
    """Login-Maske anzeigen."""
    st.title("🔐 Stage Analysis Dashboard — Login")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Benutzername")
            password = st.text_input("Passwort", type="password")
            submit = st.form_submit_button("Anmelden", use_container_width=True)
            
            if submit:
                if verify_credentials(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("Erfolgreich angemeldet!")
                    st.rerun()
                else:
                    st.error("Ungültige Anmeldedaten.")

def render_dashboard():
    """Haupt-Dashboard anzeigen."""
    st.sidebar.title(f"👤 Willkommen, {st.session_state.username}")
    if st.sidebar.button("Abmelden"):
        st.session_state.authenticated = False
        st.rerun()

    st.title("📈 Stan Weinstein Stage Analysis & Relative Strength")
    st.markdown("""
    **Methodik:** Analyse von Wochencharts auf Basis des 30-Wochen-Gleitenden-Durchschnitts (30W-SMA) 
    und der Mansfield Relative Strength gegenüber dem Benchmark (S&P 500).
    """)

    # Benchmark-Daten laden
    bench_df, _, _, _, _ = get_data_with_info(BENCHMARK_TICKER)
    if bench_df is None:
        st.error("Fehler beim Laden der Benchmark-Daten (S&P 500). Bitte später erneut versuchen.")
        return

    tabs = st.tabs(["🔎 Einzelaktien-Analyse", "📊 Sektor- & Marktübersicht"])

    # TAB 1: EINZELAKTIEN
    with tabs[0]:
        st.subheader("Einzelwert-Analyse")
        col_search, col_space = st.columns([1, 2])
        with col_search:
            symbol = st.text_input("Ticker Symbol (z.B. NVDA, DNO.WA, BTC-USD)", value="NVDA").upper()

        if symbol:
            with st.spinner(f"Lade Daten für {symbol}..."):
                df, currency, exchange, is_open, info = get_data_with_info(symbol)

                if df is not None and not df.empty:
                    df["Mansfield_RS"] = calculate_mansfield_rs(df, bench_df)

                    curr_price = df["Close"].iloc[-1]
                    curr_sma = df["SMA30"].iloc[-1]
                    curr_slope = df["SMA30_Slope_4W"].iloc[-1]
                    curr_mrs = df["Mansfield_RS"].iloc[-1]
                    curr_vol = df["Volume"].iloc[-1]
                    curr_vol_avg = df["Vol_Avg_10W"].iloc[-1]

                    is_top = check_stan_weinstein_top_candidate(
                        curr_price, curr_sma, curr_slope, curr_mrs, curr_vol, curr_vol_avg
                    )

                    # KPIs anzeigen
                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Aktueller Kurs", f"{curr_price:.2f} {currency}")
                    m2.metric("30W-SMA", f"{curr_sma:.2f} {currency}")
                    m3.metric("SMA-Steigung (4W)", f"{curr_slope:+.2f}%")
                    m4.metric("Mansfield RS", f"{curr_mrs:+.2f}")
                    m5.metric("Status", "⭐ TOP KANDIDAT" if is_top else "Kein Breakout", delta_color="normal")

                    # Chart anzeigen
                    fig = create_stage_analysis_chart(df, symbol)
                    st.plotly_chart(fig, use_container_width=True)

                    if is_top:
                        st.success("🟢 **Stage 2 Breakout Signal:** Der Kurs liegt über der steigenden 30W-Linie, zeigt Outperformance gegenüber dem Markt und wird von hohem Volumen gestützt.")
                else:
                    st.warning(f"Keine Daten für das Symbol '{symbol}' gefunden.")

    # TAB 2: SEKTORÜBERSICHT
    with tabs[1]:
        st.subheader("Sektor- & Gruppenübersicht (Parallele Analyse)")
        
        for sector_name, sector_data in SECTORS.items():
            with st.expander(f"📁 {sector_name} (ETF: {sector_data['etf']})", expanded=False):
                stocks_map = sector_data["stocks"]
                
                # Multi-Threading Abfrage für maximale Performance
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [
                        executor.submit(fetch_single_stock_data, ticker, name, bench_df)
                        for ticker, name in stocks_map.items()
                    ]
                    results = [f.result() for f in futures if f.result() is not None]

                if results:
                    res_df = pd.DataFrame(results)
                    st.dataframe(res_df, hide_index=True, use_container_width=True)
                else:
                    st.info("Keine Daten für diesen Sektor verfügbar.")

# ==============================================================================
# 6. APPLICATION ENTRY POINT
# ==============================================================================
def main():
    init_session_state()
    if not st.session_state.authenticated:
        render_login()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()
