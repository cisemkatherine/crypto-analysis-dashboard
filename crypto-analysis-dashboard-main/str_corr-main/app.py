import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

# 1. COIN LISTESI
ALL_COINS = ["BTC-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "ETH-USD"]

st.set_page_config(page_title="Crypto Dashboard", layout="wide")

# VERİ ÇEKME (En Sade Hal)
@st.cache_data(ttl=300)
def load_data():
    # Toplu indirme yapıyoruz
    data = yf.download(ALL_COINS, period="1mo", interval="1d", progress=False)
    return data

st.sidebar.title("Kripto Navigasyon")
page = st.sidebar.radio("Sayfa Seçiniz:", ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"])

raw_data = load_data()

if raw_data.empty:
    st.error("Veri çekilemedi, lütfen sayfayı yenileyin.")
    st.stop()

# --- VERİ HAZIRLAMA (Her sayfa için ortak) ---
# Kapanış ve Hacim verilerini ayrı tablolar haline getiriyoruz
close_df = raw_data['Close']
volume_df = raw_data['Volume']

# --- SAYFALAR ---

if page == "Korelasyon Analizi":
    st.title("📊 Korelasyon Analizi")
    if st.button("Hesapla"):
        corr = close_df.pct_change().corr().fillna(0)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)

elif page == "Para Akış Sinyalleri":
    st.title("💰 Para Akış Sinyalleri")
    res = []
    for coin in ALL_COINS:
        # Veri sütununu al ve boşlukları temizle
        prices = close_df[coin].dropna()
        vols = volume_df[coin].dropna()
        
        if len(prices) > 6:
            # En son ve 5 gün önceki veri
            current_price = float(prices.iloc[-1])
            old_price = float(prices.iloc[-6])
            change = ((current_price / old_price) - 1) * 100
            
            # Hacim gücü (Son hacim / 20 günlük ortalama)
            current_vol = float(vols.iloc[-1])
            avg_vol = vols.rolling(20, min_periods=1).mean().iloc[-1]
            vol_power = current_vol / avg_vol if avg_vol > 0 else 0
            
            durum = "GÜÇLÜ GİRİŞ" if change > 0 and vol_power > 1.1 else ("GÜÇLÜ ÇIKIŞ" if change < 0 and vol_power > 1.1 else "ROTASYON")
            res.append({'Coin': coin.replace('-USD',''), 'Değişim %': round(change, 2), 'Hacim Gücü': round(vol_power, 2), 'Sinyal': durum})
    
    st.dataframe(pd.DataFrame(res), use_container_width=True)

elif page == "Kategori Analizi":
    st.title("📊 Kategori Analizi")
    harita = {'BTC-USD':'Major', 'ETH-USD':'L1', 'SOL-USD':'L1', 'AVAX-USD':'L1', 'XRP-USD':'Payment'}
    res = []
    for coin in ALL_COINS:
        prices = close_df[coin].dropna()
        if len(prices) > 6:
            change = ((prices.iloc[-1] / prices.iloc[-6]) - 1) * 100
            res.append({'Kripto': coin.replace('-USD',''), 'Sektör': harita.get(coin, 'Diğer'), 'Haftalık %': round(change, 2)})
    
    df_cat = pd.DataFrame(res)
    st.dataframe(df_cat, use_container_width=True)
    if not df_cat.empty:
        st.bar_chart(df_cat.groupby('Sektör')['Haftalık %'].mean())

elif page == "Hacim & Getiri Analizi":
    st.title("📊 Hacim & Getiri Analizi")
    res = []
    for coin in ALL_COINS:
        prices = close_df[coin].dropna()
        vols = volume_df[coin].dropna()
        if len(prices) > 6:
            current_p = float(prices.iloc[-1])
            change = ((current_p / prices.iloc[-6]) - 1) * 100
            v_power = float(vols.iloc[-1]) / vols.rolling(20, min_periods=1).mean().iloc[-1]
            res.append({'Kripto': coin.replace('-USD',''), 'Fiyat': round(current_p, 4), 'Haftalık %': round(change, 2), 'Hacim Gücü': round(v_power, 2)})
    
    st.table(pd.DataFrame(res))