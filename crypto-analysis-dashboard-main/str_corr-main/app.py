import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import time

# 1. SABİT COİN LİSTESİ
ALL_COINS = ["BTC-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "ETH-USD"]

st.set_page_config(page_title="Crypto Analysis Dashboard", layout="wide")

# --- GELİŞMİŞ VERİ ÇEKME FONKSİYONU (RETRY MEKANİZMALI) ---
@st.cache_data(ttl=600)
def get_crypto_data(tickers):
    data_store = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        status_text.text(f"Veri alınıyor: {ticker}...")
        success = False
        retries = 2 # Hata alırsa 2 kez daha deneyecek
        
        while retries > 0 and not success:
            try:
                # Ticker nesnesi üzerinden çekim yapmak Cloud'da daha stabildir
                t = yf.Ticker(ticker)
                df = t.history(period="1mo", interval="1d")
                
                if not df.empty:
                    df.index = df.index.tz_localize(None)
                    data_store[ticker] = df[['Close', 'Volume']]
                    success = True
                else:
                    retries -= 1
                    time.sleep(2) # Engel yememek için bekle
            except Exception as e:
                retries -= 1
                time.sleep(2)
        
        progress_bar.progress((i + 1) / len(tickers))
    
    status_text.empty()
    progress_bar.empty()
    return data_store

st.sidebar.title("Kripto Navigasyon")
page = st.sidebar.radio("Sayfa Seçiniz:", ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"])

# Verileri çek (Cache sayesinde sadece ilk seferde veya 10 dk bir çalışır)
all_data = get_crypto_data(ALL_COINS)

if not all_data:
    st.error("⚠️ Yahoo Finance şu an yanıt vermiyor. Lütfen 1 dakika sonra sayfayı yenileyip (F5) tekrar deneyin.")
    st.stop()

# --- Page 1: Korelasyon Analizi ---
if page == "Korelasyon Analizi":
    st.title("📊 Kripto Para Korelasyon Analizi")
    if st.button("Hesaplamayı Başlat"):
        # Fiyatları birleştir
        close_df = pd.DataFrame({k.replace('-USD',''): v['Close'] for k, v in all_data.items()})
        returns = close_df.pct_change().dropna()
        corr = returns.corr()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, ax=ax)
        st.pyplot(fig)
        
        excel_io = io.BytesIO()
        corr.to_excel(excel_io)
        st.download_button("Excel İndir", excel_io.getvalue(), "korelasyon.xlsx")

# --- Page 2: Para Akış Sinyalleri ---
elif page == "Para Akış Sinyalleri":
    st.title("💰 Para Akış Sinyalleri")
    res = []
    for coin, df in all_data.items():
        if len(df) >= 6:
            current = df['Close'].iloc[-1]
            prev = df['Close'].iloc[-6]
            change = ((current / prev) - 1) * 100
            
            vol_ma = df['Volume'].rolling(20, min_periods=1).mean().iloc[-1]
            vol_power = df['Volume'].iloc[-1] / vol_ma if vol_ma > 0 else 0
            
            signal = "GÜÇLÜ GİRİŞ" if change > 0 and vol_power > 1.1 else ("GÜÇLÜ ÇIKIŞ" if change < 0 and vol_power > 1.1 else "ROTASYON")
            res.append({'Coin': coin.replace('-USD',''), 'Değişim %': round(change, 2), 'Hacim Gücü': round(vol_power, 2), 'Sinyal': signal})
    
    st.dataframe(pd.DataFrame(res), use_container_width=True)

# --- Page 3: Kategori Analizi ---
elif page == "Kategori Analizi":
    st.title("📊 Kategori Analizi")
    sector_map = {'BTC-USD':'Major', 'ETH-USD':'L1', 'SOL-USD':'L1', 'AVAX-USD':'L1', 'XRP-USD':'Payment'}
    res = []
    for coin, df in all_data.items():
        if len(df) >= 6:
            change = ((df['Close'].iloc[-1] / df['Close'].iloc[-6]) - 1) * 100
            res.append({'Kripto': coin.replace('-USD',''), 'Sektör': sector_map.get(coin, 'Diğer'), 'Haftalık %': round(change, 2)})
    
    df_cat = pd.DataFrame(res)
    st.dataframe(df_cat, use_container_width=True)
    if not df_cat.empty:
        st.bar_chart(df_cat.groupby('Sektör')['Haftalık %'].mean())

# --- Page 4: Hacim & Getiri Analizi ---
elif page == "Hacim & Getiri Analizi":
    st.title("📊 Hacim & Getiri Analizi")
    res = []
    for coin, df in all_data.items():
        current = df['Close'].iloc[-1]
        change = ((current / df['Close'].iloc[-6]) - 1) * 100 if len(df) >= 6 else 0
        vol_ma = df['Volume'].rolling(20, min_periods=1).mean().iloc[-1]
        vol_power = df['Volume'].iloc[-1] / vol_ma if vol_ma > 0 else 0
        res.append({'Kripto': coin.replace('-USD',''), 'Fiyat': round(current, 4), 'Haftalık %': round(change, 2), 'Hacim Gücü': round(vol_power, 2)})
    
    st.table(pd.DataFrame(res))
