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
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    div[data-testid="stContainer"]:hover {
        border-color: rgba(0, 200, 255, 0.3);
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35);
    }
    
    /* Typography & Header Polish */
    .dashboard-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 0px;
        line-height: 1.2;
    }
    
    .dashboard-subtitle {
        font-size: 0.9rem;
        color: #8899a6;
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
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        transition: all 0.25s ease-in-out;
    }
    .stButton>button:hover {
        border-color: #00d2ff;
        color: #00d2ff;
        box-shadow: 0 0 12px rgba(0, 210, 255, 0.3);
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
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 18px;
        font-size: 0.8rem;
        line-height: 1.5;
        color: #7d8b99;
        margin-top: 40px;
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
@st.dialog("📩 Kontakt & Community-Austausch")
def show_contact_dialog():
    st.markdown("### Kontakt")
    st.write(
        "Bei Fragen zu Aktien, Chartanalysen oder Interesse an unserem Austausch "
        "erreichst du mich unter **[simon.moskwa@outlook.de](mailto:simon.moskwa@outlook.de)**."
    )
    
    st.markdown("---")
    st.markdown("#### 💬 Community-Austausch")
    st.write(
        "Wir bieten auch einen privaten Community-Austausch über WhatsApp für ambitionierte Trader an. "
        "Der Zugang zur Gruppe wird individuell auf E-Mail-Anfrage gewährt."
    )

    st.markdown("---")
    st.warning(
        "**Rechtlicher Hinweis / Disclaimer:**\n\n"
        "Alle bereitgestellten Informationen, Kennzahlen und Analysen dienen ausschließlich Informations- und Bildungszwecken. "
        "Sie stellen keine Finanzberatung, Anlageberatung oder Kauf-/Verkaufsempfehlung dar."
    )
    
    st.caption("Pulse Trading • Simon Moskwa")


# ---------------------------------------------------------
# HEADER SECTION (ELEGANT & COMPACT)
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
                        f"<span style='padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 12px; {css_style}'>"
                        f"{stage_str}</span>",
                        unsafe_allow_html=True,
                    )

                with col_mid:
                    st.write("")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Kurs", f"{p_idx:.2f}")
                    m2.metric("30W-SMA", f"{sma_idx:.2f}")
                    m3.metric("Steigung (4W)", f"{slope_idx:+.2f}%")

                with col_right:
                    plot_df = df_idx.tail(104)

                    fig_idx = go.Figure()
                    fig_idx.add_trace(
                        go.Scatter(
                            x=plot_df.index,
                            y=plot_df["Close"],
                            mode="lines",
                            name="Kurs",
                            line=dict(color="#00d2ff", width=2),
                            connectgaps=True,
                        )
                    )
                    fig_idx.add_trace(
                        go.Scatter(
                            x=plot_df.index,
                            y=plot_df["SMA30"],
                            mode="lines",
                            name="30W-SMA",
                            line=dict(color="#ff9f43", width=2, dash="dash"),
                            connectgaps=True,
                        )
                    )
                    fig_idx.update_layout(
                        height=210,
                        margin=dict(l=5, r=5, t=10, b=20),
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(
                            visible=True,
                            autorange=True,
                            tickformat="%b %Y",
                            showgrid=False
                        ),
                        yaxis=dict(visible=True, showgrid=True, gridcolor="rgba(250,250,250,0.05)"),
                    )
                    st.plotly_chart(fig_idx, use_container_width=True)
        except Exception:
            st.error(f"Daten für {idx_name} konnten nicht geladen werden.")

st.markdown("---")
st.subheader("📊 Sektoren & Top-Performer (Stage 2 Focus)")

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

sector_results = sorted(sector_results, key=lambda x: x["m_rs"], reverse=True)

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

            plot_df = item["df"].tail(104)

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["Close"],
                    mode="lines",
                    name="Kurs",
                    line=dict(color="#00d2ff", width=2),
                    connectgaps=True,
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["SMA30"],
                    mode="lines",
                    name="30W-SMA",
                    line=dict(color="#ff9f43", width=2, dash="dash"),
                    connectgaps=True,
                )
            )

            fig.update_layout(
                height=230,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=True,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
                xaxis=dict(
                    visible=True,
                    autorange=True,
                    tickformat="%b %Y",
                    showgrid=False
                ),
                yaxis=dict(visible=True, showgrid=True, gridcolor="rgba(250,250,250,0.05)"),
            )
            st.plotly_chart(fig, use_container_width=True)

            rs_color = "#2ecc71" if item["m_rs"] > 0 else "#e74c3c"
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

                        fig_stock.add_trace(
                            go.Scatter(
                                x=s_plot_df.index,
                                y=s_plot_df["Close"],
                                mode="lines",
                                name="Wochenkurs ($)",
                                line=dict(color="#00d2ff", width=2),
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
                                line=dict(color="#ff9f43", width=2, dash="dash"),
                                connectgaps=True,
                            ),
                            row=1,
                            col=1,
                        )

                        fig_stock.add_trace(
                            go.Scatter(
                                x=s_plot_df.index,
                                y=s_plot_df["Mansfield_RS"],
                                mode="lines",
                                name="Mansfield RS",
                                line=dict(color="#2ecc71", width=1.5),
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
                                line=dict(color="rgba(255,255,255,0.3)", width=1, dash="dot"),
                            ),
                            row=2,
                            col=1,
                        )

                        fig_stock.update_layout(
                            height=380,
                            margin=dict(l=10, r=10, t=20, b=10),
                            showlegend=True,
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
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

# ==========================================
# FOOTER / IMPRESSUM & DATENSCHUTZ
# ==========================================
st.markdown("---")
st.markdown(
    """
    <div class="disclaimer-box">
        <strong>⚠️ Legal Disclaimer / Rechtlicher Haftungsausschluss:</strong><br><br>
        <strong>DE:</strong> Die in dieser Anwendung bereitgestellten Inhalte, Chartanalysen, Berechnungen und Daten dienen ausschließlich Informations- und Bildungszwecken. 
        Sie stellen ausdrücklich <u>keine Anlageberatung</u>, Kauf- oder Verkaufsempfehlung oder Aufforderung zum Handel mit Finanzinstrumenten dar. 
        Der Betreiber übernimmt keinerlei Haftung für Verluste oder Schäden, die aus der Nutzung der hier dargestellten Daten entstehen. 
        Der Handel mit Wertpapieren und Kryptowährungen birgt hohe finanzielle Risiken bis hin zum Totalverlust.<br><br>
        <strong>EN:</strong> All contents, charts, metrics, and analyses displayed in this dashboard are provided strictly for educational and informational purposes only. 
        They do <u>not</u> constitute investment advice, financial analysis, or a recommendation to buy or sell any financial instrument. 
        The operator assumes no liability for any losses or damages resulting from reliance on the provided data. Trading stocks and financial products involves substantial risk of loss.
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")
with st.expander("📄 Impressum & Datenschutzerklärung"):
    st.markdown("""
    ### Impressum
    
    **Angaben gemäß § 5 DDG:**  
    Simon Moskwa  
    Pulse Trading  
    E-Mail: [simon.moskwa@outlook.de](mailto:simon.moskwa@outlook.de)

    ---

    ### Datenschutzerklärung
    
    **1. Allgemeines**  
    Der Schutz Ihrer persönlichen Daten ist mir ein wichtiges Anliegen. Diese Anwendung verarbeitet personenbezogene Daten ausschließlich im Rahmen der gesetzlichen Bestimmungen (DSGVO).

    **2. Hosting über Streamlit Inc.**  
    Diese Anwendung wird bei der Plattform Streamlit Inc. (USA) gehostet. Beim Aufrufen dieser Anwendung werden durch den Hoster automatisch Server-Logfiles (z. B. IP-Adresse, Datum/Uhrzeit des Zugriffs, Browsertyp) erfasst und verarbeitet, um den technisch fehlerfreien Betrieb und die Sicherheit der Anwendung zu gewährleisten.

    **3. Kontaktaufnahme per E-Mail**  
    Wenn Sie per E-Mail Kontakt mit mir aufnehmen, werden die von Ihnen mitgeteilten Daten (z. B. E-Mail-Adresse, Name, Nachrichteninhalt) ausschließlich zur Bearbeitung und Beantwortung Ihrer Anfrage gespeichert und genutzt. Eine Weitergabe an Dritte erfolgt nicht.

    **4. Betroffenenrechte**  
    Sie haben jederzeit das Recht auf unentgeltliche Auskunft über Ihre gespeicherten personenbezogenen Daten sowie ein Recht auf Berichtigung, Sperrung oder Löschung dieser Daten. Wenden Sie sich hierzu bitte an die im Impressum angegebene E-Mail-Adresse.
    """)

st.caption("© Pulse Trading • Simon Moskwa")
