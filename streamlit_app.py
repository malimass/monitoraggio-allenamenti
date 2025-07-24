# app_streamlit_polar.py

# [CONTENUTO PRECEDENTE INVARIATO QUI SOPRA ...]

# Salva i dati in uno storico CSV per apprendimento continuo
HISTORICAL_CSV = "data/historical_dataset.csv"
if not os.path.exists("data"):
    os.makedirs("data")

# Aggiungi i dati correnti allo storico, evitando duplicati
if not df.empty:
    df_reset = df.reset_index()
    df_reset["date"] = pd.to_datetime(df_reset["date"])
    df_reset["id"] = df_reset["date"].astype(str) + "_" + df_reset["Durata (min)"].astype(str)

    if os.path.exists(HISTORICAL_CSV):
        old = pd.read_csv(HISTORICAL_CSV)
        old["date"] = pd.to_datetime(old["date"])
        old["id"] = old["date"].astype(str) + "_" + old["Durata (min)"].astype(str)
        combined = pd.concat([old, df_reset], ignore_index=True)
        combined = combined.drop_duplicates(subset=["id"])
        combined.to_csv(HISTORICAL_CSV, index=False)
    else:
        df_reset.to_csv(HISTORICAL_CSV, index=False)

    # Carica tutti i dati storici per allenamento del modello
    storico = pd.read_csv(HISTORICAL_CSV)
    storico["Efficienza"] = storico["Velocità Media (km/h)"] / storico["Frequenza Cardiaca Media"]
    storico["Load"] = storico["Durata (min)"] * storico["Frequenza Cardiaca Media"]
    storico["Load_7d"] = storico["Load"].rolling(window=7).mean()
    storico["Load_28d"] = storico["Load"].rolling(window=28).mean()
    storico["ACWR"] = storico["Load_7d"] / storico["Load_28d"]
    storico = storico.dropna()

    X_all = storico[["Durata (min)", "Distanza (km)", "Frequenza Cardiaca Media", "Efficienza", "ACWR"]]
    y_all = (storico["Frequenza Cardiaca Massima"] > soglia_fc).astype(int)

    scaler = StandardScaler()
    X_scaled_all = scaler.fit_transform(X_all)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_scaled_all, y_all)

    # Salva modello aggiornato
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    # Applica al dataframe corrente
    df["Probabilità Infortunio"] = model.predict_proba(scaler.transform(features))[:,1]

    # Mostra previsioni future semplici: prossimi 5 giorni (con media carichi recenti)
    st.subheader("📈 Previsione rischio nei prossimi 5 giorni")
    sim_future = pd.DataFrame()
    avg = df[features.columns].tail(7).mean()
    for i in range(1, 6):
        sim_day = avg.copy()
        sim_day["ACWR"] = max(0.1, avg["ACWR"] + 0.05 * i)
        sim_future = pd.concat([sim_future, sim_day.to_frame().T], ignore_index=True)
    sim_future_scaled = scaler.transform(sim_future)
    probs = model.predict_proba(sim_future_scaled)[:, 1]
    st.line_chart(pd.Series(probs, index=[f"Giorno +{i}" for i in range(1,6)]))

    # Esportazione PDF/CSV dei consigli del giorno selezionato
    import io
    import base64

    st.subheader("📤 Esporta consigli e dati")
    export_date = df_reset["date"].max().strftime("%Y-%m-%d")
    consigli_export = df_reset[df_reset["date"] == df_reset["date"].max()][["Durata (min)", "Distanza (km)", "Frequenza Cardiaca Media", "Efficienza", "ACWR", "Probabilità Infortunio"]]
    csv = consigli_export.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Scarica consigli in CSV", csv, file_name=f"consigli_{export_date}.csv", mime="text/csv")

    # Sommario settimanale
    st.subheader("🗓️ Riepilogo settimanale")
    last7 = df.tail(7)
    km_tot = last7["Distanza (km)"].sum()
    fc_avg = last7["Frequenza Cardiaca Media"].mean()
    rischio_medio = last7["Probabilità Infortunio"].mean()
    st.markdown(f"**Distanza Totale**: {km_tot:.1f} km")
    st.markdown(f"**Frequenza Cardiaca Media**: {fc_avg:.0f} bpm")
    st.markdown(f"**Rischio Infortunio Medio**: {rischio_medio*100:.1f}%")
    if rischio_medio > 0.6:
        st.warning("⚠️ Settimana intensa – considera almeno 1 giorno di recupero")
    elif rischio_medio > 0.3:
        st.info("ℹ️ Settimana equilibrata – mantieni monitoraggio frequente")
    else:
        st.success("✅ Settimana ben gestita – continua così!")





