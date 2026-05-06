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
                "FCF Yield (%)": round((info.get("freeCashflow",0) / info.get("enterpriseValue",1))*100, 2) if info.get("enterpriseValue") else None,
                "ADX": adx_value,
                "Uppsida (%)": round((info.get("targetMeanPrice") / info.get("currentPrice") -1)*100, 2) if info.get("targetMeanPrice") else None
            }
            data.append(row)
        except:
            continue
    return pd.DataFrame(data)

def style_adx(val):
    if pd.isna(val):
        return ''
    if val <= 20:
        return 'background-color: #ff4d4d; color: white; font-weight: bold'
    elif 25 <= val <= 30:
        return 'background-color: #ffcc00; color: black; font-weight: bold'
    elif val >= 50:
        return 'background-color: #00cc66; color: white; font-weight: bold'
    return ''

# ====================== USA ======================
st.subheader("🇺🇸 USA Top 10")
us_df = fetch_data(us_tickers)

if not us_df.empty:
    us_df["Score"] = 0.0
    for col, weight in [("EV/EBITDA", 1), ("PEG", 1), ("FCF Yield (%)", -1), ("ROE (%)", -1)]:
        if col in us_df.columns and us_df[col].notna().any():
            us_df["Score"] += us_df[col].rank(ascending=weight > 0, pct=True) * weight

    top_us = us_df.nsmallest(10, "Score").round(2).copy()
    top_us["Länk"] = top_us["Ticker"].apply(lambda x: f'<a href="https://finance.yahoo.com/quote/{x}" target="_blank">🔗 Yahoo</a>')
    
    styled_us = top_us.style.map(style_adx, subset=['ADX'])
    
    st.dataframe(
        styled_us,
        use_container_width=True,
        hide_index=True,
        column_config={"Länk": st.column_config.TextColumn("Länk")}
    )
else:
    st.warning("Ingen data för USA just nu.")

# ====================== EUROPA ======================
st.subheader("🇪🇺 Europa Top 10")
eu_df = fetch_data(eu_tickers)

if not eu_df.empty:
