import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime

st.set_page_config(page_title="Monitoraggio Allenamenti", layout="wide")
st.title("Monitoraggio Allenamenti Massimo Malivindi")

# Funzione per caricare ed estrarre dati validi dai file JSON
def estrai_dati_json(path):
    try:
        with open(path, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                record = {
                    "Data": pd.to_datetime(data.get("start_time", data.get("date", ""))),
                    "Distanza (km)": float(data.get("distance", 0)) / 1000 if "distance" in data else 0,
                    "Durata (ore)": float(data.get("duration", 0)) / 3600 if "duration" in data else 0,
                    "FC media": data.get("heart_rate", {}).get("average", None),
                    "Calorie": data.get("calories", None),
                    "Velocita media (km/h)": float(data.get("speed", {}).get("average", 0)) * 3.6
                }
                return record
    except Exception as e:
        st.warning(f"Errore nel file {path}: {e}")
    return None

# Cartella contenente i file JSON
cartella_file = "data"

dati = []
for file in os.listdir(cartella_file):
    if file.endswith(".json"):
        risultato = estrai_dati_json(os.path.join(cartella_file, file))
        if risultato:
            dati.append(risultato)

# Se non ci sono dati validi
if not dati:
    st.error("Nessun file valido trovato nella cartella 'data'.")
    st.stop()

# Creazione del DataFrame
columns = ["Data", "Distanza (km)", "Durata (ore)", "FC media", "Calorie", "Velocita media (km/h)"]
df = pd.DataFrame(dati, columns=columns)
df = df.dropna(subset=["Data"])
df = df.sort_values("Data")

# Filtro per data
st.sidebar.header("Filtra per data")
min_date = df["Data"].min().date()
max_date = df["Data"].max().date()
date_range = st.sidebar.date_input("Intervallo date", [min_date, max_date], min_value=min_date, max_value=max_date)

if len(date_range) == 2:
    df = df[(df["Data"] >= pd.to_datetime(date_range[0])) & (df["Data"] <= pd.to_datetime(date_range[1]))]

# Grafici
st.subheader("Andamento della Distanza Percorsa")
fig1, ax1 = plt.subplots()
ax1.plot(df["Data"], df["Distanza (km)"], marker='o')
ax1.set_ylabel("Distanza (km)")
ax1.tick_params(axis='x', rotation=45)
ax1.grid(True)
st.pyplot(fig1)

st.subheader("Durata Totale Allenamento (ore)")
fig2, ax2 = plt.subplots()
ax2.plot(df["Data"], df["Durata (ore)"], marker='o', color='purple')
ax2.set_ylabel("Durata (ore)")
ax2.tick_params(axis='x', rotation=45)
ax2.grid(True)
st.pyplot(fig2)

st.subheader("Frequenza Cardiaca Media")
fig3, ax3 = plt.subplots()
ax3.plot(df["Data"], df["FC media"], marker='x', color='red')
ax3.set_ylabel("FC media (bpm)")
ax3.tick_params(axis='x', rotation=45)
ax3.grid(True)
st.pyplot(fig3)

st.subheader("Calorie Bruciate")
fig4, ax4 = plt.subplots()
ax4.bar(df["Data"], df["Calorie"], color='green')
ax4.set_ylabel("Calorie")
ax4.tick_params(axis='x', rotation=45)
st.pyplot(fig4)

st.subheader("Velocita Media (km/h)")
fig5, ax5 = plt.subplots()
ax5.plot(df["Data"], df["Velocita media (km/h)"], marker='d', color='blue')
ax5.set_ylabel("Velocita media (km/h)")
ax5.tick_params(axis='x', rotation=45)
ax5.grid(True)
st.pyplot(fig5)


