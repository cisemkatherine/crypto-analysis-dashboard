import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

# 1. COIN LISTESI
ALL_COINS = ["BTC-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "ETH-USD"]

st.set_page_config(page_title="Crypto Dashboard", layout="wide")

def get_data_safe(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if df.empty:
            return None
        
        # --- KRİTİK DÜZELTME: Sütunları düzleştir ---
        # Eğer MultiIndex gelirse (örn: ('Close', 'BTC-USD')), sadece ilk kısmı al ('Close')
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        else:
            df.columns = [str(col) for col in df.columns]
            
        return df
    except Exception as e:
        st.error(f"{ticker} çekilirken teknik hata: {e}")
        return None

st.sidebar.title("Navigasyon")
page = st.sidebar.radio("Sayfa:", ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"])

# --- PAGE 1: KORELASYON ---
if page == "Korelasyon Analizi":
    st.title("📊 Korelasyon Analizi")
    if st.button("Hesapla"):
        data_dict = {}
        for t in ALL_COINS:
            df = get_data_safe(t)
            if df is not None:
                data_dict[t.replace("-USD","")] = df["Close"]
        
        if data_dict:
            final_df = pd.DataFrame(data_dict).pct_change().corr().fillna(0)
            fig, ax = plt.subplots()
            sns.heatmap(final_df, annot=True, cmap="coolwarm", ax=ax)
            st.pyplot(fig)

# --- PAGE 2: PARA AKIŞI ---
elif page == "Para Akış Sinyalleri":
    st.title("💰 Para Akış Sinyalleri")
    if st.button("Tara"):
        results = []
        for t in ALL_COINS:
            df = get_data_safe(t)
            if df is not None and len(df) > 5:
                try:
                    # Değerleri garantiye al
                    c_price = float(df["Close"].iloc[-1])
                    o_price = float(df["Close"].iloc[-6])
                    c_vol = float(df["Volume"].iloc[-1])
                    v_mean = df["Volume"].rolling(20, min_periods=1).mean().iloc[-1]
                    
                    change = ((c_price / o_price) - 1) * 100
                    v_power = c_vol / v_mean if v_mean > 0 else 0
                    
                    status = "GÜÇLÜ GİRİŞ" if change > 0 and v_power > 1.1 else ("GÜÇLÜ ÇIKIŞ" if change < 0 and v_power > 1.1 else "ROTASYON")
                    results.append({'Coin': t.replace('-USD',''), 'Değişim %': round(change, 2), 'Hacim Gücü': round(v_power, 2), 'Sinyal': status})
                except Exception as e:
                    st.warning(f"{t} hesaplanamadı: {e}")
        
        if results:
            st.table(pd.DataFrame(results))

# --- PAGE 3: KATEGORİ ---
elif page == "Kategori Analizi":
    st.title("📊 Kategori Analizi")
    mapping = {'BTC-USD':'Major', 'ETH-USD':'L1', 'SOL-USD':'L1', 'AVAX-USD':'L1', 'XRP-USD':'Payment'}
    if st.button("Çalıştır"):
        results = []
        for t in ALL_COINS:
            df = get_data_safe(t)
            if df is not None and len(df) > 5:
                change = ((float(df["Close"].iloc[-1]) / float(df["Close"].iloc[-6])) - 1) * 100
                results.append({'Kripto': t.replace('-USD',''), 'Sektör': mapping.get(t, 'Diğer'), 'Haftalık %': round(change, 2)})
        if results:
            res_df = pd.DataFrame(results)
            st.dataframe(res_df)
            st.bar_chart(res_df.groupby('Sektör')['Haftalık %'].mean())

# --- PAGE 4: HACİM & GETİRİ ---
elif page == "Hacim & Getiri Analizi":
    st.title("📊 Hacim & Getiri Analizi")
    if st.button("Başlat"):
        results = []
        for t in ALL_COINS:
            df = get_data_safe(t)
            if df is not None and len(df) > 5:
                p = float(df["Close"].iloc[-1])
                c = ((p / float(df["Close"].iloc[-6])) - 1) * 100
                v = float(df["Volume"].iloc[-1]) / df["Volume"].rolling(20, min_periods=1).mean().iloc[-1]
                results.append({'Kripto': t.replace('-USD',''), 'Fiyat': round(p, 4), 'Haftalık %': round(c, 2), 'Hacim Gücü': round(v, 2)})
        if results:
            st.table(pd.DataFrame(results))