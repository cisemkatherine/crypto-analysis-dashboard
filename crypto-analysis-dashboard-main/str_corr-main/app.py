import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. COIN LISTESI
ALL_COINS = ["BTC-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "ETH-USD"]

st.set_page_config(page_title="Crypto Dashboard", layout="wide")

# --- VERİYİ SÜTUN İSİMLERİNDEN TAMAMEN ARINDIRAN FONKSİYON ---
def get_data_by_index(ticker):
    try:
        # Tekli indirme yapıyoruz
        raw = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if raw.empty:
            return None
        
        # KRİTİK NOKTA: Sütun isimlerini çöpe atıyoruz.
        # Sadece değerleri alıp kendi tablomuzu manuel kuruyoruz.
        # Bu işlem sunucudaki MultiIndex belasını kökten yok eder.
        
        # yfinance genelde [Open, High, Low, Close, Adj Close, Volume] sırasıyla getirir.
        # Biz Close ve Volume'u (4. ve 6. sütun gibi) garantiye almak için sütun bazlı çekiyoruz:
        c_values = raw["Close"].values.flatten()
        v_values = raw["Volume"].values.flatten()
        
        clean_df = pd.DataFrame({
            "Close": c_values,
            "Volume": v_values
        })
        return clean_df
    except:
        return None

st.sidebar.title("Menü")
page = st.sidebar.radio("Sayfa:", ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"])

# --- SAYFALAR ---

if page == "Korelasyon Analizi":
    st.title("📊 Korelasyon Analizi")
    if st.button("Hesapla"):
        data_map = {}
        for t in ALL_COINS:
            df = get_data_by_index(t)
            if df is not None:
                data_map[t.replace("-USD","")] = df["Close"]
        if data_map:
            # Yeni bir dataframe oluşturup korelasyon alıyoruz
            corr_matrix = pd.DataFrame(data_map).pct_change().corr().fillna(0)
            fig, ax = plt.subplots()
            sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", ax=ax)
            st.pyplot(fig)

elif page == "Para Akış Sinyalleri":
    st.title("💰 Para Akış Sinyalleri")
    if st.button("Sinyal Tara"):
        res = []
        for t in ALL_COINS:
            df = get_data_by_index(t)
            if df is not None and len(df) > 6:
                # İsimlere değil, sıraya bakıyoruz
                prices = df["Close"].astype(float)
                volumes = df["Volume"].astype(float)
                
                c = prices.iloc[-1]
                o = prices.iloc[-6]
                v = volumes.iloc[-1]
                v_avg = volumes.rolling(20, min_periods=1).mean().iloc[-1]
                
                deg = ((c / o) - 1) * 100
                pwr = v / v_avg if v_avg > 0 else 0
                sig = "GÜÇLÜ GİRİŞ" if deg > 0 and pwr > 1.1 else ("GÜÇLÜ ÇIKIŞ" if deg < 0 and pwr > 1.1 else "ROTASYON")
                res.append({'Coin': t.replace('-USD',''), 'Değişim %': round(deg, 2), 'Hacim Gücü': round(pwr, 2), 'Sinyal': sig})
        if res:
            st.table(pd.DataFrame(res))

elif page == "Kategori Analizi":
    st.title("📊 Kategori Analizi")
    mapping = {'BTC-USD':'Major', 'ETH-USD':'L1', 'SOL-USD':'L1', 'AVAX-USD':'L1', 'XRP-USD':'Payment'}
    if st.button("Analizi Göster"):
        res = []
        for t in ALL_COINS:
            df = get_data_by_index(t)
            if df is not None and len(df) > 6:
                prices = df["Close"].astype(float)
                deg = ((prices.iloc[-1] / prices.iloc[-6]) - 1) * 100
                res.append({'Kripto': t.replace('-USD',''), 'Sektör': mapping.get(t, 'Diğer'), 'Haftalık %': round(deg, 2)})
        if res:
            df_res = pd.DataFrame(res)
            st.dataframe(df_res)
            st.bar_chart(df_res.groupby('Sektör')['Haftalık %'].mean())

elif page == "Hacim & Getiri Analizi":
    st.title("📊 Hacim & Getiri Analizi")
    if st.button("Analizi Başlat"):
        res = []
        for t in ALL_COINS:
            df = get_data_by_index(t)
            if df is not None and len(df) > 6:
                prices = df["Close"].astype(float)
                volumes = df["Volume"].astype(float)
                
                p = prices.iloc[-1]
                deg = ((p / prices.iloc[-6]) - 1) * 100
                pwr = volumes.iloc[-1] / volumes.rolling(20, min_periods=1).mean().iloc[-1]
                res.append({'Kripto': t.replace('-USD',''), 'Fiyat': round(p, 4), 'Haftalık %': round(deg, 2), 'Hacim Gücü': round(pwr, 2)})
        if res:
            st.table(pd.DataFrame(res))