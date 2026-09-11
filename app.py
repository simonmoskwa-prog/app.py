import base64
import datetime
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Stage-Analysis RS Dashboard | Pulse Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# CUSTOM CSS FOR VISUAL ENHANCEMENT
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Hauptcontainer-Hintergrund & Schrift */
    .main {
        padding-top: 1rem;
    }
    
    /* Karten-Kacheln Styling */
    div[data-testid="stContainer"] {
        border-radius: 12px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    /* Metrik-Boxen Veredelung */
    div[data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        font-weight: 700;
    }
    
    /* Button Styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_b64 = get_image_base64("logo.png")


# ---------------------------------------------------------
# DIALOG / POPUP FOR CONTACT US
# ---------------------------------------------------------
@st.dialog("📩 Contact Us")
def show_contact_dialog():
    st.markdown("### Get in Touch")
    st.write(
        "If you are interested in stocks, feel free to contact me for an exchange at "
        "**[simon.moskwa@outlook.de](mailto:simon.moskwa@outlook.de)**."
    )
    st.markdown("---")
    st.caption("Pulse Trading / Simon Moskwa")


# ---------------------------------------------------------
# HEADER SECTION
# ---------------------------------------------------------
header_col1, header_col2, header_col3 = st.columns([1.2, 5, 1.8])

with header_col1:
    if logo_b64:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: center; padding-top: 5px;">
                <img src="data:image/png;base64,{logo_b64}" 
                     style="width: 110px; height: auto; object-fit: contain; image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges; border-radius: 8px;">
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("PULSE TRADING")

with header_col2:
    st.title("Stage-Analysis RS-Dashboard")
    st.markdown("##### Powered by **Pulse Trading / Simon Moskwa**")
    st.caption(
        "Markt → Sektor → Top-Aktien | Technisches 4-Phasen-Marktmodell "
        "(Wochencharts, 30-Wochen-SMA & Mansfield Relative Strength)"
    )

with header_col3:
    st.write("") # Abstandhalter
    if st.button("📩 Contact Us", use_container_width=True, type="primary"):
        show_contact_dialog()

BENCHMARK = "^GSPC"

# Markt-Indizes Konfiguration
INDICES_CONFIG = {
    "USA (S&P 500)": {
        "ticker": "^GSPC",
        "desc": "State Street SPDR S&P 500 ETF Trust / Index",
    },
    "Nasdaq 100": {"ticker": "^NDX", "desc": "Invesco QQQ Trust / Nasdaq 100 Index"},
    "Russell 2000": {
        "ticker": "^RUT",
        "desc": "iShares Russell 2000 ETF / Small Caps",
    },
    "Euro Stoxx 600": {"ticker": "^STOXX", "desc": "STXE 600 EUR Price Index"},
    "DAX": {"ticker": "^GDAXI", "desc": "DAX Performance-Index (Deutschland)"},
    "Nikkei 225": {"ticker": "^N225", "desc": "Nikkei 225 Index (Japan)"},
    "Hang Seng": {"ticker": "^HSI", "desc": "Hang Seng Index (Hongkong)"},
    "MSCI World": {"ticker": "URTH", "desc": "iShares MSCI World ETF"},
    "VIX": {"ticker": "^VIX", "desc": "CBOE Volatility Index"},
}

# Sektoren mit ihren wichtigsten Top-Aktien
SECTOR_COMPONENTS = {
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
            "ORCL": "Oracle Corp.",
        },
    },
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
            "VLO": "Valero Energy Corp.",
        },
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
            "V": "Visa Inc.",
        },
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
            "TMO": "Thermo Fisher Scientific",
        },
    },
    "Communication Services (XLC)": {
        "ticker": "XLC",
        "stocks": {
            "META": "Meta Platforms Inc.",
            "GOOGL": "Alphabet Inc.",
            "NFLX": "Netflix Inc.",
            "TMUS": "T-Mobile US Inc.",
            "DIS": "Walt Disney Co.",
            "CMCSA": "Comcast Corp.",
        },
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
            "SBUX": "Starbucks Corp.",
        },
    },
    "Consumer Staples (XLP)": {
        "ticker": "XLP",
        "stocks": {
            "PG": "Procter & Gamble Co.",
            "COST": "Costco Wholesale Corp.",
            "PEP": "PepsiCo Inc.",
            "KO": "Coca-Cola Co.",
            "WMT": "Walmart Inc.",
            "PM": "Philip Morris Int.",
        },
    },
    "Materials (XLB)": {
        "ticker": "XLB",
        "stocks": {
            "LIN": "Linde plc",
            "APD": "Air Products & Chemicals",
            "SHW": "Sherwin-Williams Co.",
            "FCX": "Freeport-McMoRan Inc.",
            "ECL": "Ecolab Inc.",
            "NEM": "Newmont Corp.",
        },
    },
}


@st.cache_data(ttl=300)
def get_data(ticker):
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=4 * 365)

    df = yf.download(
        ticker,
        start=start_date,
        end=today + datetime.timedelta(days=2),
        interval="1wk",
        auto_adjust=True,
    )
    if isinstance(df.columns, pd.MultiIndex):
        df = df.xs(ticker, level=1, axis=1)
    df = df[["Close", "Volume"]].dropna()

    df.index = pd.to_datetime(df.index)

    # 30-Wochen-SMA (Phasenanalyse)
    df["SMA30"] = df["Close"].rolling(window=30).mean()
    df["SMA30_Slope_4W"] = (
        (df["SMA30"] - df["SMA30"].shift(4)) / df["SMA30"].shift(4)
    ) * 100
    return df


def calculate_mansfield_rs(asset_df, benchmark_df):
    combined = pd.DataFrame(
        {"Asset": asset_df["Close"], "Bench": benchmark_df["Close"]}
    ).dropna()
    base_rs = combined["Asset"] / combined["Bench"]
    rs_sma52 = base_rs.rolling(window=52).mean()
    mansfield_rs = ((base_rs / rs_sma52) - 1) * 100
    return mansfield_rs


def determine_stage(price, sma30, slope):
    if price > sma30 and slope > 0.5:
        return (
            "Stage 2 (Aufwärtstrend)",
            "background-color: #28a745; color: #ffffff; border: 1px solid #1e7e34;",
        )
    elif price < sma30 and slope < -0.5:
        return (
            "Stage 4 (Abwärtstrend)",
            "background-color: #dc3545; color: #ffffff; border: 1px solid #bd2130;",
        )
    elif price > sma30 and slope <= 0.5:
        return (
            "Stage 1 / 3 (Konsolidierung)",
            "background-color: #ffc107; color: #212529; border: 1px solid #d39e00;",
        )
    else:
        return (
            "Stage 1 / 3 (Boden / Topp)",
            "background-color: #6c757d; color: #ffffff; border: 1px solid #545b62;",
        )


# Benchmark-Daten laden
bench_df = get_data(BENCHMARK)

# ==========================================
# MARKT-ÜBERSICHT / INDEX-TABS
# ==========================================
st.markdown("---")
st.subheader("🌐 Markt-Übersicht")

tabs = st.tabs(list(INDICES_CONFIG.keys()))

for tab, (idx_name, idx_info) in zip(tabs, INDICES_CONFIG.items()):
    with tab:
        try:
            df_idx = get_data(idx_info["ticker"])
            p_idx = df_idx["Close"].iloc[-1]
            sma_idx = df_idx["SMA30"].iloc[-1]
            slope_idx = df_idx["SMA30_Slope_4W"].iloc[-1]
            stage_str, css_style = determine_stage(p_idx, sma_idx, slope_idx)

            with st.container(border=True):
                col_left, col_mid, col_right = st.columns([2.5, 2.5, 3])

                with col_left:
                    st.caption("INDEX / MARKT")
                    st.markdown(f"### {idx_name}")
                    st.caption(idx_info["desc"])
                    st.markdown(
                        f"<span style='padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 13px; {css_style}'>"
                        f"{stage_str}</span>",
                        unsafe_allow_html=True,
                    )

                with col_mid:
                    st.write("")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Kurs", f"{p_idx:.2f}")
                    m2.metric("30W-SMA", f"{sma_idx:.2f}")
                    m3.metric("MA-Steigung (4W)", f"{slope_idx:+.2f}%")

                with col_right:
                    plot_df = df_idx.tail(104)
                    future_date = pd.Timestamp.now() + pd.Timedelta(days=35)

                    fig_idx = go.Figure()
                    fig_idx.add_trace(
                        go.Scatter(
                            x=plot_df.index,
                            y=plot_df["Close"],
                            mode="lines",
                            name="Kurs",
                            line=dict(color="#0066CC", width=2),
                        )
                    )
                    fig_idx.add_trace(
                        go.Scatter(
                            x=plot_df.index,
                            y=plot_df["SMA30"],
                            mode="lines",
                            name="30W-SMA",
                            line=dict(color="#FF9900", width=2, dash="dash"),
                        )
                    )
                    fig_idx.add_trace(
                        go.Scatter(
                            x=[future_date],
                            y=[plot_df["Close"].iloc[-1]],
                            mode="markers",
                            marker=dict(size=0, color="rgba(0,0,0,0)"),
                            showlegend=False,
                            hoverinfo="skip",
                        )
                    )
                    fig_idx.update_layout(
                        height=210,
                        margin=dict(l=5, r=5, t=10, b=20),
                        showlegend=False,
                        xaxis=dict(
                            visible=True,
                            autorange=True,
                            tickformat="%b %Y",
                            showgrid=False
                        ),
                        yaxis=dict(visible=True, showgrid=True, gridcolor="rgba(200,200,200,0.2)"),
                    )
                    st.plotly_chart(fig_idx, use_container_width=True)
        except Exception:
            st.error(f"Daten für {idx_name} konnten nicht geladen werden.")

st.markdown("---")
st.subheader("📊 Sektoren & Top-Performer (Stage 2 Focus)")

# Sektoren verarbeiten
sector_results = []
for sec_name, sec_info in SECTOR_COMPONENTS.items():
    try:
        sec_df = get_data(sec_info["ticker"])
        sec_df["Mansfield_RS"] = calculate_mansfield_rs(sec_df, bench_df)
        p = sec_df["Close"].iloc[-1]
        sma = sec_df["SMA30"].iloc[-1]
        slope = sec_df["SMA30_Slope_4W"].iloc[-1]
        m_rs = sec_df["Mansfield_RS"].iloc[-1]
        stage, css = determine_stage(p, sma, slope)

        sector_results.append({
            "name": sec_name,
            "ticker": sec_info["ticker"],
            "stocks": sec_info["stocks"],
            "price": p,
            "sma": sma,
            "slope": slope,
            "m_rs": m_rs,
            "stage": stage,
            "css": css,
            "df": sec_df,
        })
    except Exception:
        pass

# Nach Mansfield-RS sortieren
sector_results = sorted(sector_results, key=lambda x: x["m_rs"], reverse=True)

# Kacheln im 2-Spalten-Grid anzeigen
cols = st.columns(2)
for idx, item in enumerate(sector_results):
    col = cols[idx % 2]
    with col:
        with st.container(border=True):
            st.markdown(f"### {item['name']}")
            st.markdown(
                f"<span style='padding:4px 10px; border-radius:12px; font-size:12px; font-weight:600; "
                f"{item['css']}'>{item['stage']}</span>",
                unsafe_allow_html=True,
            )

            # Sektor-Chart
            plot_df = item["df"].tail(104)
            future_date = pd.Timestamp.now() + pd.Timedelta(days=35)

            fig = go.Figure()

            # Wochenkurs
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["Close"],
                    mode="lines",
                    name="Kurs",
                    line=dict(color="#0066CC", width=2),
                )
            )

            # 30-Wochen-SMA
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["SMA30"],
                    mode="lines",
                    name="30W-SMA",
                    line=dict(color="#FF9900", width=2, dash="dash"),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=[future_date],
                    y=[plot_df["Close"].iloc[-1]],
                    mode="markers",
                    marker=dict(size=0, color="rgba(0,0,0,0)"),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

            fig.update_layout(
                height=230,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
                xaxis=dict(
                    visible=True,
                    autorange=True,
                    tickformat="%b %Y",
                    showgrid=False
                ),
                yaxis=dict(visible=True, showgrid=True, gridcolor="rgba(200,200,200,0.1)"),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Kennzahlen-Zeile
            st.markdown(
                f"**Mansfield-RS:** `<span style='color:{'#28a745' if item['m_rs'] > 0 else '#dc3545'};'>{item['m_rs']:+.2f}</span>` | "
                f"**30W-SMA Steigung:** `{item['slope']:+.2f}%`",
                unsafe_allow_html=True
            )

            # Einzelaktien-Analyse für diesen Sektor
            with st.expander("🔍 Top-Aktien im Stage-2-Setup anzeigen"):
                stock_data = []
                stock_dfs = {}

                for stk_ticker, stk_name in item["stocks"].items():
                    try:
                        stk_df = get_data(stk_ticker)
                        stk_df["Mansfield_RS"] = calculate_mansfield_rs(stk_df, bench_df)
                        stk_p = stk_df["Close"].iloc[-1]
                        stk_sma = stk_df["SMA30"].iloc[-1]
                        stk_slope = stk_df["SMA30_Slope_4W"].iloc[-1]
                        stk_mrs = stk_df["Mansfield_RS"].iloc[-1]

                        if stk_p > stk_sma and stk_slope > 0 and stk_mrs > 0:
                            stock_data.append({
                                "Ticker": stk_ticker,
                                "Name": stk_name,
                                "Kurs": f"${stk_p:.2f}",
                                "30W-SMA": f"${stk_sma:.2f}",
                                "SMA-Steigung": f"{stk_slope:+.2f}%",
                                "Mansfield-RS": round(stk_mrs, 2),
                            })
                            stock_dfs[stk_ticker] = (stk_name, stk_df)
                    except Exception:
                        pass

                if stock_data:
                    stock_df = pd.DataFrame(stock_data).sort_values(
                        by="Mansfield-RS", ascending=False
                    )

                    st.dataframe(
                        stock_df[[
                            "Name",
                            "Ticker",
                            "Kurs",
                            "30W-SMA",
                            "SMA-Steigung",
                            "Mansfield-RS",
                        ]],
                        hide_index=True,
                        use_container_width=True,
                    )

                    st.markdown("---")
                    selected_ticker = st.selectbox(
                        "📊 Detail-Wochenchart anzeigen für:",
                        options=list(stock_dfs.keys()),
                        format_func=lambda x: f"{stock_dfs[x][0]} ({x})",
                        key=f"select_{item['ticker']}",
                    )

                    if selected_ticker:
                        selected_name, s_df = stock_dfs[selected_ticker]
                        s_plot_df = s_df.tail(104)

                        fig_stock = make_subplots(
                            rows=2,
                            cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.08,
                            row_heights=[0.7, 0.3],
                        )

                        # Haupt-Chart (Kurs & MA)
                        fig_stock.add_trace(
                            go.Scatter(
                                x=s_plot_df.index,
                                y=s_plot_df["Close"],
                                mode="lines",
                                name="Wochenkurs ($)",
                                line=dict(color="#0066CC", width=2),
                            ),
                            row=1,
                            col=1,
                        )

                        fig_stock.add_trace(
                            go.Scatter(
                                x=s_plot_df.index,
                                y=s_plot_df["SMA30"],
                                mode="lines",
                                name="30W-SMA",
                                line=dict(color="#FF9900", width=2, dash="dash"),
                            ),
                            row=1,
                            col=1,
                        )

                        # Mansfield RS Subplot
                        fig_stock.add_trace(
                            go.Scatter(
                                x=s_plot_df.index,
                                y=s_plot_df["Mansfield_RS"],
                                mode="lines",
                                name="Mansfield RS",
                                line=dict(color="#28a745", width=1.5),
                            ),
                            row=2,
                            col=1,
                        )

                        fig_stock.add_trace(
                            go.Scatter(
                                x=s_plot_df.index,
                                y=[0] * len(s_plot_df),
                                mode="lines",
                                name="Nulllinie",
                                line=dict(color="gray", width=1, dash="dot"),
                            ),
                            row=2,
                            col=1,
                        )

                        fig_stock.update_layout(
                            height=380,
                            margin=dict(l=10, r=10, t=20, b=10),
                            showlegend=True,
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1,
                            ),
                        )

                        fig_stock.update_yaxes(title_text="Preis ($)", row=1, col=1)
                        fig_stock.update_yaxes(title_text="Mansfield RS", row=2, col=1)
                        fig_stock.update_xaxes(
                            row=2,
                            col=1,
                            autorange=True,
                            tickformat="%b %Y",
                        )

                        st.caption(f"Phasenanalyse Detail-Chart: **{selected_name} ({selected_ticker})**")
                        st.plotly_chart(fig_stock, use_container_width=True)
                else:
                    st.info(
                        "Aktuell keine Einzelaktie in diesem Sektor mit aktivem Stage-2-Setup."
                    )
