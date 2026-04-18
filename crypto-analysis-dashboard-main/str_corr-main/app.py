import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

# 1. COIN LISTESI
ALL_COINS = ["BTC-USD", "XRP-USD", "SOL-USD", "AVAX-USD", "ETH-USD"]

st.set_page_config(page_title="Crypto Analysis Dashboard", layout="wide")

# --- VERİ ÇEKME VE SÜTUNLARI DÜZLEŞTİRME ---
@st.cache_data(ttl=300)
def load_data():
    # Toplu indirme yapıyoruz
    data = yf.download(ALL_COINS, period="1mo", interval="1d", progress=False)
    
    # KRİTİK NOKTA: yfinance Multi-Index sütunları (Price, Ticker) şeklinde verir.
    # Bunu (Ticker, Price) sırasına sokup düzleştiriyoruz.
    if not data.empty:
        # Sütun yapısını düzeltiyoruz ki her sayfa coin ismini direkt bulabilsin
        data = data.stack(level=1, future_stack=True).reset_index()
        # Sütun isimleri artık: Date, Ticker, Close, High, Low, Open, Volume vb.
        return data
    return pd.DataFrame()

st.sidebar.title("Kripto Navigasyon")
page = st.sidebar.radio("Sayfa Seçiniz:", ["Korelasyon Analizi", "Para Akış Sinyalleri", "Kategori Analizi", "Hacim & Getiri Analizi"])

df_all = load_data()

if df_all.empty:
    st.error("🚨 Veri çekilemedi. Lütfen sayfayı yenileyin veya 'C' tuşu ile önbelleği temizleyin.")
    st.stop()

# --- ANALİZ MANTIĞI ---

def get_coin_stats(ticker):
    """Her coin için gerekli hesaplamaları tek yerden yapar."""
    coin_df = df_all[df_all['Ticker'] == ticker].sort_values('Date')
    if len(coin_df) >= 6:
        son_fiyat = coin_df['Close'].iloc[-1]
        onceki_fiyat = coin_df['Close'].iloc[-6]
        degisim = ((son_fiyat / onceki_fiyat) - 1) * 100
        
        son_hacim = coin_df['Volume'].iloc[-1]
        hacim_ort = coin_df['Volume'].rolling(20, min_periods=1).mean().iloc[-1]
        h_gucu = son_hacim / hacim_ort if hacim_ort > 0 else 0
        
        return {
            'fiyat': round(son_fiyat, 4),
            'degisim': round(degisim, 2),
            'hacim_gucu': round(h_gucu, 2)
        }
    return None

# --- SAYFALAR ---

if page == "Korelasyon Analizi":
    st.title("📊 Korelasyon Analizi")
    # Korelasyon için veriyi pivot yapıyoruz (Date satır, Ticker sütun)
    pivot_df = df_all.pivot(index='Date', columns='Ticker', values='Close')
    pivot_df.columns = [c.replace('-USD', '') for c in pivot_df.columns]
    
    corr = pivot_df.pct_change().corr().fillna(0)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, ax=ax)
    st.pyplot(fig)

elif page == "Para Akış Sinyalleri":
    st.title("💰 Para Akış Sinyalleri")
    res = []
    for ticker in ALL_COINS:
        stats = get_coin_stats(ticker)
        if stats:
            durum = "GÜÇLÜ GİRİŞ" if stats['degisim'] > 0 and stats['hacim_gucu'] > 1.1 else ("GÜÇLÜ ÇIKIŞ" if stats['degisim'] < 0 and stats['hacim_gucu'] > 1.1 else "ROTASYON")
            res.append({'Coin': ticker.replace('-USD',''), 'Değişim %': stats['degisim'], 'Hacim Gücü': stats['hacim_gucu'], 'Sinyal': durum})
    st.dataframe(pd.DataFrame(res), use_container_width=True)

elif page == "Kategori Analizi":
    st.title("📊 Kategori Analizi")
    harita = {'BTC-USD':'Major', 'ETH-USD':'L1', 'SOL-USD':'L1', 'AVAX-USD':'L1', 'XRP-USD':'Payment'}
    res = []
    for ticker in ALL_COINS:
        stats = get_coin_stats(ticker)
        if stats:
            res.append({'Kripto': ticker.replace('-USD',''), 'Sektör': harita.get(ticker, 'Diğer'), 'Haftalık %': stats['degisim']})
    df_cat = pd.DataFrame(res)
    st.dataframe(df_cat, use_container_width=True)
    if not df_cat.empty:
        st.bar_chart(df_cat.groupby('Sektör')['Haftalık %'].mean())

elif page == "Hacim & Getiri Analizi":
    st.title("📊 Hacim & Getiri Analizi")
    res = []
    for ticker in ALL_COINS:
        stats = get_coin_stats(ticker)
        if stats:
            res.append({'Kripto': ticker.replace('-USD',''), 'Fiyat': stats['fiyat'], 'Haftalık %': stats['degisim'], 'Hacim Gücü': stats['hacim_gucu']})
    st.table(pd.DataFrame(res))