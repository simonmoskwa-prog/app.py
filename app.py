import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Weinstein Stage-Analysis Dashboard", layout="wide")

st.title("Weinstein Stage-Analysis RS-Dashboard")
st.caption("Markt → Sektor → Top-Aktien | Basierend auf Stan Weinsteins Phasenanalyse")

BENCHMARK = "^GSPC"

# Sektoren mit ihren wichtigsten Top-Aktien (US Mega/Large Caps)
SECTOR_COMPONENTS = {
    "Energy (XLE)": {
        "ticker": "XLE",
        "stocks": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO"]
    },
    "Technology (XLK)": {
        "ticker": "XLK",
        "stocks": ["AAPL", "MSFT", "NVDA", "AVGO", "AMD", "ADBE", "CRM", "ORCL"]
    },
    "Financials (XLF)": {
        "ticker": "XLF",
        "stocks": ["JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "V"]
    },
    "Health Care (XLV)": {
        "ticker": "XLV",
        "stocks": ["LLY", "UNH", "JNJ", "ABBV", "MRK", "AMGN", "PFE", "TMO"]
    },
    "Communication Services (XLC)": {
        "ticker": "XLC",
        "stocks": ["META", "GOOGL", "NFLX", "TMUS", "DIS", "CMCSA"]
    },
    "Consumer Discretionary (XLY)": {
        "ticker": "XLY",
        "stocks": ["AMZN", "TSLA", "HD", "MCD", "NKE", "BKNG", "SBUX"]
    },
    "Consumer Staples (XLP)": {
        "ticker": "XLP",
        "stocks": ["PG", "COST", "PEP", "KO", "WMT", "PM"]
    },
    "Materials (XLB)": {
        "ticker": "XLB",
        "stocks": ["LIN", "APD", "SHW", "FCX", "ECL", "NEM"]
    }
}

@st.cache_data(ttl=3600)
def get_data(ticker):
    df = yf.download(ticker, period="3y", interval="1wk")
    if isinstance(df.columns, pd.MultiIndex):
        df = df.xs(ticker, level=1, axis=1)
    df = df[['Close', 'Volume']].dropna()
    df['SMA30'] = df['Close'].rolling(window=30).mean()
    df['SMA30_Slope_4W'] = ((df['SMA30'] - df['SMA30'].shift(4)) / df['SMA30'].shift(4)) * 100
    return df

def calculate_mansfield_rs(asset_df, benchmark_df):
    combined = pd.DataFrame({
        'Asset': asset_df['Close'],
        'Bench': benchmark_df['Close']
    }).dropna()
    base_rs = combined['Asset'] / combined['Bench']
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

# Daten für Benchmark
bench_df = get_data(BENCHMARK)

# Markt-Kopfzeile
col_a, col_b, col_c = st.columns(3)
latest_bench_price = bench_df['Close'].iloc[-1]
latest_bench_sma = bench_df['SMA30'].iloc[-1]
latest_bench_slope = bench_df['SMA30_Slope_4W'].iloc[-1]

col_a.metric("S&P 500 Kurs", f"{latest_bench_price:.2f}")
col_b.metric("30W-MA", f"{latest_bench_sma:.2f}")
col_c.metric("MA-Steigung 4W", f"{latest_bench_slope:.2f}%")

st.markdown("---")
st.subheader("Sektoren & Top-Performer (Stage 2)")

# Sektoren verarbeiten
sector_results = []
for sec_name, sec_info in SECTOR_COMPONENTS.items():
    try:
        sec_df = get_data(sec_info["ticker"])
        sec_df['Mansfield_RS'] = calculate_mansfield_rs(sec_df, bench_df)
        p = sec_df['Close'].iloc[-1]
        sma = sec_df['SMA30'].iloc[-1]
        slope = sec_df['SMA30_Slope_4W'].iloc[-1]
        m_rs = sec_df['Mansfield_RS'].iloc[-1]
        stage, css = determine_stage(p, sma, slope)
        
        sector_results.append({
            'name': sec_name,
            'ticker': sec_info["ticker"],
            'stocks': sec_info["stocks"],
            'price': p,
            'sma': sma,
            'slope': slope,
            'm_rs': m_rs,
            'stage': stage,
            'css': css,
            'df': sec_df
        })
    except Exception:
        pass

# Nach Mansfield-RS sortieren
sector_results = sorted(sector_results, key=lambda x: x['m_rs'], reverse=True)

# Kacheln anzeigen
cols = st.columns(2)
for idx, item in enumerate(sector_results):
    col = cols[idx % 2]
    with col:
        with st.container(border=True):
            st.markdown(f"### {item['name']}")
            st.markdown(f"<span style='padding:3px 8px; border-radius:5px; {item['css']}'>{item['stage']}</span>", unsafe_allow_html=True)
            
            # Mini-Chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=item['df'].index[-52:], y=item['df']['Close'].iloc[-52:], mode='lines', line=dict(color='blue', width=1.5)))
            fig.add_trace(go.Scatter(x=item['df'].index[-52:], y=item['df']['SMA30'].iloc[-52:], mode='lines', line=dict(color='orange', width=1.5)))
            fig.update_layout(height=130, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False))
            st.plotly_chart(fig, use_container_width=True)
            
            st.write(f"**Mansfield-RS:** `{item['m_rs']:+.2f}` | **MA-Steigung:** `{item['slope']:.2f}%`")
            
            # Einzelaktien-Analyse für diesen Sektor
            with st.expander("🔍 Top-Aktien im Stage-2-Setup anzeigen"):
                stock_data = []
                for stk in item['stocks']:
                    try:
                        stk_df = get_data(stk)
                        stk_df['Mansfield_RS'] = calculate_mansfield_rs(stk_df, bench_df)
                        stk_p = stk_df['Close'].iloc[-1]
                        stk_sma = stk_df['SMA30'].iloc[-1]
                        stk_slope = stk_df['SMA30_Slope_4W'].iloc[-1]
                        stk_mrs = stk_df['Mansfield_RS'].iloc[-1]
                        
                        # Filter: Nur Stage 2 & Positiver RS
                        if stk_p > stk_sma and stk_slope > 0 and stk_mrs > 0:
                            stock_data.append({
                                'Aktie': stk,
                                'Kurs': f"${stk_p:.2f}",
                                '30W-MA': f"${stk_sma:.2f}",
                                'Steigung': f"{stk_slope:.2f}%",
                                'Mansfield-RS': round(stk_mrs, 2)
                            })
                    except Exception:
                        pass
                
                if stock_data:
                    # Sortieren nach stärkstem Mansfield-RS
                    stock_df = pd.DataFrame(stock_data).sort_values(by='Mansfield-RS', ascending=False)
                    st.dataframe(stock_df, hide_index=True, use_container_width=True)
                else:
                    st.info("Aktuell keine Einzelaktie in diesem Sektor mit perfektem Stage-2-Setup.")
