import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

st.title("Analisi Allenamenti - Caricamento Multiplo JSON")

uploaded_files = st.file_uploader("Carica i file JSON degli allenamenti", type="json", accept_multiple_files=True)

if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        try:
            content = json.load(uploaded_file)
            summary = content.get("summary", {})
            samples = content.get("samples", {})

            data_attivita = datetime.strptime(content.get("start_time", ""), "%Y-%m-%dT%H:%M:%S.%fZ")
            distanza_km = summary.get("distance", 0.0) / 1000
            durata_sec = summary.get("duration", 0.0)
            durata_ore = durata_sec / 3600
            calorie = summary.get("calories", 0.0)
            fc_media = summary.get("avg_hr", 0.0)
            velocita_media_kmh = (distanza_km / durata_sec) * 3600 if durata_sec > 0 else 0

            all_data.append({
                "Data": data_attivita,
                "Distanza (km)": round(distanza_km, 2),
                "Durata (h)": round(durata_ore, 2),
                "Frequenza Cardiaca Media (bpm)": fc_media,
                "Calorie": calorie,
                "Velocità Media (km/h)": round(velocita_media_kmh, 2)
            })
        except Exception as e:
            st.error(f"Errore nel file {uploaded_file.name}: {e}")

    df = pd.DataFrame(all_data)
    df = df.sort_values("Data")

    st.subheader("Tabella riepilogativa")
    st.dataframe(df)

    # Grafici
    def plot_line_chart(x, y, ylabel):
        fig, ax = plt.subplots()
        ax.plot(x, y, marker='o')
        ax.set_xlabel("Data")
        ax.set_ylabel(ylabel)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True)
        st.pyplot(fig)

    st.subheader("Andamento della Distanza")
    plot_line_chart(df["Data"], df["Distanza (km)"], "Distanza (km)")

    st.subheader("Andamento della Durata Totale (ore)")
    plot_line_chart(df["Data"], df["Durata (h)"], "Durata (h)")

    st.subheader("Andamento della Frequenza Cardiaca Media")
    plot_line_chart(df["Data"], df["Frequenza Cardiaca Media (bpm)"], "FC Media (bpm)")

    st.subheader("Andamento delle Calorie Bruciate")
    plot_line_chart(df["Data"], df["Calorie"], "Calorie")

    st.subheader("Andamento della Velocità Media")
    plot_line_chart(df["Data"], df["Velocità Media (km/h)"], "Velocità Media (km/h)")

