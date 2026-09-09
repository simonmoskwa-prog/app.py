import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Weinstein Stage-Analysis RS-Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS für schöneres Design
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .stMetric {
        background-color: #1e222d;
        padding: 12px;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. HEADER BEREICH (Logo & Titel)
# ==========================================
col_logo, col_title = st.columns([1, 6])

with col_logo:
    # Logo mit fester Breite für scharfe Darstellung ohne Streckung
    try:
        st.image("logo.png", width=120)
    except Exception:
        st.info("Logo.png fehlt")

with col_title:
    st.title("Weinstein Stage-Analysis RS-Dashboard")
    st.subheader("Powered by Pulse Trading / Simon Moskwa")

st.caption("Markt → Sektor → Top-Aktien | Basierend auf Stan Weinsteins Phasenanalyse (Wochencharts, 30-Wochen-SMA & Mansfield Relative Strength)")
st.divider()


# ==========================================
# 3. HELPER FUNCTIONS (Analyse & Daten)
# ==========================================
@st.cache_data(ttl=3600)
def fetch_stock_data(tickers, benchmark_ticker="^GSPC", period="2y"):
    """
    Lädt historische Wochendaten von Yahoo Finance herunter
    und berechnet SMA 30 sowie Mansfield Relative Strength.
    """
    all_tickers = list(set(tickers + [benchmark_ticker]))
    data = yf.download(all_tickers, period=period, interval="1wk", progress=False)['Close']
    
    if benchmark_ticker not in data.columns:
        return pd.DataFrame()
        
    benchmark = data[benchmark_ticker]
    results = []
    
    for ticker in tickers:
        if ticker not in data.columns:
            continue
            
        df_stock = data[ticker].dropna()
        if len(df_stock) < 30:
            continue
            
        current_price = df_stock.iloc[-1]
        sma_30 = df_stock.rolling(window=30).mean().iloc[-1]
        sma_30_prev = df_stock.rolling(window=30).mean().iloc[-2]
        
        # Trend der 30-Wochen-Linie
        sma_trend = "Steigend ↗️" if sma_30 > sma_30_prev else ("Fallend ↘️" if sma_30 < sma_30_prev else "Flach ➡️")
        
        # Mansfield Relative Strength Berechnung
        rs = df_stock / benchmark.reindex(df_stock.index)
        rs_sma = rs.rolling(window=52).mean()
        
        if not rs_sma.dropna().empty:
            mansfield_rs = ((rs / rs_sma) - 1) * 100
            current_mansfield = mansfield_rs.iloc[-1]
        else:
            current_mansfield = 0.0

        # Bestimmung der Weinstein Phase
        if current_price > sma_30 and sma_30 > sma_30_prev and current_mansfield > 0:
            stage = "Phase 2 (Advancing)"
        elif current_price < sma_30 and sma_30 < sma_30_prev and current_mansfield < 0:
            stage = "Phase 4 (Declining)"
        elif current_price > sma_30 and sma_30 < sma_30_prev:
            stage = "Phase 3 (Toping)"
        else:
            stage = "Phase 1 (Basing)"

        results.append({
            "Ticker": ticker,
            "Preis": round(current_price, 2),
            "SMA 30": round(sma_30, 2),
            "SMA Trend": sma_trend,
            "Mansfield RS": round(current_mansfield, 2),
            "Weinstein Phase": stage
        })
        
    return pd.DataFrame(results)


# ==========================================
# 4. SIDEBAR & MARKTAUSWAHL
# ==========================================
st.sidebar.header("⚙️ Filter & Märkte")

market_dict = {
    "USA (S&P 500 Top Selection)": ["AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "UNH", "JNJ"],
    "Nasdaq 100 Tech Leaders": ["NVDA", "AAPL", "MSFT", "AMD", "AVGO", "QCOM", "AMZN", "META", "TSLA", "NFLX"],
    "DAX (Deutschland)": ["SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "AIR.DE", "MBG.DE", "BMW.DE", "BAYN.DE", "BAS.DE", "RHM.DE"],
    "Euro Stoxx 50": ["ASML.AS", "MC.PA", "SAP.DE", "OR.PA", "TTE.PA", "SIE.DE", "SAN.MC", "SU.PA"]
}

selected_market_name = st.sidebar.selectbox("Markt / Liste wählen", list(market_dict.keys()))
benchmark_ticker = st.sidebar.selectbox("Benchmark für Mansfield RS", ["^GSPC", "^NDX", "^GDAXI"], index=0)

min_rs = st.sidebar.slider("Mindest Mansfield RS", -10.0, 10.0, 0.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.info("""
**Stan Weinsteins Regeln:**
* **Phase 1 (Basing):** Bodenbildung, SMA 30 verflacht.
* **Phase 2 (Advancing):** Ausbruch über SMA 30 + positive Mansfield RS ➔ **Kaufbereich**.
* **Phase 3 (Toping):** Toppbildung, SMA 30 wird flach.
* **Phase 4 (Declining):** Abwärtstrend unter SMA 30 ➔ **Meiden / Short**.
""")


# ==========================================
# 5. DASHBOARD MAIN CONTENT
# ==========================================
st.header(f"Markt-Übersicht: {selected_market_name}")

tickers_to_scan = market_dict[selected_market_name]

with st.spinner("Lade Daten von Yahoo Finance und berechne 30-Wochen-SMA & Mansfield RS..."):
    df_results = fetch_stock_data(tickers_to_scan, benchmark_ticker=benchmark_ticker)

if not df_results.empty:
    # Filter anwenden
    df_filtered = df_results[df_results["Mansfield RS"] >= min_rs]

    # Metriken / KPIs anzeigen
    col1, col2, col3, col4 = st.columns(4)
    total_count = len(df_results)
    p2_count = len(df_results[df_results["Weinstein Phase"] == "Phase 2 (Advancing)"])
    p4_count = len(df_results[df_results["Weinstein Phase"] == "Phase 4 (Declining)"])
    rs_pos_count = len(df_results[df_results["Mansfield RS"] > 0])

    col1.metric("Analysierte Titel", total_count)
    col2.metric("In Phase 2 (Bullish)", f"{p2_count}", f"{round((p2_count/total_count)*100, 1)}%")
    col3.metric("In Phase 4 (Bearish)", f"{p4_count}", f"-{round((p4_count/total_count)*100, 1)}%")
    col4.metric("Stärke vs. Benchmark (RS > 0)", f"{rs_pos_count}", f"{round((rs_pos_count/total_count)*100, 1)}%")

    st.markdown("### Top-Aktien Übersicht")
    
    # Styling für die Tabelle (Verwendet .map() statt veraltetem .applymap())
    def highlight_phase(val):
        if "Phase 2" in str(val):
            return "background-color: #1b4332; color: #74c69d; font-weight: bold;"
        elif "Phase 4" in str(val):
            return "background-color: #49111c; color: #f87171;"
        return ""

    styled_df = df_filtered.style.map(highlight_phase, subset=["Weinstein Phase"])\
                                 .format({"Preis": "{:.2f} €", "SMA 30": "{:.2f} €", "Mansfield RS": "{:+.2f}"})

    st.dataframe(styled_df, use_container_width=True, height=400)

else:
    st.error("Keine Daten geladen. Bitte prüfe die Internetverbindung oder Ticker-Symbole.")


# ==========================================
# 6. FOOTER
# ==========================================
st.divider()
st.markdown("<p style='text-align: center; color: gray;'>© Pulse Trading | Dashboard für Stan Weinstein Phasenanalyse</p>", unsafe_allow_html=True)
