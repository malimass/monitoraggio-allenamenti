import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime
import re

st.title("Monitoraggio Allenamenti - Massimo Malivindi")

# Cartella contenente i file JSON esportati da Polar Flow
data_dir = "dati"

data = []

# Funzione per convertire la durata da formato ISO 8601 (es. 'PT4819.500S') a secondi
def parse_iso_duration(duration_str):
    match = re.match(r"PT(\d+(\.\d+)?)S", duration_str)
    if match:
        return float(match.group(1))
    return 0

# Verifica che la cartella esista
if os.path.exists(data_dir):
    for file in os.listdir(data_dir):
        if file.endswith(".json"):
            filepath = os.path.join(data_dir, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    record = json.load(f)
                    if isinstance(record, dict):
                        try:
                            # Supporto a formato Polar moderno
                            start_time_raw = record.get("startTime") or record.get("start_time")
                            distance_raw = record.get("distance", 0)
                            duration_raw = record.get("duration", 0)
                            calories_raw = record.get("kiloCalories") or record.get("calories")

                            heart_data = record.get("heartRate") or record.get("heart_rate") or {}
                            hr_raw = heart_data.get("avg") or heart_data.get("average")

                            # Parsing orario
                            try:
                                if isinstance(start_time_raw, str):
                                    start_time = datetime.fromisoformat(start_time_raw).date()
                                elif isinstance(start_time_raw, (int, float)):
                                    start_time = datetime.fromtimestamp(start_time_raw / 1000).date()
                                else:
                                    start_time = None
                            except Exception:
                                start_time = None

                            # Parsing durata
                            if isinstance(duration_raw, str):
                                if duration_raw.startswith("PT"):
                                    duration_raw = parse_iso_duration(duration_raw)
                                else:
                                    duration_raw = float(duration_raw.replace(",", "."))
                            elif isinstance(duration_raw, (int, float)):
                                duration_raw = float(duration_raw)
                            else:
                                duration_raw = 0

                            distanza_km = round(float(distance_raw) / 1000, 2) if distance_raw else 0
                            durata_ore = round(duration_raw / 3600, 2) if duration_raw else 0
                            velocita = round(distanza_km / durata_ore, 2) if durata_ore else 0

                            data.append({
                                "Data": start_time,
                                "Distanza (km)": distanza_km,
                                "Durata (h)": durata_ore,
                                "FC media": float(hr_raw) if hr_raw else None,
                                "Calorie": float(calories_raw) if calories_raw else None,
                                "Velocità media (km/h)": velocita
                            })
                        except Exception as e:
                            st.warning(f"Errore nel file {file}: {e}")
            except Exception as e:
                st.warning(f"Errore nell'apertura del file {file}: {e}")
else:
    st.error(f"La cartella '{data_dir}' non esiste. Creala nel repository e inserisci i file JSON dentro.")

if data:
    df = pd.DataFrame(data)
    df = df.dropna(subset=["Data"])
    df = df.sort_values("Data")

    # Selezione intervallo date
    st.sidebar.header("Filtra per data")

    if not df["Data"].isnull().all():
        min_date = df["Data"].min()
        max_date = df["Data"].max()
        try:
            date_range = st.sidebar.date_input("Intervallo date", [min_date, max_date], min_value=min_date, max_value=max_date)

            if len(date_range) == 2:
                start_date, end_date = date_range
                df = df[(df["Data"] >= pd.to_datetime(start_date)) & (df["Data"] <= pd.to_datetime(end_date))]
        except Exception as e:
            st.warning(f"Errore nella selezione delle date: {e}")
    else:
        st.warning("Non ci sono date valide nei dati. Controlla i file JSON nella cartella 'dati'.")

    # Grafici
    st.subheader("Distanza Percorsa (km)")
    fig1, ax1 = plt.subplots()
    ax1.plot(df["Data"], df["Distanza (km)"], marker="o")
    ax1.set_xlabel("Data")
    ax1.set_ylabel("Km")
    ax1.tick_params(axis='x', rotation=45)
    st.pyplot(fig1)

    st.subheader("Durata Totale (ore)")
    fig2, ax2 = plt.subplots()
    ax2.plot(df["Data"], df["Durata (h)"], marker="s", color='purple')
    ax2.set_xlabel("Data")
    ax2.set_ylabel("Ore")
    ax2.tick_params(axis='x', rotation=45)
    st.pyplot(fig2)

    st.subheader("Frequenza Cardiaca Media (bpm)")
    fig3, ax3 = plt.subplots()
    ax3.plot(df["Data"], df["FC media"], marker="^", color='red')
    ax3.set_xlabel("Data")
    ax3.set_ylabel("BPM")
    ax3.tick_params(axis='x', rotation=45)
    st.pyplot(fig3)

    st.subheader("Calorie Bruciate")
    fig4, ax4 = plt.subplots()
    ax4.bar(df["Data"], df["Calorie"], color='green')
    ax4.set_xlabel("Data")
    ax4.set_ylabel("Calorie")
    ax4.tick_params(axis='x', rotation=45)
    st.pyplot(fig4)

    st.subheader("Velocità Media (km/h)")
    fig5, ax5 = plt.subplots()
    ax5.plot(df["Data"], df["Velocità media (km/h)"], marker="d", color='orange')
    ax5.set_xlabel("Data")
    ax5.set_ylabel("Km/h")
    ax5.tick_params(axis='x', rotation=45)
    st.pyplot(fig5)
else:
    st.info("Nessun dato disponibile da visualizzare.")




