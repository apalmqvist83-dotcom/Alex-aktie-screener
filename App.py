import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🚀 Automatisk Value Dashboard - Topp 10 Undervärderade Aktier")
st.write(f"Uppdaterad: {datetime.now().strftime('%Y-%m-%d %H:%M')} (uppdateras vid refresh)")

# === TICKERS (utöka gärna själv) ===
us_tickers = ["ALL", "MU", "GEV", "RYAAY", "ACGL", "UHS", "T", "CINF", "ALV", "CTSH", "JPM", "BAC", "LEN", "MOS", "PDD"]
eu_tickers = ["SAN.PA", "DNO.OL", "DOM.ST", "ALV.ST", "RYAAY", "SBC.MI", "DEZ.DE", "BSGR.AS", "COLO-B.CO", "HAYPP.ST"]

def calculate_adx(hist, period=14):
    """Enkel manuell ADX-beräkning utan extra paket"""
    if len(hist) < period * 2:
        return None
    high = hist['High']
    low = hist['Low']
    close = hist['Close']
    
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Directional Movement
    plus_dm = high - high.shift(1)
    minus_dm = low.shift(1) - low
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    # Smoothed values (Wilder's method)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
    
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    return round(adx.iloc[-1], 1)

@st.cache_data(ttl=3600)
def fetch_data(tickers):
    data = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            hist = stock.history(period="3mo")
            
            adx_value = calculate_adx(hist) if not hist.empty else None

            row = {
                "Ticker": t,
                "Bolag": info.get("longName", t),
                "Sektor": info.get("sector", "N/A"),
                "Pris": round(info.get("currentPrice", info.get("previousClose", 0)), 2),
                "Forward P/E": round(info.get("forwardPE"), 2) if info.get("forwardPE") else None,
                "PEG": round(info.get("pegRatio"), 2) if info.get("pegRatio") else None,
                "EV/EBITDA": round(info.get("enterpriseToEbitda"), 2) if info.get("enterpriseToEbitda") else None,
                "ROE (%)": round(info.get("returnOnEquity") * 100, 1) if info.get("returnOnEquity") else None,
                "D/E": round(info.get("debtToEquity"), 2) if info.get("debtToEquity") else None,
                "FCF Yield (%)": round((info.get("freeCashflow", 0) / info.get("enterpriseValue", 1)) * 100, 2) if info.get("enterpriseValue") and info.get("freeCashflow") else None,
                "ADX": adx_value,
                "Uppsida (%)": round((info.get("targetMeanPrice") / info.get("currentPrice") - 1) * 100, 1) if info.get("targetMeanPrice") and info.get("currentPrice") else None
            }
            data.append(row)
        except:
            continue
    return pd.DataFrame(data)

# ====================== USA ======================
st.subheader("🇺🇸 USA Top 10")
us_df = fetch_data(us_tickers)

if not us_df.empty:
    us_df["Score"] = 0.0
    for col, weight in [("EV/EBITDA", 1), ("PEG", 1), ("FCF Yield (%)", -1), ("ROE (%)", -1)]:
        if col in us_df.columns:
            us_df["Score"] += us_df[col].rank(ascending=True if weight > 0 else False, pct=True) * weight
    
    top_us = us_df.nsmallest(10, "Score").round(2).copy()
    top_us["Bolag"] = top_us.apply(lambda x: f'<a href="https://finance.yahoo.com/quote/{x["Ticker"]}" target="_blank">{x["Bolag"]}</a>', axis=1)
    
    st.dataframe(
        top_us.drop(columns=["Score", "Ticker"]),
        use_container_width=True,
        hide_index=True,
        column_config={"Bolag": st.column_config.TextColumn("Bolag")}
    )

# ====================== EUROPA ======================
st.subheader("🇪🇺 Europa Top 10")
eu_df = fetch_data(eu_tickers)

if not eu_df.empty:
    eu_df["Score"] = 0.0
    for col, weight in [("EV/EBITDA", 1), ("PEG", 1), ("FCF Yield (%)", -1), ("ROE (%)", -1)]:
        if col in eu_df.columns:
            eu_df["Score"] += eu_df[col].rank(ascending=True if weight > 0 else False, pct=True) * weight
    
    top_eu = eu_df.nsmallest(10, "Score").round(2).copy()
    top_eu["Bolag"] = top_eu.apply(lambda x: f'<a href="https://finance.yahoo.com/quote/{x["Ticker"]}" target="_blank">{x["Bolag"]}</a>', axis=1)
    
    st.dataframe(
        top_eu.drop(columns=["Score", "Ticker"]),
        use_container_width=True,
        hide_index=True,
        column_config={"Bolag": st.column_config.TextColumn("Bolag")}
    )

# ADX-färgkodning
st.markdown("""
**ADX-färgkodning:**  
<span style='color:red'>0–20</span>: Svag trend (röd) | 
<span style='color:orange'>25–30</span>: Börjande trend (gul) | 
<span style='color:green'>50–100</span>: Stark trend (grön)
""", unsafe_allow_html=True)

# Förklaringar
with st.expander("📘 Förklaring av indikatorerna"):
    st.markdown("""
    - **Forward P/E**: Förväntat pris/vinst. Lägre = billigare.  
    - **PEG**: Tar hänsyn till tillväxt. **<1** = undervärderad med tillväxt.  
    - **EV/EBITDA**: Bra värderingsmått. Lägre värde = mer prisvärd.  
    - **ROE (%)**: Hur bra bolaget använder eget kapital. Högre = bättre.  
    - **D/E**: Skuldsättning. Lägre = stabilare.  
    - **FCF Yield (%)**: Fritt kassaflöde i procent. Högre = mer kontanter.  
    - **ADX**: Trendstyrka (0–100).  
    - **Uppsida (%)**: Analytikernas genomsnittliga kursmål.
    """)

st.caption("Data från Yahoo Finance • Gör alltid egen analys • Uppdateras vid varje sidvisning")
if st.button("🔄 Uppdatera data nu"):
    st.rerun()
