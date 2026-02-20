"""
Live Coach — Streamlit application entry point.
Roles: admin | coach | user
Run with: streamlit run coach_app.py
"""
from __future__ import annotations

import datetime
import io
import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules import database as db
from modules import coaching as coach
from modules.file_parser import parse_file

# ── App config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Live Coach",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Init DB on first run ──────────────────────────────────────────────────────

@st.cache_resource
def _init():
    db.init_db()

_init()

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# ── Session-state helpers ─────────────────────────────────────────────────────

def is_logged_in() -> bool:
    return st.session_state.get("user_id") is not None


def current_user() -> dict:
    return {
        "id": st.session_state["user_id"],
        "username": st.session_state["username"],
        "role": st.session_state["role"],
    }


def login_user(user_row):
    st.session_state["user_id"] = user_row["id"]
    st.session_state["username"] = user_row["username"]
    st.session_state["role"] = user_row["role"]


def logout():
    for k in ["user_id", "username", "role"]:
        st.session_state.pop(k, None)
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Login / Register
# ─────────────────────────────────────────────────────────────────────────────

def page_auth():
    st.title("🏋️ Live Coach")
    st.subheader("Il tuo coach sportivo personale")
    st.markdown("---")

    tab_login, tab_register = st.tabs(["🔑 Accedi", "📝 Registrati"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Accedi", use_container_width=True)
        if submitted:
            if not username or not password:
                st.error("Inserisci username e password.")
            else:
                user = db.get_user(username)
                if user and db.verify_password(password, user["password_hash"]):
                    login_user(user)
                    st.success(f"Benvenuto, {username}!")
                    st.rerun()
                else:
                    st.error("Credenziali non valide.")

    with tab_register:
        with st.form("register_form"):
            new_user = st.text_input("Username")
            new_email = st.text_input("Email")
            new_pass = st.text_input("Password", type="password", key="r_pass")
            new_pass2 = st.text_input("Conferma password", type="password", key="r_pass2")
            submitted_r = st.form_submit_button("Registrati", use_container_width=True)
        if submitted_r:
            if not new_user or not new_pass:
                st.error("Compila tutti i campi obbligatori.")
            elif new_pass != new_pass2:
                st.error("Le password non coincidono.")
            elif len(new_pass) < 6:
                st.error("La password deve avere almeno 6 caratteri.")
            else:
                ok = db.create_user(new_user, new_email, new_pass, "user")
                if ok:
                    st.success("Account creato! Ora puoi accedere.")
                else:
                    st.error("Username già in uso.")

    st.markdown("---")
    st.caption("Account demo admin: **admin** / **admin123**")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Dashboard
# ─────────────────────────────────────────────────────────────────────────────

def page_dashboard():
    user = current_user()
    st.title(f"Dashboard — {user['username']}")

    # Daily motivational quote
    quote = coach.get_daily_quote()
    st.info(f"💬 *{quote}*")
    st.markdown("---")

    activities = db.get_activities(user["id"])
    acts_df = pd.DataFrame([dict(a) for a in activities]) if activities else pd.DataFrame()

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    total = len(acts_df)
    week_stats = coach.weekly_summary(acts_df)

    col1.metric("Allenamenti totali", total)
    col2.metric("Sessioni questa settimana", week_stats.get("sessions", 0))
    col3.metric(
        "Km questa settimana",
        f"{week_stats.get('total_distance_km', 0):.1f}" if week_stats.get("total_distance_km") else "–",
    )
    col4.metric(
        "Minuti questa settimana",
        f"{week_stats.get('total_duration_min', 0):.0f}" if week_stats.get("total_duration_min") else "–",
    )

    if acts_df.empty:
        st.info("Non hai ancora registrato allenamenti. Vai su **Carica Attività** per iniziare!")
        return

    st.markdown("---")
    col_left, col_right = st.columns(2)

    # Distance over time
    with col_left:
        st.subheader("Distanza nel tempo (km)")
        df_plot = acts_df.dropna(subset=["date", "distance_km"]).copy()
        df_plot["date"] = pd.to_datetime(df_plot["date"])
        if not df_plot.empty:
            fig = px.bar(df_plot.sort_values("date"), x="date", y="distance_km",
                         color="sport", text_auto=".1f")
            fig.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=300)
            st.plotly_chart(fig, use_container_width=True)

    # HR over time
    with col_right:
        st.subheader("Frequenza cardiaca media")
        df_hr = acts_df.dropna(subset=["date", "avg_hr"]).copy()
        df_hr["date"] = pd.to_datetime(df_hr["date"])
        if not df_hr.empty:
            fig2 = px.line(df_hr.sort_values("date"), x="date", y="avg_hr",
                           markers=True, color="sport")
            fig2.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=300)
            st.plotly_chart(fig2, use_container_width=True)

    # ACWR chart
    st.subheader("Carico di allenamento — ACWR (Acute:Chronic Workload Ratio)")
    df_acwr = coach.compute_acwr(acts_df)
    if "acwr" in df_acwr.columns:
        df_acwr["acwr"] = pd.to_numeric(df_acwr["acwr"], errors="coerce")
        df_valid = df_acwr.dropna(subset=["acwr"])
        if not df_valid.empty:
            fig3 = go.Figure()
            fig3.add_hline(y=0.8, line_dash="dot", line_color="blue",
                           annotation_text="Sotto-allenamento", annotation_position="left")
            fig3.add_hline(y=1.3, line_dash="dot", line_color="orange",
                           annotation_text="Soglia attenzione", annotation_position="left")
            fig3.add_hline(y=1.5, line_dash="dot", line_color="red",
                           annotation_text="Rischio infortunio", annotation_position="left")
            fig3.add_trace(go.Scatter(
                x=df_valid["date"], y=df_valid["acwr"],
                mode="lines+markers", name="ACWR",
                line=dict(color="#3498db", width=2),
            ))
            fig3.update_layout(
                height=280, margin=dict(l=0, r=0, t=20, b=0),
                yaxis_title="ACWR", xaxis_title="Data",
            )
            st.plotly_chart(fig3, use_container_width=True)

            last_acwr = df_valid["acwr"].iloc[-1]
            label, colour = coach.acwr_risk_label(last_acwr)
            st.markdown(
                f"**Stato attuale:** <span style='color:{colour};font-weight:bold'>{label}</span> "
                f"(ACWR = {last_acwr:.2f})",
                unsafe_allow_html=True,
            )

    # Coach notes (if any)
    notes = db.get_coach_notes(user["id"])
    if notes:
        st.markdown("---")
        st.subheader("Note dal tuo coach")
        for n in notes:
            st.markdown(f"**{n['date']}** — {n['coach_name']}: _{n['note']}_")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Profile
# ─────────────────────────────────────────────────────────────────────────────

def page_profile():
    user = current_user()
    st.title("Profilo Atleta")

    profile = db.get_profile(user["id"])
    p = dict(profile) if profile else {}

    GOALS = ["Perdere peso", "Aumentare resistenza", "Costruire muscoli",
             "Prepararsi per gare", "Mantenersi in forma"]
    SPORTS = ["Corsa", "Ciclismo", "Nuoto", "Palestra", "Trekking", "Camminata", "Triathlon", "Altro"]
    LEVELS = ["principiante", "intermedio", "avanzato"]
    SEXES = ["M", "F", "Altro"]

    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nome", value=p.get("name", ""))
            surname = st.text_input("Cognome", value=p.get("surname", ""))
            height = st.number_input("Altezza (cm)", 100, 250, value=int(p.get("height_cm") or 170))
            weight = st.number_input("Peso (kg)", 30.0, 250.0, value=float(p.get("weight_kg") or 70.0), step=0.5)
        with col2:
            sex = st.selectbox("Sesso", SEXES, index=SEXES.index(p.get("sex") or "M") if p.get("sex") in SEXES else 0)
            birth_year = st.number_input("Anno di nascita", 1940, datetime.date.today().year - 5,
                                         value=int(p.get("birth_year") or 1990))
            goal = st.selectbox("Obiettivo principale", GOALS,
                                 index=GOALS.index(p.get("goal")) if p.get("goal") in GOALS else 0)
            sport = st.selectbox("Sport principale", SPORTS,
                                  index=SPORTS.index(p.get("sport")) if p.get("sport") in SPORTS else 0)

        fitness = st.select_slider("Livello di fitness", options=LEVELS,
                                   value=p.get("fitness_level") or "principiante")
        notes = st.text_area("Note e obiettivi aggiuntivi", value=p.get("target_notes") or "")
        submitted = st.form_submit_button("Salva profilo", use_container_width=True)

    if submitted:
        db.upsert_profile(user["id"], {
            "name": name, "surname": surname,
            "height_cm": height, "weight_kg": weight,
            "sex": sex, "birth_year": birth_year,
            "goal": goal, "sport": sport,
            "fitness_level": fitness, "target_notes": notes,
        })
        st.success("Profilo salvato!")

    # BMI indicator
    if p.get("weight_kg") and p.get("height_cm"):
        bmi, bmi_label = coach.compute_bmi(float(p["weight_kg"]), float(p["height_cm"]))
        st.markdown("---")
        col_a, col_b = st.columns(2)
        col_a.metric("BMI", bmi, delta=None)
        col_b.markdown(f"**Categoria:** {bmi_label}")

    # Estimated HR zones
    if p.get("birth_year") and p.get("sex"):
        max_hr = coach.calc_max_hr(int(p["birth_year"]), p["sex"])
        zones = coach.get_hr_zones(max_hr)
        st.markdown("---")
        st.subheader(f"Zone di frequenza cardiaca (FCmax stimata: {max_hr} bpm)")
        rows = [{"Zona": k, "Min (bpm)": v[0], "Max (bpm)": v[1], "Descrizione": v[2]}
                for k, v in zones.items()]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Upload Activity
# ─────────────────────────────────────────────────────────────────────────────

def page_upload():
    user = current_user()
    st.title("Carica Attività")

    tab_file, tab_manual = st.tabs(["📂 Carica file (FIT / TCX / GPX)", "✏️ Inserimento manuale"])

    # ── File upload ───────────────────────────────────────────────────────────
    with tab_file:
        uploaded = st.file_uploader(
            "Seleziona uno o più file di attività",
            type=["fit", "tcx", "gpx"],
            accept_multiple_files=True,
        )
        if uploaded:
            for f in uploaded:
                st.markdown(f"---\n**File:** `{f.name}`")
                try:
                    parsed = parse_file(f.read(), f.name)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Dati estratti:**")
                        preview = {k: v for k, v in parsed.items() if v is not None and k != "notes"}
                        st.json(preview)
                    with col2:
                        sport_opt = parsed.get("sport") or "Corsa"
                        add_notes = st.text_area(f"Note per {f.name}", key=f"note_{f.name}")
                        if st.button(f"Salva '{f.name}'", key=f"save_{f.name}"):
                            data = {**parsed, "user_id": user["id"], "notes": add_notes}
                            db.insert_activity(user["id"], {k: data.get(k) for k in [
                                "date","sport","duration_min","distance_km",
                                "avg_hr","max_hr","calories","elevation_m","avg_pace","file_name","notes",
                            ]})
                            st.success(f"'{f.name}' salvato!")
                except Exception as e:
                    st.error(f"Errore nel parsing di {f.name}: {e}")

    # ── Manual input ──────────────────────────────────────────────────────────
    with tab_manual:
        SPORTS = ["Corsa", "Ciclismo", "Nuoto", "Palestra", "Trekking", "Camminata", "Triathlon", "Altro"]
        with st.form("manual_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                act_date = st.date_input("Data", value=datetime.date.today())
                sport_m = st.selectbox("Sport", SPORTS)
                duration = st.number_input("Durata (min)", 1.0, 600.0, value=30.0)
            with col2:
                distance = st.number_input("Distanza (km)", 0.0, 500.0, value=0.0, step=0.1)
                avg_hr = st.number_input("FC media (bpm)", 0, 250, value=0)
                max_hr = st.number_input("FC massima (bpm)", 0, 250, value=0)
            with col3:
                calories = st.number_input("Calorie bruciate", 0, 10000, value=0)
                elevation = st.number_input("Dislivello positivo (m)", 0.0, 9000.0, value=0.0)
                notes_m = st.text_area("Note")
            submitted_m = st.form_submit_button("Salva allenamento", use_container_width=True)

        if submitted_m:
            avg_pace = (duration / distance) if distance > 0 else None
            db.insert_activity(user["id"], {
                "date": str(act_date),
                "sport": sport_m,
                "duration_min": duration,
                "distance_km": distance if distance > 0 else None,
                "avg_hr": avg_hr if avg_hr > 0 else None,
                "max_hr": max_hr if max_hr > 0 else None,
                "calories": calories if calories > 0 else None,
                "elevation_m": elevation if elevation > 0 else None,
                "avg_pace": round(avg_pace, 2) if avg_pace else None,
                "file_name": None,
                "notes": notes_m or None,
            })
            st.success("Allenamento salvato!")
            st.balloons()
            st.info(f"💪 {coach.get_motivational_message('post')}")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Activities list
# ─────────────────────────────────────────────────────────────────────────────

def page_activities():
    user = current_user()
    st.title("I miei allenamenti")

    activities = db.get_activities(user["id"])
    if not activities:
        st.info("Nessun allenamento registrato. Vai su **Carica Attività**!")
        return

    df = pd.DataFrame([dict(a) for a in activities])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Filters
    with st.expander("Filtri"):
        sports = ["Tutti"] + sorted(df["sport"].dropna().unique().tolist())
        sel_sport = st.selectbox("Sport", sports)
        if sel_sport != "Tutti":
            df = df[df["sport"] == sel_sport]

    # Table
    display_cols = ["date", "sport", "duration_min", "distance_km", "avg_hr", "calories", "elevation_m", "notes"]
    show_df = df[[c for c in display_cols if c in df.columns]].rename(columns={
        "date": "Data", "sport": "Sport", "duration_min": "Durata (min)",
        "distance_km": "Distanza (km)", "avg_hr": "FC media", "calories": "Calorie",
        "elevation_m": "Dislivello (m)", "notes": "Note",
    })
    st.dataframe(show_df.sort_values("Data", ascending=False), use_container_width=True, hide_index=True)

    # Delete
    st.markdown("---")
    st.subheader("Elimina allenamento")
    act_ids = {f"{dict(a)['date']} — {dict(a)['sport']} — id:{a['id']}": a["id"] for a in activities}
    sel = st.selectbox("Seleziona allenamento da eliminare", list(act_ids.keys()))
    if st.button("Elimina", type="primary"):
        db.delete_activity(act_ids[sel], user["id"])
        st.success("Eliminato!")
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Coaching
# ─────────────────────────────────────────────────────────────────────────────

def page_coaching():
    user = current_user()
    st.title("Il tuo Coach AI")

    profile = db.get_profile(user["id"])
    if not profile:
        st.warning("Completa prima il tuo **profilo** per ricevere consigli personalizzati!")
        return

    p = dict(profile)
    advice = coach.get_coaching_advice(p, [])

    # Motivational banner
    msg = coach.get_motivational_message("pre")
    st.success(f"🔥 {msg}")
    st.markdown("---")

    # Goal overview
    col1, col2, col3 = st.columns(3)
    col1.metric("Obiettivo", p.get("goal") or "–")
    col2.metric("Sport principale", p.get("sport") or "–")
    col3.metric("Sessioni consigliate / settimana", advice.get("sessions_week", "–"))

    st.markdown("---")

    # Detailed advice
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Piano settimanale", "💡 Consigli", "❤️ Zone FC", "🛌 Recupero"])

    with tab1:
        st.subheader(f"Piano settimanale — {p.get('goal', 'Forma fisica')}")
        st.markdown(f"**Zona target:** {advice.get('target_zone', '–')}")
        for day in advice.get("weekly_plan", []):
            st.markdown(f"- {day}")

        if advice.get("sport_advice"):
            st.markdown("---")
            st.subheader(f"Consigli specifici per {p.get('sport')}")
            st.markdown(advice["sport_advice"])

    with tab2:
        st.subheader("Strategia di allenamento")
        st.markdown(advice.get("advice", ""))

        if advice.get("beginner_note"):
            st.info(advice["beginner_note"])

        # Recent performance context
        activities = db.get_activities(user["id"])
        if activities:
            df = pd.DataFrame([dict(a) for a in activities])
            week = coach.weekly_summary(df)
            st.markdown("---")
            st.subheader("La tua settimana corrente")
            c1, c2, c3 = st.columns(3)
            c1.metric("Sessioni", week.get("sessions", 0),
                      delta=f"{advice.get('sessions_week',0) - week.get('sessions',0)} vs obiettivo")
            c2.metric("Km totali", f"{week.get('total_distance_km',0):.1f}")
            c3.metric("Minuti totali", f"{week.get('total_duration_min',0):.0f}")

    with tab3:
        st.subheader("Zone di frequenza cardiaca personalizzate")
        zones = advice.get("zones")
        if zones:
            max_hr_est = advice.get("max_hr_estimated")
            st.markdown(f"FCmax stimata: **{max_hr_est} bpm** (formula Tanaka)")
            rows = [{"Zona": k, "FC min (bpm)": v[0], "FC max (bpm)": v[1], "Obiettivo": v[2]}
                    for k, v in zones.items()]
            zone_df = pd.DataFrame(rows)
            st.dataframe(zone_df, use_container_width=True, hide_index=True)

            # Zone distribution from activities
            activities = db.get_activities(user["id"])
            if activities and max_hr_est:
                df = pd.DataFrame([dict(a) for a in activities]).dropna(subset=["avg_hr"])
                if not df.empty:
                    df["zona"] = df["avg_hr"].apply(lambda hr: coach.classify_hr(int(hr), max_hr_est))
                    zone_counts = df["zona"].value_counts().reset_index()
                    zone_counts.columns = ["Zona", "Sessioni"]
                    st.markdown("---")
                    st.subheader("Distribuzione allenamenti per zona")
                    fig = px.pie(zone_counts, names="Zona", values="Sessioni", hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Inserisci anno di nascita e sesso nel profilo per visualizzare le zone.")

    with tab4:
        st.subheader("Consigli per il recupero")
        for tip in coach.recovery_tips():
            st.markdown(f"- {tip}")
        st.markdown("---")
        st.info(coach.get_motivational_message("recovery"))


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Admin panel
# ─────────────────────────────────────────────────────────────────────────────

def page_admin():
    st.title("Pannello Admin")

    users = db.get_all_users()
    coaches = db.get_coaches()
    coach_map = {c["id"]: c["username"] for c in coaches}
    coach_opts = {c["username"]: c["id"] for c in coaches}

    st.subheader("Gestione utenti")
    df = pd.DataFrame([dict(u) for u in users])
    st.dataframe(df[["id", "username", "email", "role", "coach_id", "active", "created_at"]],
                 use_container_width=True, hide_index=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Modifica ruolo")
        usernames = [u["username"] for u in users if u["username"] != "admin"]
        sel_user = st.selectbox("Utente", usernames, key="admin_usr")
        new_role = st.selectbox("Nuovo ruolo", ["user", "coach", "admin"], key="admin_role")
        if st.button("Aggiorna ruolo"):
            target = next(u for u in users if u["username"] == sel_user)
            db.update_user_role(target["id"], new_role)
            st.success(f"Ruolo di {sel_user} aggiornato a {new_role}")
            st.rerun()

    with col2:
        st.subheader("Assegna coach")
        sel_user2 = st.selectbox("Utente", [u["username"] for u in users if u["role"] == "user"], key="admin_usr2")
        sel_coach = st.selectbox("Coach", ["(nessuno)"] + list(coach_opts.keys()), key="admin_coach")
        if st.button("Assegna"):
            target = next((u for u in users if u["username"] == sel_user2), None)
            if target:
                cid = coach_opts.get(sel_coach) if sel_coach != "(nessuno)" else None
                db.assign_coach(target["id"], cid)
                st.success("Coach assegnato!")
                st.rerun()

    st.markdown("---")
    st.subheader("Crea nuovo utente")
    with st.form("admin_create_user"):
        nu = st.text_input("Username")
        ne = st.text_input("Email")
        np_ = st.text_input("Password", type="password")
        nr = st.selectbox("Ruolo", ["user", "coach", "admin"])
        if st.form_submit_button("Crea utente"):
            if db.create_user(nu, ne, np_, nr):
                st.success(f"Utente '{nu}' creato con ruolo '{nr}'.")
            else:
                st.error("Username già in uso.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Coach panel
# ─────────────────────────────────────────────────────────────────────────────

def page_coach_panel():
    user = current_user()
    st.title("Pannello Coach")

    clients = db.get_coach_clients(user["id"])
    if not clients:
        st.info("Non hai ancora clienti assegnati. Contatta l'amministratore.")
        return

    client_opts = {f"{c['username']} (id:{c['id']})": c["id"] for c in clients}
    sel_label = st.selectbox("Seleziona cliente", list(client_opts.keys()))
    client_id = client_opts[sel_label]
    client_name = sel_label.split(" ")[0]

    tab_overview, tab_acts, tab_notes = st.tabs(["Panoramica", "Allenamenti", "Note Coach"])

    with tab_overview:
        profile = db.get_profile(client_id)
        if profile:
            p = dict(profile)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Nome", f"{p.get('name','')} {p.get('surname','')}")
            c2.metric("Obiettivo", p.get("goal") or "–")
            c3.metric("Sport", p.get("sport") or "–")
            c4.metric("Livello", p.get("fitness_level") or "–")

            if p.get("weight_kg") and p.get("height_cm"):
                bmi, bmi_label = coach.compute_bmi(float(p["weight_kg"]), float(p["height_cm"]))
                st.metric("BMI", f"{bmi} ({bmi_label})")
        else:
            st.warning(f"{client_name} non ha ancora completato il profilo.")

    with tab_acts:
        acts = db.get_activities(client_id)
        if acts:
            df = pd.DataFrame([dict(a) for a in acts])
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            week = coach.weekly_summary(df)
            c1, c2, c3 = st.columns(3)
            c1.metric("Sessioni questa settimana", week.get("sessions", 0))
            c2.metric("Km questa settimana", f"{week.get('total_distance_km',0):.1f}")
            c3.metric("Min questa settimana", f"{week.get('total_duration_min',0):.0f}")

            st.markdown("---")
            show = df[["date","sport","duration_min","distance_km","avg_hr","calories","notes"]].rename(columns={
                "date":"Data","sport":"Sport","duration_min":"Durata","distance_km":"Km",
                "avg_hr":"FC media","calories":"Calorie","notes":"Note",
            })
            st.dataframe(show.sort_values("Data", ascending=False), use_container_width=True, hide_index=True)

            # ACWR
            df_acwr = coach.compute_acwr(df)
            if "acwr" in df_acwr.columns:
                last_acwr = df_acwr["acwr"].dropna().iloc[-1] if not df_acwr["acwr"].dropna().empty else None
                label, colour = coach.acwr_risk_label(last_acwr)
                st.markdown(
                    f"**Stato carico attuale:** <span style='color:{colour};font-weight:bold'>{label}</span>",
                    unsafe_allow_html=True,
                )
        else:
            st.info(f"{client_name} non ha ancora registrato allenamenti.")

    with tab_notes:
        st.subheader(f"Aggiungi nota per {client_name}")
        with st.form("coach_note_form"):
            note_date = st.date_input("Data nota", value=datetime.date.today())
            note_text = st.text_area("Nota / feedback / piano")
            if st.form_submit_button("Salva nota"):
                if note_text.strip():
                    db.insert_coach_note(user["id"], client_id, note_text.strip(), str(note_date))
                    st.success("Nota salvata!")
                else:
                    st.warning("Scrivi qualcosa prima di salvare.")

        st.markdown("---")
        st.subheader("Note precedenti")
        notes = db.get_coach_notes(client_id)
        if notes:
            for n in notes:
                if n["coach_name"] == user["username"]:
                    st.markdown(f"**{n['date']}:** {n['note']}")
        else:
            st.info("Nessuna nota per questo atleta.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Progress & Stats
# ─────────────────────────────────────────────────────────────────────────────

def page_progress():
    user = current_user()
    st.title("Progressi e Statistiche")

    activities = db.get_activities(user["id"])
    if not activities:
        st.info("Nessun dato disponibile. Carica i tuoi allenamenti prima!")
        return

    df = pd.DataFrame([dict(a) for a in activities])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")

    act_count = len(df)
    msg = coach.get_motivational_message("progress", act_count)
    st.success(f"🏅 {msg}")
    st.markdown("---")

    # Personal records
    st.subheader("Record personali")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Distanza massima (km)", f"{df['distance_km'].max():.2f}" if df['distance_km'].notna().any() else "–")
    c2.metric("Durata massima (min)", f"{df['duration_min'].max():.0f}" if df['duration_min'].notna().any() else "–")
    c3.metric("FC max registrata (bpm)", f"{df['max_hr'].max():.0f}" if df['max_hr'].notna().any() else "–")
    c4.metric("Calorie massime", f"{df['calories'].max():.0f}" if df['calories'].notna().any() else "–")

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Monthly volume
    with col1:
        st.subheader("Volume mensile (minuti)")
        df["month"] = df["date"].dt.to_period("M").astype(str)
        monthly = df.groupby("month")["duration_min"].sum().reset_index()
        fig = px.bar(monthly, x="month", y="duration_min", text_auto=".0f")
        fig.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)

    # Pace trend
    with col2:
        st.subheader("Passo medio nel tempo (min/km)")
        df_pace = df.dropna(subset=["avg_pace"])
        if not df_pace.empty:
            fig2 = px.scatter(df_pace, x="date", y="avg_pace", color="sport",
                              trendline="ols", title="Andamento del passo")
            fig2.update_layout(height=300, margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Dati di passo non disponibili.")

    # Elevation cumulative
    st.subheader("Dislivello accumulato nel tempo (m)")
    df_elev = df.dropna(subset=["elevation_m"])
    if not df_elev.empty:
        df_elev["elev_cumsum"] = df_elev["elevation_m"].cumsum()
        fig3 = px.area(df_elev, x="date", y="elev_cumsum")
        fig3.update_layout(height=250, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig3, use_container_width=True)

    # Sport breakdown
    st.markdown("---")
    st.subheader("Distribuzione per sport")
    sport_df = df.groupby("sport").agg(
        sessioni=("id", "count"),
        km_totali=("distance_km", "sum"),
        minuti_totali=("duration_min", "sum"),
    ).reset_index()
    st.dataframe(sport_df.rename(columns={
        "sport":"Sport","sessioni":"Sessioni","km_totali":"Km totali","minuti_totali":"Min totali"
    }), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar navigation & main router
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if not is_logged_in():
        page_auth()
        return

    user = current_user()
    role = user["role"]

    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/sport.png", width=60)
        st.markdown(f"### {user['username']}")
        st.caption(f"Ruolo: **{role.capitalize()}**")
        st.markdown("---")

        # Navigation options per role
        pages = {
            "Dashboard": "dashboard",
            "Profilo": "profile",
            "Carica Attività": "upload",
            "I miei Allenamenti": "activities",
            "Coach AI": "coaching",
            "Progressi": "progress",
        }
        if role in ("admin", "coach"):
            pages["Pannello Coach"] = "coach_panel"
        if role == "admin":
            pages["Pannello Admin"] = "admin"

        icons = {
            "dashboard": "🏠",
            "profile": "👤",
            "upload": "📂",
            "activities": "📋",
            "coaching": "🤖",
            "progress": "📈",
            "coach_panel": "👨‍🏫",
            "admin": "⚙️",
        }

        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "dashboard"

        for label, key in pages.items():
            if st.button(f"{icons.get(key,'')} {label}", use_container_width=True,
                         type="primary" if st.session_state["current_page"] == key else "secondary"):
                st.session_state["current_page"] = key
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout()

        st.markdown("---")
        st.caption("Live Coach v1.0")

    # Route
    page = st.session_state.get("current_page", "dashboard")
    if page == "dashboard":
        page_dashboard()
    elif page == "profile":
        page_profile()
    elif page == "upload":
        page_upload()
    elif page == "activities":
        page_activities()
    elif page == "coaching":
        page_coaching()
    elif page == "progress":
        page_progress()
    elif page == "coach_panel" and role in ("admin", "coach"):
        page_coach_panel()
    elif page == "admin" and role == "admin":
        page_admin()
    else:
        page_dashboard()


if __name__ == "__main__":
    main()
