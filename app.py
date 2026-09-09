import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Weinstein Stage-Analysis Dashboard | Simon Moskwa", layout="wide")

# Titel & Autor-Information
st.title("Weinstein Stage-Analysis RS-Dashboard")
st.markdown("### Erstellt von **Simon Moskwa**")
st.caption("Markt → Sektor → Top-Aktien | Basierend auf Stan Weinsteins Phasenanalyse (Wochencharts, 30-Wochen-SMA & Mansfield Relative Strength)")

BENCHMARK = "^GSPC"

# Sektoren mit ihren wichtigsten Top-Aktien (Ticker & Vollständiger Name)
SECTOR_COMPONENTS = {
    "Energy (XLE)": {
        "ticker": "XLE",
        "stocks": {
            "XOM": "Exxon Mobil Corp.",
            "CVX": "Chevron Corp.",
            "COP": "ConocoPhillips",
            "SLB": "Schlumberger Ltd.",
            "EOG": "EOG Resources Inc.",
            "MPC": "Marathon Petroleum Corp.",
            "PSX": "Phillips 66",
            "VLO": "Valero Energy Corp."
        }
    },
    "Technology (XLK)": {
        "ticker": "XLK",
        "stocks": {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corp.",
            "NVDA": "NVIDIA Corp.",
            "AVGO": "Broadcom Inc.",
            "AMD": "Advanced Micro Devices",
            "ADBE": "Adobe Inc.",
            "CRM": "Salesforce Inc.",
            "ORCL": "Oracle Corp."
        }
    },
    "Financials (XLF)": {
        "ticker": "XLF",
        "stocks": {
            "JPM": "JPMorgan Chase & Co.",
            "BAC": "Bank of America Corp.",
            "WFC": "Wells Fargo & Co.",
            "C": "Citigroup Inc.",
            "GS": "Goldman Sachs Group",
            "MS": "Morgan Stanley",
            "BLK": "BlackRock Inc.",
            "V": "Visa Inc."
        }
    },
    "Health Care (XLV)": {
        "ticker": "XLV",
        "stocks": {
            "LLY": "Eli Lilly and Co.",
            "UNH": "UnitedHealth Group",
            "JNJ": "Johnson & Johnson",
            "ABBV": "AbbVie Inc.",
            "MRK": "Merck & Co. Inc.",
            "AMGN": "Amgen Inc.",
            "PFE": "Pfizer Inc.",
            "TMO": "Thermo Fisher Scientific"
        }
    },
    "Communication Services (XLC)": {
        "ticker": "XLC",
        "stocks": {
            "META": "Meta Platforms Inc.",
            "GOOGL": "Alphabet Inc.",
            "NFLX": "Netflix Inc.",
            "TMUS": "T-Mobile US Inc.",
            "DIS": "Walt Disney Co.",
            "CMCSA": "Comcast Corp."
        }
    },
    "Consumer Discretionary (XLY)": {
        "ticker": "XLY",
        "stocks": {
            "AMZN": "Amazon.com Inc.",
            "TSLA": "Tesla Inc.",
            "HD": "Home Depot Inc.",
            "MCD": "McDonald's Corp.",
            "NKE": "NIKE Inc.",
            "BKNG": "Booking Holdings Inc.",
            "SBUX": "Starbucks Corp."
        }
    },
    "Consumer Staples (XLP)": {
        "ticker": "XLP",
        "stocks": {
            "PG": "Procter & Gamble Co.",
            "COST": "Costco Wholesale Corp.",
            "PEP": "PepsiCo Inc.",
            "KO": "Coca-Cola Co.",
            "WMT": "Walmart Inc.",
            "PM": "Philip Morris Int."
        }
    },
    "Materials (XLB)": {
        "ticker": "XLB",
        "stocks": {
            "LIN": "Linde plc",
            "APD": "Air Products & Chemicals",
            "SHW": "Sherwin-Williams Co.",
            "FCX": "Freeport-McMoRan Inc.",
            "ECL": "Ecolab Inc.",
            "NEM": "Newmont Corp."
        }
    }
}

@st.cache_data(ttl=1800)
def get_data(ticker):
    df = yf.download(ticker, period="3y", interval="1wk", auto_adjust=True)
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

# Daten für Benchmark (S&P 500)
bench_df = get_data(BENCHMARK)

# Markt-Kopfzeile
col_a, col_b, col_c = st.columns(3)
latest_bench_price = bench_df['Close'].iloc[-1]
latest_bench_sma = bench_df['SMA30'].iloc[-1]
latest_bench_slope = bench_df['SMA30_Slope_4W'].iloc[-1]

col_a.metric("S&P 500 Kurs (Wochenbasis)", f"{latest_bench_price:.2f}")
col_b.metric("30-Wochen-SMA", f"{latest_bench_sma:.2f}")
col_c.metric("30W-MA Steigung (4W)", f"{latest_bench_slope:.2f}%")

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
            
            # Sektor-Chart (2 Jahre Wochenbasis = ~104 Kerzen)
            plot_df = item['df'].tail(104)
            
            # Dynamische Grenzen für die X-Achse (mit 21 Tagen Puffer nach rechts)
            x_min = plot_df.index.min()
            x_max = plot_df.index.max() + pd.Timedelta(days=21)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=plot_df.index, y=plot_df['Close'],
                mode='lines', name='Wochenkurs',
                line=dict(color='#1f77b4', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=plot_df.index, y=plot_df['SMA30'],
                mode='lines', name='30-Wochen SMA',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
            fig.update_layout(
                height=230, 
                margin=dict(l=10, r=10, t=10, b=10), 
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(title="Datum (Wochen)", visible=True, range=[x_min, x_max]),
                yaxis=dict(title="Kurs ($)", visible=True)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.write(f"**Mansfield-RS:** `{item['m_rs']:+.2f}` | **30W-MA Steigung:** `{item['slope']:.2f}%`")
            
            # Einzelaktien-Analyse für diesen Sektor
            with st.expander("🔍 Top-Aktien im Stage-2-Setup anzeigen"):
                stock_data = []
                stock_dfs = {}
                
                for stk_ticker, stk_name in item['stocks'].items():
                    try:
                        stk_df = get_data(stk_ticker)
                        stk_df['Mansfield_RS'] = calculate_mansfield_rs(stk_df, bench_df)
                        stk_p = stk_df['Close'].iloc[-1]
                        stk_sma = stk_df['SMA30'].iloc[-1]
                        stk_slope = stk_df['SMA30_Slope_4W'].iloc[-1]
                        stk_mrs = stk_df['Mansfield_RS'].iloc[-1]
                        
                        if stk_p > stk_sma and stk_slope > 0 and stk_mrs > 0:
                            stock_data.append({
                                'Ticker': stk_ticker,
                                'Name': stk_name,
                                'Kurs': f"${stk_p:.2f}",
                                '30W-SMA': f"${stk_sma:.2f}",
                                'SMA-Steigung': f"{stk_slope:.2f}%",
                                'Mansfield-RS': round(stk_mrs, 2)
                            })
                            stock_dfs[stk_ticker] = (stk_name, stk_df)
                    except Exception:
                        pass
                
                if stock_data:
                    stock_df = pd.DataFrame(stock_data).sort_values(by='Mansfield-RS', ascending=False)
                    
                    st.dataframe(
                        stock_df[['Name', 'Ticker', 'Kurs', '30W-SMA', 'SMA-Steigung', 'Mansfield-RS']], 
                        hide_index=True, 
                        use_container_width=True
                    )
                    
                    st.markdown("---")
                    selected_ticker = st.selectbox(
                        "📊 Detail-Wochenchart anzeigen für:",
                        options=list(stock_dfs.keys()),
                        format_func=lambda x: f"{stock_dfs[x][0]} ({x})",
                        key=f"select_{item['ticker']}"
                    )
                    
                    if selected_ticker:
                        selected_name, s_df = stock_dfs[selected_ticker]
                        s_plot_df = s_df.tail(104)
                        
                        s_x_min = s_plot_df.index.min()
                        s_x_max = s_plot_df.index.max() + pd.Timedelta(days=21)
                        
                        fig_stock = make_subplots(
                            rows=2, cols=1, 
                            shared_xaxes=True, 
                            vertical_spacing=0.08,
                            row_heights=[0.7, 0.3]
                        )
                        
                        fig_stock.add_trace(go.Scatter(
                            x=s_plot_df.index, y=s_plot_df['Close'],
                            mode='lines', name='Wochenkurs ($)',
                            line=dict(color='#1f77b4', width=2)
                        ), row=1, col=1)
                        
                        fig_stock.add_trace(go.Scatter(
                            x=s_plot_df.index, y=s_plot_df['SMA30'],
                            mode='lines', name='30-Wochen SMA',
                            line=dict(color='#ff7f0e', width=2, dash='dash')
                        ), row=1, col=1)
                        
                        fig_stock.add_trace(go.Scatter(
                            x=s_plot_df.index, y=s_plot_df['Mansfield_RS'],
                            mode='lines', name='Mansfield RS',
                            line=dict(color='#2ca02c', width=1.5)
                        ), row=2, col=1)
                        
                        fig_stock.add_trace(go.Scatter(
                            x=s_plot_df.index, y=[0]*len(s_plot_df),
                            mode='lines', name='RS Zero Line',
                            line=dict(color='gray', width=1, dash='dot')
                        ), row=2, col=1)
                        
                        fig_stock.update_layout(
                            height=380, 
                            margin=dict(l=10, r=10, t=20, b=10), 
                            showlegend=True,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        
                        fig_stock.update_yaxes(title_text="Preis ($)", row=1, col=1)
                        fig_stock.update_yaxes(title_text="Mansfield RS", row=2, col=1)
                        fig_stock.update_xaxes(title_text="Datum (Wochen)", row=2, col=1, range=[s_x_min, s_x_max])
                        
                        st.caption(f"Stan Weinstein Phasen-Chart: **{selected_name} ({selected_ticker})**")
                        st.plotly_chart(fig_stock, use_container_width=True)
                else:
                    st.info("Aktuell keine Einzelaktie in diesem Sektor mit perfektem Stage-2-Setup.")
