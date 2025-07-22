import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime
import re

st.set_page_config(page_title="Monitoraggio Allenamenti", layout="wide")

st.title("🏃‍♂️ Dashboard Allenamenti - Massimo Malivindi")

# Funzione per convertire la durata da formato ISO 8601 a secondi
def parse_iso_duration(duration_str):
    match = re.match(r"PT(\d+(\.\d+)?)S", duration_str)
    if match:
        return float(match.group(1))
    return 0

# Caricamento file manuale
data = []
st.sidebar.header("📁 Caricamento file JSON")
uploaded_files = st.sidebar.file_uploader("Trascina qui i file JSON", type="json", accept_multiple_files=True)

if uploaded_files:
    st.sidebar.markdown("### ✅ Seleziona i file da includere")
    selected_files = []
    for uploaded_file in uploaded_files:
        include = st.sidebar.checkbox(f"{uploaded_file.name}", value=True)
        if include:
            selected_files.append(uploaded_file)

    for uploaded_file in selected_files:
        try:
            record = json.load(uploaded_file)
            exercises = record.get("exercises", [])
            for ex in exercises:
                try:
                    start_time = datetime.fromisoformat(ex["startTime"]).date()
                    duration_raw = ex.get("duration", 0)
                    distance_raw = ex.get("distance", 0)
                    calories_raw = ex.get("kiloCalories")

                    heart_data = ex.get("heartRate", {})
                    hr_raw = heart_data.get("avg")

                    # Durata
                    if isinstance(duration_raw, str) and duration_raw.startswith("PT"):
                        duration_raw = parse_iso_duration(duration_raw)
                    durata_ore = round(duration_raw / 3600, 2) if duration_raw else 0
                    distanza_km = round(distance_raw / 1000, 2)
                    velocita = round(distanza_km / durata_ore, 2) if durata_ore else 0

                    data.append({
                        "Data": start_time,
                        "Distanza (km)": distanza_km,
                        "Durata (h)": durata_ore,
                        "FC media": hr_raw,
                        "Calorie": calories_raw,
                        "Velocità media (km/h)": velocita
                    })
                except Exception as e:
                    st.warning(f"Errore nei dati dell'esercizio: {e}")
        except Exception as e:
            st.warning(f"Errore nel file caricato {uploaded_file.name}: {e}")
else:
    st.info("Carica uno o più file JSON per iniziare l'analisi degli allenamenti.")

if data:
    df = pd.DataFrame(data)
    df = df.dropna(subset=["Data"])
    df = df.sort_values("Data")

    # Filtraggio intervallo di date
    st.sidebar.header("📆 Filtra per intervallo di date")
    min_date = df["Data"].min()
    max_date = df["Data"].max()
    date_range = st.sidebar.date_input("Intervallo date", [min_date, max_date], min_value=min_date, max_value=max_date)

    if len(date_range) == 2:
        start_date, end_date = date_range
        df = df[(df["Data"] >= pd.to_datetime(start_date)) & (df["Data"] <= pd.to_datetime(end_date))]

    # Pulsanti grafici
    st.markdown("## 📊 Seleziona un grafico")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    show_all = False
    if col1.button("📅 Distanza"):
        selected_chart = "distanza"
    elif col2.button("⏱ Durata"):
        selected_chart = "durata"
    elif col3.button("❤️ FC Media"):
        selected_chart = "fc"
    elif col4.button("🔥 Calorie"):
        selected_chart = "calorie"
    elif col5.button("🚀 Velocità"):
        selected_chart = "velocita"
    elif col6.button("📈 Tutti i dati"):
        show_all = True
    else:
        selected_chart = ""

    def plot_line(y, label, color='blue'):
        fig, ax = plt.subplots()
        ax.plot(df["Data"], df[y], marker="o", color=color)
        ax.set_xlabel("Data")
        ax.set_ylabel(label)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True)
        st.pyplot(fig)

    if selected_chart == "distanza":
        plot_line("Distanza (km)", "Distanza (km)", 'blue')
    elif selected_chart == "durata":
        plot_line("Durata (h)", "Durata (h)", 'purple')
    elif selected_chart == "fc":
        plot_line("FC media", "Frequenza Cardiaca Media (bpm)", 'red')
    elif selected_chart == "calorie":
        plot_line("Calorie", "Calorie Bruciate", 'green')
    elif selected_chart == "velocita":
        plot_line("Velocità media (km/h)", "Velocità media (km/h)", 'orange')

    if show_all:
        st.markdown("### 📉 Panoramica completa")
        fig, ax = plt.subplots()
        ax.plot(df["Data"], df["Distanza (km)"], label="Distanza (km)", marker='o')
        ax.plot(df["Data"], df["Durata (h)"], label="Durata (h)", marker='s')
        ax.plot(df["Data"], df["FC media"], label="FC media", marker='^')
        ax.plot(df["Data"], df["Calorie"], label="Calorie", marker='*')
        ax.plot(df["Data"], df["Velocità media (km/h)"], label="Velocità", marker='d')
        ax.set_xlabel("Data")
        ax.set_ylabel("Valori")
        ax.legend()
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True)
        st.pyplot(fig)
else:
    st.warning("Nessun dato disponibile da visualizzare. Carica almeno un file JSON valido.")

