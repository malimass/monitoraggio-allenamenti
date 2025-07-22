# Modifica per evitare errori se non ci sono dati validi nel dataset filtrato

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime

# Funzione per convertire tempo da secondi a ore:minuti
def convert_seconds_to_hours_minutes(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return hours + minutes / 60

# Parsing dei file nella cartella "data"
@st.cache_data

def load_activities():
    data = []
    for filename in os.listdir("data"):
        if filename.endswith(".json"):
            try:
                with open(os.path.join("data", filename)) as f:
                    activity = json.load(f)
                    summary = activity.get("summary", {})
                    if not summary:
                        continue
                    date_str = summary.get("start_time", "")
                    try:
                        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    except:
                        continue
                    duration = convert_seconds_to_hours_minutes(summary.get("duration", 0))
                    distance_km = summary.get("distance", 0) / 1000  # da metri a km
                    avg_hr = summary.get("heart_rate", {}).get("average", 0)
                    calories = summary.get("calories", 0)
                    speed = summary.get("speed", {}).get("average", 0) * 3.6  # m/s a km/h

                    data.append({
                        "Data": date,
                        "Distanza (km)": distance_km,
                        "Durata (h)": duration,
                        "FC media (bpm)": avg_hr,
                        "Calorie": calories,
                        "Velocità media (km/h)": speed
                    })
            except Exception as e:
                st.warning(f"Errore nel file {filename}: {e}")
    df = pd.DataFrame(data)
    return df

# Caricamento dati
st.title("Monitoraggio Allenamenti Massimo Malivindi")
df = load_activities()

if df.empty:
    st.error("Nessun dato valido caricato. Verifica i file nella cartella 'data'.")
    st.stop()

# Filtro per date
st.sidebar.header("Filtra per data")
min_date = df["Data"].min().date()
max_date = df["Data"].max().date()
date_range = st.sidebar.date_input("Intervallo date", [min_date, max_date], min_value=min_date, max_value=max_date)

if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df = df[(df["Data"] >= start_date) & (df["Data"] <= end_date)]

if df.empty:
    st.warning("Nessuna attività trovata per l'intervallo selezionato.")
    st.stop()

# Grafici
st.subheader("Andamento Distanza Percorsa")
fig1, ax1 = plt.subplots()
ax1.plot(df["Data"], df["Distanza (km)"], marker='o')
ax1.set_xlabel("Data")
ax1.set_ylabel("Distanza (km)")
ax1.tick_params(axis='x', rotation=45)
ax1.grid(True)
st.pyplot(fig1)

st.subheader("Durata Totale (h)")
fig2, ax2 = plt.subplots()
ax2.plot(df["Data"], df["Durata (h)"], color='purple', marker='s')
ax2.set_xlabel("Data")
ax2.set_ylabel("Durata (h)")
ax2.tick_params(axis='x', rotation=45)
ax2.grid(True)
st.pyplot(fig2)

st.subheader("Frequenza Cardiaca Media")
fig3, ax3 = plt.subplots()
ax3.plot(df["Data"], df["FC media (bpm)"], color='red', marker='x')
ax3.set_xlabel("Data")
ax3.set_ylabel("FC media (bpm)")
ax3.tick_params(axis='x', rotation=45)
ax3.grid(True)
st.pyplot(fig3)

st.subheader("Calorie Bruciate")
fig4, ax4 = plt.subplots()
ax4.bar(df["Data"], df["Calorie"], color='green')
ax4.set_xlabel("Data")
ax4.set_ylabel("Calorie")
ax4.tick_params(axis='x', rotation=45)
ax4.grid(True)
st.pyplot(fig4)

st.subheader("Velocità Media (km/h)")
fig5, ax5 = plt.subplots()
ax5.plot(df["Data"], df["Velocità media (km/h)"], color='orange', marker='D')
ax5.set_xlabel("Data")
ax5.set_ylabel("Velocità media (km/h)")
ax5.tick_params(axis='x', rotation=45)
ax5.grid(True)
st.pyplot(fig5)
