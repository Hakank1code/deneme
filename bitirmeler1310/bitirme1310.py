import streamlit as st
import xraydb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import periodictable

# --- Sayfa Ayarları ve Başlık ---
st.set_page_config(page_title="Birleşik Zayıflama Simülatörü", layout="wide")
st.title("Aşamalı Zayıflama Simülatörü")
st.write("""
Bu simülasyon, bir radyasyonun kaynaktan dedektöre olan yolculuğunu adım adım modeller.
Işınım şiddetinin her aşamada (mesafe, malzeme, tekrar mesafe) nasıl azaldığını ayrı ayrı ve birleşik bir grafikte görselleştirir.
""")

# --- Temel Kavramlar ---
with st.expander("Simülasyonun Arkasındaki Temel Kavramları Gör"):
    st.subheader("1. Ters Kare Yasası")
    st.write("Noktasal bir kaynaktan yayılan radyasyonun şiddeti, kaynaktan olan mesafenin karesiyle ters orantılı olarak azalır.")
    st.latex(r"I \propto \frac{1}{d^2}")

    st.subheader("2. Beer-Lambert Yasası")
    st.write("Bir malzemeden geçen radyasyonun şiddeti, malzemenin kalınlığı ve zayıflatma katsayısı ile üstel (exponential) olarak azalır.")
    st.latex(r"I = I_0 e^{-\mu x}")

    st.subheader("Birleşik Formül")
    st.write("Bu simülasyon, dedektördeki son şiddeti ($I_{final}$) hesaplamak için bu iki yasayı birleştirir:")
    st.latex(r"I_{final} = \frac{\text{Kaynak Gücü}}{d_{total}^2} \times e^{-\mu x}")


# --- Kullanıcı Girdilerini Kenar Çubuğuna Alma ---
st.sidebar.header("Sistem Kurulum Parametreleri")

# Çoklu Element Seçimi
element_list = [f"{i} - {xraydb.atomic_name(i)} ({xraydb.atomic_symbol(i)})" for i in range(1, 99)]
selected_elements = st.sidebar.multiselect(
    "Zırhlama Malzemesi/Malzemeleri Seçin:",
    element_list,
    default=[element_list[81], element_list[12]] # 82-1=81 (Pb), 13-1=12 (Al)
)

# Enerji girdisi
energy_kev = st.sidebar.number_input(
    "Foton Enerjisi (keV):",
    min_value=1.0, value=150.0, step=10.0
)

# Başlangıç şiddeti
source_activity = st.sidebar.number_input(
    "Kaynak Gücü / Aktivitesi (Keyfi Birim):",
    min_value=1.0, value=100000.0, step=1000.0,
    help="Bu, kaynağın toplam gücünü temsil eder. Sonuçlar bu değerden geriye kalanı gösterecektir."
)

# Mesafe ve Kalınlık Girdileri
st.sidebar.subheader("Mesafe ve Kalınlık (cm)")
d1 = st.sidebar.number_input("Kaynak -> Malzeme Mesafesi (d1):", min_value=1.0, value=50.0, step=1.0)
thickness_cm = st.sidebar.number_input("Malzeme Kalınlığı (x):", min_value=0.0, value=2.0, step=0.1)
d2 = st.sidebar.number_input("Malzeme -> Dedektör Mesafesi (d2):", min_value=1.0, value=50.0, step=1.0)

# --- Hesaplama Fonksiyonu ---
@st.cache_data
def calculate_mu(symbol, energy_kev):
    """Lineer zayıflatma katsayısını hesaplar."""
    try:
        density = periodictable.elements.symbol(symbol).density
    except (AttributeError, KeyError):
        return None
    energy_ev = energy_kev * 1000
    mu_mass_total = xraydb.mu_elam(symbol, energy_ev, kind='total')
    mu_linear_total = mu_mass_total * density
    return mu_linear_total

# --- Ana Hesaplamalar ve Görselleştirme ---
if not selected_elements:
    st.warning("Lütfen karşılaştırmak için en az bir zırhlama malzemesi seçin.")
else:
    # Sadece ilk seçilen element üzerinden detaylı grafikler çizilir.
    primary_element_str = selected_elements[0]
    element_symbol = primary_element_str.split('(')[1].split(')')[0]
    element_name = xraydb.atomic_name(element_symbol)
    mu_linear = calculate_mu(element_symbol, energy_kev)

    if mu_linear is None:
        st.error(f"**{element_name}** için yoğunluk verisi bulunamadı. Lütfen başka bir element seçin.")
    else:
        # --- AŞAMALI HESAPLAMALAR ---
        # 1. Malzemeye girmeden hemen önceki şiddet
        intensity_front = source_activity / (d1**2)
        # 2. Malzemeden çıktıktan hemen sonraki şiddet (sadece malzeme etkisi)
        intensity_back = intensity_front * np.exp(-mu_linear * thickness_cm)
        # 3. Dedektördeki nihai şiddet (toplam mesafe ve malzeme etkisi)
        total_distance_cm = d1 + thickness_cm + d2
        final_intensity = (source_activity / (total_distance_cm**2)) * np.exp(-mu_linear * thickness_cm)

        # --- Gelişmiş Kurulum Görselleştirmesi ---
        st.header("Simülasyon Kurulumu ve Aşamalı Sonuçlar")
        st.info(f"Aşağıdaki detaylı grafikler ilk seçtiğiniz malzeme olan **{element_name}** için çizilmiştir.")

        col1, col2, col3, col4, col5 = st.columns([1.5, 2.5, 1.5, 2.5, 1.5])
        with col1:
            st.image("https://emojigraph.org/media/google/1f4a1.png", width=60)
            st.metric("Kaynak Gücü", f"{source_activity:,.0f}")
        with col2:
            st.html(f"""<div style="text-align: center; margin-top: 15px;">
            <p>➡️ <b>{d1} cm</b> ➡️</p></div>""")
            st.metric("Malzeme Girişindeki Şiddet", f"{intensity_front:.3f}")
        with col3:
            st.image("https://emojigraph.org/media/google/1f9f1.png", width=60)
            st.metric(f"{element_name} ({thickness_cm} cm)", f"{mu_linear:.4f} cm⁻¹ (μ)")
        with col4:
            st.html(f"""<div style="text-align: center; margin-top: 15px;">
            <p>➡️ <b>{d2} cm</b> ➡️</p></div>""")
            st.metric("Malzeme Çıkışındaki Şiddet", f"{intensity_back:.3f}")
        with col5:
            st.image("https://emojigraph.org/media/google/1f4bb.png", width=60)
            st.metric("💥 Dedektördeki Şiddet", f"{final_intensity:.3f}")
        st.divider()

        # --- AYRI GRAFİKLER ---
        st.header(f"Zayıflama Aşamaları ({element_name})")
        gcol1, gcol2, gcol3 = st.columns(3)
        
        # GRAFİK 1: d1 Mesafesinin Etkisi
        with gcol1:
            fig1, ax1 = plt.subplots()
            dist_range1 = np.linspace(1, d1, 100)
            intens_range1 = source_activity / (dist_range1**2)
            ax1.plot(dist_range1, intens_range1, color='dodgerblue')
            ax1.set_title("1. d1 Mesafesinin Etkisi")
            ax1.set_xlabel("Mesafe (cm)")
            ax1.set_ylabel("Şiddet")
            ax1.grid(True, ls='--')
            st.pyplot(fig1)

        # GRAFİK 2: Malzeme Kalınlığının Etkisi
        with gcol2:
            fig2, ax2 = plt.subplots()
            thick_range = np.linspace(0, thickness_cm, 100)
            intens_range2 = intensity_front * np.exp(-mu_linear * thick_range)
            ax2.plot(thick_range, intens_range2, color='darkorange')
            ax2.set_title("2. Malzeme Zayıflamasının Etkisi")
            ax2.set_xlabel("Malzeme İçindeki Derinlik (cm)")
            ax2.set_ylabel("Şiddet")
            ax2.grid(True, ls='--')
            st.pyplot(fig2)

        # GRAFİK 3: d2 Mesafesinin Etkisi
        with gcol3:
            fig3, ax3 = plt.subplots()
            dist_range2 = np.linspace(0, d2, 100)
            # Fiziksel olarak doğru azalmayı göstermek için toplam mesafeyi kullanmalıyız
            total_dist_range3 = d1 + thickness_cm + dist_range2
            intens_range3 = (source_activity / (total_dist_range3**2)) * np.exp(-mu_linear * thickness_cm)
            ax3.plot(dist_range2, intens_range3, color='forestgreen')
            ax3.set_title("3. d2 Mesafesinin Etkisi")
            ax3.set_xlabel("Malzemeden Sonraki Mesafe (cm)")
            ax3.set_ylabel("Şiddet")
            ax3.grid(True, ls='--')
            st.pyplot(fig3)
        st.divider()

        # --- GRAFİK 4: BİRLEŞİK YOLCULUK GRAFİĞİ (GÜNCELLENMİŞ VE DÜZELTİLMİŞ BÖLÜM) ---
        st.header(f"Birleşik Yolculuk Grafiği ({', '.join([s.split('(')[0].split('-')[1].strip() for s in selected_elements])})")
        st.write("Bu grafik, radyasyonun kaynaktan dedektöre olan tüm yolculuğunu gösterir. Y ekseni, hem yüksek hem de çok düşük şiddet değerlerini net görebilmek için **logaritmik** olarak ayarlanmıştır.")
        
        fig4, ax4 = plt.subplots(figsize=(12, 6))

        for element_str in selected_elements:
            elem_sym = element_str.split('(')[1].split(')')[0]
            elem_name = xraydb.atomic_name(elem_sym)
            mu = calculate_mu(elem_sym, energy_kev)
            
            if mu is not None:
                # TEK BİR X EKSENİ OLUŞTURUYORUZ
                # Kaynağa çok yakın yerlerdeki sonsuz değeri önlemek için 0.1'den başlatıyoruz.
                full_dist_range = np.linspace(0.1, total_distance_cm, 500)

                # ŞİDDETİ MESAFENİN HER NOKTASI İÇİN TEK BİR FONKSİYONLA HESAPLIYORUZ
                # Bu yöntem, üç ayrı parçayı birleştirmekten daha sağlamdır.
                # np.piecewise, farklı koşullara göre farklı formüller uygular.
                
                # Koşullar:
                # 1. İlk boşlukta (d <= d1)
                # 2. Malzeme içinde (d1 < d <= d1 + kalınlık)
                # 3. İkinci boşlukta (d > d1 + kalınlık)
                conditions = [
                    full_dist_range <= d1,
                    (full_dist_range > d1) & (full_dist_range <= d1 + thickness_cm)
                ]
                
                # Formüller:
                functions = [
                    lambda d: source_activity / (d**2), # Sadece mesafe etkisi
                    lambda d: (source_activity / (d**2)) * np.exp(-mu * (d - d1)), # Mesafe + Kısmi malzeme etkisi
                    lambda d: (source_activity / (d**2)) * np.exp(-mu * thickness_cm) # Mesafe + Tam malzeme etkisi
                ]

                full_intensity_range = np.piecewise(full_dist_range, conditions, functions)
                
                # Çok küçük veya negatif değerlerin logaritmasını almayı önle
                # Görselleştirmede bir taban değeri belirleyebiliriz
                min_intensity = 1e-9 
                full_intensity_range[full_intensity_range < min_intensity] = min_intensity
                
                ax4.plot(full_dist_range, full_intensity_range, label=elem_name, linewidth=2.5)

        # Grafiğin geri kalanı
        ax4.axvspan(d1, d1 + thickness_cm, color='gray', alpha=0.3, label='Zırhlama Malzemesi')
        ax4.set_title(f"Radyasyonun Toplam Yolculuğu ({energy_kev} keV)")
        ax4.set_xlabel("Kaynaktan Toplam Mesafe (cm)")
        
        # ANAHTAR DEĞİŞİKLİK: Y EKSENİNİ LOGARİTMİK YAPIYORUZ
        ax4.set_yscale('log')
        ax4.set_ylabel("Işınım Şiddeti (Logaritmik Ölçek)")

        ax4.grid(True, which="both", ls="--")
        ax4.set_xlim(left=0, right=total_distance_cm)
        ax4.legend()
        st.pyplot(fig4)
