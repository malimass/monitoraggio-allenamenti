import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime

st.title("Monitoraggio Allenamenti - Massimo Malivindi")

# Cartella contenente i file JSON esportati da Polar Flow
data_dir = "dati"

data = []

# Verifica che la cartella esista
if os.path.exists(data_dir):
    for file in os.listdir(data_dir):
        if file.endswith(".json"):
            filepath = os.path.join(data_dir, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    record = json.load(f)
                    if isinstance(record, dict):
                        # Estrai i dati chiave
                        data.append({
                            "Data": datetime.fromtimestamp(record.get("start_time", 0)/1000).date() if record.get("start_time") else None,
                            "Distanza (km)": round(record.get("distance", 0)/1000, 2),
                            "Durata (h)": round(record.get("duration", 0)/3600, 2),
                            "FC media": record.get("heart_rate", {}).get("average", None),
                            "Calorie": record.get("calories", None),
                            "Velocità media (km/h)": round((record.get("distance", 0)/1000) / (record.get("duration", 1)/3600), 2) if record.get("duration") else None
                        })
            except Exception as e:
                st.warning(f"Errore nel file {file}: {e}")
else:
    st.error(f"La cartella '{data_dir}' non esiste. Creala nel repository e inserisci i file JSON dentro.")

if data:
    df = pd.DataFrame(data)
    df = df.dropna(subset=["Data"])
    df = df.sort_values("Data")

    # Selezione intervallo date
    st.sidebar.header("Filtra per data")
    min_date = df["Data"].min()
    max_date = df["Data"].max()
    date_range = st.sidebar.date_input("Intervallo date", [min_date, max_date], min_value=min_date, max_value=max_date)

    if len(date_range) == 2:
        start_date, end_date = date_range
        df = df[(df["Data"] >= start_date) & (df["Data"] <= end_date)]

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



