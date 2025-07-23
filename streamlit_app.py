import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Inserisci qui i tuoi dati (puoi anche leggerli da un file CSV)
data = {
    "Data": ["8-lug", "10-lug", "11-lug", "13-lug", "15-lug-A", "15-lug-B", "17-lug", "20-lug", "21-lug", "22-lug", "23-lug"],
    "Distanza_km": [18.79, 7.18, 8.41, 20.04, 20.04, 18.39, 12.34, 22.69, 7.54, 16.37, 9.41],
    "Durata_min": [180, 82, 82, 251, 251, 204, 127, 257, 80, 187, 77],
    "FC_media": [112, 112, 118, 112, 112, 90, 103, 122, 110, 91, 125],
    "FC_max": [155, 126, 146, 159, 159, 124, 115, 156, 138, 99, 162],
    "Vel_media": [6.2, 5.2, 6.1, 4.7, 4.7, 5.4, 5.8, 5.3, 5.6, 5.2, 7.3],
    "Vel_max": [19.0, 7.5, 9.9, 12.5, 12.5, 12.7, 8.9, 9.2, 9.3, 11.8, 11.1],
    "Calorie": [1686, 750, 814, 2320, 2320, 1552, 1016, 2668, 722, 1377, 823],
    "Dislivello": [470, 215, 255, 300, 300, 385, 165, 536, 180, 255, 340]
}

df = pd.DataFrame(data)

# Conversione della colonna Data in formato stringa ordinabile
st.title("Andamento Allenamenti Luglio 2025")

# Imposta il grafico
fig, ax = plt.subplots(figsize=(14, 8))

# Traccia le linee
ax.plot(df["Data"], df["Distanza_km"], label="Distanza (km)", marker='o')
ax.plot(df["Data"], df["Durata_min"], label="Durata (min)", marker='o')
ax.plot(df["Data"], df["FC_media"], label="FC Media", marker='o')
ax.plot(df["Data"], df["FC_max"], label="FC Massima", marker='o')
ax.plot(df["Data"], df["Vel_media"], label="Vel. Media", marker='o')
ax.plot(df["Data"], df["Vel_max"], label="Vel. Massima", marker='o')
ax.plot(df["Data"], df["Calorie"], label="Calorie", marker='o')
ax.plot(df["Data"], df["Dislivello"], label="Dislivello Positivo (m)", marker='o')

# Personalizza il grafico
ax.set_xlabel("Data Allenamento")
ax.set_ylabel("Valore")
ax.set_title("Grafico Riassuntivo delle Metriche di Allenamento")
ax.grid(True)
plt.xticks(rotation=45)
ax.legend()

st.pyplot(fig)



