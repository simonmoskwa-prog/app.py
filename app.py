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
# CUSTOM CSS FOR HIGH-END MODERN UI
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Global Container Styling */
    .main {
        padding-top: 1rem;
    }
    
    /* Modern Glassmorphism Cards */
    div[data-testid="stContainer"] {
        border-radius: 14px;
        background: rgba(22, 27, 34, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: all 0.3s ease;
    }
    
    div[data-testid="stContainer"]:hover {
        border-color: rgba(0, 210, 255, 0.4);
        box-shadow: 0 8px 32px 0 rgba(0, 210, 255, 0.15);
    }
    
    /* Typography & Header Polish */
    .dashboard-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 0px;
        line-height: 1.2;
        background: linear-gradient(90deg, #ffffff 0%, #a5b4fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .dashboard-subtitle {
        font-size: 0.9rem;
        color: #94a3b8;
        margin-top: 4px;
        font-weight: 500;
    }

    /* Metric Formatting */
    div[data-testid="stMetricValue"] {
        font-size: 1.35rem !important;
        font-weight: 700;
        letter-spacing: -0.3px;
    }
    
    /* Modernized Buttons */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.15);
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #f8fafc;
        transition: all 0.25s ease-in-out;
    }
    .stButton>button:hover {
        border-color: #38bdf8;
        color: #38bdf8;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
    }
    
    /* Elegant Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    /* Disclaimer & Footer */
    .disclaimer-box {
        background-color: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 18px;
        font-size: 0.8rem;
        line-height: 1.5;
        color: #64748b;
        margin-top: 40px;
    }
    
    .status-badge-open {
        color: #4ade80;
        background: rgba(74, 222, 128, 0.12);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid rgba(74, 222, 128, 0.3);
    }

    .status-badge-closed {
        color: #f87171;
        background: rgba(248, 113, 113, 0.12);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid rgba(248, 113, 113, 0.3);
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
# DIALOG / POPUP FOR CONTACT US & COMMUNITY
# ---------------------------------------------------------
@st.dialog("📩 Kontakt & Private Community")
def show_contact_dialog():
    st.markdown("### Kontakt")
    st.write(
        "Bei Fragen zu Aktien, Chartanalysen oder Interesse an unserem Austausch "
        "erreichst du mich unter **[simon.moskwa@outlook.de](mailto:simon.moskwa@outlook.de)**."
    )
    
    st.markdown("---")
    st.markdown("#### 💬 Privater Community-Austausch")
    st.write(
        "Wir bieten einen rein privaten, unentgeltlichen Austausch über WhatsApp für interessierte Trader an. "
        "Der Zugang wird individuell auf E-Mail-Anfrage gewährt."
    )

    st.markdown("---")
    st.warning(
        "**Rechtlicher Hinweis / Disclaimer:**\n\n"
        "Alle bereitgestellten Informationen, Kennzahlen und Analysen dienen ausschließlich rein informativen und privaten Bildungszwecken. "
        "Sie stellen keine Finanzberatung, Anlageberatung oder Kauf-/Verkaufsempfehlung dar."
    )
    
    st.caption("Pulse Trading • Simon Moskwa")


# ---------------------------------------------------------
# HEADER SECTION
# ---------------------------------------------------------
header_col1, header_col2, header_col3 = st.columns([1, 4.8, 1.6])

with header_col1:
    if logo_b64:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: center; padding-top: 2px;">
                <img src="data:image/png;base64,{logo_b64}" 
                     style="width: 95px; height: auto; object-fit: contain; border-radius: 8px;">
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.caption("PULSE TRADING")

with header_col2:
    st.markdown("<div class='dashboard-title'>Stage-Analysis RS-Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='dashboard-subtitle'>by <b>Pulse Trading</b> | Markt → Sektor → Top-Aktien (30W-SMA & Mansfield RS)</div>", unsafe_allow_html=True)

with header_col3:
    st.write("")
    if st.button("📩 Contact Us", use_container_width=True):
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
        df = yf.download(ticker, start=start_date, end=today + datetime.timedelta(days=2), interval="1wk", auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(ticker, level=1, axis=1)

    df = df[["Close", "Volume"]].dropna()
    df.index = pd.to_datetime(df.index)

    df["SMA30"] = df["Close"].rolling(window=30).mean()
    df["SMA30_Slope_4W"] = (
        (df["SMA30"] - df["SMA30"].shift(4)) / df["SMA30"].shift(4)
    ) * 100

    currency = "USD"
    is_open = False
    try:
        info = yticker.info
        currency = info.get("currency", "USD")
        
        last_date = df.index[-1].date()
        today_date = datetime.date.today()
        if (today_date - last_date).days <= 2 and today_date.weekday() < 5:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            if "DE" in ticker or "STX" in ticker or "DAX" in ticker:
                is_open = (8 <= now_utc.hour < 16.5)
            else:
                is_open = (13.5 <= now_utc.hour + now_utc.minute/60 <= 21)
    except Exception:
        pass

    return df, currency, is_open


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
            "background-color: rgba(40, 167, 69, 0.2); color: #2ecc71; border: 1px solid rgba(40, 167, 69, 0.5);",
        )
    elif price < sma30 and slope < -0.5:
        return (
            "Stage 4 (Abwärtstrend)",
            "background-color: rgba(220, 53, 69, 0.2); color: #e74c3c; border: 1px solid rgba(220, 53, 69, 0.5);",
        )
    elif price > sma30 and slope <= 0.5:
        return (
            "Stage 1 / 3 (Konsolidierung)",
            "background-color: rgba(255, 193, 7, 0.2); color: #f1c40f; border: 1px solid rgba(255, 193, 7, 0.5);",
        )
    else:
        return (
            "Stage 1 / 3 (Boden / Topp)",
            "background-color: rgba(108, 117, 125, 0.2); color: #95a5a6; border: 1px solid rgba(108, 117, 125, 0.5);",
        )


def compute_y_range(series_list, padding=0.08):
    """ Berechnet Min und Max über alle übergebenen Serien für eine mittige Darstellung """
    min_val = min(s.min() for s in series_list if not s.dropna().empty)
    max_val = max(s.max() for s in series_list if not s.dropna().empty)
    rng = max_val - min_val
    return [min_val - (rng * padding), max_val + (rng * padding)]


bench_df, _, _ = get_data_with_info(BENCHMARK)

# ==========================================
# MARKT-ÜBERSICHT / INDEX-TABS
# ==========================================
st.markdown("---")
st.subheader("🌐 Markt-Übersicht")

tabs = st.tabs(list(INDICES_CONFIG.keys()))

for tab, (idx_name, idx_info) in zip(tabs, INDICES_CONFIG.items()):
    with tab:
        try:
            df_idx, curr, market_open = get_data_with_info(idx_info["ticker"])
            p_idx = df_idx["Close"].iloc[-1]
            sma_idx = df_idx["SMA30"].iloc[-1]
            slope_idx = df_idx["SMA30_Slope_4W"].iloc[-1]
            stage_str, css_style = determine_stage(p_idx, sma_idx, slope_idx)

            status_badge = (
                "<span class='status-badge-open'>🟢 Börse Geöffnet</span>"
                if market_open
                else "<span class='status-badge-closed'>🔴 Börse Geschlossen</span>"
            )

            with st.container(border=True):
                col_left, col_mid, col_right = st.columns([2.5, 2.5, 3])

                with col_left:
                    st.caption(f"INDEX / MARKT | Währung: **{curr}**")
                    st.markdown(f"### {idx_name}")
                    st.caption(idx_info["desc"])
                    st.markdown(
                        f"<div style='margin-top: 6px; margin-bottom: 6px;'>"
                        f"<span style='padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 12px; {css_style}'>"
                        f"{stage_str}</span> &nbsp; {status_badge}</div>",
                        unsafe_allow_html=True,
                    )

                with col_mid:
                    st.write("")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Kurs", f"{p_idx:.2f} {curr}")
                    m2.metric("30W-SMA", f"{sma_idx:.2f} {curr}")
                    m3.metric("Steigung (4W)", f"{slope_idx:+.2f}%")

                with col_right:
                    plot_df = df_idx.tail(104)
                    y_range = compute_y_range([plot_df["Close"], plot_df["SMA30"]])

                    fig_idx = go.Figure()
                    
                    fig_idx.add_trace(
                        go.Scatter(
                            x=plot_df.index,
                            y=plot_df["Close"],
                            mode="lines",
                            name=f"Kurs ({curr})",
                            line=dict(color="#38bdf8", width=2.5),
                            fill='tozeroy',
                            fillcolor='rgba(56, 189, 248, 0.06)',
                            hovertemplate=f"<b>Datum:</b> %{{x|%d.%m.%Y}}<br><b>Kurs:</b> %{{y:.2f}} {curr}<extra></extra>",
                            connectgaps=True,
                        )
                    )
                    fig_idx.add_trace(
                        go.Scatter(
                            x=plot_df.index,
                            y=plot_df["SMA30"],
                            mode="lines",
                            name="30W-SMA",
                            line=dict(color="#fbbf24", width=2, dash="dash"),
                            hovertemplate=f"<b>30W-SMA:</b> %{{y:.2f}} {curr}<extra></extra>",
                            connectgaps=True,
                        )
                    )
                    
                    start_x = plot_df.index[0]
                    end_x = plot_df.index[-1] + datetime.timedelta(days=15)

                    fig_idx.update_layout(
                        height=220,
                        margin=dict(l=10, r=20, t=15, b=25),
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        hovermode="x unified",
                        xaxis=dict(
                            type="date",
                            range=[start_x, end_x],
                            tickformat="%b %Y",
                            dtick="M3",
                            showgrid=True,
                            gridcolor="rgba(255,255,255,0.04)",
                            tickfont=dict(color="#94a3b8", size=10),
                        ),
                        yaxis=dict(
                            visible=True,
                            range=y_range,
                            title=dict(text=f"Preis ({curr})", font=dict(color="#94a3b8", size=11)),
                            showgrid=True,
                            gridcolor="rgba(255,255,255,0.05)",
                            tickfont=dict(color="#94a3b8", size=10),
                        ),
                    )
                    st.plotly_chart(fig_idx, use_container_width=True)
        except Exception:
            st.error(f"Daten für {idx_name} konnten nicht geladen werden.")

st.markdown("---")
st.subheader("📊 Sektoren & Top-Performer (Stage 2 Focus)")

sector_results = []
for sec_name, sec_info in SECTOR_COMPONENTS.items():
    try:
        sec_df, curr, market_open = get_data_with_info(sec_info["ticker"])
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
            "currency": curr,
            "is_open": market_open,
            "df": sec_df,
        })
    except Exception:
        pass

sector_results = sorted(sector_results, key=lambda x: x["m_rs"], reverse=True)

cols = st.columns(2)
for idx, item in enumerate(sector_results):
    col = cols[idx % 2]
    with col:
        with st.container(border=True):
            status_badge = (
                "<span class='status-badge-open'>🟢 Geöffnet</span>"
                if item["is_open"]
                else "<span class='status-badge-closed'>🔴 Geschlossen</span>"
            )

            st.markdown(f"### {item['name']}")
            st.markdown(
                f"<div style='margin-bottom: 8px;'>"
                f"<span style='padding:4px 10px; border-radius:12px; font-size:12px; font-weight:600; {item['css']}'>{item['stage']}</span> "
                f"&nbsp; {status_badge} &nbsp; <span style='font-size: 0.8rem; color:#94a3b8;'>Währung: <b>{item['currency']}</b></span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            plot_df = item["df"].tail(104)
            y_range_sec = compute_y_range([plot_df["Close"], plot_df["SMA30"]])

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["Close"],
                    mode="lines",
                    name=f"Kurs ({item['currency']})",
                    line=dict(color="#38bdf8", width=2.5),
                    fill='tozeroy',
                    fillcolor='rgba(56, 189, 248, 0.05)',
                    hovertemplate=f"<b>Kurs:</b> %{{y:.2f}} {item['currency']}<extra></extra>",
                    connectgaps=True,
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["SMA30"],
                    mode="lines",
                    name="30W-SMA",
                    line=dict(color="#fbbf24", width=2, dash="dash"),
                    hovertemplate=f"<b>30W-SMA:</b> %{{y:.2f}} {item['currency']}<extra></extra>",
                    connectgaps=True,
                )
            )

            start_x = plot_df.index[0]
            end_x = plot_df.index[-1] + datetime.timedelta(days=15)

            fig.update_layout(
                height=240,
                margin=dict(l=10, r=20, t=15, b=25),
                showlegend=True,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color="#cbd5e1", size=10)
                ),
                xaxis=dict(
                    type="date",
                    range=[start_x, end_x],
                    tickformat="%b %Y",
                    dtick="M3",
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.04)",
                    tickfont=dict(color="#94a3b8", size=10),
                ),
                yaxis=dict(
                    visible=True,
                    range=y_range_sec,
                    title=dict(text=f"Preis ({item['currency']})", font=dict(color="#94a3b8", size=10)),
                    showgrid=True, 
                    gridcolor="rgba(255,255,255,0.05)",
                    tickfont=dict(color="#94a3b8", size=10),
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

            rs_color = "#4ade80" if item["m_rs"] > 0 else "#f87171"
            st.markdown(
                f"**Mansfield-RS:** <span style='color:{rs_color}; font-weight:bold;'>{item['m_rs']:+.2f}</span> | "
                f"**30W-SMA Steigung:** `{item['slope']:+.2f}%`",
                unsafe_allow_html=True
            )

            with st.expander("🔍 Top-Aktien im Stage-2-Setup anzeigen"):
                stock_data = []
                stock_dfs = {}

                for stk_ticker, stk_name in item["stocks"].items():
                    try:
                        stk_df, stk_curr, stk_open = get_data_with_info(stk_ticker)
                        stk_df["Mansfield_RS"] = calculate_mansfield_rs(stk_df, bench_df)
                        stk_p = stk_df["Close"].iloc[-1]
                        stk_sma = stk_df["SMA30"].iloc[-1]
                        stk_slope = stk_df["SMA30_Slope_4W"].iloc[-1]
                        stk_mrs = stk_df["Mansfield_RS"].iloc[-1]

                        if stk_p > stk_sma and stk_slope > 0 and stk_mrs > 0:
                            stock_data.append({
                                "Ticker": stk_ticker,
                                "Name": stk_name,
                                "Kurs": f"{stk_p:.2f} {stk_curr}",
                                "30W-SMA": f"{stk_sma:.2f} {stk_curr}",
                                "SMA-Steigung": f"{stk_slope:+.2f}%",
                                "Mansfield-RS": round(stk_mrs, 2),
                                "Währung": stk_curr,
                                "Status": "🟢 Offen" if stk_open else "🔴 Zu",
                            })
                            stock_dfs[stk_ticker] = (stk_name, stk_df, stk_curr, stk_open)
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
                            "Status",
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
                        selected_name, s_df, s_curr, s_open = stock_dfs[selected_ticker]
                        s_plot_df = s_df.tail(104)

                        y_range_stk_price = compute_y_range([s_plot_df["Close"], s_plot_df["SMA30"]])
                        y_range_stk_rs = compute_y_range([s_plot_df["Mansfield_RS"]])

                        fig_stock = make_subplots(
                            rows=2,
                            cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.06,
                            row_heights=[0.72, 0.28],
                        )

                        # Oberer Chart: Preis
                        fig_stock.add_trace(
                            go.Scatter(
                                x=s_plot_df.index,
                                y=s_plot_df["Close"],
                                mode="lines",
                                name=f"Kurs ({s_curr})",
                                line=dict(color="#38bdf8", width=2.5),
                                fill='tozeroy',
                                fillcolor='rgba(56, 189, 248, 0.05)',
                                hovertemplate=f"<b>Kurs:</b> %{{y:.2f}} {s_curr}<extra></extra>",
                                connectgaps=True,
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
                                line=dict(color="#fbbf24", width=2, dash="dash"),
                                hovertemplate=f"<b>30W-SMA:</b> %{{y:.2f}} {s_curr}<extra></extra>",
                                connectgaps=True,
                            ),
                            row=1,
                            col=1,
                        )

                        # Unterer Chart: Mansfield RS
                        fig_stock.add_trace(
                            go.Scatter(
                                x=s_plot_df.index,
                                y=s_plot_df["Mansfield_RS"],
                                mode="lines",
                                name="Mansfield RS",
                                line=dict(color="#4ade80", width=2),
                                fill='tozeroy',
                                fillcolor='rgba(74, 222, 128, 0.1)',
                                hovertemplate="<b>Mansfield RS:</b> %{y:+.2f}<extra></extra>",
                                connectgaps=True,
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
                                line=dict(color="rgba(255,255,255,0.4)", width=1, dash="dot"),
                                hoverinfo="skip",
                            ),
                            row=2,
                            col=1,
                        )

                        s_start_x = s_plot_df.index[0]
                        s_end_x = s_plot_df.index[-1] + datetime.timedelta(days=15)

                        fig_stock.update_layout(
                            height=400,
                            margin=dict(l=10, r=20, t=20, b=25),
                            showlegend=True,
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            hovermode="x unified",
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1,
                                font=dict(color="#cbd5e1", size=10)
                            ),
                        )

                        fig_stock.update_yaxes(
                            title=dict(text=f"Preis ({s_curr})", font=dict(color="#94a3b8", size=10)),
                            range=y_range_stk_price,
                            showgrid=True,
                            gridcolor="rgba(255,255,255,0.05)",
                            tickfont=dict(color="#94a3b8", size=10),
                            row=1,
                            col=1
                        )
                        fig_stock.update_yaxes(
                            title=dict(text="Mansfield RS", font=dict(color="#94a3b8", size=10)),
                            range=y_range_stk_rs,
                            showgrid=True,
                            gridcolor="rgba(255,255,255,0.05)",
                            tickfont=dict(color="#94a3b8", size=10),
                            row=2,
                            col=1
                        )
                        
                        fig_stock.update_xaxes(
                            type="date",
                            range=[s_start_x, s_end_x],
                            tickformat="%b %Y",
                            dtick="M3",
                            showgrid=True,
                            gridcolor="rgba(255,255,255,0.04)",
                            tickfont=dict(color="#94a3b8", size=10),
                            row=2,
                            col=1
                        )

                        status_str = "🟢 Börse Geöffnet" if s_open else "🔴 Börse Geschlossen"
                        st.caption(f"Phasenanalyse Detail-Chart: **{selected_name} ({selected_ticker})** | Währung: **{s_curr}** | {status_str}")
                        st.plotly_chart(fig_stock, use_container_width=True)
                else:
                    st.info(
                        "Aktuell keine Einzelaktie in diesem Sektor mit aktivem Stage-2-Setup."
                    )

# ==========================================
# FOOTER / DISCLAIMER & RECHTSELEMENTE
# ==========================================
st.markdown("---")
st.markdown(
    """
    <div class="disclaimer-box">
        <strong>⚠️ Legal Disclaimer / Rechtlicher Haftungsausschluss:</strong><br><br>
        <strong>DE:</strong> Diese Webseite wird rein privat und ohne kommerzielle Absichten zu Informations- und Bildungszwecken betrieben. 
        Die bereitgestellten Inhalte, Chartanalysen und Berechnungen stellen ausdrücklich <u>keine Anlageberatung</u>, Kauf- oder Verkaufsempfehlung und keine Aufforderung zum Handel mit Finanzinstrumenten dar. 
        Der Betreiber übernimmt keinerlei Haftung für Verluste oder Schäden, die aus der Nutzung der hier dargestellten Daten entstehen.<br><br>
        <strong>EN:</strong> This website is operated purely privately for non-commercial educational and informational purposes. 
        All contents, charts, and metrics do <u>not</u> constitute investment advice, financial analysis, or a recommendation to buy or sell financial instruments.
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

# POPUP-DIALOGE FÜR ANBIETERKENNZEICHNUNG (IMPRESSUM) UND DATENSCHUTZ
@st.dialog("📄 Impressum")
def show_impressum():
    st.markdown("""
    ### Impressum
    
    **Angaben gemäß § 5 DDG:**  
    Simon Moskwa  
    Am Kohlenmeiler 81  
    42389 Wuppertal  
    Deutschland  

    **Kontakt:**  
    Telefon: 0202 9730246  
    E-Mail: [simon.moskwa@outlook.de](mailto:simon.moskwa@outlook.de)  

    **Hinweis zur Ausrichtung:**  
    Diese Internetpräsenz ist ein rein privates, unentgeltliches und nicht-kommerzielles Informations- und Bildungsprojekt. Es werden keine kostenpflichtigen Dienste, Finanzdienstleistungen oder gewerblichen Produkte angeboten.

    **Verbraucherstreitbeilegung / Universalschlichtungsstelle:**  
    Ich bin nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.
    """)

@st.dialog("🔒 Datenschutzerklärung")
def show_datenschutz():
    st.markdown("""
    ### Datenschutzerklärung
    
    **1. Allgemeines & Verantwortlicher**  
    Der Schutz Ihrer persönlichen Daten ist ein wichtiges Anliegen. Verantwortlich für die Datenverarbeitung auf dieser Webseite ist:  
    Simon Moskwa, Am Kohlenmeiler 81, 42389 Wuppertal, E-Mail: simon.moskwa@outlook.de.

    **2. Hosting über Streamlit Inc.**  
    Diese Anwendung wird bei Streamlit Inc. (USA) gehostet. Beim Aufrufen werden durch den Hoster automatisch Server-Logfiles (z. B. IP-Adresse, Datum/Uhrzeit des Zugriffs, Browsertyp) erfasst, um den technischen Betrieb und die Sicherheit der Anwendung zu gewährleisten.

    **3. Abruf von Finanzdaten (yfinance / Drittanbieter)**  
    Zur Bereitstellung von Echtzeit- und Historiencharts werden Finanzdaten automatisiert über Schnittstellen von Yahoo Finance geladen. Hierbei können technisch bedingt Anfragen an externe Server übermittelt werden.

    **4. Kontaktaufnahme per E-Mail**  
    Wenn Sie per E-Mail Kontakt aufnehmen, werden die mitgeteilten Daten ausschließlich zur Bearbeitung der Anfrage verwendet. Eine Weitergabe an Dritte erfolgt nicht.

    **5. Ihre Rechte**  
    Sie haben jederzeit das Recht auf unentgeltliche Auskunft über Ihre gespeicherten personenbezogenen Daten sowie ein Recht auf Berichtigung, Einschränkung oder Löschung. Wenden Sie sich hierzu bitte an die im Impressum angegebene E-Mail-Adresse.
    """)

# PERMANENT SICHTBARE RECHTS-BUTTONS IM FOOTER (LEICHTE ERREICHBARKEIT)
footer_col1, footer_col2, footer_col3 = st.columns([2, 1, 1])
with footer_col1:
    st.caption("© Pulse Trading • Private & Rein Informative Webseite")
with footer_col2:
    if st.button("Impressum", key="btn_impressum", use_container_width=True):
        show_impressum()
with footer_col3:
    if st.button("Datenschutz", key="btn_datenschutz", use_container_width=True):
        show_datenschutz()
