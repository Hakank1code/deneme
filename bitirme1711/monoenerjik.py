import streamlit as st
import xraylib  # Doğru kütüphane
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import periodictable

# --- Sayfa Ayarları ve Başlık ---
st.set_page_config(page_title="X-ray attenuation calculator", layout="wide")
st.title("X-ray attenuation calculator")
try:
    st.image("bitirmeresim.png", width=600)
except FileNotFoundError:
    st.warning("`bitirmeresim.png` dosyası bulunamadı.")

# --- Kullanıcı Girdilerini Kenar Çubuğuna Alma ---
st.sidebar.header("System design parameters")

# Çoklu Element Seçimi (periodictable kullanarak)
element_list = [f"{el.number} - {el.name} ({el.symbol})" for el in periodictable.elements if el.number < 99]
selected_elements = st.sidebar.multiselect(
    "shielding material elements:",
    element_list,
    default=[element_list[81]] # 82 -> Pb (Kurşun)
)

# Enerji girdisi
energy_input_kev = st.sidebar.number_input(
    "Photon energy (keV):",
    min_value=1.0, max_value=8000.0, value=100.0, step=1.0
)

# Başlangıç şiddeti
source_activity = st.sidebar.number_input(
    "source activity (arbitrary units):",
    min_value=1.0, value=100.0, step=10.0)

# Mesafe ve Kalınlık Girdileri
st.sidebar.subheader("Distances and thickness")
d1 = st.sidebar.number_input("Source -> material (d1)(cm):", min_value=1.0, value=50.0, step=1.0)
thickness_cm = st.sidebar.number_input("material thickness(cm):", min_value=0.0, value=2.0, step=0.1)
d2 = st.sidebar.number_input("material -> detector (d2)(cm):", min_value=1.0, value=50.0, step=1.0)

# --- ARA HESAPLAMALAR (xraylib ile Düzeltildi) ---
# 1. Seçim kontrolü
if not selected_elements:
    st.warning("Please select at least one shielding material element from the sidebar.")
    st.stop()

# 2. Lineer Zayıflatma Katsayısını (μ) ve ETKİLEŞİM TÜRLERİNİ Hesaplama
element_densities = []
element_mu_rhos_photo = []
element_mu_rhos_compton = []
element_mu_rhos_rayleigh = []
element_mu_rhos_pair = []

for el_string in selected_elements:
    atomic_number = int(el_string.split(" - ")[0])
    
    # 1. Gerekli sabitleri al
    density = periodictable.elements[atomic_number].density
    element_densities.append(density)
    
    # 2. KÜTLE ZAYIFLATMA KATSAYILARINI (cm²/g) xraylib'den al
    # xraylib enerji birimi olarak keV kullanır
    
    # Fotoelektrik (cm²/g)
    mu_rho_photo = xraylib.CS_Photo(atomic_number, energy_input_kev)
    element_mu_rhos_photo.append(mu_rho_photo)
    
    # Compton (inkoherent) saçılma (cm²/g)
    # HATA DÜZELTMESİ: Fonksiyon adı 'CS_Compt' olmalı
    mu_rho_compton = xraylib.CS_Compt(atomic_number, energy_input_kev)
    element_mu_rhos_compton.append(mu_rho_compton)
    
    # Rayleigh (koherent) saçılma (cm²/g)
    mu_rho_rayleigh = xraylib.CS_Rayl(atomic_number, energy_input_kev)
    element_mu_rhos_rayleigh.append(mu_rho_rayleigh)
    
    # Çift Oluşum (cm²/g) - 1022 keV üzerinde
    mu_rho_p = 0.0
    if energy_input_kev > 1022:
         mu_rho_p = xraylib.CS_Pair(atomic_number, energy_input_kev)
    element_mu_rhos_pair.append(mu_rho_p)


# Karışım ortalamaları
rho_mixture = np.mean(element_densities)

# Etkileşim türlerinin ortalamaları
mu_rho_photo_mixture = np.mean(element_mu_rhos_photo)
mu_rho_compton_mixture = np.mean(element_mu_rhos_compton)
mu_rho_rayleigh_mixture = np.mean(element_mu_rhos_rayleigh)
mu_rho_pair_mixture = np.mean(element_mu_rhos_pair)

# Parçaların toplamından toplam kütle katsayısını bul
total_mu_rho_components = mu_rho_photo_mixture + mu_rho_compton_mixture + mu_rho_rayleigh_mixture + mu_rho_pair_mixture
mu = total_mu_rho_components * rho_mixture # Toplam Lineer Katsayı (μ)

# Yüzdelikleri hesapla
if total_mu_rho_components > 0:
    percent_photo = (mu_rho_photo_mixture / total_mu_rho_components) * 100
    percent_compton = (mu_rho_compton_mixture / total_mu_rho_components) * 100
    percent_rayleigh = (mu_rho_rayleigh_mixture / total_mu_rho_components) * 100
    percent_pair = (mu_rho_pair_mixture / total_mu_rho_components) * 100
else:
    percent_photo, percent_compton, percent_rayleigh, percent_pair = 0, 0, 0, 0


# --- FİNAL HESAPLAMALAR (SİZİN YÖNTEMİNİZ) ---
final_intensity = None
if thickness_cm < 0.01:
    st.warning("Material thickness should be at least 0.01 cm for meaningful attenuation.")
else:
    I1 = source_activity / d1**2
    I2 = (I1 / thickness_cm**2) * np.exp(-mu * thickness_cm)
    I3 = I2 / d2**2
    final_intensity = I3

    st.subheader("Results (Based on Your Calculation Method):")
    st.write(f"Initial intensity at source: {source_activity:.5f} arbitrary units")
    st.write(f"Final intensity at detector: {final_intensity:.10f} arbitrary units")
    st.write(f"Material linear attenuation coefficient (μ): {mu:.5f} cm⁻¹")

    # --- IŞIMA TÜRÜ PASTASI (Aynı kaldı) ---
    st.markdown("---")
    st.subheader(f"📊 Dominant Interaction Types at {energy_input_kev} keV")
    
    labels = []
    sizes = []
    
    if percent_photo > 0.1:
        labels.append(f'Fotoelektrik (%{percent_photo:.1f})')
        sizes.append(percent_photo)
    if percent_compton > 0.1:
        labels.append(f'Compton Saçılması (%{percent_compton:.1f})')
        sizes.append(percent_compton)
    if percent_rayleigh > 0.1:
        labels.append(f'Rayleigh Saçılması (%{percent_rayleigh:.1f})')
        sizes.append(percent_rayleigh)
    if percent_pair > 0.1:
        labels.append(f'Çift Oluşum (%{percent_pair:.1f})')
        sizes.append(percent_pair)

    if not sizes:
        st.info("No interaction data to display for this energy.")
    else:
        col_pie, col_desc = st.columns([2, 1])
        with col_pie:
            fig_pie, ax_pie = plt.subplots()
            ax_pie.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, pctdistance=0.85)
            centre_circle = plt.Circle((0,0),0.70,fc='white')
            fig_pie.gca().add_artist(centre_circle)
            ax_pie.axis('equal')
            st.pyplot(fig_pie)
        
        with col_desc:
            st.markdown("#### Etkileşim Türleri:")
            interaction_dict = {
                "Fotoelektrik": percent_photo,
                "Compton": percent_compton,
                "Rayleigh": percent_rayleigh,
                "Çift Oluşum": percent_pair
            }
            dominant_interaction = max(interaction_dict, key=interaction_dict.get)
            
            if dominant_interaction == "Fotoelektrik":
                st.success(f"**Baskın Etkileşim: Fotoelektrik** ({percent_photo:.1f}%)")
                
            elif dominant_interaction == "Compton":
                st.success(f"**Baskın Etkileşim: Compton Saçılması** ({percent_compton:.1f}%)")
                
            elif dominant_interaction == "Çift Oluşum":
                st.success(f"**Baskın Etkileşim: Çift Oluşum** ({percent_pair:.1f}%)")
                
            else:
                 st.success(f"**Baskın Etkileşim: Rayleigh Saçılması** ({percent_rayleigh:.1f}%)")
                 


# --- GRAFİKSEL GÖSTERİM (Aynı kaldı) ---
st.markdown("---")
st.subheader("📈 Intensity Profile ")

if final_intensity is not None and d1 > 0 and d2 > 0:
    fig, ax = plt.subplots(figsize=(10, 6))

    # BÖLÜM 1
    x_part1 = np.linspace(1, d1, 100)
    y_part1 = source_activity / x_part1**2
    ax.plot(x_part1, y_part1, color='blue', label='Step 1: Source → Shield ')

    # BÖLÜM 2
    x_part2 = np.array([d1, d1 + thickness_cm])
    y_part2 = np.array([I1, I2])
    ax.plot(x_part2, y_part2, color='red', linestyle='--', label='Step 2: Inside Shield (Net Effect)')

    # BÖLÜM 3
    x_relative = np.linspace(1, d2, 100)
    y_part3 = I2 / x_relative**2
    x_part3_absolute = (d1 + thickness_cm - 1) + x_relative
    ax.plot(x_part3_absolute, y_part3, color='green', label='Step 3: Shield → Detector ')

    # Noktalar
    ax.scatter([d1, d1 + thickness_cm, d1 + thickness_cm + d2], [I1, I2, I3],
               s=80, c=['blue', 'red', 'green'], zorder=5) 
    ax.text(d1, I1, f' I₁={I1:.2e}', verticalalignment='bottom', horizontalalignment='right')
    ax.text(d1 + thickness_cm, I2, f' I₂={I2:.2e}', verticalalignment='bottom')
    ax.text(d1 + thickness_cm + d2, I3, f' I₃={I3:.2e}', verticalalignment='bottom')

    # Grafik ayarları
    ax.set_title("Three-Step Intensity Attenuation ")
    ax.set_xlabel("Distance from Source (cm)")
    ax.set_ylabel("Intensity (arbitrary units)")
    ax.grid(True, which="both", linestyle=':')
    ax.legend()
    ax.set_yscale('log')
    
    st.pyplot(fig)
else:
    st.info("Please provide valid distance and thickness values to generate the graph.")