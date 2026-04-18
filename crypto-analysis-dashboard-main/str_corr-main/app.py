import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import time
import requests

# 1. SABİT COİN LİSTESİ
ALL_COINS = ["BTC-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "ETH-USD"]

st.set_page_config(page_title="Crypto Analysis Dashboard", layout="wide")

# --- GELİŞMİŞ VERİ ÇEKME FONKSİYONU (PROXY/SESSION DESTEKLİ) ---
@st.cache_data(ttl=600)
def get_crypto_data(tickers):
    data_store = {}
    
    # Gerçek bir tarayıcı gibi görünmek için oturum oluşturuyoruz
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    status_placeholder = st.empty()
    
    for ticker in tickers:
        status_placeholder.info(f"🔍 {ticker} verisi çekiliyor...")
        try:
            # yfinance'e tarayıcı kimliğiyle (session) istek atıyoruz
            df = yf.download(ticker, period="1mo", interval="1d", session=session, progress=False)
            
            if not df.empty:
                df.index = df.index.tz_localize(None)
                data_store[ticker] = df[['Close', 'Volume']]
            else:
                st.warning(f"⚠️ {ticker} için veri boş döndü.")
            
            time.sleep(1) # Engeli aşmak için her coin arası 1 saniye bekle
        except Exception as e:
            st.error(f"❌ {ticker} çekilirken hata oluştu: {str(e)}")
            
    status_placeholder.empty()
    return data_store

st.sidebar.title("Kripto Navigasyon")
page = st.sidebar.radio("Sayfa Seçiniz:", ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"])

# Veriyi bir kez çekip belleğe alıyoruz
all_data = get_crypto_data(ALL_COINS)

if not all_data:
    st.error("🚨 Veriler hiçbir şekilde alınamadı. Lütfen internet bağlantınızı kontrol edip sayfayı yenileyin.")
    st.stop()

# --- Page 1: Korelasyon Analizi ---
if page == "Korelasyon Analizi":
    st.title("📊 Kripto Para Korelasyon Analizi")
    if st.button("Analizi Başlat"):
        close_df = pd.DataFrame({k.replace('-USD',''): v['Close'] for k, v in all_data.items()})
        corr = close_df.pct_change().corr().fillna(0)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, ax=ax)
        st.pyplot(fig)

# --- Page 2: Para Akış Sinyalleri ---
elif page == "Para Akış Sinyalleri":
    st.title("💰 Para Akış Sinyalleri")
    res = []
    for coin, df in all_data.items():
        if len(df) >= 6:
            son, once = df['Close'].iloc[-1], df['Close'].iloc[-6]
            degisim = ((son / once) - 1) * 100
            hacim_ort = df['Volume'].rolling(20, min_periods=1).mean().iloc[-1]
            h_gucu = df['Volume'].iloc[-1] / hacim_ort if hacim_ort > 0 else 0
            durum = "GÜÇLÜ GİRİŞ" if degisim > 0 and h_gucu > 1.1 else ("GÜÇLÜ ÇIKIŞ" if degisim < 0 and h_gucu > 1.1 else "ROTASYON")
            res.append({'Coin': coin.replace('-USD',''), 'Değişim %': round(degisim, 2), 'Hacim Gücü': round(h_gucu, 2), 'Sinyal': durum})
    st.dataframe(pd.DataFrame(res), use_container_width=True)

# --- Page 3: Kategori Analizi ---
elif page == "Kategori Analizi":
    st.title("📊 Kategori Analizi")
    sector_map = {'BTC-USD':'Major', 'ETH-USD':'L1', 'SOL-USD':'L1', 'AVAX-USD':'L1', 'XRP-USD':'Payment'}
    res = []
    for coin, df in all_data.items():
        if len(df) >= 6:
            degisim = ((df['Close'].iloc[-1] / df['Close'].iloc[-6]) - 1) * 100
            res.append({'Kripto': coin.replace('-USD',''), 'Sektör': sector_map.get(coin, 'Diğer'), 'Haftalık %': round(degisim, 2)})
    df_cat = pd.DataFrame(res)
    st.dataframe(df_cat, use_container_width=True)
    if not df_cat.empty:
        st.bar_chart(df_cat.groupby('Sektör')['Haftalık %'].mean())

# --- Page 4: Hacim & Getiri Analizi ---
elif page == "Hacim & Getiri Analizi":
    st.title("📊 Hacim & Getiri Analizi")
    res = []
    for coin, df in all_data.items():
        son = df['Close'].iloc[-1]
        degisim = ((son / df['Close'].iloc[-6]) - 1) * 100 if len(df) >= 6 else 0
        hacim_ort = df['Volume'].rolling(20, min_periods=1).mean().iloc[-1]
        h_gucu = df['Volume'].iloc[-1] / hacim_ort if hacim_ort > 0 else 0
        res.append({'Kripto': coin.replace('-USD',''), 'Fiyat': round(son, 4), 'Haftalık %': round(degisim, 2), 'Hacim Gücü': round(h_gucu, 2)})
    st.table(pd.DataFrame(res))