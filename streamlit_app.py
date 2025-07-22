import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

st.set_page_config(layout="wide")

st.title("Monitoraggio Allenamenti – Massimo Malivindi")

# Caricamento multiplo dei file JSON
uploaded_files = st.file_uploader("Carica i file JSON degli allenamenti:", accept_multiple_files=True, type="json")

# Lista per contenere i dati
data = []

# Parsing dei file
for file in uploaded_files:
    try:
        content = json.load(file)

        if isinstance(content, dict):
            if "start_time" in content and "distance" in content:
                # File valido di allenamento
                data.append({
                    "Data": pd.to_datetime(content["start_time"]).date(),
                    "Distanza (km)": round(content.get("distance", 0) / 1000, 2),
                    "Durata (h)": round(content.get("duration", 0) / 3600, 2),
                    "FC media": content.get("heart_rate", {}).get("average", 0),
                    "Calorie": content.get("calories", 0),
                    "Velocità media (km/h)": round((content.get("distance", 0) / 1000) / (content.get("duration", 1) / 3600), 2)
                })
        else:
            st.warning(f"Errore nel file {file.name}: struttura JSON non supportata.")

    except Exception as e:
        st.warning(f"Errore nel file {file.name}: {str(e)}")

# Se ci sono dati validi
if data:
    df = pd.DataFrame(data)
    df = df.sort_values("Data")

    # Filtro data
    st.sidebar.header("Filtro per intervallo di date")
    min_date = df["Data"].min()
    max_date = df["Data"].max()
    date_range = st.sidebar.date_input("Intervallo date", [min_date, max_date], min_value=min_date, max_value=max_date)

    if len(date_range) == 2:
        start, end = date_range
        df = df[(df["Data"] >= start) & (df["Data"] <= end)]

    # Grafici
    st.subheader("Grafici di andamento allenamenti")
    col1, col2 = st.columns(2)
    
    with col1:
        fig, ax = plt.subplots()
        ax.plot(df["Data"], df["Distanza (km)"], marker='o')
        ax.set_title("Distanza percorsa")
        ax.set_ylabel("Km")
        ax.set_xlabel("Data")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots()
        ax.plot(df["Data"], df["Durata (h)"], marker='s', color='purple')
        ax.set_title("Durata allenamento")
        ax.set_ylabel("Ore")
        ax.set_xlabel("Data")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

    col3, col4 = st.columns(2)

    with col3:
        fig, ax = plt.subplots()
        ax.plot(df["Data"], df["FC media"], marker='x', color='orange')
        ax.set_title("Frequenza Cardiaca Media")
        ax.set_ylabel("BPM")
        ax.set_xlabel("Data")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

    with col4:
        fig, ax = plt.subplots()
        ax.bar(df["Data"], df["Calorie"], color='green')
        ax.set_title("Calorie Bruciate")
        ax.set_ylabel("Kcal")
        ax.set_xlabel("Data")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

    fig, ax = plt.subplots()
    ax.plot(df["Data"], df["Velocità media (km/h)"], marker='^', color='red')
    ax.set_title("Velocità Media")
    ax.set_ylabel("Km/h")
    ax.set_xlabel("Data")
    ax.tick_params(axis='x', rotation=45)
    st.pyplot(fig)

else:
    st.info("Carica file validi di attività per visualizzare i grafici.")

