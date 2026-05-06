import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Value Dashboard - Top 10", layout="wide")
st.title("🚀 Automatisk Value Dashboard - Topp 10 Undervärderade Aktier")
st.write(f"Uppdaterad: {datetime.now().strftime('%Y-%m-%d %H:%M')} (uppdateras vid refresh)")

# === DINA KANDIDAT-AKTIER (utöka gärna själv) ===
us_tickers = ["ALL", "MU", "GEV", "RYAAY", "ACGL", "UHS", "T", "CINF", "ALV", "CTSH", 
              "JPM", "BAC", "LEN", "MOS", "PDD", "LRCX", "JPM"]  # lägg till fler

eu_tickers = ["SBC.MI", "OBCK.DE", "GENI.ST", "DNO.OL", "DEZ.DE", "DOM.ST", "ALV.ST", 
              "SAN.PA", "BSGR.AS", "HAYPP.ST", "COLO-B.CO", "CANATU.HE"]

@st.cache_data(ttl=3600)  # Cache 1 timme
def fetch_data(tickers):
    data = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            hist = stock.history(period="1y")
            
            row = {
                "Ticker": t,
                "Bolag": info.get("longName", t),
                "Sektor": info.get("sector", "N/A"),
                "Pris": round(info.get("currentPrice", info.get("previousClose", 0)), 2),
                "Forward P/E": info.get("forwardPE"),
                "PEG": info.get("pegRatio"),
                "EV/EBITDA": info.get("enterpriseToEbitda"),
                "ROE": info.get("returnOnEquity"),
                "D/E": info.get("debtToEquity"),
                "FCF Yield": round((info.get("freeCashflow", 0) / info.get("enterpriseValue", 1)) * 100, 2) if info.get("enterpriseValue") else None,
                "Marknadsvärde": info.get("marketCap"),
                "Uppsida": info.get("targetMeanPrice") / info.get("currentPrice") - 1 if info.get("targetMeanPrice") else None
            }
            data.append(row)
        except:
            pass
    return pd.DataFrame(data)

# Hämta data
st.subheader("🇺🇸 USA Top 10")
us_df = fetch_data(us_tickers)
if not us_df.empty:
    # Ranking: Poäng baserat på kriterier (ju lägre score desto bättre value + kvalitet)
    us_df["Score"] = 0
    if "EV/EBITDA" in us_df.columns:
        us_df["Score"] += us_df["EV/EBITDA"].rank(ascending=True, pct=True)
    if "PEG" in us_df.columns:
        us_df["Score"] += us_df["PEG"].rank(ascending=True, pct=True)
    if "ROE" in us_df.columns:
        us_df["Score"] -= us_df["ROE"].rank(ascending=True, pct=True)  # Hög ROE bra
    if "FCF Yield" in us_df.columns:
        us_df["Score"] += us_df["FCF Yield"].rank(ascending=False, pct=True)
    
    top_us = us_df.nsmallest(10, "Score").round(2)
    st.dataframe(top_us.drop(columns=["Score"]), use_container_width=True, hide_index=True)

st.subheader("🇪🇺 Europa Top 10")
eu_df = fetch_data(eu_tickers)
if not eu_df.empty:
    eu_df["Score"] = 0
    if "EV/EBITDA" in eu_df.columns:
        eu_df["Score"] += eu_df["EV/EBITDA"].rank(ascending=True, pct=True)
    if "PEG" in eu_df.columns:
        eu_df["Score"] += eu_df["PEG"].rank(ascending=True, pct=True)
    if "ROE" in eu_df.columns:
        eu_df["Score"] -= eu_df["ROE"].rank(ascending=True, pct=True)
    if "FCF Yield" in eu_df.columns:
        eu_df["Score"] += eu_df["FCF Yield"].rank(ascending=False, pct=True)
    
    top_eu = eu_df.nsmallest(10, "Score").round(2)
    st.dataframe(top_eu.drop(columns=["Score"]), use_container_width=True, hide_index=True)

st.caption("Kriterier: Låg EV/EBITDA + låg PEG + hög ROE + hög FCF-yield. Data från Yahoo Finance. Inga garantier – gör egen analys!")
st.button("🔄 Uppdatera data nu")
