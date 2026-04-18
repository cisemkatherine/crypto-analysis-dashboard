import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. COIN LISTESI
ALL_COINS = ["BTC-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "ETH-USD"]

st.set_page_config(page_title="Crypto Dashboard", layout="wide")

# --- VERİ ÇEKME FONKSİYONU (KORELASYONDA ÇALIŞAN MANTIK) ---
def get_clean_df(ticker):
    try:
        data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if data.empty:
            return None
        # Veriyi sözlük üzerinden yeniden inşa ederek MultiIndex belasından kurtuluyoruz
        clean_dict = {
            "Close": data["Close"].values.flatten(),
            "Volume": data["Volume"].values.flatten()
        }
        return pd.DataFrame(clean_dict)
    except:
        return None

st.sidebar.title("Menü")
page = st.sidebar.radio("Sayfa:", ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"])

# --- SAYFALAR ---

if page == "Korelasyon Analizi":
    st.title("📊 Korelasyon Analizi")
    if st.button("Hesapla"):
        closes = {}
        for t in ALL_COINS:
            df = get_clean_df(t)
            if df is not None:
                closes[t.replace("-USD","")] = df["Close"]
        if closes:
            st.pyplot(sns.heatmap(pd.DataFrame(closes).pct_change().corr(), annot=True, cmap="coolwarm").figure)

elif page == "Para Akış Sinyalleri":
    st.title("💰 Para Akış Sinyalleri")
    if st.button("Tara"):
        res = []
        for t in ALL_COINS:
            df = get_clean_df(t)
            if df is not None and len(df) > 6:
                c = float(df["Close"].iloc[-1])
                o = float(df["Close"].iloc[-6])
                v = float(df["Volume"].iloc[-1])
                v_avg = df["Volume"].rolling(20).mean().iloc[-1]
                
                deg = ((c / o) - 1) * 100
                pwr = v / v_avg if v_avg > 0 else 0
                sig = "GÜÇLÜ GİRİŞ" if deg > 0 and pwr > 1.1 else ("GÜÇLÜ ÇIKIŞ" if deg < 0 and pwr > 1.1 else "ROTASYON")
                res.append({'Coin': t.replace('-USD',''), 'Değişim %': round(deg, 2), 'Hacim Gücü': round(pwr, 2), 'Sinyal': sig})
        st.table(pd.DataFrame(res))

elif page == "Kategori Analizi":
    st.title("📊 Kategori Analizi")
    m = {'BTC-USD':'Major', 'ETH-USD':'L1', 'SOL-USD':'L1', 'AVAX-USD':'L1', 'XRP-USD':'Payment'}
    if st.button("Çalıştır"):
        res = []
        for t in ALL_COINS:
            df = get_clean_df(t)
            if df is not None and len(df) > 6:
                deg = ((df["Close"].iloc[-1] / df["Close"].iloc[-6]) - 1) * 100
                res.append({'Kripto': t.replace('-USD',''), 'Sektör': m.get(t, 'Diğer'), 'Haftalık %': round(deg, 2)})
        df_res = pd.DataFrame(res)
        st.dataframe(df_res)
        if not df_res.empty:
            st.bar_chart(df_res.groupby('Sektör')['Haftalık %'].mean())

elif page == "Hacim & Getiri Analizi":
    st.title("📊 Hacim & Getiri Analizi")
    if st.button("Başlat"):
        res = []
        for t in ALL_COINS:
            df = get_clean_df(t)
            if df is not None and len(df) > 6:
                p = float(df["Close"].iloc[-1])
                deg = ((p / df["Close"].iloc[-6]) - 1) * 100
                pwr = float(df["Volume"].iloc[-1]) / df["Volume"].rolling(20).mean().iloc[-1]
                res.append({'Kripto': t.replace('-USD',''), 'Fiyat': round(p, 4), 'Haftalık %': round(deg, 2), 'Hacim Gücü': round(pwr, 2)})
        st.table(pd.DataFrame(res))