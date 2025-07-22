import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import json

st.title("Analisi Allenamenti - Caricamento File JSON")

uploaded_files = st.file_uploader("Carica i file JSON degli allenamenti", type="json", accept_multiple_files=True)

if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        try:
            content = json.load(uploaded_file)

            if "summary" in content:
                s = content["summary"]
                record = {
                    "Data": content.get("start_time", ""),
                    "Distanza (km)": s.get("distance", 0) / 1000,  # metri in km
                    "Durata (min)": s.get("duration", 0) / 60,     # secondi in minuti
                    "FC media": s.get("avg_heart_rate", None),
                    "Calorie": s.get("energy", None),
                }
                all_data.append(record)
        except Exception as e:
            st.error(f"Errore nel file {uploaded_file.name}: {e}")

    if all_data:
        df = pd.DataFrame(all_data)
        df["Data"] = pd.to_datetime(df["Data"])
        df = df.sort_values("Data")

        # Selezione intervallo
        st.sidebar.header("Filtra per data")
        min_date = df["Data"].min()
        max_date = df["Data"].max()
        date_range = st.sidebar.date_input("Seleziona intervallo", [min_date, max_date], min_value=min_date, max_value=max_date)

        if len(date_range) == 2:
            start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            df = df[(df["Data"] >= start) & (df["Data"] <= end)]

        st.subheader("Grafico Distanza (km)")
        fig1, ax1 = plt.subplots()
        ax1.plot(df["Data"], df["Distanza (km)"], marker='o')
        ax1.set_ylabel("Distanza (km)")
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True)
        st.pyplot(fig1)

        st.subheader("Grafico Frequenza Cardiaca Media")
        fig2, ax2 = plt.subplots()
        ax2.plot(df["Data"], df["FC media"], marker='x', color='orange')
        ax2.set_ylabel("FC Media (bpm)")
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True)
        st.pyplot(fig2)

        st.subheader("Grafico Calorie")
        fig3, ax3 = plt.subplots()
        ax3.bar(df["Data"], df["Calorie"], color='green')
        ax3.set_ylabel("Calorie")
        ax3.tick_params(axis='x', rotation=45)
        st.pyplot(fig3)

        st.success("Analisi completata con successo.")

