import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="Value Dashboard", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# ====================== MODERN MIDNATTBLÅ THEME ======================
st.markdown("""
<style>
    /* Huvudbakgrund - Midnattsblå */
    .stApp {
        background-color: #1A202C !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161D2A !important;
    }

    /* Kort och sektioner */
    .stMarkdown, .stDataFrame, .stExpander, div[data-testid="stExpander"] {
        background-color: #1E293B !important;
        border-radius: 12px;
        border: 1px solid #334155;
    }

    /* Tabell */
    .stDataFrame {
        background-color: #1E293B !important;
    }

    /* Textfärger */
    h1, h2, h3, h4, p, label, .stMarkdown, div {
        color: #E2E8F0 !important;
    }
    h1 {
        color: #F1F5F9 !important;
    }

    /* Länkar */
    a {
        color: #60A5FA !important;
    }

    /* Knappar */
    button {
        background-color: #334155 !important;
        color: #E2E8F0 !important;
        border: none !important;
        border-radius: 8px;
    }
    button:hover {
        background-color: #475569 !important;
        color: white !important;
    }

    /* Expander */
    .stExpanderHeader {
        background-color: #25334A !important;
    }

    /* Förbättrad tabellstil */
    .dataframe th {
        background-color: #25334A !important;
        color: #E2E8F0 !important;
    }
    .dataframe td {
        background-color: #1E293B !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Topp 10 Undervärderade Aktier")

cest_time = datetime.now(ZoneInfo("Europe/Stockholm"))
st.write(f"Uppdaterad: {cest_time.strftime('%Y-%m-%d %H:%M')} CEST")

# ====================== CANDIDATE POOLS ======================
us_candidates = ["ALL", "MU", "GEV", "RYAAY", "ACGL", "UHS", "T", "CINF", "ALV", "CTSH", 
                 "JPM", "BAC", "LEN", "MOS", "PDD", "CSCO", "GS", "MS", "BK", "USB"]

eu_candidates = [
    "SAN.PA", "DNO.OL", "DOM.ST", "ALIV-SDB.ST", "RYAAY", "SBC.MI", "DEZ.DE", 
    "COLO-B.CO", "HAYPP.ST", "VOLV-B.ST", "NOKIA.HE", "NOVO-B.CO", "EQNR.OL",
    "OR.PA", "MC.PA", "ASML.AS", "RMS.PA", "KNEBV.HE", "SAND.ST", "TEL.OL"
]

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
def fetch_data(candidates, n=10):
    data = []
    for t in candidates:
        if len(data) >= n:
            break
        try:
            stock = yf.Ticker(t)
            info = stock.info
            hist = stock.history(period="3mo")
            adx_value = calculate_adx(hist)

            if info is None or len(hist) < 20 or not info.get("currentPrice"):
                continue

            currency = info.get("currency", "USD").upper()
            price = info.get("currentPrice") or info.get("previousClose") or 0

            row = {
                "Ticker": t,
                "Bolag": info.get("longName", t)[:35],
                "Yahoo": f"https://finance.yahoo.com/quote/{t}",
                "Sektor": info.get("sector", "N/A"),
                "Pris": round(price, 2),
                "Valuta": currency,
                "Forward P/E": round(info.get("forwardPE"), 2) if info.get("forwardPE") is not None else None,
                "PEG": round(info.get("pegRatio"), 2) if info.get("pegRatio") is not None else None,
                "EV/EBITDA": round(info.get("enterpriseToEbitda"), 2) if info.get("enterpriseToEbitda") is not None else None,
                "ROE (%)": round(info.get("returnOnEquity") * 100, 1) if info.get("returnOnEquity") is not None else None,
                "D/E": round(info.get("debtToEquity"), 2) if info.get("debtToEquity") is not None else None,
                "FCF Yield (%)": round((info.get("freeCashflow", 0) / info.get("enterpriseValue", 1)) * 100, 2) 
                                 if info.get("enterpriseValue") and info.get("freeCashflow") else None,
                "ADX": adx_value,
                "Uppsida (%)": round((info.get("targetMeanPrice") / price - 1) * 100, 1) 
                               if info.get("targetMeanPrice") and price else None
            }
            data.append(row)
        except:
            continue
    return pd.DataFrame(data)

def style_adx(val):
    if pd.isna(val):
        return ''
    if val <= 20.9: return 'background-color: #ff4d4d; color: white; font-weight: bold'
    elif 21 <= val <= 30.9: return 'background-color: #ffcc00; color: black; font-weight: bold'
    elif 31 <= val <= 50: return 'background-color: #00cc66; color: white; font-weight: bold'
    return ''

# ====================== KOLUMN KONFIG ======================
column_config = {
    "Yahoo": st.column_config.LinkColumn(" ", display_text="🔗", width=50),
    "Ticker": st.column_config.TextColumn("Ticker", width=70),
    "Bolag": st.column_config.TextColumn("Bolag", width=190),
    "Sektor": st.column_config.TextColumn("Sektor", width=110),
    "Pris": st.column_config.NumberColumn("Pris", format="%.2f", width=90),
    "Valuta": st.column_config.TextColumn("Val", width=55),
    "Forward P/E": st.column_config.NumberColumn("F P/E", format="%.2f", width=80),
    "PEG": st.column_config.NumberColumn("PEG", format="%.2f", width=70),
    "EV/EBITDA": st.column_config.NumberColumn("EV/EB", format="%.2f", width=95),
    "ROE (%)": st.column_config.NumberColumn("ROE %", format="%.1f", width=75),
    "D/E": st.column_config.NumberColumn("D/E", format="%.2f", width=65),
    "FCF Yield (%)": st.column_config.NumberColumn("FCF %", format="%.2f", width=95),
    "ADX": st.column_config.NumberColumn("ADX", format="%.1f", width=65),
    "Uppsida (%)": st.column_config.NumberColumn("Uppsida %", format="%.1f", width=90),
}

# ====================== USA ======================
st.markdown('<h3><img src="https://flagcdn.com/w40/us.png" width="34" style="vertical-align:middle;margin-right:8px;">USA Top 10</h3>', unsafe_allow_html=True)
us_df = fetch_data(us_candidates, n=10)

if not us_df.empty:
    us_df = us_df.copy()
    us_df["Score"] = 0.0
    for col, weight in [("EV/EBITDA", 1), ("PEG", 1), ("FCF Yield (%)", -1), ("ROE (%)", -1)]:
        if col in us_df.columns and us_df[col].notna().any():
            us_df["Score"] += us_df[col].rank(ascending=weight > 0, pct=True) * weight

    top_us = us_df.nsmallest(10, "Score").copy()
    styled_us = top_us.style.map(style_adx, subset=['ADX'])

    st.dataframe(styled_us, use_container_width=True, hide_index=True,
                 column_order=["Ticker", "Bolag", "Yahoo", "Sektor", "Pris", "Valuta", "Forward P/E", "PEG", 
                              "EV/EBITDA", "ROE (%)", "D/E", "FCF Yield (%)", "ADX", "Uppsida (%)"],
                 column_config=column_config,
                 height=340)

# ====================== EUROPA ======================
st.markdown('<h3><img src="https://flagcdn.com/w40/eu.png" width="34" style="vertical-align:middle;margin-right:8px;">Europa Top 10</h3>', unsafe_allow_html=True)
eu_df = fetch_data(eu_candidates, n=10)

if not eu_df.empty:
    eu_df = eu_df.copy()
    eu_df["Score"] = 0.0
    for col, weight in [("EV/EBITDA", 1), ("PEG", 1), ("FCF Yield (%)", -1), ("ROE (%)", -1)]:
        if col in eu_df.columns and eu_df[col].notna().any():
            eu_df["Score"] += eu_df[col].rank(ascending=weight > 0, pct=True) * weight

    top_eu = eu_df.nsmallest(10, "Score").copy()
    styled_eu = top_eu.style.map(style_adx, subset=['ADX'])

    st.dataframe(styled_eu, use_container_width=True, hide_index=True,
                 column_order=["Ticker", "Bolag", "Yahoo", "Sektor", "Pris", "Valuta", "Forward P/E", "PEG", 
                              "EV/EBITDA", "ROE (%)", "D/E", "FCF Yield (%)", "ADX", "Uppsida (%)"],
                 column_config=column_config,
                 height=340)

# ====================== INFO & FÖRKLARING ======================
st.markdown("**ADX-färgkodning:** <span style='color:#ff4d4d'>■</span> 0–20 Svag  <span style='color:#ffcc00'>■</span> 21–30 Börjande  <span style='color:#00cc66'>■</span> 31–50 Stark", unsafe_allow_html=True)

with st.expander("📘 Förklaring av indikatorerna", expanded=False):
    st.markdown("""
    - **Forward P/E**: Pris i förhållande till förväntat resultat per aktie. Ju lägre = billigare.
    - **PEG**: Forward P/E dividerat med förväntad tillväxt. Ju lägre = bättre värde.
    - **EV/EBITDA**: Företagsvärde i förhållande till rörelseresultat. Ju lägre = undervärderad.
    - **ROE (%)**: Avkastning på eget kapital. Ju högre = bättre lönsamhet.
    - **D/E**: Skuldsättningsgrad. Lägre är säkrare.
    - **FCF Yield (%)**: Fritt kassaflöde i förhållande till företagsvärde. Ju högre = bättre.
    - **ADX**: Trendstyrka (0–50). Färgad i tabellen.
    - **Uppsida (%)**: Genomsnittlig analytikerkursmål minus nuvarande pris.
    """)

col_btn, _ = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Uppdatera data nu", use_container_width=True):
        st.rerun()

st.caption("Klicka på 🔗 för att öppna Yahoo Finance")
