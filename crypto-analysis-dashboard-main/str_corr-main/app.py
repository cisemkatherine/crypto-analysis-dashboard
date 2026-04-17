import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import time # Zaman geciktirme için eklendi

# 1. SABİT COİN LİSTESİ (5 Adet)
ALL_COINS = ["BTC-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "ETH-USD"]

st.set_page_config(page_title="Crypto Analysis Dashboard", layout="wide")

st.sidebar.title("Kripto Navigasyon")
page = st.sidebar.radio(
    "Sayfa Seçiniz:",
    ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"]
)

# --- Page 1: Korelasyon Analizi ---
if page == "Korelasyon Analizi":
    st.title("📊 Kripto Para Korelasyon Analizi")
    period_options = ["3d", "7d", "1mo", "1y"]
    selected_period = st.selectbox("Zaman Dilimi Seçiniz:", options=period_options, index=0)
    
    if st.button("Korelasyonu Hesapla"):
        status_text = st.empty()
        progress_bar = st.progress(0)
        ordered_names = [t.replace('-USD', '') for t in ALL_COINS]
        main_df = pd.DataFrame() 

        for i, tick in enumerate(ALL_COINS):
            try:
                status_text.text(f"Veri çekiliyor: {tick}")
                df = yf.download(tick, period=selected_period, interval="1h" if selected_period in ["3d", "7d"] else "1d", progress=False)
                if not df.empty:
                    s = df['Close'].astype(float)
                    s.index = s.index.tz_localize(None)
                    main_df[tick.replace('-USD', '')] = s
                time.sleep(0.5) # Sunucuyu yormamak için kısa bekleme
            except: pass
            progress_bar.progress((i + 1) / len(ALL_COINS))

        if main_df.empty:
            st.error("Veri çekilemedi.")
        else:
            for name in ordered_names:
                if name not in main_df.columns:
                    main_df[name] = 0.0
            main_df = main_df[ordered_names]
            returns = main_df.pct_change().fillna(0)
            corr = returns.corr().fillna(0)
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, center=0, ax=ax)
            st.pyplot(fig)
            status_text.success("Tamamlandı!")

# --- Page 2, 3 ve 4 İçin Ortak Hata Gidermeli Yapı ---
else:
    st.title(f"📊 {page}")
    if st.button("Analizi Başlat"):
        veriler = []
        progress = st.progress(0)
        
        for i, coin in enumerate(ALL_COINS):
            try:
                # Cloud dostu veri çekme
                df = yf.download(coin, period="1mo", interval="1d", progress=False)
                time.sleep(1) # CRITICAL: Sunucunun engellememesi için 1 saniye bekle
                
                if not df.empty and len(df) > 0:
                    son_fiyat = float(df['Close'].iloc[-1])
                    idx = -6 if len(df) >= 6 else 0
                    onceki_fiyat = float(df['Close'].iloc[idx])
                    f_degisim = ((son_fiyat / onceki_fiyat) - 1) * 100
                    hacim_ort = df['Volume'].rolling(window=20, min_periods=1).mean().iloc[-1]
                    h_gucu = float(df['Volume'].iloc[-1]) / hacim_ort if hacim_ort > 0 else 0
                    
                    if page == "Para Akış Sinyalleri":
                        durum = "GÜÇLÜ GİRİŞ" if f_degisim > 0 and h_gucu > 1.1 else ("GÜÇLÜ ÇIKIŞ" if f_degisim < 0 and h_gucu > 1.1 else "ROTASYON")
                        veriler.append({'Coin': coin.replace('-USD', ''), 'Değişim %': round(f_degisim, 2), 'Hacim Gücü': round(h_gucu, 2), 'Sinyal': durum})
                    elif page == "Kategori Analizi":
                        harita = {'BTC-USD':'Major','ETH-USD':'L1','SOL-USD':'L1','AVAX-USD':'L1','XRP-USD':'Payment'}
                        veriler.append({'Kripto': coin.replace('-USD', ''), 'Sektör': harita.get(coin, 'Diğer'), 'Haftalık %': round(f_degisim, 2)})
                    else: # Hacim & Getiri
                        veriler.append({'Kripto Para': coin.replace('-USD', ''), 'Fiyat': round(son_fiyat, 4), 'Haftalık %': round(f_degisim, 2), 'Hacim Gücü': round(h_gucu, 2)})
                else:
                    st.warning(f"{coin} için veri alınamadı.")
            except Exception as e:
                st.error(f"{coin} hatası: {e}")
            progress.progress((i + 1) / len(ALL_COINS))

        if veriler:
            res_df = pd.DataFrame(veriler)
            if page == "Kategori Analizi":
                st.dataframe(res_df)
                st.bar_chart(res_df.groupby('Sektör')['Haftalık %'].mean())
            elif page == "Hacim & Getiri Analizi":
                st.table(res_df)
            else:
                st.dataframe(res_df)
            
            excel_buffer = io.BytesIO()
            res_df.to_excel(excel_buffer, index=False)
            st.download_button("📥 Excel İndir", excel_buffer.getvalue(), "analiz.xlsx")