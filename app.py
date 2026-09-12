import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="Aktien & Index Stage Analysis", layout="centered")

st.title("USA (S&P 500)")
st.caption("State Street SPDR S&P 500 ETF Trust / Index")

# Sidebar - Symbol Auswahl
ticker_symbol = st.sidebar.text_input("Ticker Symbol", value="SPY")
period = st.sidebar.selectbox("Zeitraum", options=["1y", "2y", "5y", "max"], index=1)

# Daten abrufen
@st.cache_data
def load_data(ticker, period_val):
    data = yf.download(ticker, period=period_val, interval="1wk")
    return data

df = load_data(ticker_symbol, period)

if not df.empty:
    # Berechnungen
    # 30-Wochen SMA
    df['30W_SMA'] = df['Close'].rolling(window=30).mean()
    
    # Letzte Werte extrahieren
    latest_close = float(df['Close'].iloc[-1])
    latest_sma = float(df['30W_SMA'].iloc[-1])
    
    # 4-Wochen Steigung des SMA
    if len(df['30W_SMA']) >= 5:
        sma_4w_ago = float(df['30W_SMA'].iloc[-5])
        sma_slope_4w = ((latest_sma - sma_4w_ago) / sma_4w_ago) * 100
    else:
        sma_slope_4w = 0.0

    # Status-Bestimmung (Stage)
    if latest_close > latest_sma and sma_slope_4w > 0:
        stage_status = "Stage 2 (Aufwärtstrend)"
        badge_color = "green"
    elif latest_close < latest_sma and sma_slope_4w < 0:
        stage_status = "Stage 4 (Abwärtstrend)"
        badge_color = "red"
    else:
        stage_status = "Stage 1 / 3 (Konsolidierung)"
        badge_color = "orange"

    # Status Badges
    st.markdown(f"**Status:** :{badge_color}[{stage_status}]  |  🔴 **Börse Geschlossen**")

    # Kennzahlen
    st.metric(label="Kurs", value=f"{latest_close:.2f} USD")
    st.metric(label="30W-SMA", value=f"{latest_sma:.2f} USD")
    st.metric(label="Steigung (4W)", value=f"{sma_slope_4w:+.2f}%")

    # -------------------------------------------------------------
    # Dynamische Y-Achsen Skalierung für mittige Darstellung
    # -------------------------------------------------------------
    # Alle relevanten Min/Max Preiswerte im Zeitraum ermitteln
    min_price = float(df['Close'].min())
    max_price = float(df['Close'].max())
    
    # Sicherheitsabstand (Padding) von 5% oben und unten hinzufügen
    padding = (max_price - min_price) * 0.08 if max_price != min_price else min_price * 0.1
    y_min = min_price - padding
    y_max = max_price + padding

    # Plotly Chart erstellen
    fig = go.Figure()

    # Kursverlauf (blaue Linie)
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        mode='lines',
        name='Preis (USD)',
        line=dict(color='#29b6f6', width=2)
    ))

    # 30W-SMA (gelbe gestrichelte Linie)
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['30W_SMA'],
        mode='lines',
        name='30W-SMA',
        line=dict(color='#fbc02d', width=2, dash='dash')
    ))

    # Layout & Achsen-Optimierung
    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20),
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            showgrid=True,
            gridcolor='#222831',
            zeroline=False
        ),
        yaxis=dict(
            title="Preis (USD)",
            range=[y_min, y_max],  # Zentriert den Kursverlauf perfekt
            zeroline=False,         # Verhindert Fixierung bei 0
            showgrid=True,
            gridcolor='#222831'
        )
    )

    # Chart in Streamlit anzeigen
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Fehler beim Laden der Kursdaten. Bitte Ticker prüfen.")
