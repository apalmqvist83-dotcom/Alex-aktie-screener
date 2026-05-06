import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🚀 Automatisk Value Dashboard - Topp 10 Undervärderade Aktier")
st.write(f"Uppdaterad: {datetime.now().strftime('%Y-%m-%d %H:%M')} (uppdateras vid refresh)")

# === TICKERS ===
us_tickers = ["ALL", "MU", "RYAAY", "ACGL", "UHS", "T", "JPM", "BAC", "MOS", "PDD"]
eu_tickers = ["SAN.PA", "ALV.ST", "DOM.ST", "DNO.OL", "RYAAY", "BSGR.AS"]

def calculate_adx(hist, period=14):
    if hist.empty or len(hist) < 30:
        return None
    high = hist['High']
    low = hist['Low']
    close = hist['Close']
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    plus_dm = high - high.shift(1)
    minus_dm = low.shift(1) - low
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
    
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    return round(adx.iloc[-1], 1)

@st.cache_data(ttl=1800)
def fetch_data(tickers):
    data = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            hist = stock.history(period="3mo")
            adx_value = calculate_adx(hist)

            row = {
                "Ticker": t,
                "Bolag": info.get("longName", t),
                "Sektor": info.get("sector", "N/A"),
                "Pris": round(info.get("currentPrice", info.get("previousClose", 0)), 2),
                "Forward P/E": round(info.get("forwardPE"), 2) if info.get("forwardPE") else None,
                "PEG": round(info.get("pegRatio"), 2) if info.get("pegRatio") else None,
                "EV/EBITDA": round(info.get("enterpriseToEbitda"), 2) if info.get("enterpriseToEbitda") else None,
                "ROE (%)": round(info.get("returnOnEquity")*100, 2) if info.get("returnOnEquity") else None,
                "D/E": round(info.get("debtToEquity"), 2) if info.get("debtToEquity") else None,
                "FCF Yield (%)": round((info.get("freeCash
