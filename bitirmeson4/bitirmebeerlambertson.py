import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

veriler = pd.read_excel("/mount/src/deneme/bitirmedenemesi2/denemeverilerifoton.xlsx", engine="openpyxl")


maddeler = veriler["Element/Compound"].unique()
matter_choose = st.selectbox("Madde seçiniz", maddeler)

enerjiler = veriler[veriler["Element/Compound"] == matter_choose]["PhotonEnergy/MeV"].unique()
Energy_choose = st.selectbox("Enerji (MeV) seçiniz", enerjiler)

x = st.number_input("Kalınlığı giriniz (cm)", min_value=0.0, step=0.1)
mesafe = st.number_input("Mesafe giriniz (cm)", min_value=0.0, step=0.1)

if st.button("Hesapla"):
    mu = veriler[
        (veriler["Element/Compound"] == matter_choose) &
        (veriler["PhotonEnergy/MeV"] == Energy_choose)
    ]["Linear absorbion coefficientcm-1"].values[0]

    I0 = 100
    
    # Doz–mesafe
    I_mesafe = I0 / (mesafe**2)
    # Beer–Lambert
    I_final = I_mesafe * np.exp(-mu * x)

    st.success(f"100 birimden kalan: {I_final}")

    # ----------------------------
    # Grafik 1: Doz–Mesafe Yasası
    # ----------------------------
    mesafe_deger = np.linspace(1, mesafe, 100)
    I_r = I0 / (mesafe_deger**2)

    fig1, ax1 = plt.subplots()
    ax1.plot(mesafe_deger, I_r, color="blue")
    ax1.set_xlabel("Mesafe (cm)")
    ax1.set_ylabel("Işın Şiddeti (I)")
    ax1.set_title("Doz–Mesafe Yasası (Inverse Square Law)")
    ax1.grid(True)
    st.pyplot(fig1)

    # ----------------------------
    # Grafik 2: Beer–Lambert Yasası
    # ----------------------------
    thickness = np.linspace(0, x, 100)
    I_material = I_mesafe * np.exp(-mu * thickness)

    fig2, ax2 = plt.subplots()
    ax2.plot(thickness, I_material, color="red")
    ax2.set_xlabel("Kalınlık (cm)")
    ax2.set_ylabel("Işın Şiddeti (I)")
    ax2.set_title(f"Beer–Lambert Yasası ({matter_choose}, {Energy_choose} MeV)")
    ax2.grid(True)
    st.pyplot(fig2)

    # ----------------------------
    # Grafik 3: Birleşik
    # ----------------------------
    fig3, ax3 = plt.subplots()
    ax3.plot(mesafe_deger, I_r, label="Doz–Mesafe Yasası", color="blue")
    ax3.plot(mesafe + thickness, I_material, 
             label=f"Beer–Lambert ({matter_choose}, {Energy_choose} MeV)", color="red")
    ax3.set_xlabel("Mesafe (cm)")
    ax3.set_ylabel("Işın Şiddeti (I)")
    ax3.set_title("Doz–Mesafe + Beer–Lambert Birleşimi")
    ax3.legend()
    ax3.grid(True)

    st.pyplot(fig3)

