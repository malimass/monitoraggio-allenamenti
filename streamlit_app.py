import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Monitoraggio Allenamenti - Analisi Multi-file")

# Caricamento multiplo dei file JSON
data_files = st.file_uploader("Carica i file JSON degli allenamenti", type="json", accept_multiple_files=True)

# Lista per raccogliere i dati
data = []

# Estrazione dei dati dagli allenamenti
for file in data_files:
    try:
        obj = json.load(file)
        if isinstance(obj, dict):
            # Verifica chiave 'start_time' per identificare un file attività valido
            if 'start_time' in obj:
                data.append({
                    "Data": pd.to_datetime(obj.get("start_time")),
                    "Distanza (km)": round(obj.get("distance", 0) / 1000, 2),
                    "Durata (ore)": round(obj.get("duration", 0) / 3600, 2),
                    "Frequenza cardiaca media (bpm)": obj.get("heart_rate", {}).get("average", None),
                    "Calorie": obj.get("calories", None),
                    "Velocità media (km/h)": round((obj.get("distance", 0) / 1000) / (obj.get("duration", 1) / 3600), 2)
                })
        else:
            st.warning(f"Errore nel file {file.name}: struttura JSON non supportata.")
    except Exception as e:
        st.warning(f"Errore nel file {file.name}: {e}")

# Se ci sono dati, creare DataFrame e visualizzare grafici
if data:
    df = pd.DataFrame(data)
    df = df.sort_values("Data")

    # Filtro per data
    st.sidebar.header("Filtro per data")
    min_date = df["Data"].min()
    max_date = df["Data"].max()
    date_range = st.sidebar.date_input("Intervallo date", [min_date, max_date], min_value=min_date, max_value=max_date)

    if len(date_range) == 2:
        df = df[(df["Data"] >= pd.to_datetime(date_range[0])) & (df["Data"] <= pd.to_datetime(date_range[1]))]

    st.markdown("### Grafici di Performance")
    col1, col2 = st.columns(2)

    with col1:
        fig1, ax1 = plt.subplots()
        ax1.plot(df["Data"], df["Distanza (km)"], marker='o')
        ax1.set_title("Distanza Percorsa")
        ax1.set_ylabel("Km")
        ax1.tick_params(axis='x', rotation=45)
        st.pyplot(fig1)

        fig2, ax2 = plt.subplots()
        ax2.plot(df["Data"], df["Durata (ore)"], color='green', marker='x')
        ax2.set_title("Durata Totale")
        ax2.set_ylabel("Ore")
        ax2.tick_params(axis='x', rotation=45)
        st.pyplot(fig2)

    with col2:
        fig3, ax3 = plt.subplots()
        ax3.plot(df["Data"], df["Frequenza cardiaca media (bpm)"], color='red', marker='s')
        ax3.set_title("Frequenza Cardiaca Media")
        ax3.set_ylabel("BPM")
        ax3.tick_params(axis='x', rotation=45)
        st.pyplot(fig3)

        fig4, ax4 = plt.subplots()
        ax4.bar(df["Data"], df["Calorie"], color='orange')
        ax4.set_title("Calorie Bruciate")
        ax4.set_ylabel("kcal")
        ax4.tick_params(axis='x', rotation=45)
        st.pyplot(fig4)

    st.markdown("### Grafico Velocità Media")
    fig5, ax5 = plt.subplots()
    ax5.plot(df["Data"], df["Velocità media (km/h)"], color='purple', marker='d')
    ax5.set_ylabel("km/h")
    ax5.set_xlabel("Data")
    ax5.set_title("Velocità Media")
    ax5.tick_params(axis='x', rotation=45)
    st.pyplot(fig5)
else:
    st.info("Carica uno o più file JSON per iniziare l'analisi.")

