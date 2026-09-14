import streamlit as st
import pandas as pd
import numpy as np

# Setze Seitenkonfiguration
st.set_page_config(
    page_title="Stan Weinstein Stock Screener",
    page_icon="📈",
    layout="wide"
)

# ---------------------------------------------------------
# MANSFIELD RS BERECHNUNG & STAGE LOGIK (KORRIGIERT)
# ---------------------------------------------------------
def calculate_mansfield_rs(stock_prices, benchmark_prices, period=52):
    """
    Berechnet die Mansfield Relative Stärke (MRS) im Vergleich zum Benchmark (z.B. S&P 500).
    Formula: MRS = ((Stock_Price / Benchmark_Price) / MA(Stock_Price / Benchmark_Price, period) - 1) * 100
    """
    relative_performance = stock_prices / benchmark_prices
    base_ma = relative_performance.rolling(window=period).mean()
    mansfield_rs = ((relative_performance / base_ma) - 1) * 100
    return mansfield_rs

def determine_stage(price, sma30, slope):
    """
    Klassifikation nach Stan Weinstein Stage Analysis:
    - Stage 1 (Bodenbildung): Kurs pendelt um den flachen 30W-SMA nach einem Abwärtstrend.
    - Stage 2 (Aufstiegsphase): Kurs liegt klar über dem 30W-SMA und die Steigung ist positiv (> 0.5%).
    - Stage 3 (Topbildung): Kurs pendelt um den abflachenden 30W-SMA nach einem langen Aufwärtstrend.
    - Stage 4 (Abstiegsphase): Kurs liegt klar unter dem 30W-SMA und die Steigung ist negativ (< -0.5%).
    """
    # Stage 2: Klarer Aufwärtstrend (Kurs > SMA und deutliche positive Steigung)
    if price > sma30 and slope > 0.5:
        return ("Stage 2 (Aufstiegsphase)", "background-color: rgba(40, 167, 69, 0.2); color: #2ecc71; border: 1px solid rgba(40, 167, 69, 0.5);")
    
    # Stage 4: Klarer Abwärtstrend (Kurs < SMA und deutliche negative Steigung)
    elif price < sma30 and slope < -0.5:
        return ("Stage 4 (Abstiegsphase)", "background-color: rgba(220, 53, 69, 0.2); color: #e74c3c; border: 1px solid rgba(220, 53, 69, 0.5);")
    
    # Stage 1 vs. Stage 3 (Konsolidierungs- / Übergangsphasen mit flachem/neutralem SMA):
    # Wenn die Steigung nahe 0 ist (-0.5% bis +0.5%):
    else:
        # Liegt der Kurs leicht über dem flachen/leicht fallenden SMA nach einem Abwärtstrend -> Stage 1 (Bodenbildung/Ausbruch)
        if price >= sma30:
            return ("Stage 1 (Bodenbildungsphase)", "background-color: rgba(108, 117, 125, 0.2); color: #95a5a6; border: 1px solid rgba(108, 117, 125, 0.5);")
        # Liegt der Kurs unter dem abflachenden SMA nach einer Hochphase -> Stage 3 / Übergang zu 4
        else:
            return ("Stage 3 (Topbildungsphase)", "background-color: rgba(255, 193, 7, 0.2); color: #f1c40f; border: 1px solid rgba(255, 193, 7, 0.5);")


# ---------------------------------------------------------
# ERWEITERTE HILFESEITE / GLOSSAR DIALOG
# ---------------------------------------------------------
@st.dialog("📖 Hilfeseite & Screening-Logik (Glossar)", width="large")
def show_glossary_dialog():
    st.markdown("## 📊 Regelwerk & Stage Analysis nach Stan Weinstein")
    st.write("Hier findest du die genaue Klassifizierung der 4 Marktphasen sowie unsere Screening-Filter:")

    st.markdown("---")

    st.markdown("### 🔄 1. Die 4 Marktphasen (Stan Weinstein Stage Analysis)")
    st.markdown("""
    Jede Aktie durchläuft kontinuierlich vier zyklische Phasen im Wochenchart bezogen auf den **30-Wochen-Durchschnitt (30W-SMA)**:

    * **🏛️ Stage 1 – Bodenbildungsphase (Base Area):**
      * **Kriterien:** Der Kurs pendelt nach einem längeren Abwärtstrend seitwärts um den abflachenden 30W-SMA. Der Kurs beginnt, den SMA wieder nach oben zu kreuzen, während die Steigung des SMA noch neutral oder leicht negativ ist (Steigung zwischen $-0,5\%$ und $+0,5\%$).
      * **Bedeutung:** Angebot und Nachfrage kommen ins Gleichgewicht. Institutionen bauen erste Positionen auf. Noch kein Kaufsignal für Momentum-Trader.

    * **🚀 Stage 2 – Aufstiegsphase (Uptrend / Breakout):**
      * **Kriterien:** Der Kurs bricht unter starkem Volumen über den Widerstand der Bodenbildung aus. Der Kurs notiert klar über dem 30W-SMA (`Kurs > 30W-SMA`) und der 30W-SMA steigt kraftvoll an (`Steigung (4W) > +0,5%`).
      * **Bedeutung:** Das optimale Kauf- und Haltedienst-Zeitfenster. Höchste Gewinnwahrscheinlichkeit für Long-Trades.

    * **⛰️ Stage 3 – Topbildungsphase (Top Area):**
      * **Kriterien:** Nach einem langen Aufwärtstrend verliert der Anstieg an Dynamik. Die Steigung des 30W-SMA flacht ab ($\le +0,5\%$). Der Kurs schwankt heftig um die geglättete Linie und fällt erstmals unter den 30W-SMA.
      * **Bedeutung:** Institutionen veräußern ihre Gewinne (Distribution). Erhöhte Volatilität. Gewinne sollten gesichert und Stopps nachgezogen werden.

    * **📉 Stage 4 – Abstiegsphase (Downtrend):**
      * **Kriterien:** Der Kurs notiert klar unter dem 30W-SMA (`Kurs < 30W-SMA`) und die Trendlinie fällt steil ab (`Steigung (4W) < -0,5%`).
      * **Bedeutung:** Finger weg! Auf keinen Fall nachkaufen ("Falle in ein fallendes Messer").
    """)

    st.markdown("---")

    st.markdown("### 🔍 2. Erstfilter: Wann erscheint eine Aktie in der Liste?")
    st.markdown("""
    * **1. Kurs über dem 30W-SMA (`Preis > 30W-SMA`):** Der aktuelle Schlusskurs liegt über dem einfachen gleitenden Durchschnitt der letzten 30 Wochen.
    * **2. Positiver Trend (`Steigung (4W) > 0.0%`):** Der 30-Wochen-Durchschnitt muss im Vergleich zu vor 4 Wochen ansteigen.
    """)

    st.markdown("---")

    st.markdown("### ⭐ 3. Wann wird eine Aktie zum ⭐ TOP KANDIDATEN?")
    st.markdown("""
    1. **Kurs über 30W-SMA:** Der Kurs notiert klar oberhalb der Trendlinie.
    2. **Starke Steigung (`> +0,5%`):** Die 4-Wochen-Steigung des 30W-SMA ist kraftvoll ausgerichtet.
    3. **Outperformance (`Mansfield RS > 0,0`):** Die Aktie entwickelt sich stärkere als der Gesamtmarkt (S&P 500).
    4. **Volumen-Bestätigung (`Volumen >= 120% des 10W-Schnitts`):** Das Handelsvolumen liegt mindestens 20% über dem Durchschnitt der letzten 10 Wochen.
    """)


# ---------------------------------------------------------
# HAUPT-ANWENDUNG (UI & ANALYSE)
# ---------------------------------------------------------
def main():
    st.title("📈 Stock Screener & Stage Analysis")
    
    # Header-Buttons
    col_title, col_btn = st.columns([4, 1])
    with col_btn:
        if st.button("📖 Hilfe & Glossar", use_container_width=True):
            show_glossary_dialog()

    # Beispieldaten für Demonstration
    sample_data = [
        {"Ticker": "DINO.WA", "Name": "Dino Polska", "Price": 385.0, "SMA30": 372.0, "Slope_4W": 0.2, "Mansfield_RS": 1.4, "Vol_Ratio": 1.15},
        {"Ticker": "NVDA", "Name": "NVIDIA Corp.", "Price": 128.5, "SMA30": 112.0, "Slope_4W": 1.8, "Mansfield_RS": 5.2, "Vol_Ratio": 1.45},
        {"Ticker": "UBER", "Name": "Uber Tech.", "Price": 74.2, "SMA30": 68.0, "Slope_4W": 0.9, "Mansfield_RS": 2.1, "Vol_Ratio": 1.25},
        {"Ticker": "INTC", "Name": "Intel Corp.", "Price": 20.1, "SMA30": 24.5, "Slope_4W": -1.2, "Mansfield_RS": -4.8, "Vol_Ratio": 0.85},
        {"Ticker": "XYZ", "Name": "Sample Top Shares", "Price": 48.0, "SMA30": 51.0, "Slope_4W": -0.1, "Mansfield_RS": -0.5, "Vol_Ratio": 0.95},
    ]

    df = pd.DataFrame(sample_data)

    # Berechne Phasen und Top-Kandidaten-Status
    stages = []
    styles = []
    top_candidates = []

    for idx, row in df.iterrows():
        stage_text, style_css = determine_stage(row["Price"], row["SMA30"], row["Slope_4W"])
        stages.append(stage_text)
        styles.append(style_css)

        # Prüfung Top-Kandidat
        is_top = (
            row["Price"] > row["SMA30"] and
            row["Slope_4W"] > 0.5 and
            row["Mansfield_RS"] > 0.0 and
            row["Vol_Ratio"] >= 1.2
        )
        top_candidates.append("⭐ Top-Kandidat" if is_top else "Standard")

    df["Weinstein Stage"] = stages
    df["Status"] = top_candidates

    # Filter-Optionen in der Sidebar
    st.sidebar.header("🔍 Filter Einstellungen")
    selected_stage = st.sidebar.multiselect(
        "Phase auswählen:",
        options=["Stage 1 (Bodenbildungsphase)", "Stage 2 (Aufstiegsphase)", "Stage 3 (Topbildungsphase)", "Stage 4 (Abstiegsphase)"],
        default=["Stage 1 (Bodenbildungsphase)", "Stage 2 (Aufstiegsphase)"]
    )

    only_top = st.sidebar.checkbox("Nur ⭐ Top-Kandidaten anzeigen")

    # Filter anwenden
    filtered_df = df[df["Weinstein Stage"].isin(selected_stage)]
    if only_top:
        filtered_df = filtered_df[filtered_df["Status"] == "⭐ Top-Kandidat"]

    # Anzeige der Daten
    st.subheader("📋 Analyse-Ergebnisse")
    
    st.dataframe(
        filtered_df[[
            "Ticker", "Name", "Price", "SMA30", "Slope_4W", 
            "Mansfield_RS", "Vol_Ratio", "Weinstein Stage", "Status"
        ]],
        use_container_width=True
    )

if __name__ == "__main__":
    main()
