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

    # Dönem seçimi
    period_options = ["3d", "7d", "1mo", "1y"]
    selected_period = st.selectbox(
        "Zaman Dilimi Seçiniz:",
        options=period_options,
        index=0
    )
    
    # Veri türü seçimi
    column_options = {"Kapanış Fiyatı": "Close", "İşlem Hacmi": "Volume"}
    selected_column_label = st.selectbox(
        "Analiz Edilecek Veri Türü:",
        options=list(column_options.keys()),
        index=0
    )
    selected_column = column_options[selected_column_label]

    # Interval belirleme
    if selected_period in ["3d", "7d"]:
        selected_interval = "1h"
    else:
        selected_interval = "1d"

    run_bt = st.button("Korelasyonu Hesapla", key="run_analysis_crypto")

    if run_bt:
        # Analiz edilecek ana kripto listesi
        tickers = [
            "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", 
            "ADA-USD", "AVAX-USD", "DOT-USD", "LINK-USD", "DOGE-USD", "LTC-USD"
        ]
        
        ticks = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, tick in enumerate(tickers):
            try:
                status_text.text(f"Veri çekiliyor: {tick}")
                df = yf.Ticker(tick).history(period=selected_period, interval=selected_interval)
                if not df.empty:
                    ticks[tick] = df[selected_column]
                time.sleep(0.5) # Throttling önlemi
                progress_bar.progress((i + 1) / len(tickers))
            except Exception as e:
                st.error(f"{tick} verisi alınamadı: {e}")

        if ticks:
            close_df = pd.DataFrame(ticks)
            # Tüm değerleri 0 olan satırları temizle
            close_df = close_df.loc[~(close_df == 0).all(axis=1)]
            
            # Yüzdesel değişim üzerinden korelasyon hesapla
            returns = close_df.pct_change().dropna()
            corr = returns.corr()

            # Isı haritası (Heatmap) çizimi
            st.subheader(f"Isı Haritası: {selected_column_label} ({selected_period})")
            fig, ax = plt.subplots(figsize=(10, 7))
            sns.heatmap(
                corr, 
                annot=True, 
                fmt=".2f", 
                cmap="coolwarm", 
                vmin=-1, vmax=1, 
                center=0,
                linewidths=.5, 
                ax=ax
            )
            # Ticker isimlerini temizle (USD kısmını at)
            ax.set_xticklabels([t.split('-')[0] for t in corr.columns])
            ax.set_yticklabels([t.split('-')[0] for t in corr.index])
            
            plt.tight_layout()
            st.pyplot(fig)

            # Excel indirme işlemi
            excel_buffer = io.BytesIO()
            corr.to_excel(excel_buffer, index=True)
            excel_buffer.seek(0)

            st.download_button(
                label="Korelasyon Matrisini Excel Olarak İndir",
                data=excel_buffer,
                file_name=f"kripto_korelasyon_{selected_period}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            status_text.success("Analiz tamamlandı!")
        else:
            st.error("Veri alınamadığı için analiz yapılamadı.")

# Page 2: Para Akış Sinyalleri
elif page == "Para Akış Sinyalleri":
    st.title("💰 Kripto Para Akış Sinyal Terminali")
    st.write("Bu sayfa, fiyatı artarken hacmi de desteklenen (breakout) coinleri tespit eder.")
    
    # Analiz edilecek coinler
    coinler = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "AVAX-USD", "FET-USD", "RENDER-USD", "PEPE-USD", "DOGE-USD"]
    
    if st.button("Sinyalleri Tara"):
        with st.spinner("Kripto piyasası taranıyor..."):
            analiz_listesi = []
            for coin in coinler:
                try:
                    # Veriyi çek
                    temp_df = yf.download(coin, period="1mo", interval="1d", progress=False)
                    
                    # Veri boş mu veya yeterli gün var mı kontrolü
                    if temp_df.empty or len(temp_df) < 6:
                        continue
                    
                    # BELİRSİZLİK (AMBIGUOUS) HATASINI ÖNLEMEK İÇİN FLOAT KULLANIMI
                    son_fiyat = float(temp_df['Close'].iloc[-1])
                    bes_gun_once = float(temp_df['Close'].iloc[-6])
                    fiyat_5g = ((son_fiyat / bes_gun_once) - 1) * 100
                    
                    # Hacim hesaplama
                    hacim_ort_20 = float(temp_df['Volume'].rolling(window=20).mean().iloc[-1])
                    son_hacim = float(temp_df['Volume'].iloc[-1])
                    
                    # Hacim Gücü (Sıfıra bölünme kontrolü)
                    hacim_gucu = son_hacim / hacim_ort_20 if hacim_ort_20 > 0 else 0
                    
                    # Sinyal Karar Mekanizması
                    if fiyat_5g > 0 and hacim_gucu > 1.2:
                        durum, skor = "GÜÇLÜ GİRİŞ", 3
                    elif fiyat_5g < 0 and hacim_gucu > 1.2:
                        durum, skor = "GÜÇLÜ ÇIKIŞ", -3
                    else:
                        durum, skor = "ROTASYON", 0
                        
                    analiz_listesi.append({
                        'Coin': coin.replace('-USD', ''),
                        '5G Değişim %': round(fiyat_5g, 2),
                        'Hacim Gücü': round(hacim_gucu, 2),
                        'Sinyal': durum,
                        'Skor': skor
                    })
                except Exception as e:
                    # Hata mesajını sessizce terminale bas, arayüzü kirletme
                    print(f"{coin} hatası: {e}")
                    continue
            
            # --- TABLO OLUŞTURMA VE GÖSTERİM ---
            if len(analiz_listesi) > 0:
                res_df = pd.DataFrame(analiz_listesi)
                # 'Skor' sütunu varsa sırala
                if 'Skor' in res_df.columns:
                    res_df = res_df.sort_values(by='Skor', ascending=False)
                    st.dataframe(res_df, use_container_width=True)
                else:
                    st.error("Analiz yapılamadı, skor sütunu oluşturulamadı.")
            else:
                st.warning("Hiçbir coin için veri çekilemedi. Lütfen internet bağlantınızı veya ticker listesini kontrol edin.")

# Page 3:Kategori Analizi (Kripto Versiyon)
elif page == "Kategori Analizi":
    st.title("📊 Kripto Kategori Analizi")

    st.write(
        """
        Bu sayfa seçili kripto paralar üzerinden **kategori bazlı para giriş hızını** analiz eder.
        - **Kategori Skoru:** Haftalık Getiri % x Hacim Gücü (Relative Volume).
        - Pozitif skorlar o kategoriye olan ilgiyi, yüksek skorlar ise "sıcak para" girişini temsil eder.
        """
    )

    # 1. Kripto Kategori Gruplandırma (Sektör Haritası)
    sektor_haritasi = {
        'BTC-USD': 'Major Assets', 'ETH-USD': 'L1 / Smart Contracts',
        'SOL-USD': 'L1 / Smart Contracts', 'AVAX-USD': 'L1 / Smart Contracts',
        'BNB-USD': 'Exchange / Layer 1', 'FET-USD': 'Artificial Intelligence',
        'RENDER-USD': 'Artificial Intelligence', 'NEAR-USD': 'Artificial Intelligence',
        'TAO-USD': 'Artificial Intelligence', 'DOGE-USD': 'Memecoins',
        'SHIB-USD': 'Memecoins', 'PEPE-USD': 'Memecoins', 'WIF-USD': 'Memecoins',
        'BONK-USD': 'Memecoins', 'UNI-USD': 'DeFi', 'AAVE-USD': 'DeFi',
        'LINK-USD': 'Oracle', 'PYTH-USD': 'Oracle', 'ARB-USD': 'Layer 2',
        'OP-USD': 'Layer 2', 'MATIC-USD': 'Layer 2 / Scalability'
    }

    hisseler = list(sektor_haritasi.keys())

    if st.button("Sektörel Analizi Çalıştır", key="run_sector_analysis"):
        with st.spinner("Kategoriler taranıyor ve trendler hesaplanıyor..."):
            try:
                # Veri çekimi - MultiIndex sorununu önlemek için taze indirme
                data = yf.download(hisseler, period="1mo", interval="1d", progress=False)

                if data.empty:
                    st.warning("Veri çekilemedi. Lütfen internet bağlantınızı veya sembolleri kontrol edin.")
                else:
                    close_data = data['Close']
                    volume_data = data['Volume']
                    analiz_verileri = []

                    # 2. Verileri Tek Tek İşleme
                    for coin in hisseler:
                        try:
                            # Coin verilerini çek ve Series belirsizliğini (ambiguity) gider
                            c_close = close_data[coin]
                            c_vol = volume_data[coin]
                            
                            if len(c_close) < 6: continue

                            # Hesaplamalar (float dönüşümü ile hata payını sıfırlıyoruz)
                            son_fiyat = float(c_close.iloc[-1])
                            eski_fiyat = float(c_close.iloc[-6])
                            fiyat_5g = ((son_fiyat / eski_fiyat) - 1) * 100
                            
                            hacim_ort_20 = float(c_vol.rolling(window=20).mean().iloc[-1])
                            son_hacim = float(c_vol.iloc[-1])
                            hacim_gucu = son_hacim / hacim_ort_20 if hacim_ort_20 > 0 else 0
                            
                            analiz_verileri.append({
                                'Kripto': coin.replace('-USD', ''),
                                'Sektör': sektor_haritasi[coin],
                                'Haftalık Getiri %': round(fiyat_5g, 2),
                                'Hacim Gücü': round(hacim_gucu, 2),
                                'Skor': float(fiyat_5g * hacim_gucu)
                            })
                        except: continue

                    # 3. DataFrame Oluşturma ve Gruplama
                    df = pd.DataFrame(analiz_verileri)
                    
                    if not df.empty:
                        # Sektörel Ortalama Hesaplama
                        sektor_ozet = df.groupby('Sektör')['Skor'].mean().sort_values(ascending=False).reset_index()
                        sektor_ozet.columns = ['Kategori', 'Ortalama Güç Skoru']
                        
                        st.subheader("Sektörel Güç Sıralaması (Para Nereye Gidiyor?)")
                        st.dataframe(sektor_ozet, use_container_width=True)

                        # 4. Görselleştirme (Barplot)
                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.barplot(
                            data=sektor_ozet,
                            x='Ortalama Güç Skoru',
                            y='Kategori',
                            palette='RdYlGn',
                            ax=ax
                        )
                        ax.set_title('Kripto Kategorilerine Göre Para Giriş Hızı')
                        ax.set_xlabel('Güç Skoru (Fiyat x Hacim)')
                        st.pyplot(fig)

                        # 5. Detaylı Tablo
                        st.subheader("Varlık Bazında Detaylı Veriler")
                        st.dataframe(df.sort_values(by='Skor', ascending=False).reset_index(drop=True), use_container_width=True)
                        
                        # Excel İndirme Butonu
                        excel_buffer = io.BytesIO()
                        df.to_excel(excel_buffer, index=False, engine='openpyxl')
                        excel_buffer.seek(0)
                        st.download_button(
                            label="Tüm Detayları Excel Olarak İndir",
                            data=excel_buffer,
                            file_name=f"kripto_sektorel_analiz_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        )
                    else:
                        st.error("Hesaplanacak veri bulunamadı.")
            except Exception as e:
                st.error(f"Sektörel analiz sırasında bir hata oluştu: {e}")
# Page 4: Kripto Hacim & Getiri Analizi
elif page == "Hacim & Getiri Analizi":
    st.title("📊 Kripto Hacim & Getiri Analizi")

    st.write(
        """
        Bu sayfa seçili kripto paralar için **haftalık getiri ve hacim gücü** analizi yapar.
        - **Hacim Gücü:** Son 24 saatlik hacmin, son 20 günlük ortalama hacme oranıdır.
        - **Haftalık Getiri %:** Son 5 gündeki fiyat değişimini ifade eder.
        """
    )

    kriptolar = [
        'BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'AVAX-USD', 'XRP-USD',
        'ADA-USD', 'DOT-USD', 'LINK-USD', 'NEAR-USD', 'FET-USD',
        'RENDER-USD', 'TAO-USD', 'AR-USD', 'PEPE-USD', 'DOGE-USD', 'SHIB-USD'
    ]

    if st.button("Analizi Çalıştır", key="run_vol_analysis"):
        with st.spinner("Kripto verileri işleniyor..."):
            try:
                # 1. Veri İndirme (MultiIndex yapısını düzeltmek için group_by='column' kullanıyoruz)
                data = yf.download(kriptolar, period="1mo", interval="1d")

                if data.empty:
                    st.warning("Veri çekilemedi.")
                else:
                    # MultiIndex sütun yapısından dolayı Close ve Volume'u güvenli çekiyoruz
                    close_prices = data['Close']
                    volume_data = data['Volume']

                    analiz_sonuclari = []

                    for coin in kriptolar:
                        try:
                            # Her bir coin için serileri al
                            coin_close = close_prices[coin]
                            coin_volume = volume_data[coin]

                            # Hesaplamalar
                            fiyat_5g = ((coin_close.iloc[-1] / coin_close.iloc[-6]) - 1) * 100
                            hacim_ort_20 = coin_volume.rolling(window=20).mean().iloc[-1]
                            son_hacim = coin_volume.iloc[-1]
                            hacim_gucu = son_hacim / hacim_ort_20 if hacim_ort_20 > 0 else 0

                            analiz_sonuclari.append({
                                'Kripto Para': coin.replace('-USD', ''),
                                'Güncel Fiyat ($)': coin_close.iloc[-1],
                                'Haftalık Getiri %': fiyat_5g,
                                'Hacim Gücü': hacim_gucu
                            })
                        except:
                            continue

                    # DataFrame Oluşturma
                    df = pd.DataFrame(analiz_sonuclari)
                    
                    # Formatlama
                    df['Güncel Fiyat ($)'] = df['Güncel Fiyat ($)'].apply(lambda x: round(x, 4) if x < 1 else round(x, 2))
                    df['Haftalık Getiri %'] = df['Haftalık Getiri %'].round(2)
                    df['Hacim Gücü'] = df['Hacim Gücü'].round(2)

                    # Sıralama
                    df_sorted = df.sort_values('Hacim Gücü', ascending=False).reset_index(drop=True)
                    st.session_state.kripto_hacim_df = df_sorted

                    # Tablo Gösterimi
                    st.subheader("Hacim Gücü Sıralaması")
                    
                    def highlight_high_vol(val):
                        color = 'background-color: #155724; color: white' if val > 1.5 else ''
                        return color

                    st.dataframe(df_sorted.style.applymap(highlight_high_vol, subset=['Hacim Gücü']), use_container_width=True)

                    # Excel İndirme
                    excel_buffer = io.BytesIO()
                    df_sorted.to_excel(excel_buffer, index=False, engine='openpyxl')
                    excel_buffer.seek(0)
                    
                    st.download_button(
                        label="Excel Olarak İndir",
                        data=excel_buffer,
                        file_name=f"kripto_analiz_{datetime.now().strftime('%d-%m')}.xlsx",
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
            except Exception as e:
                st.error(f"Hata detayı: {e}")
