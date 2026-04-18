import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import time

# 1. SABİT COİN LİSTESİ (5 Adet)
ALL_COINS = ["BTC-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "ETH-USD"]

st.set_page_config(page_title="Crypto Analysis Dashboard", layout="wide")

# MERKEZİ VERİ ÇEKME FONKSİYONU (Hataları engellemek için önbellek kullanır)
@st.cache_data(ttl=600) # 10 dakika boyunca veriyi saklar, tekrar çekmez
def fetch_all_data(tickers, period, interval="1d"):
    combined_data = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            if not df.empty:
                # Sütunları temizle ve sadece Close/Volume al
                df = df[['Close', 'Volume']].copy()
                df.index = df.index.tz_localize(None)
                combined_data[ticker] = df
            time.sleep(0.5) # Cloud için her indirme arası kısa mola
        except:
            continue
    return combined_data

st.sidebar.title("Kripto Navigasyon")
page = st.sidebar.radio("Sayfa Seçiniz:", ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"])

# --- Ortak Veri Çekme Hazırlığı ---
# Sinyaller ve diğer analizler için genelde 1 aylık veri lazım
all_history = fetch_all_data(ALL_COINS, "1mo", "1d")

# --- Page 1: Korelasyon Analizi ---
if page == "Korelasyon Analizi":
    st.title("📊 Kripto Para Korelasyon Analizi")
    period_options = ["7d", "1mo", "1y"]
    selected_period = st.selectbox("Zaman Dilimi Seçiniz:", options=period_options, index=1)
    
    if st.button("Korelasyonu Hesapla"):
        # Korelasyon için taze veri çekelim (seçilen periyoda göre)
        data_dict = fetch_all_data(ALL_COINS, selected_period, "1d")
        
        if not data_dict:
            st.error("Veri çekilemedi. Lütfen bir süre bekleyip tekrar deneyin.")
        else:
            close_prices = pd.DataFrame({k: v['Close'] for k, v in data_dict.items()})
            # İsimleri temizle
            close_prices.columns = [c.replace('-USD', '') for c in close_prices.columns]
            
            returns = close_prices.pct_change().fillna(0)
            corr = returns.corr().fillna(0)

            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, center=0, ax=ax)
            st.pyplot(fig)
            
            excel_buffer = io.BytesIO()
            corr.to_excel(excel_buffer)
            st.download_button("📊 Excel İndir", excel_buffer.getvalue(), "korelasyon.xlsx")

# --- Page 2: Para Akış Sinyalleri ---
elif page == "Para Akış Sinyalleri":
    st.title("💰 Para Akış Sinyalleri")
    if st.button("Sinyalleri Tara"):
        if not all_history:
            st.error("Veri çekilemedi. Cloud bağlantısı zayıf.")
        else:
            res = []
            for coin, df in all_history.items():
                if len(df) >= 6:
                    son = float(df['Close'].iloc[-1])
                    once = float(df['Close'].iloc[-6]) # 5 gün önceki kapanış
                    degisim = ((son / once) - 1) * 100
                    hacim_ort = df['Volume'].rolling(20, min_periods=1).mean().iloc[-1]
                    h_gucu = float(df['Volume'].iloc[-1]) / hacim_ort if hacim_ort > 0 else 0
                    
                    durum = "GÜÇLÜ GİRİŞ" if degisim > 0 and h_gucu > 1.1 else ("GÜÇLÜ ÇIKIŞ" if degisim < 0 and h_gucu > 1.1 else "ROTASYON")
                    res.append({'Coin': coin.replace('-USD',''), 'Değişim %': round(degisim, 2), 'Hacim Gücü': round(h_gucu, 2), 'Sinyal': durum})
            
            st.dataframe(pd.DataFrame(res), use_container_width=True)

# --- Page 3: Kategori Analizi ---
elif page == "Kategori Analizi":
    st.title("📊 Kategori Analizi")
    harita = {'BTC-USD':'Major', 'ETH-USD':'L1', 'SOL-USD':'L1', 'AVAX-USD':'L1', 'XRP-USD':'Payment'}
    
    if st.button("Analizi Çalıştır"):
        res = []
        for coin, df in all_history.items():
            if len(df) >= 6:
                degisim = ((float(df['Close'].iloc[-1]) / float(df['Close'].iloc[-6])) - 1) * 100
                res.append({'Kripto': coin.replace('-USD',''), 'Sektör': harita.get(coin, 'Diğer'), 'Haftalık %': round(degisim, 2)})
        
        if res:
            df_res = pd.DataFrame(res)
            st.dataframe(df_res, use_container_width=True)
            st.bar_chart(df_res.groupby('Sektör')['Haftalık %'].mean())

# --- Page 4: Hacim & Getiri Analizi ---
elif page == "Hacim & Getiri Analizi":
    st.title("📊 Hacim & Getiri Analizi")
    if st.button("Analizi Başlat"):
        res = []
        for coin, df in all_history.items():
            if len(df) >= 6:
                son = float(df['Close'].iloc[-1])
                degisim = ((son / float(df['Close'].iloc[-6])) - 1) * 100
                h_ort = df['Volume'].rolling(20, min_periods=1).mean().iloc[-1]
                h_gucu = float(df['Volume'].iloc[-1]) / h_ort if h_ort > 0 else 0
                res.append({'Kripto Para': coin.replace('-USD',''), 'Fiyat': round(son, 4), 'Haftalık %': round(degisim, 2), 'Hacim Gücü': round(h_gucu, 2)})
        
        if res:
            st.table(pd.DataFrame(res))