import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
import io

# 1. SABİT COİN LİSTESİ
ALL_COINS = [
    "BTC-USD", "TAO-USD", "XRP-USD", "AAVE-USD", "SOL-USD", "HYPE-USD", 
    "OKB-USD", "ZEN-USD", "PUMP-USD", "XMR-USD", "SLERF-USD", "DOT-USD", 
    "EIGEN-USD", "AVAX-USD", "ETH-USD", "ARB-USD", "DOGE-USD", "PEPE-USD"
]

st.set_page_config(page_title="Crypto Analysis Dashboard", layout="wide")

st.sidebar.title("Kripto Navigasyon")
page = st.sidebar.radio(
    "Sayfa Seçiniz:",
    ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"]
)

# --- Page 1: Korelasyon Analizi (HATA GEÇİRMEYEN SON VERSİYON) ---
if page == "Korelasyon Analizi":
    st.title("📊 Kripto Para Korelasyon Analizi")
    period_options = ["3d", "7d", "1mo", "1y"]
    selected_period = st.selectbox("Zaman Dilimi Seçiniz:", options=period_options, index=0)
    
    if st.button("Korelasyonu Hesapla"):
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        ordered_names = [t.replace('-USD', '') for t in ALL_COINS]
        
        # HATAYI ÖNLEYEN ADIM: Önce boş bir DataFrame oluşturuyoruz (İndeks hatasını engeller)
        main_df = pd.DataFrame() 

        for i, tick in enumerate(ALL_COINS):
            try:
                status_text.text(f"Veri çekiliyor: {tick}")
                df = yf.download(tick, period=selected_period, interval="1h" if selected_period in ["3d", "7d"] else "1d", progress=False)
                
                if not df.empty:
                    s = df['Close'].astype(float)
                    s.index = s.index.tz_localize(None)
                    name = tick.replace('-USD', '')
                    # Sütun sütun ekleme yapıyoruz
                    main_df[name] = s
            except:
                pass
            progress_bar.progress((i + 1) / len(ALL_COINS))

        # Eğer hiçbir veri çekilemediyse boş bir DataFrame oluştur (18 coinli)
        if main_df.empty:
            # Boş bir tarih indeksi uyduruyoruz ki tablo oluşabilsin
            dummy_index = pd.date_range(end=datetime.now(), periods=10)
            main_df = pd.DataFrame(index=dummy_index)

        # Eksik olan coin sütunlarını 0 ile oluştur (Sayıyı 18'e tamamlar)
        for name in ordered_names:
            if name not in main_df.columns:
                main_df[name] = 0.0
        
        # Sütunları sırala
        main_df = main_df[ordered_names]

        # Korelasyonu hesapla (Boşlukları 0 ile doldurarak)
        returns = main_df.pct_change().fillna(0)
        # Bazı coinler sabit 0 ise korelasyon NaN çıkar, onları da 0 yapıyoruz
        corr = returns.corr().fillna(0)

        st.subheader(f"Isı Haritası ({selected_period})")
        
        fig, ax = plt.subplots(figsize=(14, 10))
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
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

        # Excel Butonu
        excel_buffer = io.BytesIO()
        corr.to_excel(excel_buffer)
        st.download_button(
            label="📊 Korelasyonu Excel İndir", 
            data=excel_buffer.getvalue(), 
            file_name=f"korelasyon_{selected_period}.xlsx"
        )
        status_text.success("Analiz tamamlandı!")

# --- Page 2: Para Akış Sinyalleri (Excel Eklendi) ---
elif page == "Para Akış Sinyalleri":
    st.title("💰 Para Akış Sinyalleri")
    if st.button("Sinyalleri Tara"):
        analiz_listesi = []
        with st.spinner("Taranıyor..."):
            for coin in ALL_COINS:
                try:
                    df = yf.download(coin, period="1mo", interval="1d", progress=False)
                    if not df.empty and len(df) >= 6:
                        son = float(df['Close'].iloc[-1])
                        once = float(df['Close'].iloc[-6])
                        f_degisim = ((son / once) - 1) * 100
                        h_gucu = float(df['Volume'].iloc[-1]) / float(df['Volume'].rolling(20, min_periods=1).mean().iloc[-1])
                        durum = "GÜÇLÜ GİRİŞ" if f_degisim > 0 and h_gucu > 1.2 else ("GÜÇLÜ ÇIKIŞ" if f_degisim < 0 and h_gucu > 1.2 else "ROTASYON")
                        analiz_listesi.append({'Coin': coin.replace('-USD', ''), 'Değişim %': round(f_degisim, 2), 'Hacim Gücü': round(h_gucu, 2), 'Sinyal': durum})
                    else:
                        analiz_listesi.append({'Coin': coin.replace('-USD', ''), 'Değişim %': 0, 'Hacim Gücü': 0, 'Sinyal': "VERİ YOK"})
                except:
                    analiz_listesi.append({'Coin': coin.replace('-USD', ''), 'Değişim %': 0, 'Hacim Gücü': 0, 'Sinyal': "HATA"})
            
            res_df = pd.DataFrame(analiz_listesi)
            st.dataframe(res_df, use_container_width=True)

            # EXCEL BUTONU
            excel_buffer = io.BytesIO()
            res_df.to_excel(excel_buffer, index=False)
            st.download_button(label="📥 Sinyalleri Excel Olarak İndir", data=excel_buffer.getvalue(), file_name="sinyaller.xlsx")

# --- Page 3: Kategori Analizi ---
elif page == "Kategori Analizi":
    st.title("📊 Kategori Analizi")
    sektor_haritasi = {
        'BTC-USD': 'Major', 'ETH-USD': 'L1', 'SOL-USD': 'L1', 'AVAX-USD': 'L1', 'DOT-USD': 'L1',
        'TAO-USD': 'AI', 'HYPE-USD': 'AI', 'EIGEN-USD': 'Restaking', 'ARB-USD': 'L2',
        'XRP-USD': 'Payment', 'AAVE-USD': 'DeFi', 'DOGE-USD': 'Meme', 'PEPE-USD': 'Meme',
        'SLERF-USD': 'Meme', 'OKB-USD': 'Exchange', 'ZEN-USD': 'Privacy', 'XMR-USD': 'Privacy', 'PUMP-USD': 'Meme'
    }

    if st.button("Sektörel Analizi Çalıştır"):
        veriler = []
        with st.spinner("Analiz ediliyor..."):
            for coin in ALL_COINS:
                try:
                    df = yf.download(coin, period="1mo", interval="1d", progress=False)
                    f_degisim = ((float(df['Close'].iloc[-1]) / float(df['Close'].iloc[-6])) - 1) * 100 if not df.empty and len(df) >=6 else 0
                    veriler.append({'Kripto': coin.replace('-USD', ''), 'Sektör': sektor_haritasi.get(coin, 'Diğer'), 'Haftalık %': round(f_degisim, 2)})
                except:
                    veriler.append({'Kripto': coin.replace('-USD', ''), 'Sektör': sektor_haritasi.get(coin, 'Diğer'), 'Haftalık %': 0})
            
            res_df = pd.DataFrame(veriler)
            st.dataframe(res_df, use_container_width=True)
            st.bar_chart(res_df.groupby('Sektör')['Haftalık %'].mean())
            
            # EXCEL BUTONU
            excel_buffer = io.BytesIO()
            res_df.to_excel(excel_buffer, index=False)
            st.download_button(label="📥 Kategoriyi Excel Olarak İndir", data=excel_buffer.getvalue(), file_name="kategori.xlsx")

# --- Page 4: Hacim & Getiri Analizi ---
elif page == "Hacim & Getiri Analizi":
    st.title("📊 Hacim & Getiri Analizi")
    if st.button("Analizi Başlat"):
        sonuclar = []
        with st.spinner("Veriler işleniyor..."):
            for coin in ALL_COINS:
                try:
                    df = yf.download(coin, period="1mo", interval="1d", progress=False)
                    if not df.empty and len(df) >= 6:
                        fiyat = float(df['Close'].iloc[-1])
                        f_degisim = ((fiyat / float(df['Close'].iloc[-6])) - 1) * 100
                        h_gucu = float(df['Volume'].iloc[-1]) / float(df['Volume'].rolling(20, min_periods=1).mean().iloc[-1])
                        sonuclar.append({'Kripto Para': coin.replace('-USD', ''), 'Fiyat': round(fiyat, 4), 'Haftalık %': round(f_degisim, 2), 'Hacim Gücü': round(h_gucu, 2)})
                    else:
                        sonuclar.append({'Kripto Para': coin.replace('-USD', ''), 'Fiyat': 0, 'Haftalık %': 0, 'Hacim Gücü': 0})
                except:
                    sonuclar.append({'Kripto Para': coin.replace('-USD', ''), 'Fiyat': 0, 'Haftalık %': 0, 'Hacim Gücü': 0})
            
            res_df = pd.DataFrame(sonuclar)
            st.table(res_df)
            
            # EXCEL BUTONU
            excel_buffer = io.BytesIO()
            res_df.to_excel(excel_buffer, index=False)
            st.download_button(label="📥 Verileri Excel Olarak İndir", data=excel_buffer.getvalue(), file_name="hacim_getiri.xlsx")