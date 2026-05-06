import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🚀 Automatisk Value Dashboard - Topp 10 Undervärderade Aktier")
st.write(f"Uppdaterad: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Tickers
us_tickers = ["ALL", "MU", "RYAAY", "ACGL", "UHS"]
eu_tickers = ["SAN.PA", "ALV.ST", "DOM.ST"]

@st.cache_data(ttl=600)
def fetch_data(tickers):
    data = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            row = {
                "Ticker": t,
                "Bolag": info.get("longName", t),
                "Pris": round(info.get("currentPrice", 0), 2),
                "Forward P/E": round(info.get("forwardPE"), 2) if info.get("forwardPE") else None,
                "EV/EBITDA": round(info.get("enterpriseToEbitda"), 2) if info.get("enterpriseToEbitda") else None,
                "ROE (%)": round(info.get("returnOnEquity")*100, 2) if info.get("returnOnEquity") else None,
            }
            data.append(row)
        except Exception as e:
            st.error(f"Fel på {t}: {str(e)[:100]}")
    return pd.DataFrame(data)

st.subheader("🇺🇸 USA Top 10")
us_df = fetch_data(us_tickers)
if not us_df.empty:
    st.dataframe(us_df, use_container_width=True, hide_index=True)
else:
    st.warning("Ingen data laddades för USA")

st.subheader("🇪🇺 Europa Top 10")
eu_df = fetch_data(eu_tickers)
if not eu_df.empty:
    st.dataframe(eu_df, use_container_width=True, hide_index=True)
else:
    st.warning("Ingen data laddades för Europa")

st.caption("Om du ser varningar ovan → yfinance har problem. Försök uppdatera sidan.")
if st.button("🔄 Uppdatera data nu"):
    st.rerun()
