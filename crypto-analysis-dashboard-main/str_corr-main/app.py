import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
from datetime import datetime

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
            except: pass
            progress_bar.progress((i + 1) / len(ALL_COINS))

        if main_df.empty:
            st.error("Veri çekilemedi. Lütfen tekrar deneyin.")
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

            excel_buffer = io.BytesIO()
            corr.to_excel(excel_buffer)
            st.download_button("📊 Korelasyon Excel İndir", excel_buffer.getvalue(), f"korelasyon_{selected_period}.xlsx")
            status_text.success("Analiz tamamlandı!")

# --- Page 2: Para Akış Sinyalleri ---
elif page == "Para Akış Sinyalleri":
    st.title("💰 Para Akış Sinyalleri")
    if st.button("Sinyalleri Tara"):
        analiz_listesi = []
        with st.spinner("Veriler analiz ediliyor..."):
            for coin in ALL_COINS:
                try:
                    df = yf.download(coin, period="1mo", interval="1d", progress=False)
                    if not df.empty and len(df) >= 2:
                        son_fiyat = float(df['Close'].iloc[-1])
                        idx = -6 if len(df) >= 6 else 0
                        onceki_fiyat = float(df['Close'].iloc[idx])
                        
                        f_degisim = ((son_fiyat / onceki_fiyat) - 1) * 100
                        hacim_serisi = df['Volume'].rolling(window=20, min_periods=1).mean()
                        hacim_ort = hacim_serisi.iloc[-1] if not hacim_serisi.empty else 1
                        h_gucu = float(df['Volume'].iloc[-1]) / hacim_ort
                        
                        durum = "GÜÇLÜ GİRİŞ" if f_degisim > 0 and h_gucu > 1.1 else ("GÜÇLÜ ÇIKIŞ" if f_degisim < 0 and h_gucu > 1.1 else "ROTASYON")
                        analiz_listesi.append({'Coin': coin.replace('-USD', ''), 'Değişim %': round(f_degisim, 2), 'Hacim Gücü': round(h_gucu, 2), 'Sinyal': durum})
                    else:
                        analiz_listesi.append({'Coin': coin.replace('-USD', ''), 'Değişim %': 0, 'Hacim Gücü': 0, 'Sinyal': "VERİ YOK"})
                except:
                    analiz_listesi.append({'Coin': coin.replace('-USD', ''), 'Değişim %': 0, 'Hacim Gücü': 0, 'Sinyal': "HATA"})
            
            res_df = pd.DataFrame(analiz_listesi)
            st.dataframe(res_df, use_container_width=True)
            
            excel_buffer = io.BytesIO()
            res_df.to_excel(excel_buffer, index=False)
            st.download_button("📥 Sinyalleri Excel İndir", excel_buffer.getvalue(), "sinyaller.xlsx")

# --- Page 3: Kategori Analizi ---
elif page == "Kategori Analizi":
    st.title("📊 Kategori Analizi")
    sektor_haritasi = {
        'BTC-USD': 'Major', 'ETH-USD': 'L1', 'SOL-USD': 'L1', 'AVAX-USD': 'L1', 'XRP-USD': 'Payment'
    }

    if st.button("Sektörel Analizi Çalıştır"):
        veriler = []
        with st.spinner("Kategoriler işleniyor..."):
            for coin in ALL_COINS:
                try:
                    df = yf.download(coin, period="1mo", interval="1d", progress=False)
                    if not df.empty:
                        idx = -6 if len(df) >= 6 else 0
                        f_degisim = ((float(df['Close'].iloc[-1]) / float(df['Close'].iloc[idx])) - 1) * 100
                        veriler.append({
                            'Kripto': coin.replace('-USD', ''), 
                            'Sektör': sektor_haritasi.get(coin, 'Diğer'), 
                            'Haftalık %': round(f_degisim, 2)
                        })
                except:
                    veriler.append({'Kripto': coin.replace('-USD', ''), 'Sektör': sektor_haritasi.get(coin, 'Diğer'), 'Haftalık %': 0})
            
            if veriler:
                res_df = pd.DataFrame(veriler)
                st.dataframe(res_df, use_container_width=True)
                # Kategori bazlı gruplama
                chart_data = res_df.groupby('Sektör')['Haftalık %'].mean()
                st.bar_chart(chart_data)
                
                excel_buffer = io.BytesIO()
                res_df.to_excel(excel_buffer, index=False)
                st.download_button("📥 Kategoriyi Excel İndir", excel_buffer.getvalue(), "kategori.xlsx")

# --- Page 4: Hacim & Getiri Analizi ---
elif page == "Hacim & Getiri Analizi":
    st.title("📊 Hacim & Getiri Analizi")
    if st.button("Analizi Başlat"):
        sonuclar = []
        with st.spinner("Hacim verileri çekiliyor..."):
            for coin in ALL_COINS:
                try:
                    df = yf.download(coin, period="1mo", interval="1d", progress=False)
                    if not df.empty:
                        fiyat = float(df['Close'].iloc[-1])
                        idx = -6 if len(df) >= 6 else 0
                        f_degisim = ((fiyat / float(df['Close'].iloc[idx])) - 1) * 100
                        hacim_ort = df['Volume'].rolling(window=20, min_periods=1).mean().iloc[-1]
                        h_gucu = float(df['Volume'].iloc[-1]) / hacim_ort if hacim_ort > 0 else 0
                        
                        sonuclar.append({
                            'Kripto Para': coin.replace('-USD', ''), 
                            'Fiyat': round(fiyat, 4), 
                            'Haftalık %': round(f_degisim, 2), 
                            'Hacim Gücü': round(h_gucu, 2)
                        })
                except:
                    sonuclar.append({'Kripto Para': coin.replace('-USD', ''), 'Fiyat': 0, 'Haftalık %': 0, 'Hacim Gücü': 0})
            
            if sonuclar:
                res_df = pd.DataFrame(sonuclar)
                st.table(res_df)
                
                excel_buffer = io.BytesIO()
                res_df.to_excel(excel_buffer, index=False)
                st.download_button("📥 Verileri Excel İndir", excel_buffer.getvalue(), "hacim_getiri.xlsx")