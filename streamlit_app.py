import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import json

st.set_page_config(layout="wide")
st.title("Monitoraggio Allenamenti Massimo Malivindi")

# Cartella contenente i file JSON esportati
FOLDER_PATH = "./data"

# Funzione per estrarre dati dai file JSON di attività compatibili
def extract_data_from_json(file_path):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                summary = data.get("summary", {})
                record = {
                    "Data": pd.to_datetime(summary.get("start_time", "")),
                    "Distanza (km)": round(summary.get("distance", 0) / 1000, 2),
                    "Durata (ore)": round(summary.get("duration", 0) / 3600, 2),
                    "FC media": summary.get("heart_rate", {}).get("average", 0),
                    "Calorie": summary.get("calories", 0),
                    "Velocità media (km/h)": round((summary.get("distance", 0) / 1000) / (summary.get("duration", 0) / 3600), 2) if summary.get("duration", 0) > 0 else 0
                }
                return record
    except Exception as e:
        st.warning(f"Errore nel file {file_path}: {e}")
    return None

# Lettura dei file JSON
records = []
for filename in os.listdir(FOLDER_PATH):
    if filename.endswith(".json"):
        path = os.path.join(FOLDER_PATH, filename)
        record = extract_data_from_json(path)
        if record:
            records.append(record)

# Creazione DataFrame
if records:
    df = pd.DataFrame(records)
    df = df.sort_values("Data")

    # Filtro per data
    st.sidebar.header("Filtro per data")
    min_date = df["Data"].min().date()
    max_date = df["Data"].max().date()
    date_range = st.sidebar.date_input("Intervallo date", [min_date, max_date], min_value=min_date, max_value=max_date)

    if len(date_range) == 2:
        df = df[(df["Data"] >= pd.to_datetime(date_range[0])) & (df["Data"] <= pd.to_datetime(date_range[1]))]

    # Visualizza grafici
    st.subheader("Grafici di allenamento")
    col1, col2 = st.columns(2)

    with col1:
        fig1, ax1 = plt.subplots()
        ax1.plot(df["Data"], df["Distanza (km)"], marker='o')
        ax1.set_title("Distanza Percorsa")
        ax1.set_xlabel("Data")
        ax1.set_ylabel("Km")
        ax1.tick_params(axis='x', rotation=45)
        st.pyplot(fig1)

        fig2, ax2 = plt.subplots()
        ax2.plot(df["Data"], df["FC media"], color='orange', marker='x')
        ax2.set_title("Frequenza Cardiaca Media")
        ax2.set_xlabel("Data")
        ax2.set_ylabel("BPM")
        ax2.tick_params(axis='x', rotation=45)
        st.pyplot(fig2)

    with col2:
        fig3, ax3 = plt.subplots()
        ax3.plot(df["Data"], df["Durata (ore)"], marker='s', linestyle='--', color='purple')
        ax3.set_title("Durata Allenamento")
        ax3.set_xlabel("Data")
        ax3.set_ylabel("Ore")
        ax3.tick_params(axis='x', rotation=45)
        st.pyplot(fig3)

        fig4, ax4 = plt.subplots()
        ax4.bar(df["Data"], df["Calorie"], color='green')
        ax4.set_title("Calorie Bruciate")
        ax4.set_xlabel("Data")
        ax4.set_ylabel("kcal")
        ax4.tick_params(axis='x', rotation=45)
        st.pyplot(fig4)

    st.subheader("Velocità media")
    fig5, ax5 = plt.subplots()
    ax5.plot(df["Data"], df["Velocità media (km/h)"], marker='^', color='red')
    ax5.set_title("Velocità media")
    ax5.set_xlabel("Data")
    ax5.set_ylabel("Km/h")
    ax5.tick_params(axis='x', rotation=45)
    st.pyplot(fig5)
else:
    st.error("Nessun file valido trovato nella cartella 'data'. Assicurati che contenga file .json esportati da Polar Flow.")
