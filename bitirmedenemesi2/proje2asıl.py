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

if st.button("Hesapla"):
    mu = veriler[
        (veriler["Element/Compound"] == matter_choose) &
        (veriler["PhotonEnergy/MeV"] == Energy_choose)
    ]["Linear absorbion coefficientcm-1"].values[0]

    I0 = 100
    I = I0 * np.exp(-mu * x)

    st.success(f"100 birimden kalan: {I}")

        # Grafik için veriler
    thickness = np.linspace(0, x, 100)
    intensity = I0 * np.exp(-mu * thickness)

    fig, ax = plt.subplots()
    ax.plot(thickness, intensity, label=f"{matter_choose}, {Energy_choose} MeV")
    ax.set_xlabel("Kalınlık (cm)")
    ax.set_ylabel("Işın Şiddeti (I)")
    ax.set_title("Beer–Lambert Yasası")
    ax.legend()
    ax.grid(True)


    st.pyplot(fig)

