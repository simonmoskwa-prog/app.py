import base64
import datetime
import json
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
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
# BENUTZER-VERWALTUNG (PERSISTENT PER JSON-DATEI)
# ---------------------------------------------------------
USERS_FILE = "users.json"

DEFAULT_USERS = {
    "admin": {
        "password": "change_me_admin_2026",
        "display_name": "Simon",
        "welcome_msg": "Willkommen Simon",
        "role": "admin"
    },
    "marcin.plonka": {
        "password": "change_me_user_1",
        "display_name": "Marcin Płonka",
        "welcome_msg": "Willkommen Marcin Płonka",
        "role": "user"
    },
    "murat.seyfi": {
        "password": "change_me_user_2",
        "display_name": "Murat Seyfi",
        "welcome_msg": "Willkommen Murat Seyfi",
        "role": "user"
    },
    "artur.boch": {
        "password": "change_me_user_3",
        "display_name": "Artur",
        "welcome_msg": "Willkommen Artur",
        "role": "user"
    },
    "marcin.brudnik": {
        "password": "change_me_user_4",
        "display_name": "Marcin",
        "welcome_msg": "Willkommen Marcin",
        "role": "user"
    },
    "janusz.grochowski": {
        "password": "change_me_user_5",
        "display_name": "Janusz",
        "welcome_msg": "Willkommen Janusz",
        "role": "user"
    },
    "zbyszek.skora": {
        "password": "change_me_user_6",
        "display_name": "Zbyszek",
        "welcome_msg": "Willkommen Zbyszek",
        "role": "user"
    },
    "karsten.gerhardt": {
        "password": "change_me_user_7",
        "display_name": "Karsten",
        "welcome_msg": "Willkommen Karsten",
        "role": "user"
    },
    "patrick.mansilla": {
        "password": "change_me_user_8",
        "display_name": "Patrick",
        "welcome_msg": "Willkommen Patrick",
        "role": "user"
    }
}

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_USERS.copy()
    else:
        save_users(DEFAULT_USERS)
        return DEFAULT_USERS.copy()

def save_users(users_dict):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_dict, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Fehler beim Speichern der Benutzerdaten: {e}")

if "users_db" not in st.session_state:
    st.session_state["users_db"] = load_users()

# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "user_key" not in st.session_state:
    st.session_state["user_key"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = "user"
if "welcome_msg" not in st.session_state:
    st.session_state["welcome_msg"] = ""

def render_login_screen():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.write("")
        st.write("")
        with st.container(border=True):
            st.markdown("### 🔐 Pulse Trading Login")
            st.caption("Bitte Zugangsdaten eingeben, um auf das Dashboard zuzugreifen.")
            
            with st.form("login_form"):
                user_input = st.text_input("Benutzername", key="login_user").strip().lower()
                pwd_input = st.text_input("Passwort", type="password", key="login_pwd")
                login_btn = st.form_submit_button("Anmelden", use_container_width=True)
                
                if login_btn:
                    users = st.session_state["users_db"]
                    if user_input in users and users[user_input]["password"] == pwd_input:
                        st.session_state["authenticated"] = True
                        st.session_state["user_key"] = user_input
                        st.session_state["username"] = users[user_input]["display_name"]
                        st.session_state["role"] = users[user_input].get("role", "user")
                        st.session_state["welcome_msg"] = users[user_input]["welcome_msg"]
                        st.success(f"Anmeldung erfolgreich: {st.session_state['welcome_msg']}!")
                        st.rerun()
                    else:
                        st.error("Ungültiger Benutzername oder Passwort.")

if not st.session_state["authenticated"]:
    render_login_screen()
    st.stop()

# ---------------------------------------------------------
# DIALOGE (GLOSSAR / HILFESEITE & KONTAKT)
# ---------------------------------------------------------
@st.dialog("📖 Hilfeseite & Screening-Logik (Glossar)", width="large")
def show_glossary_dialog():
    st.markdown("## 📊 Regelwerk & Filter-Logik")
    st.write("Hier findest du genaue Details darüber, wie Aktien gefiltert und als TOP KANDIDAT ausgezeichnet werden:")
    
    st.markdown("---")

    st.markdown("### 🔍 1. Erstfilter: Wann erscheint eine Aktie in der Liste?")
    st.write(
        "Damit eine Sektor-Aktie überhaupt in der Tabelle auftaucht, muss sie zwei grundlegende **Trend-Mindestanforderungen** erfüllen:"
    )
    st.markdown("""
    * **1. Kurs über dem 30W-SMA (`Preis > 30W-SMA`):** Der aktuelle Schlusskurs liegt über dem einfachen gleitenden Durchschnitt der letzten 30 Wochen.
    * **2. Positiver Trend (`Steigung (4W) > 0.0%`):** Der 30-Wochen-Durchschnitt muss im Vergleich zu vor 4 Wochen ansteigen (aufwärtsgerichteter Trend).
    
    *Aktien unter dem 30W-SMA oder in einem fallenden Trend werden sofort herausgefiltert.*
    """)

    st.markdown("---")

    st.markdown("### ⭐ 2. Wann wird eine Aktie zum ⭐ TOP KANDIDATEN?")
    st.write(
        "Um das begehrte **`⭐ TOP`** Badge zu erhalten, reicht ein normaler Aufwärtstrend nicht aus. "
        "Die Aktie muss ein vollkommen intaktes **Stage 2 Breakout-Setup nach Stan Weinstein** aufweisen. "
        "Hierfür müssen **alle 4 Kriterien gleichzeitig** erfüllt sein:"
    )
    st.markdown("""
    1. **Kurs über 30W-SMA:** Der Kurs notiert klar oberhalb der Trendlinie.
    2. **Starke Steigung (`> +0.5%`):** Die 4-Wochen-Steigung des 30W-SMA muss kraftvoll sein (> +0,5%).
    3. **Outperformance (`Mansfield RS > 0.0`):** Die Aktie ist stärker als der Gesamtmarkt (S&P 500 Benchmark).
    4. **Volumen-Bestätigung (`Volumen >= 120% des 10W-Schnitts`):** Das Handelsvolumen der aktuellen Woche muss mindestens 20% über dem Durchschnitt der letzten 10 Wochen liegen (institutionelles Kaufinteresse).
    """)

    st.markdown("---")

    st.markdown("### 📈 3. Allgemeines Glossar zu Indikatoren")
    st.markdown("""
    * **Mansfield RS:** Misst die Stärke einer Aktie relativ zum S&P 500. Werte über 0 signalisieren Marktführerschaft.
    * **30W-SMA:** 30-Wochen-Durchschnitt. Wichtigste Demarkationslinie für institutionelle Investoren.
    * **Stage 2 (Aufstiegsphase):** Das optimale Zeitfenster für Long-Investments.
    """)

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

# ---------------------------------------------------------
# SIDEBAR & ADMIN-BENUTZERVERWALTUNG
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 👤 Benutzer-Session")
    st.markdown(f"**{st.session_state['welcome_msg']}**")
    st.caption(f"Konto: {st.session_state['username']} (`{st.session_state['role']}`)")
    
    # CHARTS AKTUALISIEREN BUTTON IN SIDEBAR
    if st.button("🔄 Charts aktualisieren", use_container_width=True, help="Leert den Daten-Cache und lädt aktuelle Marktdaten neu."):
        st.cache_data.clear()
        st.success("Daten-Cache geleert! Charts werden aktualisiert...")
        st.rerun()

    if st.button("🔒 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["user_key"] = ""
        st.session_state["username"] = ""
        st.session_state["role"] = "user"
        st.session_state["welcome_msg"] = ""
        st.rerun()

    if st.session_state["role"] == "admin":
        st.markdown("---")
        st.markdown("### ⚙️ Admin-Verwaltung")
        
        with st.expander("👥 Benutzer-Verwaltung", expanded=False):
            tab_add, tab_edit, tab_del = st.tabs(["➕ Neu", "✏️ Ändern", "❌ Löschen"])
            
            with tab_add:
                st.caption("Neuen Zugang erstellen")
                new_key = st.text_input("Benutzername (Login-Key)", key="add_key").strip().lower()
                new_pass = st.text_input("Passwort", key="add_pass").strip()
                new_name = st.text_input("Anzeigename (z.B. Max)", key="add_name").strip()
                new_role = st.selectbox("Rolle", ["user", "admin"], key="add_role")
                
                if st.button("User Anlegen", use_container_width=True):
                    if not new_key or not new_pass or not new_name:
                        st.warning("Bitte alle Felder ausfüllen.")
                    elif new_key in st.session_state["users_db"]:
                        st.error("Benutzername existiert bereits.")
                    else:
                        st.session_state["users_db"][new_key] = {
                            "password": new_pass,
                            "display_name": new_name,
                            "welcome_msg": f"Willkommen {new_name}",
                            "role": new_role
                        }
                        save_users(st.session_state["users_db"])
                        st.success(f"User '{new_key}' erfolgreich angelegt!")
                        st.rerun()

            with tab_edit:
                st.caption("Benutzerdaten bearbeiten")
                user_list = list(st.session_state["users_db"].keys())
                
                if user_list:
                    edit_user = st.selectbox("User auswählen", user_list, key="edit_select")
                    curr_data = st.session_state["users_db"][edit_user]
                    
                    edit_pass = st.text_input("Neues Passwort", value=curr_data.get("password", ""), key=f"edit_pass_{edit_user}")
                    edit_name = st.text_input("Anzeigename", value=curr_data.get("display_name", ""), key=f"edit_name_{edit_user}")
                    
                    role_idx = 0 if curr_data.get("role") == "user" else 1
                    edit_role = st.selectbox("Rolle", ["user", "admin"], index=role_idx, key=f"edit_role_{edit_user}")
                    
                    if st.button("Änderungen Speichern", key=f"btn_save_{edit_user}", use_container_width=True):
                        st.session_state["users_db"][edit_user] = {
                            "password": edit_pass,
                            "display_name": edit_name,
                            "welcome_msg": f"Willkommen {edit_name}",
                            "role": edit_role
                        }
                        save_users(st.session_state["users_db"])
                        st.success(f"Daten für '{edit_user}' aktualisiert!")
                        st.rerun()

            with tab_del:
                st.caption("Zugang entfernen")
                del_user = st.selectbox("User zum Löschen", [u for u in st.session_state["users_db"].keys() if u != st.session_state["user_key"]], key="del_select")
                
                if del_user:
                    if st.button(f"❌ '{del_user}' löschen", use_container_width=True, type="primary"):
                        del st.session_state["users_db"][del_user]
                        save_users(st.session_state["users_db"])
                        st.success(f"User '{del_user}' wurde gelöscht.")
                        st.rerun()

# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    .main { padding-top: 1rem; }
    
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

    .top-candidate-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: #ffffff;
        font-weight: 800;
        font-size: 0.85rem;
        padding: 6px 14px;
        border-radius: 20px;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.5);
        display: inline-block;
        border: 1px solid #34d399;
    }

    .update-banner {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.15) 0%, rgba(129, 140, 248, 0.15) 100%);
        border: 1px solid rgba(56, 189, 248, 0.4);
        border-radius: 14px;
        padding: 16px 22px;
        margin-top: 15px;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        gap: 14px;
        box-shadow: 0 6px 25px rgba(0, 210, 255, 0.1);
    }

    .badge-new {
        background-color: #38bdf8;
        color: #0f172a;
        font-weight: 800;
        font-size: 0.75rem;
        padding: 3px 8px;
        border-radius: 6px;
        margin-right: 8px;
        text-transform: uppercase;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.35rem !important;
        font-weight: 700;
        letter-spacing: -0.3px;
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

    .disclaimer-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 15px 20px;
        font-size: 0.82rem;
        color: #94a3b8;
        line-height: 1.5;
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

def get_ticker_from_name(query):
    query = query.strip()
    if not query:
        return None
        
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=5"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        quotes = data.get('quotes', [])
        
        if quotes:
            for q in quotes:
                if q.get('quoteType') == 'EQUITY':
                    return q.get('symbol')
            return quotes[0].get('symbol')
    except Exception:
        pass
        
    return query.upper()

logo_b64 = get_image_base64("logo.png")

# ---------------------------------------------------------
# HEADER SECTION
# ---------------------------------------------------------
header_col1, header_col2, header_col3 = st.columns([1, 4.2, 2.2])

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
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("❓ Hilfeseite", use_container_width=True):
            show_glossary_dialog()
    with btn_col2:
        if st.button("📩 Contact Us", use_container_width=True):
            show_contact_dialog()

# GROSSES NEUES UPDATE BANNER
st.markdown(
    f"""
    <div class="update-banner">
        <span style="font-size: 1.8rem;">🚀</span>
        <div class="update-banner-text">
            <span class="badge-new">Großes Update</span>
            <strong>Transparente Filter-Logik & ⭐ TOP Candidate System:</strong> Wir haben unser Screening-System grundlegend optimiert! Ab sofort erkennst du echte Stage-2-Ausbrüche durch automatische <strong>⭐ TOP</strong> Auszeichnungen. Öffne die <strong>Hilfeseite</strong> für die genaue Formel-Erläuterung.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

BENCHMARK = "^GSPC"

INDICES_CONFIG = {
    "USA (S&P 500)": {"ticker": "^GSPC", "desc": "State Street SPDR S&P 500 ETF Trust / Index"},
    "Nasdaq 100": {"ticker": "^NDX", "desc": "Invesco QQQ Trust / Nasdaq 100 Index"},
    "Russell 2000": {"ticker": "^RUT", "desc": "iShares Russell 2000 ETF / Small Caps"},
    "Euro Stoxx 600": {"ticker": "^STOXX", "desc": "STXE 600 EUR Price Index"},
    "DAX": {"ticker": "^GDAXI", "desc": "DAX Performance-Index (Deutschland)"},
    "Nikkei 225": {"ticker": "^N225", "desc": "Nikkei 225 Index (Japan)"},
    "Hang Seng": {"ticker": "^HSI", "desc": "Hang Seng Index (Hongkong)"},
    "MSCI World": {"ticker": "URTH", "desc": "iShares MSCI World ETF"},
    "VIX": {"ticker": "^VIX", "desc": "CBOE Volatility Index"},
}

SECTOR_COMPONENTS = {
    "Technology (XLK)": {
        "ticker": "XLK",
        "stocks": {
            "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "NVDA": "NVIDIA Corp.",
            "AVGO": "Broadcom Inc.", "AMD": "Advanced Micro Devices", "ADBE": "Adobe Inc.",
            "CRM": "Salesforce Inc.", "ORCL": "Oracle Corp.",
        },
    },
    "Energy (XLE)": {
        "ticker": "XLE",
        "stocks": {
            "XOM": "Exxon Mobil Corp.", "CVX": "Chevron Corp.", "COP": "ConocoPhillips",
            "SLB": "Schlumberger Ltd.", "EOG": "EOG Resources Inc.", "MPC": "Marathon Petroleum Corp.",
            "PSX": "Phillips 66", "VLO": "Valero Energy Corp.",
        },
    },
    "Financials (XLF)": {
        "ticker": "XLF",
        "stocks": {
            "JPM": "JPMorgan Chase & Co.", "BAC": "Bank of America Corp.", "WFC": "Wells Fargo & Co.",
            "C": "Citigroup Inc.", "GS": "Goldman Sachs Group", "MS": "Morgan Stanley",
            "BLK": "BlackRock Inc.", "V": "Visa Inc.",
        },
    },
    "Health Care (XLV)": {
        "ticker": "XLV",
        "stocks": {
            "LLY": "Eli Lilly and Co.", "UNH": "UnitedHealth Group", "JNJ": "Johnson & Johnson",
            "ABBV": "AbbVie Inc.", "MRK": "Merck & Co. Inc.", "AMGN": "Amgen Inc.",
            "PFE": "Pfizer Inc.", "TMO": "Thermo Fisher Scientific",
        },
    },
    "Communication Services (XLC)": {
        "ticker": "XLC",
        "stocks": {
            "META": "Meta Platforms Inc.", "GOOGL": "Alphabet Inc.", "NFLX": "Netflix Inc.",
            "TMUS": "T-Mobile US Inc.", "DIS": "Walt Disney Co.", "CMCSA": "Comcast Corp.",
        },
    },
    "Consumer Discretionary (XLY)": {
        "ticker": "XLY",
        "stocks": {
            "AMZN": "Amazon.com Inc.", "TSLA": "Tesla Inc.", "HD": "Home Depot Inc.",
            "MCD": "McDonald's Corp.", "NKE": "NIKE Inc.", "BKNG": "Booking Holdings Inc.",
            "SBUX": "Starbucks Corp.",
        },
    },
    "Consumer Staples (XLP)": {
        "ticker": "XLP",
        "stocks": {
            "PG": "Procter & Gamble Co.", "COST": "Costco Wholesale Corp.", "PEP": "PepsiCo Inc.",
            "KO": "Coca-Cola Co.", "WMT": "Walmart Inc.", "PM": "Philip Morris Int.",
            "DINO.WA": "Dino Polska S.A."
        },
    },
    "Materials (XLB)": {
        "ticker": "XLB",
        "stocks": {
            "LIN": "Linde plc", "APD": "Air Products & Chemicals", "SHW": "Sherwin-Williams Co.",
            "FCX": "Freeport-McMoRan Inc.", "ECL": "Ecolab Inc.", "NEM": "Newmont Corp.",
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

    if "Volume" not in df.columns:
        df["Volume"] = 0

    df = df[["Close", "Volume"]].dropna()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()

    df["SMA30"] = df["Close"].rolling(window=30).mean()
    df["SMA30_Slope_4W"] = ((df["SMA30"] - df["SMA30"].shift(4)) / df["SMA30"].shift(4)) * 100
    df["Vol_Avg_10W"] = df["Volume"].rolling(window=10).mean()

    currency = "USD"
    exchange = "N/A"
    is_open = False
    company_name = ticker
    try:
        info = yticker.info
        currency = info.get("currency", "USD")
        exchange = info.get("exchange", "N/A")
        company_name = info.get("longName") or info.get("shortName") or ticker
        
        last_date = df.index[-1].date()
        today_date = datetime.date.today()
        if (today_date - last_date).days <= 2 and today_date.weekday() < 5:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            if "DE" in ticker or "STX" in ticker or "DAX" in ticker or "WA" in ticker or "PA" in ticker:
                is_open = (8 <= now_utc.hour < 16.5)
            else:
                is_open = (13.5 <= now_utc.hour + now_utc.minute/60 <= 21)
    except Exception:
        pass

    return df, currency, exchange, is_open, company_name

# ---------------------------------------------------------
# MANSFIELD RS BERECHNUNG
# ---------------------------------------------------------
def calculate_mansfield_rs(asset_df, benchmark_df):
    if asset_df.empty or benchmark_df.empty:
        return pd.Series(0.0, index=asset_df.index)

    s_asset = asset_df["Close"].copy()
    s_bench = benchmark_df["Close"].copy()

    s_asset.index = pd.to_datetime(s_asset.index).tz_localize(None).normalize()
    s_bench.index = pd.to_datetime(s_bench.index).tz_localize(None).normalize()

    combined = pd.DataFrame({"Asset": s_asset, "Bench": s_bench})
    combined = combined.sort_index().ffill().bfill()

    base_rs = combined["Asset"] / combined["Bench"]
    rs_sma52 = base_rs.rolling(window=52, min_periods=10).mean()

    mansfield = ((base_rs / rs_sma52) - 1.0) * 100.0
    
    res = mansfield.reindex(s_asset.index).ffill().bfill().fillna(0.0)
    return res

def determine_stage(price, sma30, slope):
    if price > sma30 and slope > 0.5:
        return ("Stage 2 (Aufstiegsphase)", "background-color: rgba(40, 167, 69, 0.2); color: #2ecc71; border: 1px solid rgba(40, 167, 69, 0.5);")
    elif price < sma30 and slope < -0.5:
        return ("Stage 4 (Abstiegsphase)", "background-color: rgba(220, 53, 69, 0.2); color: #e74c3c; border: 1px solid rgba(220, 53, 69, 0.5);")
    elif price > sma30 and slope <= 0.5:
        return ("Stage 3 (Topbildungsphase)", "background-color: rgba(255, 193, 7, 0.2); color: #f1c40f; border: 1px solid rgba(255, 193, 7, 0.5);")
    else:
        return ("Stage 1 (Bodenbildungsphase)", "background-color: rgba(108, 117, 125, 0.2); color: #95a5a6; border: 1px solid rgba(108, 117, 125, 0.5);")

# ---------------------------------------------------------
# STRIKTE PRÜFUNG NACH METHODIK (ALLE BEDINGUNGEN ERFÜLLT)
# ---------------------------------------------------------
def check_stan_weinstein_top_candidate(price, sma30, slope, mansfield_rs, volume=None, vol_avg_10w=None):
    c1_price_above_sma = price > sma30
    c2_sma_rising = slope > 0.5
    c3_mansfield_positive = mansfield_rs > 0.0

    c4_volume_confirmed = True
    if volume is not None and vol_avg_10w is not None and vol_avg_10w > 0:
        c4_volume_confirmed = volume >= (vol_avg_10w * 1.2)

    return c1_price_above_sma and c2_sma_rising and c3_mansfield_positive and c4_volume_confirmed

bench_df, _, _, _, _ = get_data_with_info(BENCHMARK)

# ==========================================
# AKTIEN-SUCHE & PHASEN-ANALYSE
# ==========================================
st.markdown("---")
st.subheader("🔍 Aktiensuche & Phasen-Analyse")

with st.container(border=True):
    search_col1, search_col2, search_col3 = st.columns([3, 1, 1])
    with search_col1:
        search_query = st.text_input(
            "Aktienname oder Ticker eingeben (z.B. Dino Polska, NVDA, Apple, LVMH, MC.PA):",
            value="Dino Polska",
            key="search_ticker_input"
        ).strip()
    with search_col2:
        st.write("")
        st.write("")
        search_btn = st.button("🔎 Analyse starten", use_container_width=True)
    with search_col3:
        st.write("")
        st.write("")
        if st.button("🔄 Charts aktualisieren", key="btn_refresh_charts", use_container_width=True):
            st.cache_data.clear()
            st.success("Charts werden neu geladen...")
            st.rerun()

    if search_query:
        resolved_ticker = get_ticker_from_name(search_query)
        
        try:
            with st.spinner(f"Lade Daten für '{search_query}' (Handelszeichen: {resolved_ticker})..."):
                stock_df, stock_curr, stock_exchange, stock_open, comp_name = get_data_with_info(resolved_ticker)
                stock_df["Mansfield_RS"] = calculate_mansfield_rs(stock_df, bench_df)

                s_price = stock_df["Close"].iloc[-1]
                s_sma = stock_df["SMA30"].iloc[-1]
                s_slope = stock_df["SMA30_Slope_4W"].iloc[-1]
                s_mrs = stock_df["Mansfield_RS"].iloc[-1]
                s_vol = stock_df["Volume"].iloc[-1]
                s_vol_avg = stock_df["Vol_Avg_10W"].iloc[-1]
                s_stage, s_css = determine_stage(s_price, s_sma, s_slope)
                
                is_top_candidate = check_stan_weinstein_top_candidate(s_price, s_sma, s_slope, s_mrs, s_vol, s_vol_avg)

                s_status_badge = (
                    "<span class='status-badge-open'>🟢 Börse Geöffnet</span>"
                    if stock_open
                    else "<span class='status-badge-closed'>🔴 Börse Geschlossen</span>"
                )

                st.markdown("---")
                header_s1, header_s2 = st.columns([2, 1])
                with header_s1:
                    top_badge_html = "<span class='top-candidate-badge'>⭐ TOP KANDIDAT (Stage 2)</span> &nbsp;" if is_top_candidate else ""
                    st.markdown(f"### {comp_name} (`{resolved_ticker}`)")
                    st.markdown(
                        f"<div style='margin-top: 4px; margin-bottom: 8px;'>"
                        f"{top_badge_html}"
                        f"<span style='padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 13px; {s_css}'>"
                        f"{s_stage}</span> &nbsp; {s_status_badge} &nbsp; "
                        f"<span style='font-size: 0.85rem; color:#94a3b8;'>Börse: <b>{stock_exchange}</b> | Handelszeichen: <b>{resolved_ticker}</b> | Währung: <b>{stock_curr}</b></span></div>",
                        unsafe_allow_html=True,
                    )
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Aktueller Kurs", f"{s_price:.2f} {stock_curr}")
                m2.metric("30W-SMA", f"{s_sma:.2f} {stock_curr}")
                m3.metric("SMA Steigung (4W)", f"{s_slope:+.2f}%")
                m4.metric("Mansfield RS", f"{s_mrs:+.2f}")

                plot_df_search = stock_df.tail(104)
                
                fig_search = make_subplots(
                    rows=3, cols=1, shared_xaxes=True, 
                    vertical_spacing=0.05, row_heights=[0.55, 0.20, 0.25]
                )

                fig_search.add_trace(
                    go.Scatter(
                        x=plot_df_search.index, y=plot_df_search["Close"], 
                        mode="lines", name=f"Kurs ({stock_curr})", 
                        line=dict(color="#38bdf8", width=2.5),
                        fill='tozeroy', fillcolor='rgba(56, 189, 248, 0.05)'
                    ), row=1, col=1
                )
                fig_search.add_trace(
                    go.Scatter(
                        x=plot_df_search.index, y=plot_df_search["SMA30"], 
                        mode="lines", name="30W-SMA", 
                        line=dict(color="#fbbf24", width=2, dash="dash")
                    ), row=1, col=1
                )

                vol_colors = ['#2ecc71' if plot_df_search["Close"].iloc[i] >= plot_df_search["Close"].iloc[i-1] else '#e74c3c' for i in range(len(plot_df_search))]
                fig_search.add_trace(
                    go.Bar(
                        x=plot_df_search.index, y=plot_df_search["Volume"],
                        name="Volumen", marker_color=vol_colors, opacity=0.7
                    ), row=2, col=1
                )

                rs_colors_search = ['#2ecc71' if val >= 0 else '#e74c3c' for val in plot_df_search["Mansfield_RS"]]
                fig_search.add_trace(
                    go.Bar(
                        x=plot_df_search.index, y=plot_df_search["Mansfield_RS"], 
                        name="Mansfield RS", marker_color=rs_colors_search
                    ), row=3, col=1
                )

                fig_search.update_layout(
                    height=500, margin=dict(l=10, r=20, t=20, b=25), showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
                    xaxis3=dict(type="date", tickformat="%b %Y", dtick="M3", showgrid=True, gridcolor="rgba(255,255,255,0.04)"),
                    yaxis=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", title=f"Preis ({stock_curr})"),
                    yaxis2=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Volumen"),
                    yaxis3=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor="rgba(255,255,255,0.2)", title="Mansfield RS")
                )
                st.plotly_chart(fig_search, use_container_width=True)

        except Exception as e:
            st.error(f"Aktie '{search_query}' (gefundener Ticker: '{resolved_ticker}') konnte nicht geladen werden. Bitte überprüfe die Eingabe.")

# ==========================================
# MARKT-ÜBERSICHT / INDEX-TABS
# ==========================================
st.markdown("---")
st.subheader("🌐 Markt-Übersicht")

tabs = st.tabs(list(INDICES_CONFIG.keys()))

for tab, (idx_name, idx_info) in zip(tabs, INDICES_CONFIG.items()):
    with tab:
        try:
            df_idx, curr, exchange, market_open, _ = get_data_with_info(idx_info["ticker"])
            df_idx["Mansfield_RS"] = calculate_mansfield_rs(df_idx, bench_df)
            
            p_idx = df_idx["Close"].iloc[-1]
            sma_idx = df_idx["SMA30"].iloc[-1]
            slope_idx = df_idx["SMA30_Slope_4W"].iloc[-1]
            mrs_idx = df_idx["Mansfield_RS"].iloc[-1]
            stage_str, css_style = determine_stage(p_idx, sma_idx, slope_idx)

            status_badge = (
                "<span class='status-badge-open'>🟢 Börse Geöffnet</span>"
                if market_open
                else "<span class='status-badge-closed'>🔴 Börse Geschlossen</span>"
            )

            with st.container(border=True):
                col_left, col_mid, col_right = st.columns([2.5, 2.5, 3])

                with col_left:
                    st.caption(f"INDEX / MARKT | Börse: **{exchange}** | Ticker: **{idx_info['ticker']}** | Währung: **{curr}**")
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
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Kurs", f"{p_idx:.2f} {curr}")
                    m2.metric("30W-SMA", f"{sma_idx:.2f} {curr}")
                    m3.metric("Steigung (4W)", f"{slope_idx:+.2f}%")
                    m4.metric("Mansfield RS", f"{mrs_idx:+.2f}")

                with col_right:
                    plot_df = df_idx.tail(104)
                    
                    fig_idx = make_subplots(
                        rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.06, row_heights=[0.5, 0.2, 0.3]
                    )

                    fig_idx.add_trace(go.Scatter(x=plot_df.index, y=plot_df["Close"], mode="lines", name=f"Kurs ({curr})", line=dict(color="#38bdf8", width=2.5), fill='tozeroy', fillcolor='rgba(56, 189, 248, 0.06)'), row=1, col=1)
                    fig_idx.add_trace(go.Scatter(x=plot_df.index, y=plot_df["SMA30"], mode="lines", name="30W-SMA", line=dict(color="#fbbf24", width=2, dash="dash")), row=1, col=1)
                    
                    vol_colors_idx = ['#2ecc71' if plot_df["Close"].iloc[i] >= plot_df["Close"].iloc[i-1] else '#e74c3c' for i in range(len(plot_df))]
                    fig_idx.add_trace(go.Bar(x=plot_df.index, y=plot_df["Volume"], name="Volumen", marker_color=vol_colors_idx, opacity=0.6), row=2, col=1)

                    rs_colors_idx = ['#2ecc71' if val >= 0 else '#e74c3c' for val in plot_df["Mansfield_RS"]]
                    fig_idx.add_trace(go.Bar(x=plot_df.index, y=plot_df["Mansfield_RS"], name="Mansfield RS", marker_color=rs_colors_idx), row=3, col=1)

                    fig_idx.update_layout(
                        height=360, margin=dict(l=10, r=20, t=15, b=25), showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
                        xaxis3=dict(type="date", tickformat="%b %Y", dtick="M3", showgrid=True, gridcolor="rgba(255,255,255,0.04)"),
                        yaxis=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                        yaxis2=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Volumen"),
                        yaxis3=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor="rgba(255,255,255,0.2)", title="Mansfield RS")
                    )
                    st.plotly_chart(fig_idx, use_container_width=True)
        except Exception:
            st.error(f"Daten für {idx_name} konnten nicht geladen werden.")

# ==========================================
# SEKTOREN & TOP-PERFORMER
# ==========================================
st.markdown("---")
st.subheader("📊 Sektoren & Top-Performer (Stage 2 Focus)")

all_sector_results = []
for sec_name, sec_info in SECTOR_COMPONENTS.items():
    try:
        sec_df, curr, exchange, market_open, _ = get_data_with_info(sec_info["ticker"])
        sec_df["Mansfield_RS"] = calculate_mansfield_rs(sec_df, bench_df)
        p = sec_df["Close"].iloc[-1]
        sma = sec_df["SMA30"].iloc[-1]
        slope = sec_df["SMA30_Slope_4W"].iloc[-1]
        m_rs = sec_df["Mansfield_RS"].iloc[-1]
        vol = sec_df["Volume"].iloc[-1]
        vol_avg = sec_df["Vol_Avg_10W"].iloc[-1]
        stage, css = determine_stage(p, sma, slope)
        is_top = check_stan_weinstein_top_candidate(p, sma, slope, m_rs, vol, vol_avg)

        all_sector_results.append({
            "name": sec_name, "ticker": sec_info["ticker"], "stocks": sec_info["stocks"],
            "price": p, "sma": sma, "slope": slope, "m_rs": m_rs, "stage": stage,
            "css": css, "currency": curr, "exchange": exchange, "is_open": market_open, "df": sec_df, "is_top": is_top
        })
    except Exception:
        pass

with st.container(border=True):
    filter_col1, filter_col2 = st.columns([2.5, 1.5])
    
    sector_names = [s["name"] for s in all_sector_results]
    
    with filter_col1:
        selected_sectors = st.multiselect(
            "🔍 Sektoren filtern:",
            options=sector_names,
            default=sector_names,
            help="Wähle bestimmte Sektoren aus, die du analysieren möchtest."
        )
    
    with filter_col2:
        sort_option = st.selectbox("🔀 Sortieren nach:", [
            "Mansfield RS (Höchste zuerst)",
            "30W-SMA Steigung (4W)",
            "Alphabetisch (A-Z)"
        ])

filtered_sectors = [s for s in all_sector_results if s["name"] in selected_sectors]

if sort_option == "Mansfield RS (Höchste zuerst)":
    sector_results = sorted(filtered_sectors, key=lambda x: x["m_rs"], reverse=True)
elif sort_option == "30W-SMA Steigung (4W)":
    sector_results = sorted(filtered_sectors, key=lambda x: x["slope"], reverse=True)
else:
    sector_results = sorted(filtered_sectors, key=lambda x: x["name"])

if sector_results:
    stage2_count = sum(1 for s in sector_results if "Stage 2" in s["stage"])
    top_sec = max(sector_results, key=lambda x: x["m_rs"])
    
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    stat_col1.metric("Ausgewählte Sektoren", f"{len(sector_results)} von {len(all_sector_results)}")
    stat_col2.metric("Im Stage 2 Setup", f"{stage2_count}")
    stat_col3.metric("Top Sektor (RS)", f"{top_sec['name'].split(' ')[0]} ({top_sec['m_rs']:+.2f})")
    
    st.write("")

cols = st.columns(2)
for idx, item in enumerate(sector_results):
    col = cols[idx % 2]
    with col:
        with st.container(border=True):
            status_badge = "<span class='status-badge-open'>🟢 Geöffnet</span>" if item["is_open"] else "<span class='status-badge-closed'>🔴 Geschlossen</span>"
            top_candidate_html = "<span class='top-candidate-badge'>⭐ TOP KANDIDAT</span> &nbsp;" if item["is_top"] else ""

            st.markdown(f"### {item['name']} (`{item['ticker']}`)")
            st.markdown(
                f"<div style='margin-bottom: 8px;'>"
                f"{top_candidate_html}"
                f"<span style='padding:4px 10px; border-radius:12px; font-size:12px; font-weight:600; {item['css']}'>{item['stage']}</span> "
                f"&nbsp; {status_badge} &nbsp; <span style='font-size: 0.8rem; color:#94a3b8;'>Börse: <b>{item['exchange']}</b> | Währung: <b>{item['currency']}</b></span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            plot_df = item["df"].tail(104)
            
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.5, 0.2, 0.3])

            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["Close"], mode="lines", name=f"Kurs ({item['currency']})", line=dict(color="#38bdf8", width=2.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["SMA30"], mode="lines", name="30W-SMA", line=dict(color="#fbbf24", width=2, dash="dash")), row=1, col=1)

            vol_colors_sec = ['#2ecc71' if plot_df["Close"].iloc[i] >= plot_df["Close"].iloc[i-1] else '#e74c3c' for i in range(len(plot_df))]
            fig.add_trace(go.Bar(x=plot_df.index, y=plot_df["Volume"], name="Volumen", marker_color=vol_colors_sec, opacity=0.6), row=2, col=1)

            rs_colors = ['#2ecc71' if val >= 0 else '#e74c3c' for val in plot_df["Mansfield_RS"]]
            fig.add_trace(go.Bar(x=plot_df.index, y=plot_df["Mansfield_RS"], name="Mansfield RS", marker_color=rs_colors), row=3, col=1)

            fig.update_layout(
                height=380, margin=dict(l=10, r=20, t=15, b=25), showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified",
                xaxis3=dict(type="date", tickformat="%b %Y", dtick="M3", showgrid=True, gridcolor="rgba(255,255,255,0.04)"),
                yaxis=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis2=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Volumen"),
                yaxis3=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor="rgba(255,255,255,0.2)", title="Mansfield RS")
            )
            st.plotly_chart(fig, use_container_width=True)

            rs_disp = f"{item['m_rs']:+.2f}"
            rs_color = "#4ade80" if item["m_rs"] > 0 else "#f87171"
            st.markdown(
                f"**Mansfield-RS:** <span style='color:{rs_color}; font-weight:bold;'>{rs_disp}</span> | "
                f"**30W-SMA Steigung:** `{item['slope']:+.2f}%`",
                unsafe_allow_html=True
            )

            # Nebeneinander-Layout: Expander-Titel links, Hilfebutton mit Kurztitel rechts in der gleichen Zeile
            exp_header_col1, exp_header_col2 = st.columns([0.65, 0.35])
            
            with exp_header_col2:
                if st.button("❓ Logik-Erklärung", key=f"help_icon_{item['ticker']}_{idx}", help="Klicken für Erläuterung der Stage-2 & Top-Kandidat Logik"):
                    show_glossary_dialog()

            with exp_header_col1:
                expander_target = st.expander("🔎 Top-Aktien im Stage-2-Setup anzeigen")

                with expander_target:
                    stock_data = []
                    stock_dfs = {}

                    for stk_ticker, stk_name in item["stocks"].items():
                        try:
                            stk_df, stk_curr, stk_exchange, stk_open, _ = get_data_with_info(stk_ticker)
                            stk_df["Mansfield_RS"] = calculate_mansfield_rs(stk_df, bench_df)
                            stk_p = stk_df["Close"].iloc[-1]
                            stk_sma = stk_df["SMA30"].iloc[-1]
                            stk_slope = stk_df["SMA30_Slope_4W"].iloc[-1]
                            stk_mrs = stk_df["Mansfield_RS"].iloc[-1]
                            stk_vol = stk_df["Volume"].iloc[-1]
                            stk_vol_avg = stk_df["Vol_Avg_10W"].iloc[-1]

                            # Erstfilter: Kurs über 30W-SMA und Steigung > 0
                            if stk_p > stk_sma and stk_slope > 0:
                                stk_is_top = check_stan_weinstein_top_candidate(stk_p, stk_sma, stk_slope, stk_mrs, stk_vol, stk_vol_avg)
                                stock_data.append({
                                    "Top": "⭐ TOP" if stk_is_top else "",
                                    "Handelszeichen": stk_ticker, 
                                    "Name": stk_name, 
                                    "Börse": stk_exchange,
                                    "Kurs": f"{stk_p:.2f} {stk_curr}",
                                    "30W-SMA": f"{stk_sma:.2f} {stk_curr}", 
                                    "SMA-Steigung": f"{stk_slope:+.2f}%",
                                    "Mansfield-RS": round(stk_mrs, 2), 
                                    "Status": "🟢 Offen" if stk_open else "🔴 Zu",
                                })
                                stock_dfs[stk_ticker] = (stk_name, stk_df, stk_curr, stk_open)
                        except Exception:
                            pass

                    if stock_data:
                        stock_df = pd.DataFrame(stock_data).sort_values(by="Mansfield-RS", ascending=False)
                        st.dataframe(
                            stock_df[["Top", "Name", "Handelszeichen", "Börse", "Kurs", "30W-SMA", "SMA-Steigung", "Mansfield-RS", "Status"]],
                            hide_index=True,
                            use_container_width=True,
                            column_config={
                                "Top": st.column_config.TextColumn(
                                    "Top",
                                    help="⭐ TOP = Aktie erfüllt alle 4 Kriterien nach Stan Weinstein (Preis > 30W-SMA, Steigung > +0.5%, Mansfield RS > 0, Volumen >= 120%). Klicke auf '❓ Logik-Erklärung' für das vollständige Regelwerk."
                                ),
                                "Handelszeichen": st.column_config.TextColumn("Handelszeichen (Ticker)"),
                                "Börse": st.column_config.TextColumn("Börse / Handelsplatz")
                            }
                        )
                    else:
                        st.info("Aktuell keine Einzelaktie in diesem Sektor mit aktivem Stage-2-Setup.")

# ==========================================
# FOOTER / DISCLAIMER
# ==========================================
st.markdown("---")
st.markdown(
    """
    <div class="disclaimer-box">
        <strong>⚠️ Legal Disclaimer / Rechtlicher Haftungsausschluss:</strong><br><br>
        <strong>DE:</strong> Diese Webseite wird rein privat und ohne kommerzielle Absichten zu Informations- und Bildungszwecken betrieben. 
        Die bereitgestellten Inhalte, Chartanalysen und Berechnungen stellen ausdrücklich <u>keine Anlageberatung</u>, Kauf- oder Verkaufsempfehlung und keine Aufforderung zum Handel mit Finanzinstrumenten dar.<br><br>
        <strong>EN:</strong> This website is operated purely privately for non-commercial educational and informational purposes.
    </div>
    """,
    unsafe_allow_html=True
)

@st.dialog("📄 Impressum")
def show_impressum():
    st.markdown("""
    ### Impressum
    **Angaben gemäß § 5 DDG:**  
    Simon Moskwa
    Am Kohlenmeiler 81, 42389 Wuppertal, Deutschland
    E-Mail: [simon.moskwa@outlook.de](mailto:simon.moskwa@outlook.de)  
    """)

@st.dialog("🔒 Datenschutzerklärung")
def show_datenschutz():
    st.markdown("""
    ### Datenschutzerklärung
    Der Schutz Ihrer persönlichen Daten ist ein wichtiges Anliegen. Verantwortlich: Simon Moskwa.
    """)

footer_col1, footer_col2, footer_col3 = st.columns([2, 1, 1])
with footer_col1:
    st.caption("© Pulse Trading • Private & Rein Informative Webseite")
with footer_col2:
    if st.button("Impressum", key="btn_impressum", use_container_width=True):
        show_impressum()
with footer_col3:
    if st.button("Datenschutz", key="btn_datenschutz", use_container_width=True):
        show_datenschutz()
