"""
Coaching engine — HR zones, ACWR, goal-based advice, motivational messages.
All text is in Italian.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

import pandas as pd
import numpy as np


# ── Heart-rate zones ──────────────────────────────────────────────────────────

def calc_max_hr(birth_year: int, sex: str = "M") -> int:
    """Estimate max HR using the Tanaka formula (sex-adjusted)."""
    age = date.today().year - birth_year
    if sex and sex.upper() == "F":
        return int(206 - 0.88 * age)
    return int(208 - 0.7 * age)


def get_hr_zones(max_hr: int) -> dict[str, tuple[int, int, str]]:
    """Return 5 training zones: {zone_name: (min_hr, max_hr, description)}."""
    return {
        "Zona 1 – Recupero Attivo":  (int(max_hr * 0.50), int(max_hr * 0.60), "Recupero e rigenerazione"),
        "Zona 2 – Aerobico Base":    (int(max_hr * 0.60), int(max_hr * 0.70), "Brucia grassi, resistenza"),
        "Zona 3 – Aerobico Tempo":   (int(max_hr * 0.70), int(max_hr * 0.80), "Soglia aerobica"),
        "Zona 4 – Soglia Lattato":   (int(max_hr * 0.80), int(max_hr * 0.90), "Migliora la soglia"),
        "Zona 5 – VO2max / Sprint":  (int(max_hr * 0.90), max_hr,            "Massima intensità"),
    }


def classify_hr(avg_hr: int, max_hr: int) -> str:
    pct = avg_hr / max_hr
    if pct < 0.60:
        return "Zona 1 – Recupero Attivo"
    if pct < 0.70:
        return "Zona 2 – Aerobico Base"
    if pct < 0.80:
        return "Zona 3 – Aerobico Tempo"
    if pct < 0.90:
        return "Zona 4 – Soglia Lattato"
    return "Zona 5 – VO2max / Sprint"


# ── ACWR (Acute:Chronic Workload Ratio) ───────────────────────────────────────

def compute_acwr(activities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add an 'acwr' column to a DataFrame that has 'date' and 'load' columns.
    load = duration_min * (avg_hr / 100) as a simple Training Stress proxy.
    """
    if activities_df.empty or "date" not in activities_df.columns:
        return activities_df

    df = activities_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")

    # Compute load proxy
    hr_col = df["avg_hr"].fillna(130)
    dur_col = df["duration_min"].fillna(30)
    df["load"] = dur_col * (hr_col / 100)

    # Rolling sums (calendar-day gaps handled by reindexing)
    df = df.set_index("date")
    daily = df["load"].resample("D").sum()
    acute = daily.rolling(7, min_periods=1).mean()
    chronic = daily.rolling(28, min_periods=1).mean()
    acwr_series = acute / chronic.replace(0, np.nan)

    df = df.reset_index()
    df["acwr"] = df["date"].map(acwr_series)
    return df


def acwr_risk_label(acwr: float | None) -> tuple[str, str]:
    """Return (risk_label, colour)."""
    if acwr is None or np.isnan(acwr):
        return "Dati insufficienti", "grey"
    if acwr < 0.8:
        return "Sottoallenamento", "#3498db"
    if acwr <= 1.3:
        return "Carico ottimale", "#2ecc71"
    if acwr <= 1.5:
        return "Carico elevato – attenzione", "#f39c12"
    return "Rischio infortunio alto", "#e74c3c"


# ── Goal-based coaching advice ────────────────────────────────────────────────

SPORT_ADVICE: dict[str, str] = {
    "Corsa": (
        "Per la corsa, alterna giorni di corsa lenta (Zona 2) con sessioni di interval training "
        "e una uscita lunga settimanale. Aumenta il volume massimo del **10% a settimana**."
    ),
    "Ciclismo": (
        "Per il ciclismo, includi uscite di endurance in Zona 2, salite ripetute e sedute in piano "
        "ad alta cadenza. Usa il rullo nei giorni di mal tempo."
    ),
    "Nuoto": (
        "Per il nuoto, lavora su tecnica e drill almeno 1-2 volte a settimana. "
        "Alterna vasche lente, serie di velocità e serie a ritmo gara."
    ),
    "Palestra": (
        "Per la palestra, segui un piano di progressione (forza, ipertrofia o resistenza muscolare). "
        "Varia gli esercizi ogni 4-6 settimane per evitare l'adattamento."
    ),
    "Trekking": (
        "Per il trekking, costruisci le gambe con salite e discese. Allena la resistenza aerobica "
        "con camminate progressive e porta sempre equipaggiamento adatto."
    ),
    "Camminata": (
        "Cammina a passo svelto (4-6 km/h) per restare in Zona 2. Aumenta la distanza "
        "o includi tratti in salita per stimolare il progresso."
    ),
}

GOAL_PLANS: dict[str, dict] = {
    "Perdere peso": {
        "sessions_week": 4,
        "target_zone": "Zona 2 – Aerobico Base",
        "session_duration": "45–60 min",
        "advice": (
            "Per dimagrire in modo efficace: **4 sessioni settimanali** prevalentemente in Zona 2 "
            "(60–70% FCmax). Aggiungi **2 sessioni di forza** per preservare la massa muscolare e "
            "aumentare il metabolismo basale. Deficit calorico moderato: –300/–500 kcal/giorno."
        ),
        "weekly_plan": [
            "Lunedì: Cardio Zona 2 – 45 min",
            "Martedì: Forza (full body) – 40 min",
            "Mercoledì: Riposo o stretching",
            "Giovedì: Cardio Zona 2 – 50 min",
            "Venerdì: Forza (full body) – 40 min",
            "Sabato: Uscita lunga Zona 2 – 60 min",
            "Domenica: Recupero attivo / camminata",
        ],
    },
    "Aumentare resistenza": {
        "sessions_week": 5,
        "target_zone": "Zona 2 – Aerobico Base / Zona 3",
        "session_duration": "45–90 min",
        "advice": (
            "Regola **80/20**: 80% degli allenamenti in Zona 2, 20% ad alta intensità. "
            "Includi un'**uscita lunga** settimanale (progressivamente +10% di durata) e "
            "1 sessione di **interval training** o **fartlek**."
        ),
        "weekly_plan": [
            "Lunedì: Riposo o recupero attivo",
            "Martedì: Interval training – 45 min (Zona 4-5)",
            "Mercoledì: Zona 2 leggero – 40 min",
            "Giovedì: Tempo run/ride – 50 min (Zona 3)",
            "Venerdì: Zona 2 facile – 45 min",
            "Sabato: Uscita lunga Zona 2 – 70–90 min",
            "Domenica: Recupero completo",
        ],
    },
    "Costruire muscoli": {
        "sessions_week": 4,
        "target_zone": "Zona 1–2 (cardio minimo)",
        "session_duration": "50–70 min (forza)",
        "advice": (
            "Priorità alla **forza e ipertrofia**: 3–4 sessioni di pesi con **overload progressivo** "
            "(aumenta peso o reps ogni settimana). Cardio limitato a 2x20 min di Zona 2 per la salute "
            "cardiaca. Proteine adeguate: **1.6–2.2 g/kg** di peso corporeo al giorno."
        ),
        "weekly_plan": [
            "Lunedì: Upper body (petto/spalle/tricipiti)",
            "Martedì: Lower body (squat/stacchi/gambe)",
            "Mercoledì: Cardio Zona 2 – 20 min + core",
            "Giovedì: Upper body (schiena/bicipiti)",
            "Venerdì: Lower body (affondi/leg press)",
            "Sabato: Cardio leggero o sport ricreativo",
            "Domenica: Recupero completo",
        ],
    },
    "Prepararsi per gare": {
        "sessions_week": 6,
        "target_zone": "Zona 2–5 (periodizzato)",
        "session_duration": "30–120 min",
        "advice": (
            "Usa la **periodizzazione**: cicli di 3 settimane di carico + 1 di recupero. "
            "Includi sessioni a **ritmo gara**, simulazioni di gara parziali e un **tapering** "
            "di 1–2 settimane prima dell'evento (riduzione del 20–40% del volume)."
        ),
        "weekly_plan": [
            "Lunedì: Recupero attivo",
            "Martedì: Interval training specifico – 50 min",
            "Mercoledì: Volume a Zona 2 – 60 min",
            "Giovedì: Sessione a ritmo gara – 45 min",
            "Venerdì: Zona 2 recovery – 30 min",
            "Sabato: Uscita lunga simulazione gara",
            "Domenica: Recupero completo",
        ],
    },
    "Mantenersi in forma": {
        "sessions_week": 3,
        "target_zone": "Zona 2–3",
        "session_duration": "30–45 min",
        "advice": (
            "**3–4 sessioni settimanali** di attività mista mantengono la forma senza sovraccaricare. "
            "Varia le attività per mantenere la motivazione alta. Almeno **150 min/settimana** di "
            "attività aerobica moderata (linee guida OMS)."
        ),
        "weekly_plan": [
            "Lunedì: Cardio Zona 2 – 30 min",
            "Martedì: Forza o yoga – 40 min",
            "Mercoledì: Riposo",
            "Giovedì: Sport preferito – 45 min",
            "Venerdì: Riposo o camminata",
            "Sabato: Attività all'aperto – 45 min",
            "Domenica: Recupero / stretching",
        ],
    },
}


def get_coaching_advice(profile: Any, recent_activities: list) -> dict:
    """
    Generate personalised coaching output based on profile and recent data.
    Returns a dict with keys: summary, weekly_plan, sport_advice, acwr_comment, zones.
    """
    result: dict = {}

    goal = getattr(profile, "goal", None) or (profile["goal"] if isinstance(profile, dict) else None)
    sport = getattr(profile, "sport", None) or (profile["sport"] if isinstance(profile, dict) else None)
    fitness = getattr(profile, "fitness_level", "principiante") or "principiante"

    plan = GOAL_PLANS.get(goal or "", GOAL_PLANS["Mantenersi in forma"])
    result["advice"] = plan["advice"]
    result["weekly_plan"] = plan["weekly_plan"]
    result["sessions_week"] = plan["sessions_week"]
    result["target_zone"] = plan["target_zone"]
    result["sport_advice"] = SPORT_ADVICE.get(sport or "", "")

    # HR zones
    birth_year = None
    sex = "M"
    try:
        birth_year = profile["birth_year"] if isinstance(profile, dict) else profile.birth_year
        sex = profile["sex"] if isinstance(profile, dict) else profile.sex
    except Exception:
        pass

    if birth_year:
        max_hr = calc_max_hr(int(birth_year), sex or "M")
        result["max_hr_estimated"] = max_hr
        result["zones"] = get_hr_zones(max_hr)
    else:
        result["zones"] = {}

    # Fitness level adjustments
    if fitness == "principiante":
        result["beginner_note"] = (
            "Sei alla fase iniziale: concentrati sulla **regolarità** più che sull'intensità. "
            "Non saltare il riscaldamento (10 min) e il defaticamento (10 min)."
        )
    elif fitness == "avanzato":
        result["beginner_note"] = (
            "Livello avanzato: puoi spingere sulle intensità, ma rispetta sempre le settimane "
            "di recupero ogni 3–4 settimane di carico."
        )
    else:
        result["beginner_note"] = (
            "Livello intermedio: consolida la base aerobica prima di aumentare l'intensità. "
            "Cerca di mantenere 2 sessioni dure e 2 facili a settimana."
        )

    return result


# ── Recovery advice ───────────────────────────────────────────────────────────

def recovery_tips() -> list[str]:
    return [
        "Dormi **7–9 ore** per notte: il corpo si ricostruisce durante il sonno.",
        "Idratati: bevi almeno **35 ml per kg** di peso corporeo al giorno.",
        "Proteine post-workout entro **30–45 minuti** dall'allenamento.",
        "Stretching statico dopo ogni sessione per almeno **10 minuti**.",
        "Un bagno freddo o crioterapia riduce l'infiammazione muscolare.",
        "Massaggio o foam rolling dopo le sessioni intense accelera il recupero.",
        "Ascolta il corpo: la stanchezza persistente è un segnale da non ignorare.",
    ]


# ── Motivational messages ─────────────────────────────────────────────────────

PRE_WORKOUT: list[str] = [
    "Ogni grande atleta ha iniziato esattamente da dove sei tu ora. Vai!",
    "Non importa quanto vai piano — stai superando tutti quelli che sono ancora sul divano.",
    "Il corpo ottiene ciò per cui lo alleni. Allenalo forte.",
    "La fatica di oggi è la forza di domani.",
    "Il momento in cui vuoi smettere è esattamente il momento in cui devi continuare.",
    "Non si tratta di essere il migliore degli altri. Si tratta di essere il meglio di te.",
    "Un altro allenamento completato significa un altro passo verso i tuoi obiettivi!",
    "La disciplina è fare quello che sai di dover fare anche quando non ne hai voglia.",
    "Ogni sessione conta. Ogni passo conta. Ogni goccia di sudore conta.",
    "Chi si allena oggi, vince domani.",
]

POST_WORKOUT: list[str] = [
    "Allenamento completato! Sei più forte di quanto eri ieri.",
    "Ben fatto! Il recupero è parte dell'allenamento — rispettalo.",
    "Hai lavorato duro oggi. Goditi la sensazione.",
    "Un altro mattone nel muro del tuo successo. Ottimo lavoro!",
    "Ogni volta che ti alleni, costruisci la versione migliore di te stesso.",
    "Fatto! Ora nutriti bene e riposa: il corpo si adatta durante il recupero.",
    "Congratulazioni! Ogni allenamento è una vittoria contro la versione di ieri di te.",
    "Sudore, fatica, risultati. Hai fatto la tua parte oggi!",
]

PROGRESS: list[str] = [
    "I progressi si vedono a lungo termine, non da un giorno all'altro. Continua così!",
    "Ogni piccolo miglioramento è un successo. Celebra anche i traguardi piccoli.",
    "La costanza batte il talento quando il talento non si allena con costanza.",
    "Stai costruendo abitudini che dureranno tutta la vita.",
    "Il cambiamento non è mai lineare, ma la direzione conta più della velocità.",
    "Ogni dato che registri è un passo verso la comprensione del tuo corpo.",
]

RECOVERY_QUOTES: list[str] = [
    "Il recupero non è ozio — è parte del processo. Rispetta il riposo.",
    "I muscoli crescono durante il riposo, non durante l'allenamento.",
    "Ascolta il tuo corpo: sa quando ha bisogno di pausa.",
    "Il riposo attivo è comunque allenamento. Una camminata leggera conta.",
]

MILESTONE_MESSAGES: dict[int, str] = {
    1: "Primo allenamento registrato! Il viaggio inizia con il primo passo.",
    5: "5 allenamenti completati! Stai costruendo un'abitudine vincente.",
    10: "10 allenamenti! Sei ufficialmente in movimento verso i tuoi obiettivi.",
    25: "25 allenamenti! La costanza sta diventando il tuo punto di forza.",
    50: "50 allenamenti! Sei a metà di un percorso straordinario.",
    100: "100 ALLENAMENTI! Sei un atleta. Punto.",
}


def get_motivational_message(context: str = "general", activity_count: int = 0) -> str:
    # Check milestones
    if activity_count in MILESTONE_MESSAGES:
        return f"🏆 **TRAGUARDO!** {MILESTONE_MESSAGES[activity_count]}"

    if context == "pre":
        return random.choice(PRE_WORKOUT)
    if context == "post":
        return random.choice(POST_WORKOUT)
    if context == "progress":
        return random.choice(PROGRESS)
    if context == "recovery":
        return random.choice(RECOVERY_QUOTES)
    return random.choice(PRE_WORKOUT + PROGRESS)


def get_daily_quote() -> str:
    """Deterministic daily quote based on day of year."""
    all_quotes = PRE_WORKOUT + POST_WORKOUT + PROGRESS
    idx = date.today().timetuple().tm_yday % len(all_quotes)
    return all_quotes[idx]


# ── Performance analysis helpers ──────────────────────────────────────────────

def compute_bmi(weight_kg: float, height_cm: float) -> tuple[float, str]:
    bmi = weight_kg / ((height_cm / 100) ** 2)
    if bmi < 18.5:
        label = "Sottopeso"
    elif bmi < 25:
        label = "Normopeso"
    elif bmi < 30:
        label = "Sovrappeso"
    else:
        label = "Obesità"
    return round(bmi, 1), label


def weekly_summary(activities_df: pd.DataFrame) -> dict:
    """Return aggregated weekly stats."""
    if activities_df.empty:
        return {}
    df = activities_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    one_week_ago = pd.Timestamp.now() - pd.Timedelta(days=7)
    week = df[df["date"] >= one_week_ago]
    return {
        "sessions": len(week),
        "total_duration_min": week["duration_min"].sum(),
        "total_distance_km": week["distance_km"].sum(),
        "total_calories": week["calories"].sum(),
        "avg_hr": week["avg_hr"].mean(),
    }
