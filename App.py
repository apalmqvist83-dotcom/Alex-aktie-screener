import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime

st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🚀 Automatisk Value Dashboard - Topp 10 Undervärderade Aktier")
st.write(f"Uppdaterad: {datetime.now().strftime('%Y-%m-%d %H:%M')} (uppdateras vid refresh)")

# === TICKERS (utöka gärna) ===
us_tickers = ["ALL", "MU", "GEV", "RYAAY", "ACGL", "UHS", "T", "CINF", "ALV", "CTSH", "JPM", "BAC", "LEN", "MOS", "PDD"]
eu_tickers = ["SAN.PA", "DNO.OL", "DOM.ST", "ALV.ST", "RYAAY", "SBC.MI", "DEZ.DE", "BSGR.AS", "COLO-B.CO", "HAYPP.ST"]

@st.cache_data(ttl=3600)
def fetch_data(tickers):
    data = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            hist = stock.history(period="3mo")  # Behövs för ADX
            
            # Beräkna ADX
            if not hist.empty:
                hist['ADX'] = ta.adx(high=hist['High'], low=hist['Low'], close=hist['Close'], length=14)['ADX_14']
                adx_latest = round(hist['ADX'].iloc[-1], 1) if not hist['ADX'].isna().all() else None
            else:
                adx_latest = None

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
                "FCF Yield (%)": round((info.get("freeCashflow", 0) / info.get("enterpriseValue", 1)) * 100, 2) if info.get("enterpriseValue") else None,
                "ADX": adx_latest,
                "Uppsida (%)": round((info.get("targetMeanPrice") / info.get("currentPrice") - 1) * 100, 1) if info.get("targetMeanPrice") else None
            }
            data.append(row)
        except:
            continue
    return pd.DataFrame(data)

# ====================== USA ======================
st.subheader("🇺🇸 USA Top 10")
us_df = fetch_data(us_tickers)

if not us_df.empty:
    # Ranking
    us_df["Score"] = 0
    for col, weight in [("EV/EBITDA", 1), ("PEG", 1), ("FCF Yield (%)", -1), ("ROE (%)", -1)]:
        if col in us_df.columns:
            us_df["Score"] += us_df[col].rank(ascending=True if "Yield" not in col and "ROE" not in col else False, pct=True) * weight
    
    top_us = us_df.nsmallest(10, "Score").round(2).copy()
    
    # Lägg till klickbar länk
    top_us["Bolag"] = top_us.apply(lambda x: f'<a href="https://finance.yahoo.com/quote/{x["Ticker"]}" target="_blank">{x["Bolag"]}</a>', axis=1)
    
    # Visa med styling
    st.dataframe(
        top_us.drop(columns=["Score", "Ticker"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Bolag": st.column_config.TextColumn("Bolag", help="Klicka för Yahoo Finance"),
            "ADX": st.column_config.NumberColumn("ADX", help="Trendstyrka")
        }
    )

# ====================== EUROPA ======================
st.subheader("🇪🇺 Europa Top 10")
eu_df = fetch_data(eu_tickers)

if not eu_df.empty:
    eu_df["Score"] = 0
    for col, weight in [("EV/EBITDA", 1), ("PEG", 1), ("FCF Yield (%)", -1), ("ROE (%)", -1)]:
        if col in eu_df.columns:
            eu_df["Score"] += eu_df[col].rank(ascending=True if "Yield" not in col and "ROE" not in col else False, pct=True) * weight
    
    top_eu = eu_df.nsmallest(10, "Score").round(2).copy()
    top_eu["Bolag"] = top_eu.apply(lambda x: f'<a href="https://finance.yahoo.com/quote/{x["Ticker"]}" target="_blank">{x["Bolag"]}</a>', axis=1)
    
    st.dataframe(
        top_eu.drop(columns=["Score", "Ticker"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Bolag": st.column_config.TextColumn("Bolag", help="Klicka för Yahoo Finance"),
            "ADX": st.column_config.NumberColumn("ADX", help="Trendstyrka")
        }
    )

# ====================== FÄRGKODNING ADX ======================
st.markdown("""
**ADX-färgkodning:**
- <span style='color:red'>0–20</span>: Svag trend / ingen klar riktning (röd)
- <span style='color:orange'>25–30</span>: Börjande trend (gul)
- <span style='color:green'>50–100</span>: Stark trend (grön)
""", unsafe_allow_html=True)

# ====================== FÖRKLARINGAR ======================
with st.expander("📘 Förklaring av indikatorerna"):
    st.markdown("""
    - **Forward P/E**: Förväntat pris/vinst-tal. Lägre = billigare.
    - **PEG**: P/E dividerat med förväntad tillväxt. **< 1** = undervärderad med tillväxt.
    - **EV/EBITDA**: Företagsvärde i förhållande till rörelseresultat. **< 8–10** ses ofta som attraktivt.
    - **ROE (%)**: Avkastning på eget kapital. Högre = bättre lönsamhet.
    - **D/E**: Skuldsättningsgrad. Lägre = stabilare bolag.
    - **FCF Yield (%)**: Fritt kassaflöde i % av företagsvärdet. Högre = mer kontanter till ägarna.
    - **ADX**: Trendstyrka (0–100). Används för att se om aktien har momentum.
    - **Uppsida (%)**: Analytikernas genomsnittliga kursmål vs nuvarande pris.
    """)

st.caption("Data från Yahoo Finance • Inga garantier • Gör alltid egen analys • Uppdateras vid varje sidvisning")
st.button("🔄 Uppdatera data nu")
