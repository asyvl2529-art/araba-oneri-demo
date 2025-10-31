import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import textwrap
import re # 5. özellik için regular expression modülünü ekliyoruz

# --- Custom CSS Function for Professional Look ---
def set_custom_style():
    """Arka planı ve genel görünümü profesyonel hale getiren CSS kodlarını ekler."""
    st.markdown("""
        <style>
        /* Ana Kapsayıcı */
        .stApp {
            background-color: #f0f2f6; /* Hafif Gri Arka Plan */
            color: #1c1e21; /* Koyu Metin */
        }
        /* Başlıklar ve Vurgular */
        h1 {
            color: #1a237e; /* Koyu Kurumsal Mavi */
            text-align: center;
            font-weight: 700;
            padding-bottom: 20px;
        }
        h3 {
            border-left: 5px solid #1a237e; /* Kurumsal Mavi Çizgi */
            padding-left: 10px;
            margin-top: 30px;
            margin-bottom: 20px;
            color: #333;
            font-weight: 600;
        }
        /* Sidebar Filtre Başlıkları */
        .st-emotion-cache-1wv7efx {
            color: #1a237e !important;
            font-weight: 600;
        }
        /* Metrik Kutuları */
        div[data-testid="stMetric"] {
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            box-shadow: 1px 1px 3px rgba(0,0,0,0.05);
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)


# --- Sayfa Ayarları ---
st.set_page_config(
    page_title="Akıllı Araba Öneri Sistemi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom stil ayarlarını uygula
set_custom_style()

# --- Uygulama Başlığı ve Tanıtım ---
st.title("Akıllı Araba Öneri ve Karşılaştırma Aracı")
st.markdown("<h3 style='text-align: center; color: #555;'>Milyonlarca Kombinasyon İçinden Size En Uygun Aracı Bulun</h3>", unsafe_allow_html=True)


# --- Veri Yükleme ve Hata Kontrolü ---
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path, sep=',', quotechar='"', skipinitialspace=True)
        
        required_cols = [
            'model', 'marka', 'motor_donanim', 'fiyat_tl', 'donanim_skor', 
            'guvenlik_skor', 'performans_skor', 'konfor_skor', 'ikinci_el_skor', 
            'tuketim_kwh', 'ev_sarj_tl', 'yillik_mtv', 'yillik_sigorta', 
            'yillik_bakim', 'ortalama_tuketim', 'beygir_gucu', 'tork_nm', 
            'hizlanma_0_100s', 'elektrikli_menzil_km', 'gövde_uzunlugu_mm', 
            'bagaj_hacmi_lt', 'kasa_tipi', 'yakit_tipi', 'sanziman', 'kullanim_amaci'
        ]
        
        for col in required_cols:
            if col not in df.columns:
                st.error(f"Hata: CSV dosyasında **'{col}'** sütunu eksik. Lütfen size gönderdiğim **son CSV içeriğini** kontrol edin.")
                return None
        
        score_cols = ['donanim_skor', 'guvenlik_skor', 'performans_skor', 'konfor_skor', 'ikinci_el_skor']
        for col in score_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        maliyet_cols = [
            'tuketim_kwh', 'ev_sarj_tl', 'yillik_mtv', 'yillik_sigorta', 
            'yillik_bakim', 'fiyat_tl', 'ortalama_tuketim', 'beygir_gucu', 
            'tork_nm', 'hizlanma_0_100s', 'elektrikli_menzil_km', 'gövde_uzunlugu_mm', 
            'bagaj_hacmi_lt'
        ]
        for col in maliyet_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        for col in ['marka', 'model', 'motor_donanim', 'kasa_tipi', 'yakit_tipi', 'sanziman', 'kullanim_amaci']:
            df[col] = df[col].astype(str).str.strip().replace('nan', '') 
            
        return df
    except FileNotFoundError:
        st.error(f"Hata: 'arabalar.csv' dosyası bulunamadı. Lütfen dosya adını kontrol edin.")
        return None
    except Exception as e:
        st.error(f"Veri yüklenirken kritik bir hata oluştu: CSV dosyası formatı hatalı. (Detay: {e})")
        return None

df_original = load_data('arabalar.csv')

if df_original is None:
    st.stop()


# --- Sol Sütun: CANLI Filtreler ---
st.sidebar.header("Öneri Sistemi Kriterleri")
st.sidebar.markdown("---")


# --- 1. Bütçe ve Temel Filtreler ---
# Session State'i başlat veya mevcut değerleri al
if 'onem_tuketim' not in st.session_state:
    st.session_state['onem_tuketim'] = 3
if 'onem_performans' not in st.session_state:
    st.session_state['onem_performans'] = 3
if 'onem_ikinci_el' not in st.session_state:
    st.session_state['onem_ikinci_el'] = 3
if 'onem_guvenlik' not in st.session_state:
    st.session_state['onem_guvenlik'] = 3
if 'onem_konfor' not in st.session_state:
    st.session_state['onem_konfor'] = 3


with st.sidebar.container(border=True):
    st.subheader("1. Kapsam ve Temel Filtreler")
    min_fiyat = int(df_original['fiyat_tl'].min()) if not df_original.empty else 0
    max_fiyat_csv = int(df_original['fiyat_tl'].max()) if not df_original.empty else 1000000
    max_fiyat = int(max_fiyat_csv * 1.5) 

    secilen_fiyat_araligi = st.slider(
        "Maksimum Bütçeniz (TL):",
        min_value=min_fiyat,
        max_value=max_fiyat,
        value=int(max_fiyat_csv),
        step=50000,
        format='%.0f',
        key='slider_fiyat' # NLP güncellemeleri için anahtar ekledik
    )

    marka_secenekleri = ['Farketmez'] + sorted(df_original['marka'].unique().tolist())
    secilen_marka = st.selectbox("Marka Tercihi:", marka_secenekleri, key='select_marka')

    if secilen_marka != 'Farketmez':
        modeller_df = df_original[df_original['marka'] == secilen_marka]
        model_secenekleri = ['Farketmez'] + sorted(modeller_df['model'].unique().tolist())
    else:
        model_secenekleri = ['Farketmez'] + sorted(df_original['model'].unique().tolist())
    secilen_model = st.selectbox("Model Tercihi:", model_secenekleri)

    if secilen_model != 'Farketmez':
        motor_df = df_original[(df_original['marka'] == secilen_marka) & (df_original['model'] == secilen_model)]
        motor_secenekleri = ['Farketmez'] + sorted(motor_df['motor_donanim'].unique().tolist())
    elif secilen_marka != 'Farketmez':
        motor_df = df_original[df_original['marka'] == secilen_marka]
        motor_secenekleri = ['Farketmez'] + sorted(motor_df['motor_donanim'].unique().tolist())
    else:
        motor_secenekleri = ['Farketmez'] 

    secilen_motor = st.selectbox("Motor / Donanım Tercihi:", motor_secenekleri)

    kasa_secenekleri = ['Farketmez'] + sorted(df_original['kasa_tipi'].unique().tolist())
    secilen_kasa = st.selectbox("Kasa Tipi Tercihi:", kasa_secenekleri, key='select_kasa')

    yakit_secenekleri = ['Farketmez'] + sorted(df_original['yakit_tipi'].unique().tolist())
    secilen_yakit = st.selectbox("En Çok Tercih Edilen Yakıt Tipi:", yakit_secenekleri, key='select_yakit') 

    sanziman_secenekleri = ['Farketmez'] + sorted(df_original['sanziman'].unique().tolist())
    secilen_sanziman = st.selectbox("Vites Tipi Tercihi:", sanziman_secenekleri)

    kullanim_secenekleri = ['Farketmez'] + sorted(df_original['kullanim_amaci'].unique().tolist())
    secilen_kullanim = st.selectbox("Aracın Ana Kullanım Amacı:", kullanim_secenekleri)


# --- 2. Teknik ve Skor Eşikleri ---
with st.sidebar.expander("2. Performans ve Güvenlik Limitleri", expanded=True):
    min_performans = st.slider("Minimum Subjektif Performans Skoru (1-5):", 1, 5, 1)
    min_guvenlik = st.slider("Minimum Güvenlik Skoru (1-5):", 1, 5, 1)

    min_beygir_gucu = st.number_input("Minimum Beygir Gücü (HP):", min_value=0, max_value=int(df_original['beygir_gucu'].max()), value=0, step=10)
    min_bagaj_hacmi = st.number_input("Minimum Bagaj Hacmi (Litre):", min_value=0, max_value=int(df_original['bagaj_hacmi_lt'].max()), value=0, step=50)

# --- 3. Maliyet Girdileri ---
with st.sidebar.expander("3. İşletme Maliyeti Verileri", expanded=True):
    yillik_km = st.number_input("Yılda Ortalama Kaç KM Yol Yapıyorsunuz?", min_value=1000, max_value=50000, value=15000, step=1000)
    yakit_fiyat_input = st.number_input("Tahmini Yakıt Fiyatı (Litre/TL):", min_value=15.0, max_value=60.0, value=40.0, step=1.0)
    elektrik_fiyat_input = st.number_input("Tahmini Ev Elektrik Fiyatı (kWh/TL):", min_value=1.0, max_value=10.0, value=2.5, step=0.1)

# --- 4. Öncelik Kriterleri ---
with st.sidebar.expander("4. Kriter Ağırlıklandırması (1-5)", expanded=True):
    onem_tuketim = st.slider("İşletme Maliyeti (Yakıt, MTV, Bakım) önemi", 1, 5, st.session_state['onem_tuketim'], key='slider_onem_tuketim')
    onem_performans = st.slider("Hızlanma, Tork ve sürüş keyfi önemi", 1, 5, st.session_state['onem_performans'], key='slider_onem_performans')
    onem_ikinci_el = st.slider("İkinci el değerini koruması önemi", 1, 5, st.session_state['onem_ikinci_el'], key='slider_onem_ikinci_el')
    onem_guvenlik = st.slider("Güvenlik donanımları ve derecesi önemi", 1, 5, st.session_state['onem_guvenlik'], key='slider_onem_guvenlik')
    onem_konfor = st.slider("Sürüş konforu ve kabin sessizliği önemi", 1, 5, st.session_state['onem_konfor'], key='slider_onem_konfor')

# Dinamik Ağırlıklandırma Geri Bildirimi (2. Özellik)
st.sidebar.markdown("---")
if st.sidebar.button("Sonuçlardan Memnun Kalmadım 👎"):
    agirlik_listesi = ['onem_tuketim', 'onem_performans', 'onem_ikinci_el', 'onem_guvenlik', 'onem_konfor']
    rastgele_agirlik = np.random.choice(agirlik_listesi)
    
    if st.session_state[rastgele_agirlik] < 5:
        st.session_state[rastgele_agirlik] += 1
        st.sidebar.success(f"**'{rastgele_agirlik.split('_')[1].upper()}'** kriterinin önemi artırıldı. Yeni etkiyi görmek için lütfen **filtreleri değiştirin veya sayfayı yenileyin (F5)**.")
    else:
        st.sidebar.info("Tüm kriterler zaten maksimum önemde.")

# --- 5. Serbest Metin Analizi ---
with st.sidebar.container(border=True):
    st.subheader("5. Kişisel Analiz Notu (Chatbot Filtreleme)")
    ozel_beklenti = st.text_area(
        "Özel beklentiniz hakkında serbestçe bir cümle yazın:", 
        max_chars=200,
        placeholder="Örn: 500 bin TL'yi geçmeyecek, dizel yakıtlı, geniş bagajlı bir SUV istiyorum."
    )


# --- Ana Ekran: Sonuçların Gösterilmesi ---

# 1. TEMEL FİLTRELEME 
filtreli_df = df_original.copy()
filtreli_df = filtreli_df.dropna(subset=['marka', 'model', 'fiyat_tl'])
filtreli_df = filtreli_df[(filtreli_df['fiyat_tl'] > 0) & (filtreli_df['model'] != '')]

# Fiyat Çarpanı Ekleme (VERİ TABANINI SİMÜLE OLARAK BÜYÜTME)
donanim_seviyeleri = ['Giriş', 'Orta', 'Full']
fiyat_carpanlari = [0.85, 1.0, 1.15] 
skor_degisimi = [-0.15, 0, 0.15] 

genisletilmis_data = []

for index, row in filtreli_df.iterrows():
    for seviye, carpan, skor_farki in zip(donanim_seviyeleri, fiyat_carpanlari, skor_degisimi):
        new_row = row.copy()
        
        new_row['fiyat_tl'] = row['fiyat_tl'] * carpan
        base_donanim = str(row['motor_donanim']).replace('"', '').split('(')[0].strip()
        new_row['motor_donanim'] = base_donanim + f" ({seviye})"
        
        new_row['donanim_skor'] = np.clip(row['donanim_skor'] + skor_farki, 1, 5)
        new_row['konfor_skor'] = np.clip(row['konfor_skor'] + skor_farki, 1, 5)
        
        new_row['yillik_mtv'] = int(row['yillik_mtv'] * carpan)
        new_row['yillik_sigorta'] = int(row['yillik_sigorta'] * carpan)
        
        genisletilmis_data.append(new_row)

filtreli_df = pd.DataFrame(genisletilmis_data)

# --- 5. NLP Benzeri Filtreleme (Chatbot Arayüzü) ---
if ozel_beklenti:
    
    # 1. Bütçe Analizi (Örn: 500 bin TL, 1 milyon)
    fiyat_match = re.search(r'(\d+)\s*(milyon|bin)?\s*tl', ozel_beklenti, re.IGNORECASE)
    if fiyat_match:
        try:
            fiyat = int(fiyat_match.group(1))
            birim = fiyat_match.group(2)
            if birim and 'milyon' in birim.lower():
                max_fiyat_nlp = fiyat * 1000000
            elif birim and 'bin' in birim.lower():
                max_fiyat_nlp = fiyat * 1000
            else:
                max_fiyat_nlp = fiyat
                
            if max_fiyat_nlp < secilen_fiyat_araligi:
                secilen_fiyat_araligi = max_fiyat_nlp
                st.warning(f"Özel notunuzdaki bütçe ({max_fiyat_nlp:,.0f} TL) slider değerinden daha düşük. Bütçe filtreniz otomatik olarak güncellendi. (Sidebar'da güncellenmeyi görebilirsiniz.)")
        except Exception:
            pass # Sayı formatı hatası

    # 2. Kasa Tipi Analizi (Örn: SUV, Sedan)
    kasa_tipleri = ['SUV', 'Sedan', 'Hatchback', 'Station Wagon', 'Coupe', 'Pick-up']
    for tip in kasa_tipleri:
        if tip.lower() in ozel_beklenti.lower():
            if secilen_kasa == 'Farketmez':
                secilen_kasa = tip
                st.warning(f"Özel notunuzdan **'{tip}'** Kasa Tipi tercihi algılandı ve filtreye uygulandı.")
            break
            
    # 3. Yakıt Tipi Analizi (Örn: Dizel, Elektrikli, Hibrit)
    yakit_tipleri = ['Dizel', 'Benzin', 'Elektrikli', 'Hibrit', 'LPG']
    for yakit in yakit_tipleri:
        if yakit.lower() in ozel_beklenti.lower():
            if secilen_yakit == 'Farketmez':
                secilen_yakit = yakit
                st.warning(f"Özel notunuzdan **'{yakit}'** Yakıt Tipi tercihi algılandı ve filtreye uygulandı.")
            break
            
    # 4. Bagaj Hacmi Analizi (Basit bir kontrol)
    if any(kelime in ozel_beklenti.lower() for kelime in ['geniş bagaj', 'büyük bagaj', 'yük taşıma']):
        if min_bagaj_hacmi < 400: # Eğer kullanıcı 400lt'den az girmişse, bunu zorla artır
             min_bagaj_hacmi = 400
             st.warning("Özel notunuzdaki 'geniş bagaj' isteği nedeniyle minimum bagaj hacmi 400 litreye yükseltildi.")
            
# --- KPI METRİKLERİ ---
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
col_kpi1.metric(
    label="Oluşturulan Kombinasyon Sayısı", 
    value=f"{len(filtreli_df):,}",
    delta="3x Artış (Donanıma Göre Simülasyon)"
)
col_kpi2.metric(
    label="Maksimum Bütçe Sınırı", 
    value=f"{secilen_fiyat_araligi:,.0f} TL"
)
col_kpi3.metric(
    label="Toplam Araç Sayısı (Veri Kaynağı)", 
    value=f"{df_original.shape[0]}"
)
st.markdown("---")


# Tekli Seçim Filtreleri (Genişletilmiş DF üzerinde)
filtreli_df = filtreli_df[filtreli_df['fiyat_tl'] <= secilen_fiyat_araligi]

if secilen_marka != 'Farketmez':
    filtreli_df = filtreli_df[filtreli_df['marka'] == secilen_marka]
if secilen_model != 'Farketmez':
    filtreli_df = filtreli_df[filtreli_df['model'] == secilen_model]
if secilen_motor != 'Farketmez':
    filtreli_df = filtreli_df[filtreli_df['motor_donanim'] == secilen_motor]
if secilen_kasa != 'Farketmez':
    filtreli_df = filtreli_df[filtreli_df['kasa_tipi'] == secilen_kasa]
if secilen_kullanim != 'Farketmez':
    filtreli_df = filtreli_df[filtreli_df['kullanim_amaci'].str.contains(secilen_kullanim, case=False, na=False)]
if secilen_yakit != 'Farketmez':
    filtreli_df = filtreli_df[filtreli_df['yakit_tipi'] == secilen_yakit]
if secilen_sanziman != 'Farketmez':
    filtreli_df = filtreli_df[filtreli_df['sanziman'] == secilen_sanziman]
    
# Minimum Skor Filtreleri
filtreli_df = filtreli_df[filtreli_df['performans_skor'] >= min_performans]
filtreli_df = filtreli_df[filtreli_df['guvenlik_skor'] >= min_guvenlik]
# Teknik Filtreler
filtreli_df = filtreli_df[filtreli_df['beygir_gucu'] >= min_beygir_gucu]
filtreli_df = filtreli_df[filtreli_df['bagaj_hacmi_lt'] >= min_bagaj_hacmi]
    

if filtreli_df.empty:
    st.header("Seçtiğiniz Kriterlere Uygun Araç Bulunamadı.")
    st.markdown("Lütfen filtrelerinizi gevşetmeyi veya bütçenizi yükseltmeyi deneyin.")
    st.stop()

# 2. TOPLAM YILLIK İŞLETME MALİYETİ HESAPLAMA (PHEV ve LPG Desteği Eklendi)
def hesapla_yakit_maliyeti(row, yillik_km, yakit_fiyat, elektrik_fiyat):
    
    # 1. Tam Elektrikli Araçlar
    if row['yakit_tipi'] == 'Elektrikli':
        yillik_kwh_tuketim = (yillik_km / 100) * row['tuketim_kwh']
        return yillik_kwh_tuketim * elektrik_fiyat
        
    # 2. Plug-in Hibrit (PHEV) Maliyeti Hesaplama (Elektrikli menzili kullanır)
    elif row['yakit_tipi'] == 'Plug-in Hibrit':
        menzil = row['elektrikli_menzil_km']
        
        if menzil > 0:
            # Varsayım: Elektrikli menzili olan araçlar yolun %35'ini elektrikle gidiyor
            elektrik_km = yillik_km * 0.35 
            benzin_km = yillik_km * 0.65
            
            tuketim_kwh_100km = row['tuketim_kwh'] if row['tuketim_kwh'] > 0 else 15.0 
            yillik_elektrik_maliyet = (elektrik_km / 100) * tuketim_kwh_100km * elektrik_fiyat
            
            yillik_benzin_maliyet = (benzin_km / 100) * row['ortalama_tuketim'] * yakit_fiyat
            
            return yillik_elektrik_maliyet + yillik_benzin_maliyet
        else:
            # Menzil 0 ise normal benzinli gibi hesapla
            yillik_tuketim_litre = (yillik_km / 100) * row['ortalama_tuketim']
            return yillik_tuketim_litre * yakit_fiyat

    # 3. LPG'li Araçlar
    elif row['yakit_tipi'] == 'LPG':
        yillik_tuketim_litre = (yillik_km / 100) * row['ortalama_tuketim']
        lpg_fiyat = yakit_fiyat * 0.70 
        return yillik_tuketim_litre * lpg_fiyat
        
    # 4. Benzin, Dizel, Hibrit (L/100km kullananlar)
    else:
        yillik_tuketim_litre = (yillik_km / 100) * row['ortalama_tuketim']
        return yillik_tuketim_litre * yakit_fiyat

filtreli_df['Yillik_Yakit_Maliyeti'] = filtreli_df.apply(
    lambda row: hesapla_yakit_maliyeti(row, yillik_km, yakit_fiyat_input, elektrik_fiyat_input), axis=1
)

filtreli_df['Toplam_Isletme_Maliyeti'] = (
    filtreli_df['Yillik_Yakit_Maliyeti'] + 
    filtreli_df['yillik_mtv'] + 
    filtreli_df['yillik_sigorta'] + 
    filtreli_df['yillik_bakim']
)

# 3. SKORLAMA MANTIĞI
filtreli_df['Toplam_Skor'] = 0.0

# Dinamik Performans Skoru Hesaplanması
max_hizlanma = filtreli_df['hizlanma_0_100s'].replace(0, np.nan).max()
min_hizlanma = filtreli_df['hizlanma_0_100s'].replace(0, np.nan).min()
max_tork = filtreli_df['tork_nm'].max()

filtreli_df['Tork_Skor'] = (filtreli_df['tork_nm'] / max_tork) * 5
filtreli_df.loc[filtreli_df['tork_nm'] == 0, 'Tork_Skor'] = 1 

if max_hizlanma > 0 and min_hizlanma > 0 and max_hizlanma != min_hizlanma:
    # Hızlanma ters orantılıdır: Düşük saniye = Yüksek Skor
    filtreli_df['Hizlanma_Skor'] = 5 - (5 * (filtreli_df['hizlanma_0_100s'] - min_hizlanma) / (max_hizlanma - min_hizlanma))
    filtreli_df.loc[filtreli_df['hizlanma_0_100s'] == 0, 'Hizlanma_Skor'] = 1 
else:
    filtreli_df['Hizlanma_Skor'] = 2.5 
    
filtreli_df['Hizlanma_Skor'] = np.clip(filtreli_df['Hizlanma_Skor'], 0.5, 5) 

# Performans Skorunun Güncellenmesi (Subjektif + Objektif)
filtreli_df['Performans_Guncel'] = (filtreli_df['performans_skor'] * 0.5) + ((filtreli_df['Tork_Skor'] + filtreli_df['Hizlanma_Skor']) / 2 * 0.5)
filtreli_df['Performans_Guncel'] = np.clip(filtreli_df['Performans_Guncel'], 1, 5)


# Maliyet Skoru Hesaplaması
if filtreli_df['Toplam_Isletme_Maliyeti'].max() > 0:
    max_maliyet = filtreli_df['Toplam_Isletme_Maliyeti'].max()
    # Maliyet ters orantılıdır: Yüksek maliyet = Düşük Skor
    filtreli_df['Maliyet_Skor'] = 5 * (1 - (filtreli_df['Toplam_Isletme_Maliyeti'] / max_maliyet))
    filtreli_df['Maliyet_Skor'] = np.clip(filtreli_df['Maliyet_Skor'], 0, 5) # Skoru 0-5 arasına sınırla
else:
    filtreli_df['Maliyet_Skor'] = 2.5
filtreli_df['Maliyet_Skor'] = filtreli_df['Maliyet_Skor'].fillna(0)


# Toplam Skora Ağırlıklandırılmış Puanları Ekle
filtreli_df['Toplam_Skor'] += filtreli_df['Performans_Guncel'] * onem_performans 
filtreli_df['Toplam_Skor'] += filtreli_df['ikinci_el_skor'] * onem_ikinci_el
filtreli_df['Toplam_Skor'] += filtreli_df['guvenlik_skor'] * onem_guvenlik
filtreli_df['Toplam_Skor'] += filtreli_df['konfor_skor'] * onem_konfor
filtreli_df['Toplam_Skor'] += filtreli_df['Maliyet_Skor'] * onem_tuketim # Maliyet önemini de ekle

# En iyi 30 aracı seç 
onerilen_araclar = filtreli_df.sort_values(by='Toplam_Skor', ascending=False).head(30).reset_index(drop=True)


# 4. SONUÇLARIN VE GRAFİKLERİN GÖSTERİLMESİ
st.header(f"Öncelikleriniz Doğrultusunda En İyi {len(onerilen_araclar)} Öneri")

# --- Grafikler ---
grafik_araclari = onerilen_araclar.head(10).copy()
grafik_araclari['Araba'] = grafik_araclari['marka'] + ' ' + grafik_araclari['motor_donanim'] 

col_grafik1, col_grafik2 = st.columns(2)

with col_grafik1:
    fig_maliyet = px.bar(
        grafik_araclari, 
        x='Araba', 
        y=['fiyat_tl', 'Toplam_Isletme_Maliyeti'], 
        barmode='group',
        labels={'value': 'TL', 'variable': 'Maliyet Türü'},
        title=f'İlk 10 Aracın Satın Alma Fiyatı ve TOPLAM Yıllık İşletme Maliyeti',
        color_discrete_map={'fiyat_tl': '#1a237e', 'Toplam_Isletme_Maliyeti': '#ff8a65'} # Kurumsal Mavi ve Turuncu Vurgu
    )
    st.plotly_chart(fig_maliyet, use_container_width=True)

with col_grafik2:
    radar_df = grafik_araclari.head(3).copy()
    if len(radar_df) >= 3:
        radar_data = pd.DataFrame({
            'Theta': ['Güvenlik', 'Performans', 'Konfor', '2. El Değeri', 'Donanım'],
            radar_df.iloc[0]['Araba']: [radar_df.iloc[0]['guvenlik_skor'], radar_df.iloc[0]['Performans_Guncel'], radar_df.iloc[0]['konfor_skor'], radar_df.iloc[0]['ikinci_el_skor'], radar_df.iloc[0]['donanim_skor']],
            radar_df.iloc[1]['Araba']: [radar_df.iloc[1]['guvenlik_skor'], radar_df.iloc[1]['Performans_Guncel'], radar_df.iloc[1]['konfor_skor'], radar_df.iloc[1]['ikinci_el_skor'], radar_df.iloc[1]['donanim_skor']],
            radar_df.iloc[2]['Araba']: [radar_df.iloc[2]['guvenlik_skor'], radar_df.iloc[2]['Performans_Guncel'], radar_df.iloc[2]['konfor_skor'], radar_df.iloc[2]['ikinci_el_skor'], radar_df.iloc[2]['donanim_skor']]
        }).melt(id_vars='Theta', var_name='Araç', value_name='Skor')
        
        fig_radar = px.line_polar(
            radar_data, r='Skor', theta='Theta', color='Araç', line_close=True, range_r=[0, 5],
            title="İlk 3 Aracın Detaylı Skor Karşılaştırması (5 Üzerinden)"
        )
        st.plotly_chart(fig_radar, use_container_width=True)
    else:
          st.info("Radar grafiği için en az 3 araç önerisi gereklidir.")


# Karşılaştırma Tablosu
st.subheader("Nihai Karşılaştırma Tablosu (En İyi 30)")
gosterilecek_sutunlar = [
    'marka', 'model', 'motor_donanim', 'fiyat_tl', 'Toplam_Isletme_Maliyeti', 'Yillik_Yakit_Maliyeti', 'yakit_tipi', 'sanziman', 
    'tork_nm', 'hizlanma_0_100s', 'elektrikli_menzil_km', 'bagaj_hacmi_lt',
    'guvenlik_skor', 'Performans_Guncel', 'ikinci_el_skor' 
]

karsilastirma_df = onerilen_araclar[gosterilecek_sutunlar].set_index(['marka', 'model', 'motor_donanim'])

karsilastirma_df.columns = [
    'Fiyat (TL)', 'TOPLAM İşletme Maliyeti (Yıllık, TL)', 'Yıllık Yakıt Maliyeti (TL)', 'Yakıt Tipi', 'Şanzıman', 
    'Tork (Nm)', '0-100 (s)', 'E-Menzil (km)', 'Bagaj Hacmi (lt)',
    'Güvenlik Puanı (5)', 'Performans Puanı (5)', '2. El Değeri Puanı (5)'
]

karsilastirma_df['Fiyat (TL)'] = karsilastirma_df['Fiyat (TL)'].apply(lambda x: f"{x:,.0f} TL")
karsilastirma_df['TOPLAM İşletme Maliyeti (Yıllık, TL)'] = karsilastirma_df['TOPLAM İşletme Maliyeti (Yıllık, TL)'].apply(lambda x: f"{x:,.0f} TL")
karsilastirma_df['Yıllık Yakıt Maliyeti (TL)'] = karsilastirma_df['Yıllık Yakıt Maliyeti (TL)'].apply(lambda x: f"{x:,.0f} TL")

st.dataframe(karsilastirma_df, use_container_width=True)


# --- 6. İki Aracı Yan Yana Karşılaştırma Modu (YENİ) ---
st.subheader("Seçili Araçları Yan Yana Karşılaştırın")

# Checkbox'ları eklemek için yeni bir Dataframe oluştur
secilebilir_df = onerilen_araclar.copy()
secilebilir_df['Seç'] = [False] * len(secilebilir_df)

# Gerekli sütunları hazırlayıp göster
gosterilecek_sutunlar_secim = ['Seç', 'marka', 'model', 'motor_donanim', 'fiyat_tl', 'Toplam_Isletme_Maliyeti']
secim_tablosu = st.data_editor(
    secilebilir_df[gosterilecek_sutunlar_secim].head(10),
    column_config={
        "Seç": st.column_config.CheckboxColumn(
            "Karşılaştır",
            help="Karşılaştırmak istediğiniz araçları işaretleyin",
            default=False,
        ),
        "fiyat_tl": st.column_config.NumberColumn("Fiyat (TL)", format="%.0f"),
        "Toplam_Isletme_Maliyeti": st.column_config.NumberColumn("Yıllık Maliyet (TL)", format="%.0f"),
    },
    hide_index=True,
    num_rows="dynamic",
    use_container_width=True
)

secilen_araclar = secim_tablosu[secim_tablosu.Seç]

if len(secilen_araclar) > 0:
    st.markdown("### 🔍 Detaylı Karşılaştırma Raporu")
    
    # Karşılaştırma için detaylı DF oluştur
    detay_karsilastirma = secilen_araclar.copy()
    
    # Sadece 3 araçla sınırlama
    if len(detay_karsilastirma) > 3:
        detay_karsilastirma = detay_karsilastirma.head(3)
        st.warning("Yan yana karşılaştırma 3 araçla sınırlandırılmıştır.")
        
    
    # Sadece teknik özellikleri ve skorları içeren temiz tablo
    karsilastirma_ozellikler = [
        'marka', 'model', 'motor_donanim', 'fiyat_tl', 'Toplam_Isletme_Maliyeti', 
        'yakit_tipi', 'beygir_gucu', 'tork_nm', 'hizlanma_0_100s', 
        'bagaj_hacmi_lt', 'guvenlik_skor', 'Performans_Guncel', 'konfor_skor', 'ikinci_el_skor'
    ]
    
    detay_df = detay_karsilastirma[karsilastirma_ozellikler]
    
    # Kolay okunurluk için satırları sütun yap
    detay_df = detay_df.set_index(['marka', 'model', 'motor_donanim']).T
    
    # Sütun isimlerini düzenle
    detay_df.index = [
        'Fiyat (TL)', 'Yıllık İşletme Maliyeti (TL)', 'Yakıt Tipi', 'Beygir Gücü (HP)', 
        'Tork (Nm)', '0-100 (s)', 'Bagaj Hacmi (lt)', 'Güvenlik (1-5)', 
        'Performans (1-5)', 'Konfor (1-5)', '2. El (1-5)'
    ]
    
    # Finansal değerleri formatla
    try:
        detay_df.loc['Fiyat (TL)'] = detay_df.loc['Fiyat (TL)'].apply(lambda x: f"{x:,.0f} TL")
        detay_df.loc['Yıllık İşletme Maliyeti (TL)'] = detay_df.loc['Yıllık İşletme Maliyeti (TL)'].apply(lambda x: f"{x:,.0f} TL")
    except Exception:
        pass # Hata olursa formatlama yapmaz

    st.dataframe(detay_df, use_container_width=True)
    
else:
    st.info("Lütfen yukarıdaki tablodan karşılaştırmak istediğiniz araçları işaretleyin.")


# 5. AKILLI ANALİZ RAPORU
st.header("Sistem Analiz Raporu")

if ozel_beklenti:
    if not onerilen_araclar.empty:
        en_iyi_araba = onerilen_araclar.iloc[0]
        
        ozel_istek_wrapped = textwrap.fill(ozel_beklenti, width=80) 
        
        analiz_mesaji = f"""
        **Kullanıcının Özel İsteği (Chatbot Notu):** > *"{ozel_istek_wrapped}"*
        
        **Sistem Tarafından Önerilen En Yüksek Skorlu Model:**
        **{en_iyi_araba['marka']} {en_iyi_araba['motor_donanim']}**

        **Analiz:** Seçtiğiniz detaylı filtreler, ağırlıklandırmalar ve **özel notunuzdaki talepler (Bütçe/Kasa Tipi/Yakıt tipi vb.)** dikkate alınmıştır. Sistem, bu kısıtlamalar içinde size en iyi skoru veren **{en_iyi_araba['marka']} {en_iyi_araba['motor_donanim']}** aracını önermiştir.
        
        Bu model, genel performans, güvenlik ve konfor kriterlerinizde yüksek puanlar alırken, **Tork ({en_iyi_araba['tork_nm']} Nm) ve 0-100 ({en_iyi_araba['hizlanma_0_100s']} s) gibi objektif performans verilerinin ağırlıklandırılmasıyla** kriterlerinize en yakın olandır. Bütçeniz ve işletme maliyeti hedeflerinizle de uyumludur.
        """
        st.markdown(analiz_mesaji)
    else:
        st.warning("Özel beklenti analizi için filtrelere uygun araç bulunamadı.")
else:
    st.info("5. bölüme serbest metin girişi yaparak (Kişisel Analiz Notu) sistemden daha kişiselleştirilmiş, metinsel bir analiz alabilir ve metin içindeki bütçe/kasa tipi/yakıt tipi gibi anahtar kelimelerle filtreleri otomatik olarak ayarlayabilirsiniz.")


if __name__ == "__main__":
    pass