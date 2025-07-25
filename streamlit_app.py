# app_coach_ai.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import isodate
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

# ------------------ Autenticazione Utente ------------------
def login_form():
    st.sidebar.title("🔐 Login Utente")
    username = st.sidebar.text_input("Nome utente")
    password = st.sidebar.text_input("Password", type="password")
    login = st.sidebar.button("Login")

    if login:
        if username and password:
            st.session_state.user_id = username
            st.sidebar.success(f"Benvenuto, {username}!")
            return True
        else:
            st.sidebar.error("Inserisci nome utente e password")
            return False

    if "user_id" in st.session_state:
        st.sidebar.success(f"Autenticato come {st.session_state.user_id}")
        return True

    return False

# ------------------ Inserimento Manuale Dati ------------------
def inserisci_dati_manuali():
    st.subheader("📝 Inserisci i tuoi dati di allenamento")
    with st.form("dati_allenamento"):
        data = st.date_input("Data dell'allenamento", value=datetime.date.today())
        peso = st.number_input("Peso corporeo (kg)", min_value=30.0, max_value=200.0, step=0.1)
        durata = st.number_input("Durata (min)", min_value=1.0)
        distanza = st.number_input("Distanza (km)", min_value=0.0)
        fc_media = st.number_input("Frequenza Cardiaca Media (bpm)", min_value=30, max_value=220)
        fc_max = st.number_input("Frequenza Cardiaca Massima (bpm)", min_value=30, max_value=240)
        vel_media = st.number_input("Velocità Media (km/h)", min_value=1.0, max_value=30.0)
        calorie = st.number_input("Calorie bruciate", min_value=0)

        inviato = st.form_submit_button("Aggiungi allenamento")

    if inviato:
        if not all([durata, distanza, fc_media, fc_max, vel_media, calorie]):
            st.error("❌ Tutti i campi sono obbligatori.")
            return None

        riga = {
            "Utente": st.session_state.get("user_id", "ospite"),
            "date": pd.to_datetime(data),
            "Peso": peso,
            "Durata (min)": durata,
            "Distanza (km)": distanza,
            "Frequenza Cardiaca Media": fc_media,
            "Frequenza Cardiaca Massima": fc_max,
            "Velocità Media (km/h)": vel_media,
            "Calorie": calorie,
            "Efficienza": vel_media / fc_media if fc_media > 0 else 0
        }

        return pd.DataFrame([riga])
    return None

# ------------------ Training ML & Analisi ------------------
def add_to_storico(df, file_csv="storico.csv"):
    if os.path.exists(file_csv):
        storico = pd.read_csv(file_csv, parse_dates=["date"])
        df = pd.concat([storico, df], ignore_index=True)
        df.drop_duplicates(subset=["Utente", "date", "Durata (min)"], inplace=True)
    df.to_csv(file_csv, index=False)
    return df

def allena_modello(file_csv="storico.csv"):
    df = pd.read_csv(file_csv)
    df["Efficienza"] = df["Velocità Media (km/h)"] / df["Frequenza Cardiaca Media"]
    df["Load"] = df["Durata (min)"] * df["Frequenza Cardiaca Media"]
    df["Load_7d"] = df["Load"].rolling(window=7).mean()
    df["Load_28d"] = df["Load"].rolling(window=28).mean()
    df["ACWR"] = df["Load_7d"] / df["Load_28d"]
    df.dropna(inplace=True)
    X = df[["Durata (min)", "Distanza (km)", "Frequenza Cardiaca Media", "Efficienza", "ACWR"]]
    y = (df["Frequenza Cardiaca Massima"] > 150).astype(int)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)
    return model, scaler

def prevedi_rischio(df, model, scaler):
    df["ACWR"] = (df["Durata (min)"] * df["Frequenza Cardiaca Media"]) / (df["Durata (min)"].rolling(28).mean() * df["Frequenza Cardiaca Media"].rolling(28).mean())
    df["ACWR"].fillna(1.0, inplace=True)
    X_pred = df[["Durata (min)", "Distanza (km)", "Frequenza Cardiaca Media", "Efficienza", "ACWR"]]
    df["Probabilità Infortunio"] = model.predict_proba(scaler.transform(X_pred))[:, 1]
    return df

# ------------------ Visualizzazioni ------------------
def mostra_grafici(df):
    st.line_chart(df.set_index("date")["Frequenza Cardiaca Media"])
    st.bar_chart(df.set_index("date")["Probabilità Infortunio"])

def riepilogo_settimanale(df):
    st.subheader("📊 Riepilogo settimanale")
    last7 = df.tail(7)
    km_tot = last7["Distanza (km)"].sum()
    fc_avg = last7["Frequenza Cardiaca Media"].mean()
    rischio_medio = last7["Probabilità Infortunio"].mean()
    st.markdown(f"**Distanza Totale**: {km_tot:.1f} km")
    st.markdown(f"**Frequenza Cardiaca Media**: {fc_avg:.0f} bpm")
    st.markdown(f"**Rischio Infortunio Medio**: {rischio_medio*100:.1f}%")

# ------------------ Suggerimenti ML ------------------
def suggerisci_carico(df, model, scaler):
    media = df[["Durata (min)", "Distanza (km)", "Frequenza Cardiaca Media", "Efficienza"]].mean()
    st.markdown("Proiezione prossimi 5 giorni")
    sim = []
    for i in range(1, 6):
        giorno = media.copy()
        acwr = 1.0 + (0.05 * i)
        x = giorno.tolist() + [acwr]
        prob = model.predict_proba(scaler.transform([x]))[0][1]
        sim.append(prob)
    st.line_chart(pd.Series(sim, index=[f"Giorno +{i}" for i in range(1,6)]))

# ------------------ MAIN ------------------
st.set_page_config(page_title="Coach AI", layout="wide")
st.title("🤖 Coach AI - Allenamento predittivo personalizzato")

if not login_form():
    st.stop()

df = inserisci_dati_manuali()
if df is not None:
    df = add_to_storico(df)
    model, scaler = allena_modello()
    df = prevedi_rischio(df, model, scaler)
    mostra_grafici(df)
    suggerisci_carico(df, model, scaler)
    riepilogo_settimanale(df)

    st.subheader("💬 Fai una domanda al tuo Coach AI")
    domanda = st.text_input("Scrivi qui la tua domanda")
    if domanda:
        st.info("🔍 Funzione di risposta intelligente in arrivo")



