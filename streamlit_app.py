import streamlit as st
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
from datetime import datetime

st.title("Analisi Avanzata Allenamenti – Massimo Malivindi")

# Selezione cartella contenente i file JSON
st.sidebar.header("Carica i file JSON degli allenamenti")
uploaded_files = st.sidebar.file_uploader("Seleziona i file JSON", accept_multiple_files=True, type="json")

# Contenitori per dati aggregati
data_totale = {
    "Data": [],
    "Durata (min)": [],
    "METs medi": [],
    "Passi totali": [],
    "Calorie totali": []
}

# Elaborazione di ciascun file JSON
for uploaded_file in uploaded_files:
    content = json.load(uploaded_file)
    samples = content.get("samples", [])

    if not samples:
        continue

    # Dati temporanei per ogni allenamento
    durata = len(samples)
    met_tot = sum(s.get("mets", 0) for s in samples)
    passi_tot = sum(s.get("steps", 0) for s in samples)
    cal_tot = samples[-1].get("caloriesCumulative", 0)

    # Estrazione data da filename o da file
    try:
        raw_name = uploaded_file.name
        date_str = raw_name.split("-")[1:4]  # ['2017', '01', '01']
        data_str = "-".join(date_str)
        data_obj = datetime.strptime(data_str, "%Y-%m-%d")
    except:
        data_obj = datetime.today()

    # Inserimento nei dati totali
    data_totale["Data"].append(data_obj)
    data_totale["Durata (min)"].append(durata)
    data_totale["METs medi"].append(round(met_tot / durata, 2))
    data_totale["Passi totali"].append(passi_tot)
    data_totale["Calorie totali"].append(cal_tot)

# Creazione DataFrame
if data_totale["Data"]:
    df = pd.DataFrame(data_totale)
    df = df.sort_values("Data")

    # Selettore di intervallo
    st.sidebar.header("Filtra per data")
    min_date = df["Data"].min()
    max_date = df["Data"].max()
    date_range = st.sidebar.date_input("Intervallo date", [min_date, max_date], min_value=min_date, max_value=max_date)

    if len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        df = df[(df["Data"] >= start_date) & (df["Data"] <= end_date)]

    # Grafico METs
    st.subheader("METs medi giornalieri")
    fig1, ax1 = plt.subplots()
    ax1.plot(df["Data"], df["METs medi"], marker='o', color='purple')
    ax1.set_ylabel("METs")
    ax1.set_xlabel("Data")
    ax1.grid(True)
    st.pyplot(fig1)

    # Grafico Passi
    st.subheader("Passi Totali per Allenamento")
    fig2, ax2 = plt.subplots()
    ax2.bar(df["Data"], df["Passi totali"], color='teal')
    ax2.set_ylabel("Passi")
    ax2.set_xlabel("Data")
    ax2.tick_params(axis='x', rotation=45)
    st.pyplot(fig2)

    # Grafico Calorie
    st.subheader("Calorie Totali per Allenamento")
    fig3, ax3 = plt.subplots()
    ax3.plot(df["Data"], df["Calorie totali"], marker='s', color='darkred')
    ax3.set_ylabel("Calorie")
    ax3.set_xlabel("Data")
    ax3.grid(True)
    st.pyplot(fig3)
else:
    st.warning("Carica almeno un file JSON per visualizzare i dati.")
