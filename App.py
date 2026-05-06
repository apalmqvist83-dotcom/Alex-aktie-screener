import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🚀 Automatisk Value Dashboard - Topp 10 Undervärderade Aktier")
st.write(f"Uppdaterad: {datetime.now().strftime('%Y-%m-%d %H:%M')} (uppdateras vid refresh)")

# === TICKERS ===
us_tickers = ["ALL", "MU", "GEV", "RYAAY", "ACGL", "UHS", "T", "CINF", "ALV", "CTSH", "JPM", "BAC", "LEN", "MOS", "PDD"]
eu_tickers = ["SAN.PA", "DNO.OL", "DOM.ST", "ALV.ST", "RYAAY", "SBC.MI", "DEZ.DE", "BSGR.AS", "COLO-B.CO", "HAYPP.ST"]

def calculate_adx(hist, period=14):
    if len(hist) < period * 2 or hist.empty:
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
    return round(adx.iloc[-1], 2)

@st.cache_data(ttl=3600)
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
                "Forward P/E": round(info.get("forwardPE"), 2) if info.get("forwardPE") is not None else None,
                "PEG": round(info.get("pegRatio"), 2) if info.get("pegRatio") is not None else None,
                "EV/EBITDA": round(info.get("enterpriseToEbitda"), 2) if info.get("enterpriseToEbitda") is not None else None,
                "ROE (%)": round(info.get("returnOnEquity") * 100, 2) if info.get("returnOnEquity") is not None else None,
                "D/E": round(info.get("debtToEquity"), 2) if info.get("debtToEquity") is not None else None,
                "FCF Yield (%)": round((info.get("freeCashflow", 0) / info.get("enterpriseValue", 1)) * 100, 2) 
                                 if info.get("enterpriseValue") and info.get("freeCashflow") else None,
                "ADX": adx_value,
                "Uppsida (%)": round((info.get("targetMeanPrice") / info.get("currentPrice", 1) - 1) *
