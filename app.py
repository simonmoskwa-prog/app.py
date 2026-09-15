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
# HASHING HILFSFUNKTION (SHA-256)
# ---------------------------------------------------------
def hash_password(password: str) -> str:
    """Erstellt einen SHA-256 Hash für ein gegebenes Klartext-Passwort."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# ---------------------------------------------------------
# BÖRSENZEITEN-PRÜFUNG
# ---------------------------------------------------------
def is_market_open(ticker: str) -> bool:
    """Prüft, ob für den Ticker GERADE gehandelt werden kann."""
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
            and datetime.time(9, 0) <= now_berlin.time() <= datetime.time(17, 30)
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
# BENUTZER-VERWALTUNG (PERSISTENT PER JSON UND STREAMLIT SECRETS)
# ---------------------------------------------------------
USERS_FILE = "users.json"

DEFAULT_USERS = {
    "admin": {
        "password": hash_password("pulse2026"),
        "display_name": "Simon",
        "welcome_msg": "Willkommen Simon",
        "role": "admin"
    },
    "marcin.plonka": {
        "password": hash_password("change_me_user_1"),
        "display_name": "Marcin Płonka",
        "welcome_msg": "Willkommen Marcin Płonka",
        "role": "user"
    },
    "murat.seyfi": {
        "password": hash_password("change_me_user_2"),
        "display_name": "Murat Seyfi",
        "welcome_msg": "Willkommen Murat Seyfi",
        "role": "user"
    },
    "artur.boch": {
        "password": hash_password("change_me_user_3"),
        "display_name": "Artur",
        "welcome_msg": "Willkommen Artur",
        "role": "user"
    },
    "marcin.brudnik": {
        "password": hash_password("change_me_user_4"),
        "display_name": "Marcin",
        "welcome_msg": "Willkommen Marcin",
        "role": "user"
    },
    "janusz.grochowski": {
        "password": hash_password("change_me_user_5"),
        "display_name": "Janusz",
        "welcome_msg": "Willkommen Janusz",
        "role": "user"
    },
    "zbyszek.skora": {
        "password": hash_password("change_me_user_6"),
        "display_name": "Zbyszek",
        "welcome_msg": "Willkommen Zbyszek",
        "role": "user"
    },
    "karsten.gerhardt": {
        "password": hash_password("change_me_user_7"),
        "display_name": "Karsten",
        "welcome_msg": "Willkommen Karsten",
        "role": "user"
    },
    "patrick.mansilla": {
        "password": hash_password("change_me_user_8"),
        "display_name": "Patrick",
        "welcome_msg": "Willkommen Patrick",
        "role": "user"
    }
}

def load_users():
    users_db = {}
    
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users_db = json.load(f)
        except Exception:
            users_db = DEFAULT_USERS.copy()
    else:
        users_db = DEFAULT_USERS.copy()

    if "passwords" in st.secrets:
        for username, password in st.secrets["passwords"].items():
            u_key = str(username).strip().lower()
            users_db[u_key] = {
                "password": hash_password(str(password)),
                "display_name": u_key.capitalize(),
                "welcome_msg": f"Willkommen {u_key.capitalize()}",
                "role": "admin" if u_key == "admin" else "user"
            }
            
    return users_db

def save_users(users_dict):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_dict, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.warning(f"Benutzerdaten konnten nicht lokal gespeichert werden (z. B. Read-Only Cloud): {e}")

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
                    if user_input in users and users[user_input]["password"] == hash_password(pwd_input):
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
@st.dialog("📖 Hilfeseite & Stage-Analyse (Glossar)", width="large")
def show_glossary_dialog():
    st.markdown("## 📊 Regelwerk & Stage-Analyse nach Stan Weinstein")
    st.write("Hier findest du die genaue Erklärung der Phasen-Logik und wie Aktien gefiltert sowie als TOP KANDIDAT ausgezeichnet werden:")

    st.markdown("---")

    st.markdown("### 🔍 1. Erstfilter: Wann erscheint eine Aktie in der Liste?")
    st.write(
        "Damit eine Einzelaktie im Sektor-Dropdown als Kandidat geführt wird, muss sie grundlegende **Trend-Mindestanforderungen** erfüllen:"
    )
    st.markdown("""
    * **1. Kurs über 30W-SMA (`Preis > 30W-SMA`):** Der aktuelle Schlusskurs liegt über dem einfachen gleitenden Durchschnitt der letzten 30 Wochen im Wochenchart.
    * **2. Positiver Trend (`Steigung (4W) > 0.0%`):** Der 30-Wochen-Durchschnitt steigt im Vergleich zum Wert vor 4 Wochen an.

    *Aktien unter dem 30W-SMA oder in einem Abwärtstrend werden in den Tabellen ausgeblendet.*
    """)

    st.markdown("---")

    st.markdown("### ⭐ 2. Wann wird eine Aktie zum ⭐ TOP KANDIDATEN?")
    st.write(
        "Für das begehrte **`⭐ TOP`** Badge muss die Aktie ein hochdynamisches **Stage 2 Breakout-Setup** aufweisen. "
        "Hierfür müssen **alle 5 Kriterien gleichzeitig** erfüllt sein:"
    )
    st.markdown("""
    1. **Kurs über 30W-SMA:** Der Kurs notiert klar oberhalb des 30-Wochen-Durchschnitts.
    2. **Dynamische Steigung (`> +0.5%` oder `> 0.0%` bei 52W-Hoch):** Die 4-Wochen-Steigung des 30W-SMA zeigt Aufwärtsdynamik. Bei einem frischen Breakout reicht eine flach steigende SMA30-Linie.
    3. **Outperformance (`Mansfield RS > 0.0`):** Die Aktie ist stärkere als der Gesamtmarkt (S&P 500 Benchmark).
    4. **Volumen-Bestätigung (`Volumen >= 120% des 10W-Schnitts`):** Das Handelsvolumen liegt mindestens 20% über dem Durchschnitt der letzten 10 Wochen.
    5. **Breakout-Kriterium / 52W-Hoch-Nähe:** Der Kurs notiert nahe am 52-Wochen-Hoch (maximal 5% unter dem Hoch der letzten 52 Wochen).
    """)

    st.markdown("---")

    st.markdown("### 📈 3. Übersicht der 4 Marktphasen (Stages)")
    st.markdown("""
    * **Stage 1 (Bodenbildung / Consolidation):** Der Kurs pendelt um den 30W-SMA nach einem vorherigen Abwärtstrend (Stage 4). Akkumulationsphase.
    * **Stage 2 (Aufstiegsphase / Advancing Stage):** Kurs bricht über den 30W-SMA aus, der SMA steigt an. **Das optimale Kauf-Fenster!**
    * **Stage 3 (Topbildung / Distribution):** Der Kurs pendelt um den 30W-SMA nach einem vorherigen Aufwärtstrend (Stage 2).
    * **Stage 4 (Abstiegsphase / Declining Stage):** Kurs fällt unter den 30W-SMA, der SMA fällt ab. Meiden oder Short.
    """)

    st.markdown("---")

    st.markdown("### 📐 4. Mansfield Relative Stärke (RS)")
    st.write(
        "Die Mansfield RS vergleicht die Wertentwicklung der Aktie mit der Benchmark (S&P 500). "
        "Ein Wert **über 0** bedeutet, dass die Aktie den Markt schlägt (Outperformance)."
    )

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

    if st.button("🔄 Charts aktualisieren", key="btn_sidebar_refresh", use_container_width=True, help="Leert den Daten-Cache und lädt aktuelle Marktdaten neu."):
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
                new_pass = st.text_input("Passwort", key="add_pass", type="password").strip()
                new_name = st.text_input("Anzeigename (z.B. Max)", key="add_name").strip()
                new_role = st.selectbox("Rolle", ["user", "admin"], key="add_role")

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

                    edit_pass = st.text_input("Neues Passwort (leer lassen für keine Änderung)", type="password", key=f"edit_pass_{edit_user}").strip()
                    edit_name = st.text_input("Anzeigename", value=curr_data.get("display_name", ""), key=f"edit_name_{edit_user}")

                    role_idx = 0 if curr_data.get("role") == "user" else 1
                    edit_role = st.selectbox("Rolle", ["user", "admin"], index=role_idx, key=f"edit_role_{edit_user}")

                    if st.button("Änderungen Speichern", key=f"btn_save_{edit_user}", use_container_width=True):
                        final_pass = hash_password(edit_pass) if edit_pass else curr_data.get("password")
                        st.session_state["users_db"][edit_user] = {
                            "password": final_pass,
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main { padding-top: 1rem; }

    .stApp {
        background:
            radial-gradient(circle at 15% 0%, rgba(56, 189, 248, 0.07) 0%, transparent 45%),
            radial-gradient(circle at 85% 20%, rgba(129, 140, 248, 0.06) 0%, transparent 45%),
            #0b0e14;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1420 0%, #0b0e14 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    div[data-testid="stContainer"] {
        border-radius: 16px;
        background: rgba(22, 27, 34, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        transition: all 0.25s ease;
        padding: 4px;
    }

    div[data-testid="stContainer"]:hover {
        border-color: rgba(56, 189, 248, 0.35);
        box-shadow: 0 10px 36px 0 rgba(56, 189, 248, 0.12);
        transform: translateY(-1px);
    }

    .dashboard-title {
        font-size: 2.35rem;
        font-weight: 800;
        letter-spacing: -0.8px;
        margin-bottom: 0px;
        line-height: 1.2;
        background: linear-gradient(90deg, #ffffff 10%, #7dd3fc 60%, #a5b4fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .dashboard-subtitle {
        font-size: 0.92rem;
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
        box-shadow: 0 0 14px rgba(16, 185, 129, 0.45);
        display: inline-block;
        border: 1px solid #34d399;
    }

    .update-banner {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.14) 0%, rgba(129, 140, 248, 0.14) 100%);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 16px;
        padding: 16px 22px;
        margin-top: 15px;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        gap: 14px;
        box-shadow: 0 6px 25px rgba(0, 210, 255, 0.08);
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
        letter-spacing: 0.3px;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        font-weight: 700;
        letter-spacing: -0.3px;
        color: #f1f5f9;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #94a3b8 !important;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.4px;
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
        border-radius: 12px;
        padding: 15px 20px;
        font-size: 0.82rem;
        color: #94a3b8;
        line-height: 1.5;
    }

    .value-fair-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: #ffffff;
        font-weight: 800;
        font-size: 0.85rem;
        padding: 6px 14px;
        border-radius: 20px;
        box-shadow: 0 0 14px rgba(16, 185, 129, 0.45);
        display: inline-block;
        border: 1px solid #34d399;
    }

    .value-expensive-badge {
        background: rgba(248, 113, 113, 0.16);
        color: #f87171;
        font-weight: 800;
        font-size: 0.85rem;
        padding: 6px 14px;
        border-radius: 20px;
        display: inline-block;
        border: 1px solid rgba(248, 113, 113, 0.4);
    }

    .value-neutral-badge {
        background: rgba(251, 191, 36, 0.14);
        color: #fbbf24;
        font-weight: 800;
        font-size: 0.85rem;
        padding: 6px 14px;
        border-radius: 20px;
        display: inline-block;
        border: 1px solid rgba(251, 191, 36, 0.4);
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        background: rgba(255, 255, 255, 0.04) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        border-color: rgba(56, 189, 248, 0.55) !important;
        color: #38bdf8 !important;
        background: rgba(56, 189, 248, 0.08) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%) !important;
        border: none !important;
        color: #0b0e14 !important;
    }

    /* Inputs */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        border-radius: 10px !important;
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        font-weight: 600;
        border-radius: 8px 8px 0 0;
    }

    /* Section headings */
    h3 { letter-spacing: -0.3px; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 8px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(56, 189, 248, 0.4); }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HELPER FUNCTIONS & PERFORMANCE BATCH-LOADING
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
        response = requests.get(url, headers=headers, timeout=5)
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

def calculate_technical_indicators(df):
    """Berechnet 30W-SMA, Steigung, 10W-Vol-Avg und 52W-Hoch."""
    df["SMA30"] = df["Close"].rolling(window=30).mean()
    df["SMA30_Slope_4W"] = ((df["SMA30"] - df["SMA30"].shift(4)) / df["SMA30"].shift(4)) * 100
    df["Vol_Avg_10W"] = df["Volume"].rolling(window=10).mean()
    df["High_52W"] = df["Close"].rolling(window=52, min_periods=10).max()
    return df

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
        df = yf.download(ticker, start=start_date, end=today + datetime.timedelta(days=2), interval="1wk", auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            if ticker in df.columns.levels[1]:
                df = df.xs(ticker, level=1, axis=1)
            else:
                df = df.iloc[:, df.columns.get_level_values(0) == 'Close']

    if "Volume" not in df.columns:
        df["Volume"] = 0

    df = df[["Close", "Volume"]].dropna()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = calculate_technical_indicators(df)

    currency = "USD"
    exchange = "N/A"
    is_open = False
    company_name = ticker

    try:
        info = yticker.info
        currency = info.get("currency", "USD")
        exchange = info.get("exchange", "N/A")
        company_name = info.get("longName") or info.get("shortName") or ticker
        is_open = is_market_open(ticker)
    except Exception:
        is_open = False

    return df, currency, exchange, is_open, company_name

@st.cache_data(ttl=300)
def get_batch_stock_data(tickers):
    """Sicherer Batch-Download für Sektoraktien zur Vermeidung von Yahoo-Limits"""
    if not tickers:
        return {}
    
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=4 * 365)
    
    data = yf.download(tickers, start=start_date, end=today + datetime.timedelta(days=2), interval="1wk", auto_adjust=True, progress=False)
    results = {}
    
    for t in tickers:
        try:
            if isinstance(data.columns, pd.MultiIndex):
                if t in data.columns.get_level_values(1):
                    df_t = data.xs(t, level=1, axis=1)[["Close", "Volume"]].dropna()
                else:
                    continue
            else:
                df_t = data[["Close", "Volume"]].dropna()
                
            df_t.index = pd.to_datetime(df_t.index).tz_localize(None).normalize()
            df_t = calculate_technical_indicators(df_t)
            results[t] = df_t
        except Exception:
            continue
            
    return results

# ---------------------------------------------------------
# MANSFIELD RS BERECHNUNG & OPTIMIERTE STAGE LOGIK
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

def determine_stage(price, sma30, slope, df=None):
    """
    Optimierte Stufenbestimmung nach Stan Weinstein mit historischem Abgleich 
    für Stage 1 vs. Stage 3 & Puffer für frische Ausbrüche.
    """
    high_52w = df["High_52W"].iloc[-1] if (df is not None and "High_52W" in df.columns) else price
    is_at_52w_high = price >= (high_52w * 0.98)

    # 1. Puffer/Gleitende Abfrage: slope > 0.0% zulassen, wenn frisches Hoch vorliegt
    if price > sma30 and (slope > 0.5 or (slope > 0.0 and is_at_52w_high)):
        return ("Stage 2 (Aufstiegsphase)", "background-color: rgba(40, 167, 69, 0.2); color: #2ecc71; border: 1px solid rgba(40, 167, 69, 0.5);")
    elif price < sma30 and slope < -0.5:
        return ("Stage 4 (Abstiegsphase)", "background-color: rgba(220, 53, 69, 0.2); color: #e74c3c; border: 1px solid rgba(220, 53, 69, 0.5);")
    else:
        # 3. Säuberung Stage 1 vs Stage 3: Historischen Trend der letzten 26 Wochen prüfen
        prior_uptrend = False
        if df is not None and len(df) >= 26:
            past_price = df["Close"].iloc[-26]
            past_sma = df["SMA30"].iloc[-26] if "SMA30" in df.columns else past_price
            if past_price > past_sma:
                prior_uptrend = True

        if prior_uptrend:
            return ("Stage 3 (Topbildungsphase)", "background-color: rgba(255, 193, 7, 0.2); color: #f1c40f; border: 1px solid rgba(255, 193, 7, 0.5);")
        else:
            return ("Stage 1 (Bodenbildungsphase)", "background-color: rgba(108, 117, 125, 0.2); color: #95a5a6; border: 1px solid rgba(108, 117, 125, 0.5);")

def check_stan_weinstein_top_candidate(price, sma30, slope, mansfield_rs, volume=None, vol_avg_10w=None, high_52w=None):
    """
    Erweiterte Prüfung mit Breakout-Kriterium (52W-Hoch-Nähe) & Puffer für Slope.
    """
    c5_near_highs = (price >= (high_52w * 0.95)) if high_52w is not None and high_52w > 0 else True
    
    # 1. Puffer für Slope bei Ausbruch nahe Hochs
    c1_price_above_sma = price > sma30
    c2_sma_rising = (slope > 0.5) or (slope > 0.0 and c5_near_highs)
    c3_mansfield_positive = mansfield_rs > 0.0

    c4_volume_confirmed = True
    if volume is not None and vol_avg_10w is not None and vol_avg_10w > 0:
        c4_volume_confirmed = volume >= (vol_avg_10w * 1.2)

    return c1_price_above_sma and c2_sma_rising and c3_mansfield_positive and c4_volume_confirmed and c5_near_highs

# ---------------------------------------------------------
# LANGFRISTIGE WERTANALYSE (VEREINFACHTES EIGENKAPITAL-MODELL)
# ---------------------------------------------------------
# Hinweis: Die folgenden Funktionen bilden ein selbst entwickeltes, stark
# vereinfachtes Bewertungsmodell ab, das sich an gängigen Grundsätzen der
# fundamentalen Qualitäts- und Wachstumsanalyse orientiert (u. a. Kapitalrendite,
# nachhaltiges Gewinn-/Umsatz-/Eigenkapitalwachstum sowie ein Sicherheitsabschlag
# auf einen rechnerisch ermittelten "fairen" Zielwert). Es handelt sich
# ausdrücklich NICHT um eine Anlageberatung, sondern um eine rein informative,
# eigenständige Modellrechnung auf Basis öffentlich verfügbarer Kennzahlen.

def _get_row_value(df, candidates):
    """Sucht in einem Financials-DataFrame die erste passende Zeile aus einer Liste möglicher Bezeichnungen."""
    if df is None or df.empty:
        return None
    for name in candidates:
        if name in df.index:
            return df.loc[name]
    return None

def _cagr(series):
    """Berechnet die durchschnittliche jährliche Wachstumsrate (CAGR) aus einer zeitlich sortierten Serie (älteste -> neueste)."""
    try:
        s = series.dropna()
        if len(s) < 2:
            return None
        start_val = float(s.iloc[0])
        end_val = float(s.iloc[-1])
        years = len(s) - 1
        if start_val <= 0 or end_val <= 0 or years <= 0:
            return None
        return (end_val / start_val) ** (1.0 / years) - 1.0
    except Exception:
        return None

@st.cache_data(ttl=3600)
def get_fundamental_bundle(ticker):
    """Lädt Bilanz-, GuV- und Cashflow-Daten sowie Stammdaten für die Wertanalyse (gecacht, 1h)."""
    t = yf.Ticker(ticker)
    info = {}
    try:
        info = t.info or {}
    except Exception:
        info = {}

    income = pd.DataFrame()
    balance = pd.DataFrame()
    cashflow = pd.DataFrame()
    try:
        income = t.financials if t.financials is not None else pd.DataFrame()
    except Exception:
        pass
    try:
        balance = t.balance_sheet if t.balance_sheet is not None else pd.DataFrame()
    except Exception:
        pass
    try:
        cashflow = t.cashflow if t.cashflow is not None else pd.DataFrame()
    except Exception:
        pass

    return info, income, balance, cashflow

def compute_quality_growth_metrics(ticker):
    """
    Ermittelt die zentralen Qualitäts- und Wachstumskennzahlen (angelehnt an die
    verbreitete "5 Kennzahlen"-Logik der fundamentalen Value-Analyse):
    Kapitalrendite (ROIC), Gewinnwachstum, Umsatzwachstum, Eigenkapitalwachstum,
    freier Cashflow-Wachstum. Fehlende Datenpunkte werden als None markiert und
    entsprechend transparent ausgewiesen.
    """
    info, income, balance, cashflow = get_fundamental_bundle(ticker)
    metrics = {
        "current_price": None, "currency": info.get("currency", "USD"),
        "eps_ttm": info.get("trailingEps"),
        "trailing_pe": info.get("trailingPE"),
        "shares_out": info.get("sharesOutstanding"),
        "roic_avg": None, "eps_cagr": None, "sales_cagr": None,
        "equity_cagr": None, "fcf_cagr": None, "years_available": 0,
    }

    metrics["current_price"] = (
        info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
    )

    # --- Umsatz & Gewinn (chronologisch: älteste zuerst) ---
    revenue = _get_row_value(income, ["Total Revenue", "TotalRevenue"])
    net_income = _get_row_value(income, ["Net Income", "NetIncome", "Net Income Common Stockholders"])
    diluted_eps = _get_row_value(income, ["Diluted EPS", "DilutedEPS"])

    if revenue is not None:
        revenue = revenue.iloc[::-1]
        metrics["sales_cagr"] = _cagr(revenue)
        metrics["years_available"] = max(metrics["years_available"], len(revenue.dropna()))

    eps_series = diluted_eps if diluted_eps is not None else None
    if eps_series is not None:
        eps_series = eps_series.iloc[::-1]
        metrics["eps_cagr"] = _cagr(eps_series)
    elif net_income is not None and metrics["shares_out"]:
        approx_eps = (net_income / metrics["shares_out"]).iloc[::-1]
        metrics["eps_cagr"] = _cagr(approx_eps)

    # --- Eigenkapital je Aktie (Buchwert-Wachstum) ---
    equity = _get_row_value(balance, ["Total Stockholder Equity", "Stockholders Equity", "Common Stock Equity"])
    if equity is not None and metrics["shares_out"]:
        equity_per_share = (equity / metrics["shares_out"]).iloc[::-1]
        metrics["equity_cagr"] = _cagr(equity_per_share)
    elif equity is not None:
        metrics["equity_cagr"] = _cagr(equity.iloc[::-1])

    # --- Freier Cashflow (operativ - Investitionen) ---
    fcf_row = _get_row_value(cashflow, ["Free Cash Flow", "FreeCashFlow"])
    if fcf_row is None:
        op_cf = _get_row_value(cashflow, ["Operating Cash Flow", "Total Cash From Operating Activities"])
        capex = _get_row_value(cashflow, ["Capital Expenditure", "CapitalExpenditure"])
        if op_cf is not None and capex is not None:
            fcf_row = op_cf + capex  # Capex ist i.d.R. negativ ausgewiesen
    if fcf_row is not None:
        metrics["fcf_cagr"] = _cagr(fcf_row.iloc[::-1])

    # --- Kapitalrendite (vereinfachtes ROIC: Nettogewinn / investiertes Kapital) ---
    total_debt = _get_row_value(balance, ["Total Debt", "TotalDebt"])
    cash_row = _get_row_value(balance, ["Cash And Cash Equivalents", "Cash", "CashAndCashEquivalents"])
    if net_income is not None and equity is not None:
        try:
            common_idx = net_income.index.intersection(equity.index)
            roic_values = []
            for dt in common_idx:
                eq_val = equity.get(dt)
                debt_val = total_debt.get(dt) if total_debt is not None else 0
                cash_val = cash_row.get(dt) if cash_row is not None else 0
                ni_val = net_income.get(dt)
                invested_capital = (eq_val or 0) + (debt_val or 0) - (cash_val or 0)
                if invested_capital and invested_capital > 0 and ni_val is not None:
                    roic_values.append(ni_val / invested_capital)
            if roic_values:
                metrics["roic_avg"] = sum(roic_values) / len(roic_values)
        except Exception:
            pass
    if metrics["roic_avg"] is None and info.get("returnOnEquity") is not None:
        metrics["roic_avg"] = info.get("returnOnEquity")

    return metrics

def compute_target_valuation(metrics, min_return=0.15, forecast_years=10, safety_margin=0.5):
    """
    Rein rechnerische Modell-Bewertung auf Basis von aktuellem Gewinn je Aktie,
    einer konservativ geschätzten Wachstumsrate sowie einer geforderten
    Mindestrendite. Ergebnis: rechnerischer Zielwert sowie ein Wert mit
    Sicherheitsabschlag. Keine Kursprognose, keine Empfehlung.
    """
    result = {
        "growth_used": None, "future_eps": None, "assumed_future_pe": None,
        "target_value": None, "safety_value": None, "payback_years": None,
        "verdict": "nicht bewertbar", "verdict_class": "value-neutral-badge",
    }

    eps = metrics.get("eps_ttm")
    price = metrics.get("current_price")
    eps_cagr = metrics.get("eps_cagr")
    trailing_pe = metrics.get("trailing_pe")

    if not eps or eps <= 0 or not price:
        return result

    # Konservative Wachstumsannahme: historisches Gewinnwachstum, nach unten auf 0%
    # und nach oben auf 15% p.a. begrenzt (Sicherheitsabschlag gegen Extrapolation).
    if eps_cagr is None:
        growth = 0.06  # neutrale Standardannahme, falls keine Historie verfügbar
    else:
        growth = max(0.0, min(eps_cagr, 0.15))
    result["growth_used"] = growth

    future_eps = eps * ((1 + growth) ** forecast_years)
    result["future_eps"] = future_eps

    # Angenommenes künftiges KGV: konservativ das Doppelte der Wachstumsrate (in %-Punkten),
    # zusätzlich gedeckelt durch das aktuelle KGV (falls vorhanden) und einen absoluten Deckel.
    pe_from_growth = growth * 100 * 2
    pe_cap_candidates = [pe_from_growth, 20.0]
    if trailing_pe and trailing_pe > 0:
        pe_cap_candidates.append(trailing_pe)
    assumed_future_pe = max(8.0, min(pe_cap_candidates))
    result["assumed_future_pe"] = assumed_future_pe

    future_value = future_eps * assumed_future_pe
    target_value = future_value / ((1 + min_return) ** forecast_years)
    safety_value = target_value * safety_margin

    result["target_value"] = target_value
    result["safety_value"] = safety_value

    # Amortisationsdauer: Jahre, bis die kumulierten (wachsenden) Gewinne je Aktie
    # den aktuellen Kurs rechnerisch "zurückgezahlt" hätten.
    cumulative = 0.0
    payback_years = None
    running_eps = eps
    for year in range(1, 31):
        running_eps *= (1 + growth)
        cumulative += running_eps
        if cumulative >= price:
            payback_years = year
            break
    result["payback_years"] = payback_years

    if price <= safety_value:
        result["verdict"] = "Rechnerisch attraktiv bewertet (Kurs unter Sicherheitsabschlag-Wert)"
        result["verdict_class"] = "value-fair-badge"
    elif price <= target_value:
        result["verdict"] = "Im rechnerisch fairen Bereich (kein Sicherheitsabschlag vorhanden)"
        result["verdict_class"] = "value-neutral-badge"
    else:
        result["verdict"] = "Rechnerisch eher hoch bewertet (Kurs über Zielwert)"
        result["verdict_class"] = "value-expensive-badge"

    return result

def format_metric_pct(value):
    return f"{value * 100:+.1f}%" if value is not None else "n. v."

def format_metric_money(value, currency=""):
    return f"{value:,.2f} {currency}".strip() if value is not None else "n. v."

# ---------------------------------------------------------
# CHART-LAYOUT & RENDERING
# ---------------------------------------------------------
def apply_current_period_view(fig, plot_df):
    if plot_df.empty:
        return fig

    first_date = plot_df.index.min()
    last_date = plot_df.index.max()
    range_end = last_date + pd.Timedelta(days=14)

    fig.update_xaxes(
        type="date",
        tickformat="%b %Y",
        dtick="M1",
        range=[first_date, range_end],
        showgrid=True,
        gridcolor="rgba(255,255,255,0.04)",
        automargin=True
    )

    fig.add_vline(
        x=last_date.timestamp() * 1000,
        line_width=1,
        line_dash="dot",
        line_color="rgba(255,255,255,0.35)",
    )
    fig.add_annotation(
        x=last_date, y=0.97, xref="x", yref="y domain",
        text="Aktuell ●", showarrow=False,
        xanchor="right", yanchor="top",
        xshift=-4,
        font=dict(color="#38bdf8", size=10, family="Inter, sans-serif"),
        row=1, col=1,
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
        modebar=dict(
            orientation="h",
            bgcolor="rgba(15, 20, 30, 0.7)"
        )
    )
    
    fig.update_yaxes(automargin=True, title_standoff=8)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

# ---------------------------------------------------------
# DETAIL-SEITE FÜR EINE EINZELNE AKTIE
# ---------------------------------------------------------
def render_stock_detail_page(ticker, benchmark_df):
    if st.button("⬅ Zurück zum Dashboard", key="btn_back_to_dashboard"):
        st.session_state["selected_stock"] = None
        st.rerun()

    st.markdown("---")

    try:
        with st.spinner(f"Lade Detailanalyse für '{ticker}'..."):
            d_df, d_curr, d_exchange, d_open, d_name = get_data_with_info(ticker)
            d_df["Mansfield_RS"] = calculate_mansfield_rs(d_df, benchmark_df)

            d_price = d_df["Close"].iloc[-1]
            d_sma = d_df["SMA30"].iloc[-1]
            d_slope = d_df["SMA30_Slope_4W"].iloc[-1]
            d_mrs = d_df["Mansfield_RS"].iloc[-1]
            d_vol = d_df["Volume"].iloc[-1]
            d_vol_avg = d_df["Vol_Avg_10W"].iloc[-1]
            d_high52 = d_df["High_52W"].iloc[-1] if "High_52W" in d_df.columns else d_price

            d_stage, d_css = determine_stage(d_price, d_sma, d_slope, d_df)
            d_is_top = check_stan_weinstein_top_candidate(d_price, d_sma, d_slope, d_mrs, d_vol, d_vol_avg, d_high52)

            d_status_badge = (
                "<span class='status-badge-open'>🟢 Börse Geöffnet</span>"
                if d_open
                else "<span class='status-badge-closed'>🔴 Börse Geschlossen</span>"
            )
            d_top_badge = "<span class='top-candidate-badge'>⭐ TOP KANDIDAT (Stage 2)</span> &nbsp;" if d_is_top else ""

            st.markdown(f"## {d_name} (`{ticker}`)")
            st.markdown(
                f"<div style='margin-top: 4px; margin-bottom: 14px;'>"
                f"{d_top_badge}"
                f"<span style='padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 13px; {d_css}'>"
                f"{d_stage}</span> &nbsp; {d_status_badge} &nbsp; "
                f"<span style='font-size: 0.85rem; color:#94a3b8;'>Börse: <b>{d_exchange}</b> | Handelszeichen: <b>{ticker}</b> | Währung: <b>{d_curr}</b></span></div>",
                unsafe_allow_html=True,
            )

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Aktueller Kurs", f"{d_price:.2f} {d_curr}")
            m2.metric("30W-SMA", f"{d_sma:.2f} {d_curr}")
            m3.metric("SMA Steigung (4W)", f"{d_slope:+.2f}%")
            m4.metric("Mansfield RS", f"{d_mrs:+.2f}")

            with st.container(border=True):
                plot_df_d = d_df.tail(104)

                fig_d = make_subplots(
                    rows=3, cols=1, shared_xaxes=True,
                    vertical_spacing=0.05, row_heights=[0.55, 0.20, 0.25]
                )

                fig_d.add_trace(
                    go.Scatter(
                        x=plot_df_d.index, y=plot_df_d["Close"],
                        mode="lines", name=f"Kurs ({d_curr})",
                        line=dict(color="#38bdf8", width=2.5),
                        fill='tozeroy', fillcolor='rgba(56, 189, 248, 0.05)'
                    ), row=1, col=1
                )
                fig_d.add_trace(
                    go.Scatter(
                        x=plot_df_d.index, y=plot_df_d["SMA30"],
                        mode="lines", name="30W-SMA",
                        line=dict(color="#fbbf24", width=2, dash="dash")
                    ), row=1, col=1
                )

                vol_colors_d = ['#2ecc71' if plot_df_d["Close"].iloc[i] >= plot_df_d["Close"].iloc[i-1] else '#e74c3c' for i in range(len(plot_df_d))]
                fig_d.add_trace(
                    go.Bar(x=plot_df_d.index, y=plot_df_d["Volume"], name="Volumen", marker_color=vol_colors_d, opacity=0.7),
                    row=2, col=1
                )

                rs_colors_d = ['#2ecc71' if val >= 0 else '#e74c3c' for val in plot_df_d["Mansfield_RS"]]
                fig_d.add_trace(
                    go.Bar(x=plot_df_d.index, y=plot_df_d["Mansfield_RS"], name="Mansfield RS", marker_color=rs_colors_d),
                    row=3, col=1
                )

                fig_d.update_layout(
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", title=f"Preis ({d_curr})"),
                    yaxis2=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Vol."),
                    yaxis3=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor="rgba(255,255,255,0.2)", title="RS")
                )
                apply_current_period_view(fig_d, plot_df_d)
                render_chart(fig_d, height=520)

            with st.expander("❓ Was bedeuten diese Kennzahlen?"):
                st.write(
                    "**Mansfield RS** misst die relative Stärke zum S&P 500 (> 0 = stärkere Performance). "
                    "**30W-SMA** ist der 30-Wochen-Durchschnitt. **⭐ TOP KANDIDAT** erfordert: Kurs über 30W-SMA, "
                    "Mansfield RS > 0, Volumen ≥ 120% des 10W-Schnitts sowie eine Notierung innerhalb von 5% des 52-Wochen-Hochs."
                )

    except Exception:
        st.error(f"Daten für '{ticker}' konnten nicht geladen werden.")

# Core Benchmark Setup
BENCHMARK = "^GSPC"
bench_df, _, _, _, _ = get_data_with_info(BENCHMARK)

if "selected_stock" not in st.session_state:
    st.session_state["selected_stock"] = None

if st.session_state.get("selected_stock"):
    render_stock_detail_page(st.session_state["selected_stock"], bench_df)
    st.stop()

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

st.markdown(
    """
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

# ==========================================
# HAUPTBEREICHE: KURZFRISTIG vs. LANGFRISTIG
# ==========================================
st.markdown("---")
tab_short, tab_long = st.tabs(["⚡ Kurzfristig – Stage-Analyse", "🏛️ Langfristig – Wertanalyse"])

with tab_short:
    # ==========================================
    # AKTIEN-SUCHE & PHASEN-ANALYSE
    # ==========================================
    st.markdown("---")
    st.subheader("🔍 Aktiensuche & Phasen-Analyse")

    if "active_search" not in st.session_state:
        st.session_state["active_search"] = None

    with st.container(border=True):
        search_col1, search_col2, search_col3 = st.columns([3, 1, 1])
        with search_col1:
            search_query_input = st.text_input(
                "Aktienname oder Ticker eingeben (z.B. Dino Polska, NVDA, Apple, LVMH, MC.PA):",
                value="Dino Polska",
                key="search_ticker_input"
            ).strip()
        with search_col2:
            st.write("")
            st.write("")
            if st.button("🔎 Analyse starten", use_container_width=True, key="btn_run_search"):
                st.session_state["active_search"] = search_query_input
        with search_col3:
            st.write("")
            st.write("")
            if st.button("🔄 Charts aktualisieren", key="btn_refresh_charts", use_container_width=True):
                st.cache_data.clear()
                st.success("Charts werden neu geladen...")
                st.rerun()

        query_to_run = st.session_state["active_search"] if st.session_state["active_search"] else search_query_input

        if query_to_run:
            resolved_ticker = get_ticker_from_name(query_to_run)

            try:
                with st.spinner(f"Lade Daten für '{query_to_run}' (Handelszeichen: {resolved_ticker})..."):
                    stock_df, stock_curr, stock_exchange, stock_open, comp_name = get_data_with_info(resolved_ticker)
                    stock_df["Mansfield_RS"] = calculate_mansfield_rs(stock_df, bench_df)

                    s_price = stock_df["Close"].iloc[-1]
                    s_sma = stock_df["SMA30"].iloc[-1]
                    s_slope = stock_df["SMA30_Slope_4W"].iloc[-1]
                    s_mrs = stock_df["Mansfield_RS"].iloc[-1]
                    s_vol = stock_df["Volume"].iloc[-1]
                    s_vol_avg = stock_df["Vol_Avg_10W"].iloc[-1]
                    s_high52 = stock_df["High_52W"].iloc[-1] if "High_52W" in stock_df.columns else s_price

                    s_stage, s_css = determine_stage(s_price, s_sma, s_slope, stock_df)
                    is_top_candidate = check_stan_weinstein_top_candidate(s_price, s_sma, s_slope, s_mrs, s_vol, s_vol_avg, s_high52)

                    s_status_badge = (
                        "<span class='status-badge-open'>🟢 Börse Geöffnet</span>"
                        if stock_open
                        else "<span class='status-badge-closed'>🔴 Börse Geschlossen</span>"
                    )

                    st.markdown("---")
                    header_s1, _ = st.columns([2, 1])
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
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        yaxis=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", title=f"Preis ({stock_curr})"),
                        yaxis2=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Vol."),
                        yaxis3=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor="rgba(255,255,255,0.2)", title="RS")
                    )
                    apply_current_period_view(fig_search, plot_df_search)
                    render_chart(fig_search, height=500)

            except Exception:
                st.error(f"Aktie '{query_to_run}' (gefundener Ticker: '{resolved_ticker}') konnte nicht geladen werden. Bitte überprüfe die Eingabe.")

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
                stage_str, css_style = determine_stage(p_idx, sma_idx, slope_idx, df_idx)

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
                            showlegend=False,
                            yaxis=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                            yaxis2=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Vol."),
                            yaxis3=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor="rgba(255,255,255,0.2)", title="RS")
                        )
                        apply_current_period_view(fig_idx, plot_df)
                        render_chart(fig_idx, height=360)
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
            high52 = sec_df["High_52W"].iloc[-1] if "High_52W" in sec_df.columns else p

            stage, css = determine_stage(p, sma, slope, sec_df)
            is_top = check_stan_weinstein_top_candidate(p, sma, slope, m_rs, vol, vol_avg, high52)

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
                    showlegend=False,
                    yaxis=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                    yaxis2=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Vol."),
                    yaxis3=dict(visible=True, showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=True, zerolinecolor="rgba(255,255,255,0.2)", title="RS")
                )
                apply_current_period_view(fig, plot_df)
                render_chart(fig, height=380)

                rs_disp = f"{item['m_rs']:+.2f}"
                rs_color = "#4ade80" if item["m_rs"] > 0 else "#f87171"
                st.markdown(
                    f"**Mansfield-RS:** <span style='color:{rs_color}; font-weight:bold;'>{rs_disp}</span> | "
                    f"**30W-SMA Steigung:** `{item['slope']:+.2f}%`",
                    unsafe_allow_html=True
                )

                exp_header_col1, exp_header_col2 = st.columns([0.65, 0.35])

                with exp_header_col2:
                    if st.button("❓ Logik-Erklärung", key=f"help_icon_{item['ticker']}_{idx}", help="Klicken für Erläuterung der Stage-2 & Top-Kandidat Logik"):
                        show_glossary_dialog()

                with exp_header_col1:
                    expander_target = st.expander("🔎 Top-Aktien im Stage-2-Setup anzeigen")

                    with expander_target:
                        stock_data = []
                        sec_stock_tickers = list(item["stocks"].keys())
                    
                        batch_dfs = get_batch_stock_data(sec_stock_tickers)

                        for stk_ticker, stk_name in item["stocks"].items():
                            if stk_ticker in batch_dfs:
                                stk_df = batch_dfs[stk_ticker]
                                if stk_df.empty or len(stk_df) < 30:
                                    continue
                                
                                stk_df["Mansfield_RS"] = calculate_mansfield_rs(stk_df, bench_df)
                                stk_p = stk_df["Close"].iloc[-1]
                                stk_sma = stk_df["SMA30"].iloc[-1]
                                stk_slope = stk_df["SMA30_Slope_4W"].iloc[-1]
                                stk_mrs = stk_df["Mansfield_RS"].iloc[-1]
                                stk_vol = stk_df["Volume"].iloc[-1]
                                stk_vol_avg = stk_df["Vol_Avg_10W"].iloc[-1]
                                stk_high52 = stk_df["High_52W"].iloc[-1] if "High_52W" in stk_df.columns else stk_p

                                # Erstfilter: Aktie muss im Aufwärtstrend über 30W-SMA notieren
                                if stk_p > stk_sma and stk_slope > 0:
                                    stk_is_top = check_stan_weinstein_top_candidate(stk_p, stk_sma, stk_slope, stk_mrs, stk_vol, stk_vol_avg, stk_high52)
                                    stock_data.append({
                                        "Top": "⭐ TOP" if stk_is_top else "",
                                        "Handelszeichen": stk_ticker,
                                        "Name": stk_name,
                                        "Börse": "US/EU",
                                        "Kurs": f"{stk_p:.2f}",
                                        "30W-SMA": f"{stk_sma:.2f}",
                                        "SMA-Steigung": f"{stk_slope:+.2f}%",
                                        "Mansfield-RS": round(stk_mrs, 2),
                                        "Status": "🟢 Offen" if is_market_open(stk_ticker) else "🔴 Zu",
                                    })

                        if stock_data:
                            stock_df_res = pd.DataFrame(stock_data).sort_values(by="Mansfield-RS", ascending=False).reset_index(drop=True)
                            st.caption("💡 Klicke auf eine Zeile, um die Detailanalyse der Aktie zu öffnen.")
                            table_cols = ["Top", "Name", "Handelszeichen", "Börse", "Kurs", "30W-SMA", "SMA-Steigung", "Mansfield-RS", "Status"]
                            selection_event = st.dataframe(
                                stock_df_res[table_cols],
                                hide_index=True,
                                use_container_width=True,
                                on_select="rerun",
                                selection_mode="single-row",
                                key=f"stock_table_{item['ticker']}_{idx}",
                                column_config={
                                    "Top": st.column_config.TextColumn("Top"),
                                    "Handelszeichen": st.column_config.TextColumn("Handelszeichen (Ticker)"),
                                    "Börse": st.column_config.TextColumn("Börse / Handelsplatz")
                                }
                            )

                            if selection_event and selection_event.get("selection", {}).get("rows"):
                                sel_row = selection_event["selection"]["rows"][0]
                                sel_ticker = stock_df_res.iloc[sel_row]["Handelszeichen"]
                                st.session_state["selected_stock"] = sel_ticker
                                st.rerun()
                        else:
                            st.info("Aktuell keine Einzelaktie in diesem Sektor mit aktivem Stage-2-Setup.")

with tab_long:
    st.subheader("🏛️ Langfristige Wertanalyse")

    st.markdown(
        """
        <div class="disclaimer-box" style="margin-bottom: 18px;">
            <strong>ℹ️ Hinweis:</strong> Dieser Bereich richtet sich an langfristig orientierte Anleger und zeigt eine
            rein rechnerische, modellbasierte Einordnung anhand öffentlich verfügbarer Kennzahlen zu Kapitalrendite,
            Gewinn-, Umsatz-, Eigenkapital- und Cashflow-Wachstum. Daraus wird ein rechnerischer Zielwert sowie ein Wert
            mit Sicherheitsabschlag ermittelt. Es handelt sich <u>ausdrücklich nicht um eine Anlageberatung, Kauf- oder
            Verkaufsempfehlung</u> und nicht um eine Kursprognose, sondern um eine unverbindliche, informative Modellrechnung.
            Alle Berechnungen basieren auf historischen und ggf. lückenhaften Daten und können jederzeit von der
            tatsächlichen Geschäftsentwicklung abweichen.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "active_search_long" not in st.session_state:
        st.session_state["active_search_long"] = None

    with st.container(border=True):
        lt_col1, lt_col2, lt_col3 = st.columns([3, 1, 1])
        with lt_col1:
            lt_query_input = st.text_input(
                "Aktienname oder Ticker eingeben (z.B. Apple, KO, Nestle, ASML):",
                value="Apple",
                key="search_ticker_input_long"
            ).strip()
        with lt_col2:
            st.write("")
            st.write("")
            if st.button("📐 Bewertung starten", use_container_width=True, key="btn_run_search_long"):
                st.session_state["active_search_long"] = lt_query_input
        with lt_col3:
            st.write("")
            st.write("")
            if st.button("🔄 Daten aktualisieren", key="btn_refresh_long", use_container_width=True):
                st.cache_data.clear()
                st.success("Daten werden neu geladen...")
                st.rerun()

        with st.expander("⚙️ Modell-Annahmen anpassen (optional)"):
            lt_min_return_pct = st.slider("Geforderte Mindestrendite p. a.", 8, 20, 15, step=1, key="lt_min_return")
            lt_safety_margin_pct = st.slider("Sicherheitsabschlag auf den Zielwert", 20, 60, 50, step=5, key="lt_safety_margin")
            lt_forecast_years = st.slider("Prognosehorizont (Jahre)", 5, 15, 10, step=1, key="lt_forecast_years")
            st.caption("Standardwerte entsprechen einer konservativen Grundeinstellung. Eine höhere Mindestrendite bzw. ein größerer Sicherheitsabschlag führen zu einem strengeren Modell.")

        lt_query_to_run = st.session_state["active_search_long"] if st.session_state["active_search_long"] else lt_query_input

        if lt_query_to_run:
            lt_resolved_ticker = get_ticker_from_name(lt_query_to_run)

            try:
                with st.spinner(f"Lade Fundamentaldaten für '{lt_query_to_run}' (Handelszeichen: {lt_resolved_ticker})..."):
                    lt_df, lt_curr, lt_exchange, lt_open, lt_name = get_data_with_info(lt_resolved_ticker)
                    lt_metrics = compute_quality_growth_metrics(lt_resolved_ticker)
                    lt_valuation = compute_target_valuation(
                        lt_metrics,
                        min_return=lt_min_return_pct / 100.0,
                        forecast_years=lt_forecast_years,
                        safety_margin=lt_safety_margin_pct / 100.0,
                    )

                    lt_price = lt_metrics.get("current_price") or lt_df["Close"].iloc[-1]
                    lt_currency = lt_metrics.get("currency") or lt_curr

                    st.markdown("---")
                    st.markdown(f"### {lt_name} (`{lt_resolved_ticker}`)")

                    st.markdown(
                        f"<div style='margin-top: 4px; margin-bottom: 14px;'>"
                        f"<span class='{lt_valuation['verdict_class']}'>{lt_valuation['verdict']}</span> &nbsp; "
                        f"<span style='font-size: 0.85rem; color:#94a3b8;'>Börse: <b>{lt_exchange}</b> | Handelszeichen: <b>{lt_resolved_ticker}</b> | Währung: <b>{lt_currency}</b></span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                    v1, v2, v3 = st.columns(3)
                    v1.metric("Aktueller Kurs", format_metric_money(lt_price, lt_currency))
                    v2.metric("Rechnerischer Zielwert", format_metric_money(lt_valuation["target_value"], lt_currency))
                    v3.metric("Wert inkl. Sicherheitsabschlag", format_metric_money(lt_valuation["safety_value"], lt_currency))

                    st.write("")
                    st.markdown("##### 📋 Zentrale Qualitäts- und Wachstumskennzahlen")

                    k1, k2, k3, k4, k5 = st.columns(5)
                    k1.metric("Ø Kapitalrendite (ROIC)", format_metric_pct(lt_metrics["roic_avg"]))
                    k2.metric("Gewinnwachstum (Ø p. a.)", format_metric_pct(lt_metrics["eps_cagr"]))
                    k3.metric("Umsatzwachstum (Ø p. a.)", format_metric_pct(lt_metrics["sales_cagr"]))
                    k4.metric("Eigenkapitalwachstum (Ø p. a.)", format_metric_pct(lt_metrics["equity_cagr"]))
                    k5.metric("Freier Cashflow (Ø p. a.)", format_metric_pct(lt_metrics["fcf_cagr"]))

                    k6, k7, k8 = st.columns(3)
                    k6.metric("Im Modell angenommenes Wachstum", format_metric_pct(lt_valuation["growth_used"]))
                    k7.metric("Angenommenes künftiges KGV", f"{lt_valuation['assumed_future_pe']:.1f}" if lt_valuation["assumed_future_pe"] else "n. v.")
                    k8.metric(
                        "Rechnerische Amortisationsdauer",
                        f"{lt_valuation['payback_years']} Jahre" if lt_valuation["payback_years"] else "> 30 Jahre",
                        help="Anzahl Jahre, bis die kumulierten (wachsenden) Gewinne je Aktie rechnerisch dem heutigen Kurs entsprechen."
                    )

                    with st.container(border=True):
                        lt_plot_df = lt_df.tail(260)
                        fig_lt = go.Figure()
                        fig_lt.add_trace(
                            go.Scatter(
                                x=lt_plot_df.index, y=lt_plot_df["Close"],
                                mode="lines", name=f"Kurs ({lt_currency})",
                                line=dict(color="#38bdf8", width=2.5),
                                fill="tozeroy", fillcolor="rgba(56, 189, 248, 0.05)",
                            )
                        )
                        if lt_valuation["target_value"]:
                            fig_lt.add_hline(
                                y=lt_valuation["target_value"], line_dash="dash", line_color="#fbbf24",
                                annotation_text="Rechnerischer Zielwert", annotation_position="top left",
                            )
                        if lt_valuation["safety_value"]:
                            fig_lt.add_hline(
                                y=lt_valuation["safety_value"], line_dash="dot", line_color="#4ade80",
                                annotation_text="Wert inkl. Sicherheitsabschlag", annotation_position="bottom left",
                            )
                        apply_current_period_view(fig_lt, lt_plot_df)
                        render_chart(fig_lt, height=380)

                    st.caption(
                        "Gestrichelte Linie: rechnerischer Zielwert auf Basis der Modellannahmen. "
                        "Gepunktete Linie: Zielwert abzüglich Sicherheitsabschlag."
                    )

                    with st.expander("❓ Wie kommen diese Werte zustande? (Modell-Erläuterung)"):
                        st.markdown("""
                        Das Modell orientiert sich an gängigen Grundsätzen fundamentaler, langfristiger Aktienanalyse:

                        1. **Kapitalrendite (ROIC):** Verhältnis von Nettogewinn zu eingesetztem Kapital (Eigenkapital + Schulden − liquide Mittel). Höhere Werte deuten auf ein effizienteres Geschäftsmodell hin.
                        2. **Wachstumskennzahlen:** Durchschnittliches jährliches Wachstum von Gewinn je Aktie, Umsatz, Eigenkapital je Aktie und freiem Cashflow über den verfügbaren historischen Zeitraum.
                        3. **Zukünftiger Gewinn:** Der aktuelle Gewinn je Aktie wird mit einer konservativen, nach oben gedeckelten Wachstumsrate über den gewählten Prognosehorizont fortgeschrieben.
                        4. **Künftiges Kurs-Gewinn-Verhältnis:** Wird konservativ geschätzt und zusätzlich durch das aktuelle KGV sowie einen absoluten Höchstwert begrenzt.
                        5. **Rechnerischer Zielwert:** Der so ermittelte künftige Unternehmenswert wird mit der geforderten Mindestrendite auf heute abgezinst.
                        6. **Sicherheitsabschlag:** Auf den Zielwert wird zusätzlich ein prozentualer Abschlag vorgenommen, um Schätzunsicherheiten abzufedern.
                        7. **Amortisationsdauer:** Rein rechnerische Kennzahl, die angibt, nach wie vielen Jahren die kumulierten (wachsenden) Gewinne je Aktie den heutigen Kaufpreis erreichen würden.

                        Alle Angaben beruhen auf historischen, öffentlich verfügbaren Daten und stellen keine Garantie oder Prognose der künftigen Kursentwicklung dar. Fehlende oder unvollständige Datenpunkte werden als "n. v." (nicht verfügbar) ausgewiesen.
                        """)

            except Exception:
                st.error(f"Für '{lt_query_to_run}' (gefundener Ticker: '{lt_resolved_ticker}') konnten nicht ausreichend Fundamentaldaten geladen werden. Bitte überprüfe die Eingabe.")

    st.markdown(
        """
        <div class="disclaimer-box" style="margin-top: 18px;">
            <strong>⚠️ Wichtiger Hinweis:</strong> Alle in diesem Bereich dargestellten Werte (Zielwert, Sicherheitsabschlag,
            Amortisationsdauer, Wachstumsraten) sind das Ergebnis einer automatisierten, vereinfachten Modellrechnung auf
            Basis historischer Daten. Sie dienen ausschließlich der eigenen Information und Bildung, stellen keine
            Anlageberatung oder Empfehlung zum Kauf oder Verkauf von Finanzinstrumenten dar und ersetzen keine eigene,
            umfassende Recherche bzw. die Beratung durch einen fachkundigen Anlageberater.
        </div>
        """,
        unsafe_allow_html=True,
    )

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
