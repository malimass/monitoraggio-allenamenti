"""
Live Coach App — Versione 2.0
UI moderna, ruoli Admin/Coach/Utente, analisi AI con LLM.
"""
import os
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules import database as db
from modules import file_parser as fp
from modules import coaching
from modules import ai_analysis as ai

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURAZIONE PAGINA
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Live Coach",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

# ─────────────────────────────────────────────────────────────────────────────
# CSS GLOBALE — TEMA MODERNO
# ─────────────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp { background: #0d1117; color: #e6edf3; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border-right: 1px solid #21262d;
    }

    .brand-header {
        background: linear-gradient(135deg, #6e40c9 0%, #0ea5e9 100%);
        border-radius: 16px; padding: 24px 20px; text-align: center;
        margin-bottom: 24px; box-shadow: 0 8px 32px rgba(110,64,201,0.3);
    }
    .brand-header h1 { color: #fff; font-size: 1.8rem; font-weight: 800; margin: 0; }
    .brand-header p  { color: rgba(255,255,255,0.75); font-size: 0.85rem; margin: 4px 0 0; }

    .card {
        background: #161b22; border: 1px solid #21262d;
        border-radius: 16px; padding: 24px; margin-bottom: 16px; transition: border-color 0.2s;
    }
    .card:hover { border-color: #6e40c9; }

    .metric-card {
        background: #161b22; border: 1px solid #21262d;
        border-radius: 14px; padding: 20px; text-align: center;
    }
    .metric-card .metric-value {
        font-size: 2rem; font-weight: 800;
        background: linear-gradient(135deg, #6e40c9, #0ea5e9);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .metric-card .metric-label {
        font-size: 0.8rem; color: #8b949e; text-transform: uppercase;
        letter-spacing: 0.05em; margin-top: 4px;
    }
    .metric-card .metric-delta { font-size: 0.8rem; margin-top: 6px; }

    .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
    .badge-admin { background: #6e40c920; color: #a78bfa; border: 1px solid #6e40c9; }
    .badge-coach { background: #0ea5e920; color: #38bdf8; border: 1px solid #0ea5e9; }
    .badge-user  { background: #10b98120; color: #34d399;  border: 1px solid #10b981; }

    .alert { border-radius: 10px; padding: 14px 18px; margin: 10px 0; font-size: 0.9rem; }
    .alert-success { background: #10b98115; border: 1px solid #10b981; color: #34d399; }
    .alert-warning { background: #f5960015; border: 1px solid #f59600; color: #fbbf24; }
    .alert-danger  { background: #ef444415; border: 1px solid #ef4444; color: #f87171; }
    .alert-info    { background: #0ea5e915; border: 1px solid #0ea5e9; color: #38bdf8; }

    .section-title {
        font-size: 1.4rem; font-weight: 700; color: #e6edf3;
        border-left: 4px solid #6e40c9; padding-left: 12px; margin-bottom: 20px;
    }

    .auth-logo {
        text-align: center; margin-bottom: 32px; font-size: 3rem; font-weight: 800;
        background: linear-gradient(135deg, #6e40c9, #0ea5e9);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }

    .stTextInput input, .stNumberInput input {
        background: #0d1117 !important; border: 1px solid #30363d !important;
        border-radius: 8px !important; color: #e6edf3 !important;
    }
    .stTextInput input:focus { border-color: #6e40c9 !important; box-shadow: 0 0 0 3px rgba(110,64,201,0.2) !important; }

    .stButton > button {
        background: linear-gradient(135deg, #6e40c9, #0ea5e9) !important;
        color: white !important; border: none !important; border-radius: 10px !important;
        font-weight: 600 !important; padding: 10px 24px !important; transition: opacity 0.2s !important;
    }
    .stButton > button:hover { opacity: 0.85 !important; }

    .stTabs [data-baseweb="tab-list"] { background: #161b22; border-radius: 12px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { color: #8b949e; border-radius: 8px; }
    .stTabs [aria-selected="true"] { background: #6e40c9 !important; color: #fff !important; }

    .stProgress > div > div { background: linear-gradient(90deg, #6e40c9, #0ea5e9); border-radius: 4px; }

    hr { border-color: #21262d; }

    .ai-box {
        background: linear-gradient(135deg, #6e40c915, #0ea5e910);
        border: 1px solid #6e40c9; border-radius: 14px; padding: 20px; margin: 12px 0;
    }
    .ai-box h4 { color: #a78bfa; margin-top: 0; }

    .coach-note {
        background: #0ea5e910; border-left: 3px solid #0ea5e9;
        border-radius: 0 10px 10px 0; padding: 14px; margin: 8px 0;
    }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS UI
# ─────────────────────────────────────────────────────────────────────────────
def metric_card(label: str, value: str, delta: str = "", color: str = ""):
    delta_html = f'<div class="metric-delta" style="color:{color or "#8b949e"}">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>""", unsafe_allow_html=True)


def alert(msg: str, kind: str = "info"):
    st.markdown(f'<div class="alert alert-{kind}">{msg}</div>', unsafe_allow_html=True)


def section_title(title: str):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def role_badge(role: str) -> str:
    labels = {"admin": "⚙️ Admin", "coach": "🏅 Coach", "user": "🏃 Atleta"}
    return f'<span class="badge badge-{role}">{labels.get(role, role)}</span>'


def plotly_dark(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", family="Inter"),
        xaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
        yaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=40, b=10, l=10, r=10),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def init_session():
    defaults = {"user": None, "page": "login", "ai_result": None,
                "uploaded_activity": None, "selected_client": None}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# PAGINA LOGIN
# ─────────────────────────────────────────────────────────────────────────────
def page_login():
    st.markdown('<div class="auth-logo">⚡ Live Coach</div>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align:center;color:#8b949e;font-weight:400;margin-bottom:28px">Accedi al tuo account</h3>', unsafe_allow_html=True)

    with st.form("login_form"):
        username  = st.text_input("Username", placeholder="il tuo username")
        password  = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Accedi →", use_container_width=True)

    if submitted:
        user = db.get_user(username)
        if user and db.verify_password(password, user["password_hash"]):
            st.session_state.user = dict(user)
            role = user["role"]
            st.session_state.page = {"admin": "admin_dashboard", "coach": "coach_clients", "user": "dashboard"}[role]
            st.rerun()
        else:
            alert("Username o password errati.", "danger")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Registrati", use_container_width=True):
            st.session_state.page = "register"
            st.rerun()
    with col2:
        st.markdown('<p style="font-size:0.75rem;color:#8b949e;text-align:center;margin-top:8px">Demo: admin / admin123</p>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGINA REGISTRAZIONE
# ─────────────────────────────────────────────────────────────────────────────
def page_register():
    st.markdown('<div class="auth-logo">⚡ Live Coach</div>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align:center;color:#8b949e;font-weight:400;margin-bottom:28px">Crea il tuo account</h3>', unsafe_allow_html=True)

    coaches = db.get_coaches()
    coach_options = {"Nessun coach (sceglierò dopo)": None}
    for c in coaches:
        coach_options[f"🏅 {c['username']}"] = c["id"]

    with st.form("register_form"):
        c1, c2 = st.columns(2)
        with c1:
            username  = st.text_input("Username *", placeholder="scegli uno username")
            password  = st.text_input("Password *", type="password", placeholder="min 6 caratteri")
        with c2:
            email     = st.text_input("Email", placeholder="la tua email")
            password2 = st.text_input("Conferma Password *", type="password", placeholder="••••••••")

        st.markdown("**Scegli il tuo Coach**")
        coach_sel = st.selectbox("Coach", list(coach_options.keys()),
                                 help="Puoi cambiare coach in seguito dal profilo")

        st.markdown("**Profilo rapido *(opzionale)***")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            nome    = st.text_input("Nome")
            cognome = st.text_input("Cognome")
        with pc2:
            peso    = st.number_input("Peso (kg)",     30.0, 250.0, 70.0, step=0.5)
            altezza = st.number_input("Altezza (cm)",  100,  250,   170)
        with pc3:
            sesso   = st.selectbox("Sesso", ["M", "F", "Altro"])
            anno    = st.number_input("Anno nascita",  1940, 2010,  1990)

        goal    = st.selectbox("Obiettivo", ["Mantenersi in forma","Perdere peso","Aumentare resistenza","Costruire muscoli","Prepararsi per gare"])
        fitness = st.selectbox("Livello fitness", ["principiante","intermedio","avanzato"])

        submitted = st.form_submit_button("Crea Account →", use_container_width=True)

    if submitted:
        if not username or not password:
            alert("Username e password obbligatori.", "danger")
        elif len(password) < 6:
            alert("La password deve avere almeno 6 caratteri.", "warning")
        elif password != password2:
            alert("Le password non coincidono.", "danger")
        else:
            coach_id = coach_options[coach_sel]
            ok = db.create_user(username, email, password, "user", coach_id)
            if ok:
                user = db.get_user(username)
                if nome or cognome:
                    db.upsert_profile(user["id"], {
                        "name": nome, "surname": cognome,
                        "height_cm": altezza, "weight_kg": peso,
                        "sex": sesso, "birth_year": int(anno),
                        "goal": goal, "sport": "Corsa",
                        "fitness_level": fitness, "target_notes": ""
                    })
                alert("✅ Account creato! Ora puoi accedere.", "success")
                st.session_state.page = "login"
                st.rerun()
            else:
                alert("Username già in uso. Scegline un altro.", "danger")

    st.markdown("---")
    if st.button("← Torna al Login", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar():
    user = st.session_state.user
    role = user["role"]

    with st.sidebar:
        st.markdown(f"""
        <div class="brand-header">
            <h1>⚡ Live Coach</h1>
            <p>Ciao, <b>{user['username']}</b> {role_badge(role)}</p>
        </div>
        """, unsafe_allow_html=True)

        if role == "user":
            pages = [
                ("dashboard",  "🏠", "Dashboard"),
                ("upload",     "⬆️",  "Carica Attività"),
                ("workouts",   "📋", "I miei Allenamenti"),
                ("ai_coach",   "🤖", "AI Coach"),
                ("profile",    "👤", "Profilo"),
                ("stats",      "📊", "Statistiche"),
            ]
        elif role == "coach":
            pages = [
                ("coach_clients", "👥", "I miei Clienti"),
                ("coach_detail",  "📋", "Dettaglio Cliente"),
            ]
        else:
            pages = [
                ("admin_dashboard", "🏠", "Dashboard"),
                ("admin_users",     "👥", "Gestione Utenti"),
                ("admin_stats",     "📊", "Statistiche"),
            ]

        for key, icon, label in pages:
            active_style = "background:#6e40c920;color:#a78bfa;font-weight:600;" if st.session_state.page == key else ""
            if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()

        st.markdown("---")
        if st.button("🚪  Esci", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "login"
            st.rerun()

        has_ai = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
        ai_icon = "🟢 Claude AI attivo" if has_ai else "🟡 Analisi locale (imposta ANTHROPIC_API_KEY)"
        st.markdown(f'<p style="font-size:0.7rem;color:#8b949e;text-align:center;margin-top:12px">{ai_icon}</p>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# UTENTE — Dashboard
# ─────────────────────────────────────────────────────────────────────────────
def page_user_dashboard():
    section_title("🏠 Dashboard")
    user       = st.session_state.user
    activities = db.get_activities(user["id"])
    profile    = db.get_profile(user["id"])

    if not activities:
        st.markdown("""
        <div class="card" style="text-align:center;padding:48px">
            <div style="font-size:3rem">🏃</div>
            <h3 style="color:#e6edf3">Nessun allenamento ancora!</h3>
            <p style="color:#8b949e">Carica il tuo primo file FIT/TCX o aggiungi un allenamento manuale.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⬆️ Carica la prima attività"):
            st.session_state.page = "upload"
            st.rerun()
        return

    df = pd.DataFrame([dict(a) for a in activities])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    total_km   = df["distance_km"].fillna(0).sum()
    total_min  = df["duration_min"].fillna(0).sum()
    total_cal  = df["calories"].fillna(0).sum()
    total_acts = len(df)
    avg_hr_val = df["avg_hr"].replace(0, None).dropna().mean()

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: metric_card("Attività",     str(total_acts),               "totali")
    with c2: metric_card("Km Totali",    f"{total_km:.0f}",             "km")
    with c3: metric_card("Ore Allena.",  f"{total_min/60:.1f}",         "ore")
    with c4: metric_card("Calorie",      f"{total_cal:.0f}",            "kcal")
    with c5: metric_card("FC Media",     f"{avg_hr_val:.0f}" if avg_hr_val else "—", "bpm")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        df_km = (df.dropna(subset=["distance_km"])
                   .groupby(df["date"].dt.strftime("%Y-%m"))["distance_km"]
                   .sum().reset_index())
        df_km.columns = ["Mese", "Km"]
        fig = px.bar(df_km, x="Mese", y="Km", title="Km per Mese",
                     color="Km", color_continuous_scale=["#6e40c9","#0ea5e9"])
        st.plotly_chart(plotly_dark(fig), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        sport_c = df["sport"].value_counts().reset_index()
        sport_c.columns = ["Sport", "Sessioni"]
        fig2 = px.pie(sport_c, names="Sport", values="Sessioni",
                      title="Sport praticati",
                      color_discrete_sequence=px.colors.sequential.Purples_r)
        st.plotly_chart(plotly_dark(fig2), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ACWR
    df_s = df.sort_values("date").copy()
    if len(df_s) >= 4:
        df_s["load"] = df_s["duration_min"] * (df_s["avg_hr"].fillna(120) / 100)
        df_s = df_s.set_index("date").resample("D")["load"].sum().fillna(0).reset_index()
        df_s["acute"]   = df_s["load"].rolling(7,  min_periods=1).mean()
        df_s["chronic"] = df_s["load"].rolling(28, min_periods=1).mean()
        df_s["acwr"]    = df_s["acute"] / df_s["chronic"].replace(0, 1)
        df_s = df_s.tail(60)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        fig3 = go.Figure()
        fig3.add_hrect(y0=0,   y1=0.8,  fillcolor="#ef444420", line_width=0)
        fig3.add_hrect(y0=0.8, y1=1.3,  fillcolor="#10b98120", line_width=0)
        fig3.add_hrect(y0=1.3, y1=1.5,  fillcolor="#f5960020", line_width=0)
        fig3.add_hrect(y0=1.5, y1=3.0,  fillcolor="#ef444420", line_width=0)
        fig3.add_scatter(x=df_s["date"], y=df_s["acwr"], mode="lines+markers",
                         name="ACWR", line=dict(color="#a78bfa", width=2))
        fig3.add_hline(y=1.0, line_dash="dash", line_color="#8b949e", annotation_text="Ottimale")
        fig3.update_layout(title="ACWR — Carico Allenamento (ultimi 60gg)",
                           yaxis_title="ACWR")
        st.plotly_chart(plotly_dark(fig3), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Ultimi 5
    section_title("📅 Ultimi Allenamenti")
    sport_icons = {"Corsa":"🏃","Ciclismo":"🚴","Nuoto":"🏊","Palestra":"💪","Trekking":"⛰️","Camminata":"🚶"}
    recent = df.sort_values("date", ascending=False).head(5)
    for _, row in recent.iterrows():
        icon = sport_icons.get(str(row.get("sport", "")), "🏅")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1: st.markdown(f"**{icon} {row.get('sport','—')}** — {row['date'].strftime('%d/%m/%Y')}")
        with c2: st.markdown(f"⏱ {row.get('duration_min',0):.0f} min")
        with c3: st.markdown(f"📍 {row.get('distance_km',0) or 0:.1f} km")
        with c4:
            hr = row.get("avg_hr", 0) or 0
            st.markdown(f"❤️ {hr:.0f} bpm" if hr else "❤️ —")
        st.markdown('<hr style="margin:4px 0;border-color:#21262d">', unsafe_allow_html=True)

    # Note coach
    notes = db.get_coach_notes(user["id"])
    if notes:
        section_title("💬 Note dal tuo Coach")
        for note in notes[:3]:
            st.markdown(f"""
            <div class="coach-note">
                <small style="color:#8b949e">{note['date']} — Coach: {note['coach_name']}</small>
                <p style="margin:4px 0 0">{note['note']}</p>
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# UTENTE — Carica Attività
# ─────────────────────────────────────────────────────────────────────────────
def page_upload():
    section_title("⬆️ Carica Attività")
    user = st.session_state.user

    tab1, tab2 = st.tabs(["📁 Carica File FIT / TCX / GPX", "✏️ Inserimento Manuale"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        uploaded = st.file_uploader("Trascina qui il file", type=["fit","tcx","gpx"],
                                    help="Supportati: Garmin FIT, Training Center TCX, GPX")
        if uploaded:
            with st.spinner("🔍 Analisi file in corso..."):
                suffix   = uploaded.name.split(".")[-1].lower()
                tmp_path = f"/tmp/{uploaded.name}"
                with open(tmp_path, "wb") as f:
                    f.write(uploaded.read())
                try:
                    if suffix == "fit":
                        data = fp.parse_fit(tmp_path)
                    elif suffix == "tcx":
                        data = fp.parse_tcx(tmp_path)
                    else:
                        data = fp.parse_gpx(tmp_path)
                    data["file_name"] = uploaded.name
                    data.setdefault("notes", "")
                    data.setdefault("date", str(datetime.date.today()))
                    st.session_state.uploaded_activity = data
                except Exception as e:
                    alert(f"Errore nel parsing del file: {e}", "danger")
                    st.session_state.uploaded_activity = None

        act = st.session_state.uploaded_activity
        if act:
            st.markdown("### 📊 Dati estratti")
            c1, c2, c3, c4 = st.columns(4)
            with c1: metric_card("Sport",    act.get("sport","—"), "")
            with c2: metric_card("Durata",   f"{act.get('duration_min',0):.0f}", "min")
            with c3: metric_card("Distanza", f"{act.get('distance_km',0):.2f}", "km")
            with c4: metric_card("FC Media", str(act.get("avg_hr",0) or "—"), "bpm")

            c5, c6, c7, c8 = st.columns(4)
            with c5: metric_card("FC Max",     str(act.get("max_hr",0) or "—"), "bpm")
            with c6: metric_card("Calorie",    str(act.get("calories",0) or "—"), "kcal")
            with c7: metric_card("Dislivello", str(act.get("elevation_m",0) or "—"), "m")
            with c8: metric_card("Passo",      str(act.get("avg_pace","—")), "min/km")

            # Analisi AI
            profile      = db.get_profile(user["id"])
            profile_dict = dict(profile) if profile else None
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("🤖 Analizza con AI", use_container_width=True):
                with st.spinner("🧠 Elaborazione AI in corso..."):
                    st.session_state.ai_result = ai.analyze_workout(act, profile_dict)

            if st.session_state.ai_result:
                res = st.session_state.ai_result
                if res["ok"]:
                    d    = res["data"]
                    src  = d.get("source","AI")
                    voto = d.get("voto", 0)
                    col  = "#10b981" if voto >= 8 else "#f59600" if voto >= 6 else "#ef4444"
                    st.markdown(f"""
                    <div class="ai-box">
                        <h4>🤖 Analisi — {src}</h4>
                        <div style="display:flex;align-items:center;gap:16px;margin-bottom:12px">
                            <span style="font-size:2.2rem;font-weight:800;color:{col}">{voto}/10</span>
                            <span style="color:#a78bfa;font-size:1.1rem;font-weight:600">{d.get('giudizio','')}</span>
                        </div>
                        <p style="color:#c9d1d9">{d.get('analisi_fc','')}</p>
                    </div>""", unsafe_allow_html=True)

                    cc1, cc2 = st.columns(2)
                    with cc1:
                        st.markdown("**✅ Punti di forza**")
                        for p in d.get("punti_forza", []):
                            st.markdown(f"- {p}")
                    with cc2:
                        st.markdown("**📈 Aree di miglioramento**")
                        for p in d.get("aree_miglioramento", []):
                            st.markdown(f"- {p}")

                    st.markdown(f"""
                    <div style="background:#10b98115;border-radius:10px;padding:14px;margin-top:12px;border:1px solid #10b981">
                        <b style="color:#34d399">🎯 Prossimo obiettivo:</b><br>
                        <span style="color:#c9d1d9">{d.get('prossimo_obiettivo','')}</span>
                    </div>
                    <div style="background:#6e40c915;border-radius:10px;padding:14px;margin-top:8px;border:1px solid #6e40c9">
                        <b style="color:#a78bfa">💪 {d.get('messaggio_motivazionale','')}</b>
                    </div>""", unsafe_allow_html=True)
                else:
                    alert(f"Errore AI: {res.get('api_error','Errore sconosciuto')}", "warning")

            st.markdown("<br>", unsafe_allow_html=True)
            notes_txt = st.text_area("Note personali (opzionale)", placeholder="Come ti sei sentito?")
            if st.button("💾 Salva Attività", use_container_width=True):
                act["notes"] = notes_txt
                act.setdefault("date", str(datetime.date.today()))
                for field in ["duration_min","distance_km","avg_hr","max_hr","calories","elevation_m","avg_pace"]:
                    act.setdefault(field, 0)
                db.insert_activity(user["id"], act)
                st.session_state.uploaded_activity = None
                st.session_state.ai_result = None
                alert("✅ Attività salvata con successo!", "success")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("manual_activity"):
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                sport = st.selectbox("Sport", ["Corsa","Ciclismo","Nuoto","Palestra","Trekking","Camminata","Altro"])
                date  = st.date_input("Data", datetime.date.today())
            with mc2:
                dur  = st.number_input("Durata (min)", 1, 600, 30)
                dist = st.number_input("Distanza (km)", 0.0, 500.0, 0.0, step=0.1)
            with mc3:
                avg_hr = st.number_input("FC Media (bpm)", 0, 220, 0)
                cal    = st.number_input("Calorie (kcal)",  0, 5000, 0)

            mc4, mc5 = st.columns(2)
            with mc4: max_hr = st.number_input("FC Max (bpm)", 0, 220, 0)
            with mc5: elev   = st.number_input("Dislivello (m)", 0.0, 5000.0, 0.0)
            notes_m = st.text_area("Note")
            saved_m = st.form_submit_button("💾 Salva", use_container_width=True)

        if saved_m:
            db.insert_activity(user["id"], {
                "sport": sport, "date": str(date),
                "duration_min": dur, "distance_km": dist,
                "avg_hr": avg_hr or None, "max_hr": max_hr or None,
                "calories": cal or None, "elevation_m": elev or None,
                "avg_pace": None, "file_name": None, "notes": notes_m
            })
            alert("✅ Attività salvata!", "success")
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# UTENTE — I miei Allenamenti
# ─────────────────────────────────────────────────────────────────────────────
def page_workouts():
    section_title("📋 I miei Allenamenti")
    user = st.session_state.user
    acts = db.get_activities(user["id"])

    if not acts:
        alert("Nessun allenamento trovato. Carica la tua prima attività!", "info")
        return

    df = pd.DataFrame([dict(a) for a in acts])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        sports  = ["Tutti"] + sorted(df["sport"].dropna().unique().tolist())
        sport_f = st.selectbox("Filtra per sport", sports)
    with fc2:
        sort_by = st.selectbox("Ordina per", ["Data ↓","Distanza ↓","Durata ↓"])
    with fc3:
        search = st.text_input("🔍 Cerca nelle note", "")

    filtered = df.copy()
    if sport_f != "Tutti":
        filtered = filtered[filtered["sport"] == sport_f]
    if search:
        filtered = filtered[filtered["notes"].fillna("").str.contains(search, case=False)]
    sort_map = {"Data ↓": "date", "Distanza ↓": "distance_km", "Durata ↓": "duration_min"}
    filtered = filtered.sort_values(sort_map[sort_by], ascending=False)

    st.markdown(f"**{len(filtered)} allenamenti trovati**")
    sport_icons = {"Corsa":"🏃","Ciclismo":"🚴","Nuoto":"🏊","Palestra":"💪","Trekking":"⛰️","Camminata":"🚶"}

    for _, row in filtered.iterrows():
        icon     = sport_icons.get(str(row.get("sport","")), "🏅")
        date_str = row["date"].strftime("%d/%m/%Y") if pd.notnull(row["date"]) else "—"
        with st.expander(f"{icon} {row.get('sport','—')} — {date_str}  |  {row.get('duration_min',0):.0f} min  |  {row.get('distance_km',0) or 0:.1f} km"):
            ec1, ec2, ec3, ec4, ec5 = st.columns(5)
            with ec1: st.metric("Durata",    f"{row.get('duration_min',0):.0f} min")
            with ec2: st.metric("Distanza",  f"{row.get('distance_km',0) or 0:.2f} km")
            with ec3: st.metric("FC Media",  f"{row.get('avg_hr',0) or '—'} bpm")
            with ec4: st.metric("Calorie",   f"{row.get('calories',0) or '—'} kcal")
            with ec5: st.metric("Dislivello",f"{row.get('elevation_m',0) or '—'} m")
            if row.get("notes"):
                st.markdown(f"📝 *{row['notes']}*")
            if st.button("🗑️ Elimina", key=f"del_{row['id']}"):
                db.delete_activity(int(row["id"]), user["id"])
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# UTENTE — AI Coach
# ─────────────────────────────────────────────────────────────────────────────
def page_ai_coach():
    section_title("🤖 AI Coach")
    user    = st.session_state.user
    profile = db.get_profile(user["id"])
    acts    = db.get_activities(user["id"])

    if not profile:
        alert("Completa il tuo profilo per ricevere consigli personalizzati.", "warning")
        if st.button("👤 Vai al Profilo"):
            st.session_state.page = "profile"
            st.rerun()
        return

    p = dict(profile)
    tab1, tab2, tab3 = st.tabs(["📅 Piano Settimanale", "💬 Consiglio AI", "❤️ Zone FC"])

    with tab1:
        plan = coaching.get_coaching_advice(p, [dict(a) for a in acts])
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"### 🎯 Piano per: **{p.get('goal','—')}**")
        week = plan.get("weekly_plan", {})
        days_order = ["Lunedì","Martedì","Mercoledì","Giovedì","Venerdì","Sabato","Domenica"]
        if isinstance(week, dict):
            for day in days_order:
                if day in week:
                    d1, d2 = st.columns([1, 4])
                    with d1: st.markdown(f"**{day}**")
                    with d2: st.markdown(week[day])
        elif isinstance(week, list):
            for item in week:
                st.markdown(f"- {item}")
        if plan.get("advice"):
            st.markdown(f"> 💡 *{plan['advice']}*")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🛌 Consigli Recovery")
        for tip in coaching.recover_tips():
            st.markdown(f"• {tip}")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 💬 Consiglio Settimanale Personalizzato")

        if acts:
            df    = pd.DataFrame([dict(a) for a in acts])
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            last7 = df[df["date"] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
            summary = {
                "sessions":  len(last7),
                "total_km":  last7["distance_km"].fillna(0).sum(),
                "total_min": last7["duration_min"].fillna(0).sum(),
                "avg_hr":    last7["avg_hr"].replace(0, None).dropna().mean() or 0,
                "sports":    last7["sport"].dropna().unique().tolist(),
            }
        else:
            summary = {"sessions":0,"total_km":0,"total_min":0,"avg_hr":0,"sports":[]}

        has_ai = bool(os.environ.get("ANTHROPIC_API_KEY","").strip())
        st.markdown(f"**Questa settimana:** {summary['sessions']} sessioni | {summary['total_km']:.1f} km | {summary['total_min']:.0f} min")

        if st.button("🧠 Genera Consiglio AI", use_container_width=True):
            with st.spinner("Elaborazione in corso..."):
                advice = ai.get_weekly_ai_advice(summary, p)
                src    = "Claude AI" if has_ai else "Analisi locale"
                st.markdown(f"""
                <div class="ai-box">
                    <h4>🤖 {src}</h4>
                    <p style="color:#c9d1d9;font-size:1rem;line-height:1.7">{advice}</p>
                </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        try:
            max_hr_val = coaching.calc_max_hr(p.get("birth_year",1990), p.get("sex","M"))
            zones      = coaching.get_hr_zones(max_hr_val)
            st.markdown(f"### ❤️ Zone FC — FC Max stimata: **{max_hr_val} bpm**")
            zone_colors = ["#3b82f6","#10b981","#f59600","#ef4444","#8b5cf6"]
            for i, (name, (lo, hi)) in enumerate(zones.items()):
                pct = (i + 1) * 20
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:12px;margin:8px 0">
                    <div style="width:12px;height:12px;border-radius:50%;background:{zone_colors[i]};flex-shrink:0"></div>
                    <span style="min-width:200px;color:#c9d1d9"><b>{name}</b></span>
                    <div style="flex:1;background:#21262d;border-radius:4px;height:10px">
                        <div style="width:{pct}%;background:{zone_colors[i]};height:10px;border-radius:4px"></div>
                    </div>
                    <span style="color:#8b949e;min-width:110px;text-align:right">{lo}–{hi} bpm</span>
                </div>""", unsafe_allow_html=True)
        except Exception:
            alert("Completa data di nascita e sesso nel profilo per calcolare le zone FC.", "warning")
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# UTENTE — Profilo
# ─────────────────────────────────────────────────────────────────────────────
def page_profile():
    section_title("👤 Profilo Atleta")
    user    = st.session_state.user
    profile = db.get_profile(user["id"])
    p       = dict(profile) if profile else {}

    coaches = db.get_coaches()
    coach_options = {"Nessun coach": None}
    for c in coaches:
        coach_options[f"🏅 {c['username']}"] = c["id"]

    current_coach_id  = user.get("coach_id")
    current_coach_lbl = next((lbl for lbl, cid in coach_options.items() if cid == current_coach_id), "Nessun coach")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🏅 Il tuo Coach")
    new_coach_lbl = st.selectbox("Coach", list(coach_options.keys()),
                                  index=list(coach_options.keys()).index(current_coach_lbl))
    if st.button("Aggiorna Coach"):
        db.assign_coach(user["id"], coach_options[new_coach_lbl])
        st.session_state.user["coach_id"] = coach_options[new_coach_lbl]
        alert("✅ Coach aggiornato!", "success")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    GOALS    = ["Mantenersi in forma","Perdere peso","Aumentare resistenza","Costruire muscoli","Prepararsi per gare"]
    SPORTS   = ["Corsa","Ciclismo","Nuoto","Palestra","Trekking","Camminata"]
    LEVELS   = ["principiante","intermedio","avanzato"]
    SEXES    = ["M","F","Altro"]

    def safe_idx(lst, val, default=0):
        return lst.index(val) if val in lst else default

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📋 Dati Personali")
    with st.form("profile_form"):
        pf1, pf2 = st.columns(2)
        with pf1:
            name    = st.text_input("Nome",    p.get("name",""))
            surname = st.text_input("Cognome", p.get("surname",""))
            sex     = st.selectbox("Sesso",    SEXES, index=safe_idx(SEXES, p.get("sex","M")))
            year    = st.number_input("Anno di nascita", 1940, 2010, int(p.get("birth_year",1990)))
        with pf2:
            weight  = st.number_input("Peso (kg)",    30.0, 250.0, float(p.get("weight_kg",70)), step=0.5)
            height  = st.number_input("Altezza (cm)", 100,  250,   int(p.get("height_cm",170)))
            goal    = st.selectbox("Obiettivo",       GOALS,  index=safe_idx(GOALS, p.get("goal","Mantenersi in forma")))
            fitness = st.selectbox("Livello fitness", LEVELS, index=safe_idx(LEVELS, p.get("fitness_level","principiante")))

        sport_main = st.selectbox("Sport principale", SPORTS, index=safe_idx(SPORTS, p.get("sport","Corsa")))
        notes_p    = st.text_area("Note / obiettivi", p.get("target_notes",""))
        saved      = st.form_submit_button("💾 Salva Profilo", use_container_width=True)

    if saved:
        db.upsert_profile(user["id"], {
            "name": name, "surname": surname, "height_cm": height, "weight_kg": weight,
            "sex": sex, "birth_year": int(year), "goal": goal, "sport": sport_main,
            "fitness_level": fitness, "target_notes": notes_p
        })
        bmi = coaching.compute_bmi(weight, height)
        alert(f"✅ Profilo salvato! BMI: {bmi['value']:.1f} ({bmi['category']})", "success")
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# UTENTE — Statistiche
# ─────────────────────────────────────────────────────────────────────────────
def page_stats():
    section_title("📊 Statistiche & Progressi")
    user = st.session_state.user
    acts = db.get_activities(user["id"])

    if not acts:
        alert("Nessun dato disponibile. Carica qualche allenamento!", "info")
        return

    df = pd.DataFrame([dict(a) for a in acts])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🏆 Record Personali")
    rc1, rc2, rc3, rc4 = st.columns(4)
    with rc1: metric_card("Distanza Max",  f"{df['distance_km'].max():.1f}",  "km")
    with rc2: metric_card("Durata Max",    f"{df['duration_min'].max():.0f}",  "min")
    with rc3: metric_card("FC Max",        f"{df['max_hr'].max() or '—'}",     "bpm")
    with rc4: metric_card("Dislivello Max",f"{df['elevation_m'].max() or '—'}","m")
    st.markdown('</div>', unsafe_allow_html=True)

    monthly = (df.groupby(df["date"].dt.to_period("M"))
                 .agg(km=("distance_km","sum"), sessions=("id","count"))
                 .reset_index())
    monthly["date"] = monthly["date"].astype(str)

    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        fig = px.line(monthly, x="date", y="km", title="Km Mensili",
                      markers=True, color_discrete_sequence=["#a78bfa"])
        st.plotly_chart(plotly_dark(fig), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with sc2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        fig2 = px.bar(monthly, x="date", y="sessions", title="Sessioni per Mese",
                      color="sessions", color_continuous_scale=["#0ea5e9","#6e40c9"])
        st.plotly_chart(plotly_dark(fig2), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    df_hr = df[df["avg_hr"].fillna(0) > 0].copy()
    if len(df_hr) > 2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        fig3 = px.scatter(df_hr, x="date", y="avg_hr", color="sport",
                          title="FC Media nel Tempo", trendline="lowess",
                          color_discrete_sequence=px.colors.qualitative.Vivid)
        st.plotly_chart(plotly_dark(fig3), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# COACH — Clienti
# ─────────────────────────────────────────────────────────────────────────────
def page_coach_clients():
    section_title("👥 I miei Clienti")
    user    = st.session_state.user
    clients = db.get_coach_clients(user["id"])

    if not clients:
        alert("Nessun cliente assegnato. Chiedi all'admin di assegnarti degli atleti.", "info")
        return

    for client in clients:
        client = dict(client)
        acts   = db.get_activities(client["id"])
        df     = pd.DataFrame([dict(a) for a in acts]) if acts else pd.DataFrame()

        with st.expander(f"🏃 {client['username']}  —  {len(acts)} allenamenti"):
            ec1, ec2, ec3 = st.columns(3)
            with ec1: st.metric("Sessioni totali", len(acts))
            with ec2:
                km = df["distance_km"].fillna(0).sum() if not df.empty else 0
                st.metric("Km totali", f"{km:.1f}")
            with ec3:
                p = db.get_profile(client["id"])
                st.metric("Obiettivo", (p["goal"] or "—") if p else "—")

            if st.button(f"📋 Dettaglio", key=f"detail_{client['id']}"):
                st.session_state.selected_client = client
                st.session_state.page = "coach_detail"
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# COACH — Dettaglio Cliente
# ─────────────────────────────────────────────────────────────────────────────
def page_coach_detail():
    section_title("📋 Dettaglio Cliente")
    client = st.session_state.get("selected_client")
    if not client:
        alert("Nessun cliente selezionato. Torna alla lista.", "warning")
        return

    if st.button("← Torna ai clienti"):
        st.session_state.page = "coach_clients"
        st.rerun()

    profile = db.get_profile(client["id"])
    acts    = db.get_activities(client["id"])

    st.markdown(f"### 👤 {client['username']}")
    if profile:
        pp = dict(profile)
        dc1, dc2, dc3, dc4 = st.columns(4)
        with dc1: metric_card("Età",     f"{2025-(pp.get('birth_year') or 1990)}", "anni")
        with dc2: metric_card("Peso",    f"{pp.get('weight_kg','—')}",             "kg")
        with dc3: metric_card("Altezza", f"{pp.get('height_cm','—')}",             "cm")
        with dc4: metric_card("Livello", pp.get("fitness_level","—"),              "")
        st.markdown(f"**Obiettivo:** {pp.get('goal','—')}  |  **Sport:** {pp.get('sport','—')}")

    if acts:
        df = pd.DataFrame([dict(a) for a in acts])
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date", ascending=False)
        st.markdown("#### 📅 Allenamenti recenti")
        st.dataframe(df[["date","sport","duration_min","distance_km","avg_hr","calories"]].head(20),
                     use_container_width=True)

    st.markdown("#### 📝 Aggiungi Nota")
    with st.form("add_note"):
        note_txt  = st.text_area("Messaggio per l'atleta")
        note_date = st.date_input("Data", datetime.date.today())
        if st.form_submit_button("Invia Nota"):
            db.insert_coach_note(st.session_state.user["id"], client["id"], note_txt, str(note_date))
            alert("✅ Nota inviata!", "success")

    existing = db.get_coach_notes(client["id"])
    if existing:
        st.markdown("#### 💬 Note inviate")
        for note in existing:
            st.markdown(f"""
            <div class="coach-note">
                <small style="color:#8b949e">{note['date']}</small>
                <p style="margin:4px 0 0">{note['note']}</p>
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN — Dashboard
# ─────────────────────────────────────────────────────────────────────────────
def page_admin_dashboard():
    section_title("⚙️ Admin Dashboard")
    stats = db.get_system_stats()

    ac1, ac2, ac3, ac4, ac5, ac6 = st.columns(6)
    with ac1: metric_card("Atleti",       str(stats["total_users"]))
    with ac2: metric_card("Coach",        str(stats["total_coaches"]))
    with ac3: metric_card("Admin",        str(stats["total_admins"]))
    with ac4: metric_card("Attività",     str(stats["total_activities"]))
    with ac5: metric_card("Note Coach",   str(stats["total_notes"]))
    with ac6: metric_card("Utenti Attivi",str(stats["active_users"]))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📋 Ultime Attività (sistema)")
    recent = db.get_all_activities_admin()
    if recent:
        df = pd.DataFrame([dict(a) for a in recent])
        st.dataframe(
            df[["username","date","sport","duration_min","distance_km","avg_hr","calories"]].head(20),
            use_container_width=True
        )
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN — Gestione Utenti
# ─────────────────────────────────────────────────────────────────────────────
def page_admin_users():
    section_title("👥 Gestione Utenti")
    users   = db.get_all_users()
    coaches = db.get_coaches()
    coach_map     = {c["id"]: c["username"] for c in coaches}
    coach_options = {"Nessun coach": None, **{f"🏅 {c['username']}": c["id"] for c in coaches}}

    with st.expander("➕ Crea nuovo utente / coach"):
        with st.form("create_user"):
            nuc1, nuc2, nuc3 = st.columns(3)
            with nuc1:
                new_user  = st.text_input("Username")
                new_email = st.text_input("Email")
            with nuc2:
                new_pass  = st.text_input("Password", type="password")
                new_role  = st.selectbox("Ruolo", ["user","coach","admin"])
            with nuc3:
                new_coach = st.selectbox("Coach assegnato", list(coach_options.keys()))
            if st.form_submit_button("Crea Utente"):
                ok = db.create_user(new_user, new_email, new_pass, new_role, coach_options[new_coach])
                if ok:
                    alert(f"✅ Utente '{new_user}' creato come {new_role}!", "success")
                    st.rerun()
                else:
                    alert("Username già esistente.", "danger")

    st.markdown("---")
    for u in users:
        u = dict(u)
        active_icon = "🟢" if u["active"] else "🔴"
        coach_name  = coach_map.get(u.get("coach_id")) or "—"
        badge_html  = role_badge(u["role"])

        with st.expander(f"{active_icon} **{u['username']}** {badge_html}  —  Coach: {coach_name}"):
            uc1, uc2, uc3 = st.columns(3)
            with uc1:
                st.markdown(f"**Email:** {u.get('email','—')}")
                st.markdown(f"**Creato:** {(u.get('created_at') or '')[:10]}")
                if st.button("Disabilita" if u["active"] else "Abilita", key=f"tog_{u['id']}"):
                    db.toggle_user_active(u["id"], not u["active"])
                    st.rerun()
            with uc2:
                new_role = st.selectbox("Ruolo", ["user","coach","admin"],
                                        index=["user","coach","admin"].index(u["role"]),
                                        key=f"role_{u['id']}")
                if st.button("Aggiorna Ruolo", key=f"upd_role_{u['id']}"):
                    db.update_user_role(u["id"], new_role)
                    alert("✅ Ruolo aggiornato!", "success")
                    st.rerun()
            with uc3:
                new_coach_lbl = st.selectbox("Coach", list(coach_options.keys()),
                                              key=f"cs_{u['id']}")
                if st.button("Aggiorna Coach", key=f"upd_coach_{u['id']}"):
                    db.assign_coach(u["id"], coach_options[new_coach_lbl])
                    alert("✅ Coach aggiornato!", "success")
                    st.rerun()
                new_pw = st.text_input("Nuova Password", type="password", key=f"pw_{u['id']}")
                if st.button("Cambia Password", key=f"cpw_{u['id']}") and new_pw:
                    db.update_user_password(u["id"], new_pw)
                    alert("✅ Password aggiornata!", "success")


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN — Statistiche
# ─────────────────────────────────────────────────────────────────────────────
def page_admin_stats():
    section_title("📊 Statistiche Sistema")
    acts = db.get_all_activities_admin()
    if not acts:
        alert("Nessuna attività nel sistema.", "info")
        return

    df = pd.DataFrame([dict(a) for a in acts])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    asc1, asc2 = st.columns(2)
    with asc1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        sport_c = df["sport"].value_counts().reset_index()
        sport_c.columns = ["Sport","Count"]
        fig = px.pie(sport_c, names="Sport", values="Count",
                     title="Sport più praticati",
                     color_discrete_sequence=px.colors.sequential.Purples_r)
        st.plotly_chart(plotly_dark(fig), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with asc2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if "username" in df.columns:
            top_u = (df.groupby("username").size()
                       .reset_index(name="Sessioni")
                       .sort_values("Sessioni", ascending=False).head(10))
            fig2 = px.bar(top_u, x="username", y="Sessioni",
                          title="Top 10 Atleti per Sessioni",
                          color="Sessioni", color_continuous_scale=["#6e40c9","#0ea5e9"])
            st.plotly_chart(plotly_dark(fig2), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    monthly = df.groupby(df["date"].dt.to_period("M")).size().reset_index(name="Sessioni")
    monthly["date"] = monthly["date"].astype(str)
    fig3 = px.area(monthly, x="date", y="Sessioni",
                   title="Attività nel Tempo (tutto il sistema)",
                   color_discrete_sequence=["#6e40c9"])
    st.plotly_chart(plotly_dark(fig3), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────
def main():
    inject_css()
    init_session()

    user = st.session_state.user
    page = st.session_state.page

    # ── Pagine pubbliche ──
    if not user:
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            if page == "register":
                page_register()
            else:
                page_login()
        return

    # ── Pagine autenticate ──
    render_sidebar()
    role = user["role"]

    user_pages  = {"dashboard","upload","workouts","ai_coach","profile","stats"}
    coach_pages = {"coach_clients","coach_detail"}
    admin_pages = {"admin_dashboard","admin_users","admin_stats"}

    if role == "user"  and page not in user_pages:
        st.session_state.page = "dashboard";       st.rerun()
    if role == "coach" and page not in coach_pages:
        st.session_state.page = "coach_clients";   st.rerun()
    if role == "admin" and page not in admin_pages:
        st.session_state.page = "admin_dashboard"; st.rerun()

    route = {
        "dashboard":       page_user_dashboard,
        "upload":          page_upload,
        "workouts":        page_workouts,
        "ai_coach":        page_ai_coach,
        "profile":         page_profile,
        "stats":           page_stats,
        "coach_clients":   page_coach_clients,
        "coach_detail":    page_coach_detail,
        "admin_dashboard": page_admin_dashboard,
        "admin_users":     page_admin_users,
        "admin_stats":     page_admin_stats,
    }
    route.get(page, page_user_dashboard)()


if __name__ == "__main__":
    main()
