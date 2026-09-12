import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Seitenkonfiguration
st.set_page_config(page_title="Aktien & Index Stage Analysis", layout="centered")

st.title("USA (S&P 500)")
st.caption("State Street SPDR S&P 500 ETF Trust / Index")

# Sidebar - Symbol Auswahl
ticker_symbol = st.sidebar.text_input("Ticker Symbol", value="SPY")
period = st.sidebar.selectbox("Zeitraum", options=["1y", "2y", "5y", "max"], index=1)

# Daten abrufen & bereinigen
@st.cache_data
def load_data(ticker, period_val):
    data = yf.download(ticker, period=period_val, interval="1wk")
    # Falls yfinance MultiIndex-Spalten zurückgibt, vereinfachen wir diese
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

df = load_data(ticker_symbol, period)

if not df.empty and 'Close' in df.columns:
    # 30-Wochen SMA berechnen
    df['30W_SMA'] = df['Close'].rolling(window=30).mean()
    
    # Skalarwerte aus den Serien extrahieren
    latest_close = float(df['Close'].dropna().iloc[-1])
    
    sma_series = df['30W_SMA'].dropna()
    latest_sma = float(sma_series.iloc[-1]) if not sma_series.empty else latest_close
    
    # 4-Wochen Steigung des SMA
    if len(sma_series) >= 5:
        sma_4w_ago = float(sma_series.iloc[-5])
        sma_slope_4w = ((latest_sma - sma_4w_ago) / sma_4w_ago) * 100
    else:
        sma_slope_4w = 0.0

    # Status-Bestimmung (Stan Weinstein Stage Analysis)
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
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Kurs", value=f"{latest_close:.2f} USD")
    col2.metric(label="30W-SMA", value=f"{latest_sma:.2f} USD")
    col3.metric(label="Steigung (4W)", value=f"{sma_slope_4w:+.2f}%")

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

    # Layout & Design
    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20),
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            showgrid=True,
            gridcolor='#222831',
            zeroline=False
        )
    )

    # Sichere Konfiguration der Y-Achse (Zentriert automatisch eng am Kursverlauf)
    fig.update_yaxes(
        title_text="Preis (USD)",
        autorange=True,
        zeroline=False,
        showgrid=True,
        gridcolor='#222831'
    )

    # Chart anzeigen
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Fehler beim Laden der Kursdaten. Bitte Ticker prüfen.")
