import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. COIN LISTESI
ALL_COINS = ["BTC-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "ETH-USD"]

st.set_page_config(page_title="Crypto Dashboard", layout="wide")

# --- EN İLKEL VE EN SAĞLAM VERİ ÇEKME YÖNTEMİ ---
@st.cache_data(ttl=300)
def fetch_all_clean_data():
    master_data = {}
    for t in ALL_COINS:
        try:
            raw = yf.download(t, period="1mo", interval="1d", progress=False)
            
            if not raw.empty:
                # --- KRİTİK DÜZELTME BURASI ---
                # Eğer veri çok katmanlı (MultiIndex) gelirse, katmanları temizle
                if isinstance(raw.columns, pd.MultiIndex):
                    raw.columns = raw.columns.get_level_values(0)
                # ------------------------------

                # Sütun isimlerini garantiye alalım (boşlukları siler)
                raw.columns = [str(c).strip() for c in raw.columns]

                # Şimdi gönül rahatlığıyla "Close" diyebiliriz
                c_vals = raw["Close"].values.flatten().tolist()
                v_vals = raw["Volume"].values.flatten().tolist()
                
                master_data[t] = {"Close": c_vals, "Volume": v_vals}
        except Exception as e:
            # Hatayı terminalde görmek istersen: print(f"Hata: {e}")
            continue
    return master_data

st.sidebar.title("Kripto Menü")
page = st.sidebar.radio("Sayfa:", ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"])

# Uygulama açılır açılmaz veriyi çek ve dondur
all_vault = fetch_all_clean_data()

if not all_vault:
    st.error("Veri merkezine ulaşılamıyor. Lütfen interneti kontrol edip sayfayı yenileyin.")
    st.stop()

# --- ANALİZLER ---

if page == "Korelasyon Analizi":
    st.title("📊 Korelasyon Analizi")
    # Vault'tan sadece kapanışları alıp tablo yap
    close_map = {t.replace("-USD",""): all_vault[t]["Close"] for t in all_vault}
    df_corr = pd.DataFrame(close_map).pct_change().corr()
    st.pyplot(sns.heatmap(df_corr, annot=True, cmap="coolwarm").figure)

elif page == "Para Akış Sinyalleri":
    st.title("💰 Para Akış Sinyalleri")
    res = []
    for t in all_vault:
        c = all_vault[t]["Close"]
        v = all_vault[t]["Volume"]
        if len(c) > 6:
            # Listeden son elemanları çekmek (iloc hatasını bitirir)
            last_c, prev_c = c[-1], c[-6]
            last_v = v[-1]
            v_avg = sum(v[-20:]) / 20 if len(v) >= 20 else sum(v) / len(v)
            
            deg = ((last_c / prev_c) - 1) * 100
            pwr = last_v / v_avg if v_avg > 0 else 0
            sig = "GÜÇLÜ GİRİŞ" if deg > 0 and pwr > 1.1 else ("GÜÇLÜ ÇIKIŞ" if deg < 0 and pwr > 1.1 else "ROTASYON")
            res.append({'Coin': t.replace('-USD',''), 'Değişim %': round(deg, 2), 'Hacim Gücü': round(pwr, 2), 'Sinyal': sig})
    st.table(pd.DataFrame(res))

elif page == "Kategori Analizi":
    st.title("📊 Kategori Analizi")
    m = {'BTC-USD':'Major', 'ETH-USD':'L1', 'SOL-USD':'L1', 'AVAX-USD':'L1', 'XRP-USD':'Payment'}
    res = []
    for t in all_vault:
        c = all_vault[t]["Close"]
        if len(c) > 6:
            deg = ((c[-1] / c[-6]) - 1) * 100
            res.append({'Kripto': t.replace('-USD',''), 'Sektör': m.get(t, 'Diğer'), 'Haftalık %': round(deg, 2)})
    df_res = pd.DataFrame(res)
    st.dataframe(df_res)
    if not df_res.empty:
        st.bar_chart(df_res.groupby('Sektör')['Haftalık %'].mean())

elif page == "Hacim & Getiri Analizi":
    st.title("📊 Hacim & Getiri Analizi")
    res = []
    for t in all_vault:
        c = all_vault[t]["Close"]
        v = all_vault[t]["Volume"]
        if len(c) > 6:
            v_avg = sum(v[-20:]) / 20 if len(v) >= 20 else sum(v) / len(v)
            res.append({
                'Kripto': t.replace('-USD',''), 
                'Fiyat': round(c[-1], 4), 
                'Haftalık %': round(((c[-1]/c[-6])-1)*100, 2), 
                'Hacim Gücü': round(v[-1]/v_avg, 2)
            })
    st.table(pd.DataFrame(res))