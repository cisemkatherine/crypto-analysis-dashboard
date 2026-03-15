import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
import io
import json
from datetime import datetime

# Page configuration
st.set_page_config(page_title="Crypto Analysis App", layout="wide")

# Resimlerden alınan tam liste (yfinance uyumlu)
ALL_COINS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "TRUMP-USD", "DOGE-USD", 
    "XRP-USD", "XAG-USD", "RIVER-USD", "COS-USD", "XAU-USD", 
    "BANANAS31-USD", "LYN-USD", "PIXEL-USD", "HYPE-USD", "BNB-USD", 
    "ZEC-USD", "1000PEPE-USD", "TAO-USD", "SUI-USD", "DEGO-USD", 
    "ADA-USD", "SIREN-USD", "LINK-USD", "AVAX-USD", "SAHARA-USD", 
    "AXS-USD", "NAORIS-USD"
]

# Sidebar navigation
st.sidebar.title("Kripto Navigasyon")
page = st.sidebar.radio(
    "Sayfa Seçiniz:",
    ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"]
)

# Page 1: Kripto Korelasyon Analizi
if page == "Korelasyon Analizi":
    st.title("📊 Kripto Para Korelasyon Analizi")
    st.write("Seçili kripto paraların birbirleriyle ne kadar uyumlu hareket ettiğini analiz edin.")

    period_options = ["3d", "7d", "1mo", "1y"]
    selected_period = st.selectbox("Zaman Dilimi Seçiniz:", options=period_options, index=0)
    
    column_options = {"Kapanış Fiyatı": "Close", "İşlem Hacmi": "Volume"}
    selected_column_label = st.selectbox("Analiz Edilecek Veri Türü:", options=list(column_options.keys()), index=0)
    selected_column = column_options[selected_column_label]

    if selected_period in ["3d", "7d"]:
        selected_interval = "1h"
    else:
        selected_interval = "1d"

    run_bt = st.button("Korelasyonu Hesapla")

    if run_bt:
        tickers = ALL_COINS
        ticks = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, tick in enumerate(tickers):
            try:
                status_text.text(f"Veri çekiliyor: {tick}")
                df = yf.Ticker(tick).history(period=selected_period, interval=selected_interval)
                if not df.empty:
                    ticks[tick] = df[selected_column]
                time.sleep(0.1) 
                progress_bar.progress((i + 1) / len(tickers))
            except Exception as e:
                st.error(f"{tick} verisi alınamadı: {e}")

        if ticks:
            close_df = pd.DataFrame(ticks)
            close_df = close_df.loc[~(close_df == 0).all(axis=1)]
            returns = close_df.pct_change().dropna()
            corr = returns.corr()

            st.subheader(f"Isı Haritası: {selected_column_label} ({selected_period})")
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, center=0, linewidths=.5, ax=ax)
            ax.set_xticklabels([t.split('-')[0] for t in corr.columns], rotation=45)
            ax.set_yticklabels([t.split('-')[0] for t in corr.index])
            plt.tight_layout()
            st.pyplot(fig)

            excel_buffer = io.BytesIO()
            corr.to_excel(excel_buffer, index=True)
            excel_buffer.seek(0)
            st.download_button(label="Excel İndir", data=excel_buffer, file_name=f"korelasyon_{selected_period}.xlsx")
            status_text.success("Analiz tamamlandı!")

# Page 2: Para Akış Sinyalleri
elif page == "Para Akış Sinyalleri":
    st.title("💰 Kripto Para Akış Sinyal Terminali")
    coinler = ALL_COINS
    
    if st.button("Sinyalleri Tara"):
        with st.spinner("Taranıyor..."):
            analiz_listesi = []
            for coin in coinler:
                try:
                    temp_df = yf.download(coin, period="1mo", interval="1d", progress=False)
                    if temp_df.empty or len(temp_df) < 6: continue
                    
                    son_fiyat = float(temp_df['Close'].iloc[-1])
                    bes_gun_once = float(temp_df['Close'].iloc[-6])
                    fiyat_5g = ((son_fiyat / bes_gun_once) - 1) * 100
                    hacim_ort_20 = float(temp_df['Volume'].rolling(window=20).mean().iloc[-1])
                    son_hacim = float(temp_df['Volume'].iloc[-1])
                    hacim_gucu = son_hacim / hacim_ort_20 if hacim_ort_20 > 0 else 0
                    
                    if fiyat_5g > 0 and hacim_gucu > 1.2: durum, skor = "GÜÇLÜ GİRİŞ", 3
                    elif fiyat_5g < 0 and hacim_gucu > 1.2: durum, skor = "GÜÇLÜ ÇIKIŞ", -3
                    else: durum, skor = "ROTASYON", 0
                        
                    analiz_listesi.append({
                        'Coin': coin.replace('-USD', ''),
                        '5G Değişim %': round(fiyat_5g, 2),
                        'Hacim Gücü': round(hacim_gucu, 2),
                        'Sinyal': durum,
                        'Skor': skor
                    })
                except: continue
            
            if analiz_listesi:
                res_df = pd.DataFrame(analiz_listesi).sort_values(by='Skor', ascending=False)
                st.dataframe(res_df, use_container_width=True)
                
                excel_buffer = io.BytesIO()
                res_df.to_excel(excel_buffer, index=False)
                excel_buffer.seek(0)
                st.download_button(label="Excel İndir", data=excel_buffer, file_name="sinyaller.xlsx")

# Page 3: Kategori Analizi
elif page == "Kategori Analizi":
    st.title("📊 Kripto Kategori Analizi")
    
    # Yeni coinlerin kategorizasyonu
    sektor_haritasi = {
        'BTC-USD': 'Major Assets', 'ETH-USD': 'L1 / Smart Contracts',
        'SOL-USD': 'L1 / Smart Contracts', 'AVAX-USD': 'L1 / Smart Contracts',
        'BNB-USD': 'Exchange / Layer 1', 'TRUMP-USD': 'PolitiFi / Meme',
        'DOGE-USD': 'Memecoins', '1000PEPE-USD': 'Memecoins',
        'XRP-USD': 'Payment', 'ADA-USD': 'L1 / Smart Contracts',
        'SUI-USD': 'L1 / Smart Contracts', 'TAO-USD': 'AI / DePIN',
        'HYPE-USD': 'AI / Trend', 'PIXEL-USD': 'Gaming / NFT',
        'AXS-USD': 'Gaming / NFT', 'LINK-USD': 'Oracle',
        'XAU-USD': 'Commodity Token', 'XAG-USD': 'Commodity Token',
        'COS-USD': 'Content / Social', 'ZEC-USD': 'Privacy',
        'DEGO-USD': 'DeFi / NFT', 'SAHARA-USD': 'AI / Infrastructure',
        'NAORIS-USD': 'Security / AI', 'RIVER-USD': 'Social / Web3',
        'LYN-USD': 'DeFi / Ecosystem', 'BANANAS31-USD': 'Meme / Ecosystem',
        'SIREN-USD': 'DeFi / Options'
    }

    hisseler = list(sektor_haritasi.keys())

    if st.button("Sektörel Analizi Çalıştır"):
        with st.spinner("Hesaplanıyor..."):
            try:
                data = yf.download(hisseler, period="1mo", interval="1d", progress=False)
                if not data.empty:
                    close_data = data['Close']
                    volume_data = data['Volume']
                    analiz_verileri = []

                    for coin in hisseler:
                        try:
                            c_close = close_data[coin]
                            c_vol = volume_data[coin]
                            if len(c_close) < 6: continue
                            fiyat_5g = ((float(c_close.iloc[-1]) / float(c_close.iloc[-6])) - 1) * 100
                            hacim_ort_20 = float(c_vol.rolling(window=20).mean().iloc[-1])
                            hacim_gucu = float(c_vol.iloc[-1]) / hacim_ort_20 if hacim_ort_20 > 0 else 0
                            
                            analiz_verileri.append({
                                'Kripto': coin.replace('-USD', ''),
                                'Sektör': sektor_haritasi[coin],
                                'Haftalık Getiri %': round(fiyat_5g, 2),
                                'Hacim Gücü': round(hacim_gucu, 2),
                                'Skor': float(fiyat_5g * hacim_gucu)
                            })
                        except: continue

                    df = pd.DataFrame(analiz_verileri)
                    if not df.empty:
                        sektor_ozet = df.groupby('Sektör')['Skor'].mean().sort_values(ascending=False).reset_index()
                        st.subheader("Kategori Güç Sıralaması")
                        st.dataframe(sektor_ozet, use_container_width=True)

                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.barplot(data=sektor_ozet, x='Skor', y='Sektör', palette='RdYlGn', ax=ax)
                        st.pyplot(fig)
                        st.dataframe(df.sort_values(by='Skor', ascending=False), use_container_width=True)
            except Exception as e:
                st.error(f"Hata: {e}")

# Page 4: Hacim & Getiri Analizi
elif page == "Hacim & Getiri Analizi":
    st.title("📊 Kripto Hacim & Getiri Analizi")
    kriptolar = ALL_COINS

    if st.button("Analizi Çalıştır"):
        with st.spinner("İşleniyor..."):
            try:
                data = yf.download(kriptolar, period="1mo", interval="1d")
                if not data.empty:
                    close_prices = data['Close']
                    volume_data = data['Volume']
                    analiz_sonuclari = []

                    for coin in kriptolar:
                        try:
                            coin_close = close_prices[coin]
                            coin_volume = volume_data[coin]
                            fiyat_5g = ((coin_close.iloc[-1] / coin_close.iloc[-6]) - 1) * 100
                            hacim_ort_20 = coin_volume.rolling(window=20).mean().iloc[-1]
                            hacim_gucu = coin_volume.iloc[-1] / hacim_ort_20 if hacim_ort_20 > 0 else 0

                            analiz_sonuclari.append({
                                'Kripto Para': coin.replace('-USD', ''),
                                'Güncel Fiyat ($)': coin_close.iloc[-1],
                                'Haftalık Getiri %': round(fiyat_5g, 2),
                                'Hacim Gücü': round(hacim_gucu, 2)
                            })
                        except: continue

                    df_sorted = pd.DataFrame(analiz_sonuclari).sort_values('Hacim Gücü', ascending=False)
                    st.dataframe(df_sorted.style.background_gradient(subset=['Hacim Gücü'], cmap='Greens'), use_container_width=True)
            except Exception as e:
                st.error(f"Hata: {e}")