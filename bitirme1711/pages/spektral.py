import streamlit as st
import xraylib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import periodictable

# --- Sayfa Ayarları ve Başlık ---
st.set_page_config(page_title="Spectral Attenuation Calculator", layout="wide")
st.title("X-ray Attenuation Calculator (Spectral)")
st.subheader("Farklı Enerji Dağılımına Sahip Kaynak Simülasyonu")

# --- KULLANICI GİRDİLERİ (KENAR ÇUBUĞU) ---
st.sidebar.header("System Design Parameters")

# Çoklu Element Seçimi
element_list = [f"{el.number} - {el.name} ({el.symbol})" for el in periodictable.elements if el.number < 99]
selected_elements = st.sidebar.multiselect(
    "shielding material elements:",
    element_list,
    default=[element_list[81]] # 82 -> Pb (Kurşun)
)

# --- Enerji Spektrumu Ayarları ---
st.sidebar.subheader("Energy Spectrum Settings")
st.sidebar.info("Burada bir X-ışını tüpü spektrumunu simüle ediyoruz. Kaynak aktivitesi, bu aralıktaki toplam aktivitedir.")

energy_min_kev = st.sidebar.number_input("Minimum Energy (keV):", min_value=1.0, value=20.0, step=1.0)
energy_max_kev = st.sidebar.number_input("Maximum Energy (keV):", min_value=energy_min_kev + 1, value=140.0, step=1.0)
num_steps = st.sidebar.slider("Number of energy steps (calculation points):", min_value=10, max_value=500, value=100)

source_activity = st.sidebar.number_input(
    "Total source activity (arbitrary units):",
    min_value=1.0, value=100.0, step=10.0)

# --- Mesafe ve Kalınlık Girdileri (Aynı) ---
st.sidebar.subheader("Distances and thickness")
d1 = st.sidebar.number_input("Source -> material (d1)(cm):", min_value=1.0, value=50.0, step=1.0)
thickness_cm = st.sidebar.number_input("material thickness(cm):", min_value=0.0, value=2.0, step=0.1)
d2 = st.sidebar.number_input("material -> detector (d2)(cm):", min_value=1.0, value=50.0, step=1.0)

# --- ARA HESAPLAMALAR (DÜZELTİLDİ) ---
if not selected_elements:
    st.warning("Please select at least one shielding material element from the sidebar.")
    st.stop()

# 1. Enerji aralığını ve spektrumu oluştur
energies_kev = np.linspace(energy_min_kev, energy_max_kev, num_steps)
activity_per_step = source_activity / num_steps

# 2. Seçilen elementlerin Z numaralarını ve yoğunluklarını *önceden* al
selected_atomic_numbers = []
selected_densities = []
for el_string in selected_elements:
    atomic_number = int(el_string.split(" - ")[0])
    selected_atomic_numbers.append(atomic_number)
    selected_densities.append(periodictable.elements[atomic_number].density)

rho_mixture = np.mean(selected_densities)

# 3. Her bir enerji için hesaplama yapacak listeler
all_I1_E_values = []
all_I2_E_values = []
all_I3_E_values = []
# mu_values listesi kaldırıldı, çünkü artık o grafiği çizmiyoruz.

# --- HESAPLAMA DÖNGÜSÜ (DÜZELTİLDİ) ---
Total_I3 = None
if thickness_cm < 0.01:
    st.warning("Material thickness should be at least 0.01 cm for meaningful attenuation.")
else:
    for energy_kev in energies_kev:
        
        # 1. O enerji için KARIŞIMIN mu (lineer katsayı) değerini hesapla
        current_mu_rhos_for_elements = []
        for z in selected_atomic_numbers:
            mu_rho_element = xraylib.CS_Total(z, energy_kev)
            current_mu_rhos_for_elements.append(mu_rho_element)
        
        mu_rho_mixture = np.mean(current_mu_rhos_for_elements)
        mu = mu_rho_mixture * rho_mixture 
        
        # 2. Sizin 3 adımlı modelinizi o enerjiye uygula
        I1_E = (activity_per_step) / d1**2
        I2_E = (I1_E / thickness_cm**2) * np.exp(-mu * thickness_cm)
        I3_E = I2_E / d2**2
        
        # 3. Sonuçları listelere ekle
        all_I1_E_values.append(I1_E)
        all_I2_E_values.append(I2_E)
        all_I3_E_values.append(I3_E)

    # 3. Tüm enerjilerin toplam sonuçlarını hesapla
    Total_I1 = np.sum(all_I1_E_values)
    Total_I2 = np.sum(all_I2_E_values)
    Total_I3 = np.sum(all_I3_E_values)
    
    st.subheader("Results :")
    st.metric(label="Total Final Intensity at Detector (Sum of all energies)", value=f"{Total_I3:.10f} arbitrary units")
    st.write(f"(Total input activity was {source_activity})")

    # --- GRAFİKSEL GÖSTERİM (DEĞİŞTİRİLDİ) ---
    st.markdown("---")
    st.subheader("📈 Total Intensity Profile (Sum of all energies)")
    st.write("Bu grafik, tüm spektrumun **toplam** şiddetinin yol boyunca nasıl azaldığını gösterir.")

    if Total_I3 is not None and d1 > 0 and d2 > 0:
        fig, ax = plt.subplots(figsize=(10, 6))

        # BÖLÜM 1: Kaynaktan zırha (Toplam aktiviteye dayalı TKY)
        x_part1 = np.linspace(1, d1, 100) 
        y_part1 = source_activity / x_part1**2 
        ax.plot(x_part1, y_part1, color='blue', label='Step 1: Source → Shield ')

        # BÖLÜM 2: Zırh içi (Toplam I1 ve Toplam I2 noktalarını birleştirir)
        x_part2 = np.array([d1, d1 + thickness_cm])
        y_part2 = np.array([Total_I1, Total_I2])
        ax.plot(x_part2, y_part2, color='red', linestyle='--', label='Step 2: Inside Shield (Net Effect)')

        # BÖLÜM 3: Zırhtan dedektöre (Toplam I2'den başlayan TKY)
        x_relative = np.linspace(1, d2, 100)
        y_part3 = Total_I2 / x_relative**2
        x_part3_absolute = (d1 + thickness_cm - 1) + x_relative
        ax.plot(x_part3_absolute, y_part3, color='green', label='Step 3: Shield → Detector ')

        # Noktalar
        ax.scatter([d1, d1 + thickness_cm, d1 + thickness_cm + d2], [Total_I1, Total_I2, Total_I3],
                   s=80, c=['blue', 'red', 'green'], zorder=5) 
        ax.text(d1, Total_I1, f' I₁_Total={Total_I1:.2e}', verticalalignment='bottom', horizontalalignment='right')
        ax.text(d1 + thickness_cm, Total_I2, f' I₂_Total={Total_I2:.2e}', verticalalignment='bottom')
        ax.text(d1 + thickness_cm + d2, Total_I3, f' I₃_Total={Total_I3:.2e}', verticalalignment='bottom')

        # Grafik ayarları
        ax.set_title("Three-Step Total Intensity Profile")
        ax.set_xlabel("Distance from Source (cm)")
        ax.set_ylabel("Total Intensity (arbitrary units)")
        ax.grid(True, which="both", linestyle=':')
        ax.legend()
        ax.set_yscale('log')
        
        st.pyplot(fig)
    else:
        st.info("Please provide valid distance and thickness values to generate the graph.")