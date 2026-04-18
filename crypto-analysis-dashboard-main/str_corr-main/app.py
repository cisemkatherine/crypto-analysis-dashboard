import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

# 1. COIN LISTESI
ALL_COINS = ["BTC-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "ETH-USD"]

st.set_page_config(page_title="Crypto Analysis Dashboard", layout="wide")

st.sidebar.title("Kripto Navigasyon")
page = st.sidebar.radio("Sayfa Seçiniz:", ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"])

# --- YARDIMCI FONKSİYON: HER COINI TEK TEK TEMİZ ÇEKER ---
def get_clean_data(ticker):
    try:
        # Tek tek indirmek, Multi-Index sütun hatasını %100 engeller
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if not df.empty:
            # Sütun isimlerini garantiye alıyoruz
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            return df
        return None
    except:
        return None

# --- SAYFALAR ---

if page == "Korelasyon Analizi":
    st.title("📊 Korelasyon Analizi")
    if st.button("Analizi Hesapla"):
        all_closes = {}
        for t in ALL_COINS:
            df = get_clean_data(t)
            if df is not None:
                all_closes[t.replace("-USD","")] = df["Close"]
        
        if all_closes:
            corr_df = pd.DataFrame(all_closes).pct_change().corr().fillna(0)
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(corr_df, annot=True, cmap="coolwarm", center=0, ax=ax)
            st.pyplot(fig)

elif page == "Para Akış Sinyalleri":
    st.title("💰 Para Akış Sinyalleri")
    if st.button("Sinyalleri Tara"):
        res = []
        for t in ALL_COINS:
            df = get_clean_data(t)
            if df is not None and len(df) >= 6:
                son = float(df["Close"].iloc[-1])
                once = float(df["Close"].iloc[-6])
                degisim = ((son / once) - 1) * 100
                h_ort = df["Volume"].rolling(20, min_periods=1).mean().iloc[-1]
                h_gucu = float(df["Volume"].iloc[-1]) / h_ort if h_ort > 0 else 0
                durum = "GÜÇLÜ GİRİŞ" if degisim > 0 and h_gucu > 1.1 else ("GÜÇLÜ ÇIKIŞ" if degisim < 0 and h_gucu > 1.1 else "ROTASYON")
                res.append({'Coin': t.replace('-USD',''), 'Değişim %': round(degisim, 2), 'Hacim Gücü': round(h_gucu, 2), 'Sinyal': durum})
        
        if res:
            st.dataframe(pd.DataFrame(res), use_container_width=True)

elif page == "Kategori Analizi":
    st.title("📊 Kategori Analizi")
    harita = {'BTC-USD':'Major', 'ETH-USD':'L1', 'SOL-USD':'L1', 'AVAX-USD':'L1', 'XRP-USD':'Payment'}
    if st.button("Analizi Çalıştır"):
        res = []
        for t in ALL_COINS:
            df = get_clean_data(t)
            if df is not None and len(df) >= 6:
                degisim = ((float(df["Close"].iloc[-1]) / float(df["Close"].iloc[-6])) - 1) * 100
                res.append({'Kripto': t.replace('-USD',''), 'Sektör': harita.get(t, 'Diğer'), 'Haftalık %': round(degisim, 2)})
        
        if res:
            df_res = pd.DataFrame(res)
            st.dataframe(df_res, use_container_width=True)
            st.bar_chart(df_res.groupby('Sektör')['Haftalık %'].mean())

elif page == "Hacim & Getiri Analizi":
    st.title("📊 Hacim & Getiri Analizi")
    if st.button("Analizi Başlat"):
        res = []
        for t in ALL_COINS:
            df = get_clean_data(t)
            if df is not None and len(df) >= 6:
                son = float(df["Close"].iloc[-1])
                degisim = ((son / float(df["Close"].iloc[-6])) - 1) * 100
                h_ort = df["Volume"].rolling(20, min_periods=1).mean().iloc[-1]
                h_gucu = float(df["Volume"].iloc[-1]) / h_ort if h_ort > 0 else 0
                res.append({'Kripto': t.replace('-USD',''), 'Fiyat': round(son, 4), 'Haftalık %': round(degisim, 2), 'Hacim Gücü': round(h_gucu, 2)})
        
        if res:
            st.table(pd.DataFrame(res))