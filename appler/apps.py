import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import math
dataset = {
    "Su": {
        "yoğunluk": 1.0,   # g/cm^3
        "enerjiler": {
            1.0: {"mu": 0.0707},   # 1 MeV
            5.0: {"mu": 0.032}     # 5 MeV
        }
    },
    "Kurşun": {
        "yoğunluk": 11.34,
        "enerjiler": {
            1.0: {"mu": 0.698},
            5.0: {"mu": 0.486}
        }
    },
    "Alüminyum": {
        "yoğunluk": 2.70,
        "enerjiler": {
            1.0: {"mu": 0.166},
            5.0: {"mu": 0.089}
        }
    },
    "Demir": {
        "yoğunluk": 7.87,
        "enerjiler": {
            1.0: {"mu": 0.571},
            5.0: {"mu": 0.410}
        }
    },
    "Karbon": {
        "yoğunluk": 2.26,
        "enerjiler": {
            1.0: {"mu": 0.095},
            5.0: {"mu": 0.048}
        }
    }
}
matter = "Su"
phoenergy = 5.0
mu = dataset[matter]["enerjiler"][phoenergy]["mu"]
print(mu)

matter_choose = st.selectbox("Madde seçiniz", list(dataset.keys()))

Energy_choose = st.selectbox(
    "Enerji (MeV) seçiniz",
    list(dataset[matter_choose]["enerjiler"].keys())
)
x = st.number_input("Kalınlığı giriniz (cm)", min_value=0.0, step=0.1)
mu = dataset[matter_choose]["enerjiler"][Energy_choose]["mu"]
rho = dataset[matter_choose]["yoğunluk"]

I0 = 100  # Başlangıç ışınım şiddeti
I = I0 * np.exp(-mu * x)
transmission_ratio = (I / I0) * 100

st.write(f"**Seçilen madde:** {matter_choose}")
st.write(f"**Yoğunluk:** {rho} g/cm³")
st.write(f"**Enerji:** {Energy_choose} MeV")
st.write(f"**Lineer soğurma katsayısı (μ):** {mu} cm⁻¹")
st.write(f"**Kalınlık:** {x} cm")
st.success(f"Geçen ışın yoğunluğu: {I} (Başlangıç {I0} birimden)")
st.success(f"Geçen oran: %{transmission_ratio}")


st.subheader("Beer–Lambert simülasyonu")

x_vals = np.linspace(0, x, 200)  # 0–50 cm arası örnek
I_vals = I0 * np.exp(-mu * x_vals)

fig, ax = plt.subplots()
ax.plot(x_vals, I_vals, label=f"{matter_choose}, {Energy_choose} MeV")
ax.set_xlabel("Kalınlık (cm)")
ax.set_ylabel("Işın Yoğunluğu (I)")
ax.set_title("Beer–Lambert Yasası")
ax.legend()
ax.grid(True)

st.pyplot(fig)