# app.py 
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Weinstein Stage-Analysis Dashboard", layout="wide")

st.title("Weinstein Stage-Analysis RS-Dashboard")
st.caption("Markt → Sektor → Aktie | Basierend auf Stan Weinsteins Phasenanalyse")

# --- TICKER DEFINITIONEN ---
BENCHMARK = "^GSPC" # S&P 500 als Referenz für Mansfield RS

SECTORS = {
    "Energy (XLE)": "XLE",
    "Health Care (XLV)": "XLV",
    "Technology (XLK)": "XLK",
    "Financials (XLF)": "XLF",
    "Communication Services (XLC)": "XLC",
    "Materials (XLB)": "XLB",
    "Consumer Staples (XLP)": "XLP",
    "Consumer Discretionary (XLY)": "XLY",
}

# --- BERECHNUNGS-FUNKTIONEN ---
@st.cache_data(ttl=3600)
def get_data(ticker):
    # Wochenkurse abrufen (Weekly / 1wk)
    df = yf.download(ticker, period="3y", interval="1wk")
    if isinstance(df.columns, pd.MultiIndex):
        df = df.xs(ticker, level=1, axis=1)
    df = df[['Close', 'Volume']].dropna()
    
    # 30-Wochen-SMA
    df['SMA30'] = df['Close'].rolling(window=30).mean()
    
    # 4-Wochen-Steigung des SMA 30 in %
    df['SMA30_Slope_4W'] = ((df['SMA30'] - df['SMA30'].shift(4)) / df['SMA30'].shift(4)) * 100
    
    return df

def calculate_mansfield_rs(asset_df, benchmark_df):
    # Synchronisiere Datenstände
    combined = pd.DataFrame({
        'Asset': asset_df['Close'],
        'Bench': benchmark_df['Close']
    }).dropna()
    
    # Basis Relative Strength
    base_rs = combined['Asset'] / combined['Bench']
    
    # Mansfield RS (zentriert um 0 mittels 52-Wochen-SMA der Base RS)
    rs_sma52 = base_rs.rolling(window=52).mean()
    mansfield_rs = ((base_rs / rs_sma52) - 1) * 100
    return mansfield_rs

def determine_stage(price, sma30, slope):
    if price > sma30 and slope > 0.5:
        return "Stage 2 (Aufwärtstrend)", "background-color: #d4edda; color: #155724;"
    elif price < sma30 and slope < -0.5:
        return "Stage 4 (Abwärtstrend)", "background-color: #f8d7da; color: #721c24;"
    elif price > sma30 and slope <= 0.5:
        return "Stage 1 / 3 (Konsolidierung)", "background-color: #fff3cd; color: #856404;"
    else:
        return "Stage 1 / 3 (Boden/Top)", "background-color: #e2e3e5; color: #383d41;"

# --- BENCHMARK DATEN ---
bench_df = get_data(BENCHMARK)

# --- TOP TABS (MÄRKTE) ---
tab_usa, tab_tech = st.tabs(["USA (S&P 500)", "Nasdaq 100"])

with tab_usa:
    # --- METRIKEN ÜBERSICHT ---
    col_a, col_b, col_c = st.columns(3)
    
    latest_bench_price = bench_df['Close'].iloc[-1]
    latest_bench_sma = bench_df['SMA30'].iloc[-1]
    latest_bench_slope = bench_df['SMA30_Slope_4W'].iloc[-1]
    
    col_a.metric("S&P 500 Kurs", f"{latest_bench_price:.2f}")
    col_b.metric("30W-MA", f"{latest_bench_sma:.2f}")
    col_c.metric("MA-Steigung 4W", f"{latest_bench_slope:.2f}%")

    st.markdown("---")
    st.subheader("Sektoren — sortiert nach Mansfield-RS")

    # --- SEKTOREN CARDS (2x4 GRID) ---
    sector_results = []
    
    for name, ticker in SECTORS.items():
        try:
            sec_df = get_data(ticker)
            sec_df['Mansfield_RS'] = calculate_mansfield_rs(sec_df, bench_df)
            
            p = sec_df['Close'].iloc[-1]
            sma = sec_df['SMA30'].iloc[-1]
            slope = sec_df['SMA30_Slope_4W'].iloc[-1]
            m_rs = sec_df['Mansfield_RS'].iloc[-1]
            stage, css = determine_stage(p, sma, slope)
            
            sector_results.append({
                'name': name,
                'ticker': ticker,
                'price': p,
                'sma': sma,
                'slope': slope,
                'm_rs': m_rs,
                'stage': stage,
                'css': css,
                'df': sec_df
            })
        except Exception as e:
            pass

    # Sortieren nach Mansfield RS
    sector_results = sorted(sector_results, key=lambda x: x['m_rs'], reverse=True)

    # Darstellung in 4 Spalten
    cols = st.columns(4)
    for idx, item in enumerate(sector_results):
        col = cols[idx % 4]
        with col:
            with st.container(border=True):
                st.markdown(f"**{item['name']}**")
                st.markdown(f"<span style='padding:3px 8px; border-radius:5px; {item['css']}'>{item['stage']}</span>", unsafe_allow_html=True)
                
                # Mini-Chart (Sparkline mit Kurs + SMA30)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=item['df'].index[-52:], y=item['df']['Close'].iloc[-52:], mode='lines', name='Kurs', line=dict(color='blue', width=1.5)))
                fig.add_trace(go.Scatter(x=item['df'].index[-52:], y=item['df']['SMA30'].iloc[-52:], mode='lines', name='SMA30', line=dict(color='orange', width=1.5)))
                fig.update_layout(height=150, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False))
                st.plotly_chart(fig, use_container_width=True)
                
                # Zahlen
                st.write(f"**Kurs:** {item['price']:.2f} | **30W-MA:** {item['sma']:.2f}")
                st.write(f"**MA-Steigung 4W:** {item['slope']:.2f}%")
                st.write(f"**Mansfield-RS:** `{item['m_rs']:+.2f}`")

