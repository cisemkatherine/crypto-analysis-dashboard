import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import time

# 1. COIN LISTESI
ALL_COINS = ["BTC-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "ETH-USD"]

st.set_page_config(page_title="Crypto Analysis Dashboard", layout="wide")

# --- TOPLU VERİ ÇEKME FONKSİYONU (EN STABİL YÖNTEM) ---
@st.cache_data(ttl=300)
def get_bulk_data(tickers):
    try:
        # Tek seferde tüm coinleri indiriyoruz (Cloud dostu yöntem)
        # 'group_by' ticker yaparak veriyi coin bazlı grupluyoruz
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        
        if data.empty:
            return None
        return data
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
        return None

st.sidebar.title("Kripto Navigasyon")
page = st.sidebar.radio("Sayfa Seçiniz:", ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"])

# Veriyi bir kez ve toplu halde çek
raw_data = get_bulk_data(ALL_COINS)

if raw_data is None:
    st.error("🚨 Yahoo Finance sunucuya cevap vermiyor. Lütfen 'C' tuşuna basarak cache temizleyin veya 1-2 dakika sonra sayfayı yenileyin.")
    st.stop()

# --- ANALİZ FONKSİYONU ---
def process_coin_data(ticker):
    # Toplu veriden ilgili coin'i çekme
    try:
        df = raw_data[ticker].copy()
        df = df.dropna() # Boş satırları temizle
        if len(df) >= 6:
            return df
        return None
    except:
        return None

# --- Sayfalar ---
if page == "Korelasyon Analizi":
    st.title("📊 Korelasyon Analizi")
    if st.button("Analizi Hesapla"):
        # Sadece Kapanış (Close) fiyatlarını birleştir
        close_prices = pd.DataFrame()
        for t in ALL_COINS:
            df = process_coin_data(t)
            if df is not None:
                close_prices[t.replace('-USD','')] = df['Close']
        
        if not close_prices.empty:
            corr = close_prices.pct_change().corr().fillna(0)
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
            st.pyplot(fig)

elif page == "Para Akış Sinyalleri":
    st.title("💰 Para Akış Sinyalleri")
    res = []
    for t in ALL_COINS:
        df = process_coin_data(t)
        if df is not None:
            son, once = df['Close'].iloc[-1], df['Close'].iloc[-6]
            degisim = ((son / once) - 1) * 100
            h_ort = df['Volume'].rolling(20, min_periods=1).mean().iloc[-1]
            h_gucu = df['Volume'].iloc[-1] / h_ort if h_ort > 0 else 0
            durum = "GÜÇLÜ GİRİŞ" if degisim > 0 and h_gucu > 1.1 else ("GÜÇLÜ ÇIKIŞ" if degisim < 0 and h_gucu > 1.1 else "ROTASYON")
            res.append({'Coin': t.replace('-USD',''), 'Değişim %': round(degisim, 2), 'Hacim Gücü': round(h_gucu, 2), 'Sinyal': durum})
    st.dataframe(pd.DataFrame(res), use_container_width=True)

elif page == "Kategori Analizi":
    st.title("📊 Kategori Analizi")
    harita = {'BTC-USD':'Major', 'ETH-USD':'L1', 'SOL-USD':'L1', 'AVAX-USD':'L1', 'XRP-USD':'Payment'}
    res = []
    for t in ALL_COINS:
        df = process_coin_data(t)
        if df is not None:
            degisim = ((df['Close'].iloc[-1] / df['Close'].iloc[-6]) - 1) * 100
            res.append({'Kripto': t.replace('-USD',''), 'Sektör': harita.get(t, 'Diğer'), 'Haftalık %': round(degisim, 2)})
    df_res = pd.DataFrame(res)
    st.dataframe(df_res, use_container_width=True)
    if not df_res.empty:
        st.bar_chart(df_res.groupby('Sektör')['Haftalık %'].mean())

elif page == "Hacim & Getiri Analizi":
    st.title("📊 Hacim & Getiri Analizi")
    res = []
    for t in ALL_COINS:
        df = process_coin_data(t)
        if df is not None:
            son = df['Close'].iloc[-1]
            degisim = ((son / df['Close'].iloc[-6]) - 1) * 100
            h_ort = df['Volume'].rolling(20, min_periods=1).mean().iloc[-1]
            h_gucu = df['Volume'].iloc[-1] / h_ort if h_ort > 0 else 0
            res.append({'Kripto': t.replace('-USD',''), 'Fiyat': round(son, 4), 'Haftalık %': round(degisim, 2), 'Hacim Gücü': round(h_gucu, 2)})
    st.table(pd.DataFrame(res))