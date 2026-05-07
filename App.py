import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🚀 Topp 10 Undervärderade Aktier")

# CEST-tid (UTC+2)
cest_time = datetime.now(ZoneInfo("Europe/Stockholm"))
st.write(f"Uppdaterad: {cest_time.strftime('%Y-%m-%d %H:%M')} CEST (uppdateras vid refresh)")

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
    return round(adx.iloc[-1], 1)

@st.cache_data(ttl=3600)
def fetch_data(tickers):
    data = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            hist = stock.history(period="3mo")
            adx_value = calculate_adx(hist)

            bolag_name = info.get("longName", t)
            yahoo_url = f"https://finance.yahoo.com/quote/{t}"

            row = {
                "Ticker": t,
                "Bolag": bolag_name,
                "Yahoo": yahoo_url,
                "Sektor": info.get("sector", "N/A"),
                "Pris": round(info.get("currentPrice") or info.get("previousClose"), 2),
                "Forward P/E": round(info.get("forwardPE"), 2) if info.get("forwardPE") is not None else None,
                "PEG": round(info.get("pegRatio"), 2) if info.get("pegRatio") is not None else None,
                "EV/EBITDA": round(info.get("enterpriseToEbitda"), 2) if info.get("enterpriseToEbitda") is not None else None,
                "ROE (%)": round(info.get("returnOnEquity") * 100, 1) if info.get("returnOnEquity") is not None else None,
                "D/E": round(info.get("debtToEquity"), 2) if info.get("debtToEquity") is not None else None,
                "FCF Yield (%)": round((info.get("freeCashflow", 0) / info.get("enterpriseValue", 1)) * 100, 2) 
                                 if info.get("enterpriseValue") and info.get("freeCashflow") else None,
                "ADX": adx_value,
                "Uppsida (%)": round((info.get("targetMeanPrice") / info.get("currentPrice") - 1) * 100, 1) 
                               if info.get("targetMeanPrice") and info.get("currentPrice") else None
            }
            data.append(row)
        except:
            continue
    return pd.DataFrame(data)

def style_adx(val):
    if pd.isna(val):
        return ''
    if val <= 20.9:
        return 'background-color: #ff4d4d; color: white; font-weight: bold'
    elif 21 <= val <= 30.9:
        return 'background-color: #ffcc00; color: black; font-weight: bold'
    elif 31 <= val <= 50:
        return 'background-color: #00cc66; color: white; font-weight: bold'
    return ''

# ====================== USA ======================
st.markdown("""
    <h3 style='margin-bottom: 0.3em;'>
        <img src="https://flagcdn.com/w40/us.png" width="36" style="vertical-align: middle; margin-right: 10px;">
        USA Top 10
    </h3>
""", unsafe_allow_html=True)

us_df = fetch_data(us_tickers)

if not us_df.empty:
    us_df["Score"] = 0.0
    for col, weight in [("EV/EBITDA", 1), ("PEG", 1), ("FCF Yield (%)", -1), ("ROE (%)", -1)]:
        if col in us_df.columns and us_df[col].notna().any():
            us_df["Score"] += us_df[col].rank(ascending=weight > 0, pct=True) * weight

    top_us = us_df.nsmallest(10, "Score").copy()
    styled_us = top_us.style.map(style_adx, subset=['ADX'])

    st.dataframe(
        styled_us,
        use_container_width=True,
        hide_index=True,
        column_order=["Ticker", "Bolag", "Yahoo", "Sektor", "Pris", "Forward P/E", "PEG", 
                     "EV/EBITDA", "ROE (%)", "D/E", "FCF Yield (%)", "ADX", "Uppsida (%)"],
        column_config={
            "Yahoo": st.column_config.LinkColumn(
                "Yahoo Finance", 
                help="Öppna aktiesidan",
                display_text="🔗 Öppna"
            ),
            "Pris": st.column_config.NumberColumn("Pris", format="%.2f"),
            "Forward P/E": st.column_config.NumberColumn("Forward P/E", format="%.2f"),
            "PEG": st.column_config.NumberColumn("PEG", format="%.2f"),
            "EV/EBITDA": st.column_config.NumberColumn("EV/EBITDA", format="%.2f"),
            "ROE (%)": st.column_config.NumberColumn("ROE (%)", format="%.1f"),
            "D/E": st.column_config.NumberColumn("D/E", format="%.2f"),
            "FCF Yield (%)": st.column_config.NumberColumn("FCF Yield (%)", format="%.2f"),
            "ADX": st.column_config.NumberColumn("ADX", format="%.1f"),
            "Uppsida (%)": st.column_config.NumberColumn("Uppsida (%)", format="%.1f"),
        }
    )

# ====================== EUROPA ======================
st.markdown("""
    <h3 style='margin-bottom: 0.3em;'>
        <img src="https://flagcdn.com/w40/eu.png" width="36" style="vertical-align: middle; margin-right: 10px;">
        Europa Top 10
    </h3>
""", unsafe_allow_html=True)

eu_df = fetch_data(eu_tickers)

if not eu_df.empty:
    eu_df["Score"] = 0.0
    for col, weight in [("EV/EBITDA", 1), ("PEG", 1), ("FCF Yield (%)", -1), ("ROE (%)", -1)]:
        if col in eu_df.columns and eu_df[col].notna().any():
            eu_df["Score"] += eu_df[col].rank(ascending=weight > 0, pct=True) * weight

    top_eu = eu_df.nsmallest(10, "Score").copy()
    styled_eu = top_eu.style.map(style_adx, subset=['ADX'])

    st.dataframe(
        styled_eu,
        use_container_width=True,
        hide_index=True,
        column_order=["Ticker", "Bolag", "Yahoo", "Sektor", "Pris", "Forward P/E", "PEG", 
                     "EV/EBITDA", "ROE (%)", "D/E", "FCF Yield (%)", "ADX", "Uppsida (%)"],
        column_config={
            "Yahoo": st.column_config.LinkColumn(
                "Yahoo Finance", 
                help="Öppna aktiesidan",
                display_text="🔗 Öppna"
            ),
            "Pris": st.column_config.NumberColumn("Pris", format="%.2f"),
            "Forward P/E": st.column_config.NumberColumn("Forward P/E", format="%.2f"),
            "PEG": st.column_config.NumberColumn("PEG", format="%.2f"),
            "EV/EBITDA": st.column_config.NumberColumn("EV/EBITDA", format="%.2f"),
            "ROE (%)": st.column_config.NumberColumn("ROE (%)", format="%.1f"),
            "D/E": st.column_config.NumberColumn("D/E", format="%.2f"),
            "FCF Yield (%)": st.column_config.NumberColumn("FCF Yield (%)", format="%.2f"),
            "ADX": st.column_config.NumberColumn("ADX", format="%.1f"),
            "Uppsida (%)": st.column_config.NumberColumn("Uppsida (%)", format="%.1f"),
        }
    )

# ====================== ADX-färgkodning ======================
st.markdown("**ADX-färgkodning:**", unsafe_allow_html=True)
st.markdown("""
<span style='color:#ff4d4d'>■</span> **0–20** Svag trend!  
<span style='color:#ffcc00'>■</span> **21–30** Börjande trend!  
<span style='color:#00cc66'>■</span> **31–50** Stark trend!
""", unsafe_allow_html=True)

with st.expander("📘 Förklaring av indikatorerna"):
    st.markdown("""
    - **Forward P/E, PEG, EV/EBITDA**: Ju lägre desto mer undervärderad.  
    - **ROE (%)**: Högre = bättre lönsamhet.  
    - **FCF Yield (%)**: Högre = mer fritt kassaflöde.  
    - **ADX**: Trendstyrka (färgkodad i tabellen).  
    - **Uppsida (%)**: Potentiell kursuppgång enligt analytiker.
    """)

st.caption("Klicka på 🔗 Öppna för att komma till Yahoo Finance • Data uppdateras vid refresh")

if st.button("🔄 Uppdatera data nu"):
    st.rerun()
