"""
Modulo AI/LLM per analisi intelligente degli allenamenti.
Supporta Anthropic Claude con fallback al motore locale.
"""
import os
import json
from typing import Optional


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(activity: dict, profile: Optional[dict] = None) -> str:
    sport   = activity.get("sport", "Sconosciuto")
    dur     = activity.get("duration_min", 0)
    dist    = activity.get("distance_km", 0)
    avg_hr  = activity.get("avg_hr", 0)
    max_hr  = activity.get("max_hr", 0)
    cal     = activity.get("calories", 0)
    elev    = activity.get("elevation_m", 0)
    pace    = activity.get("avg_pace", "")

    profile_text = ""
    if profile:
        profile_text = f"""
Profilo atleta:
- Nome: {profile.get('name', '')} {profile.get('surname', '')}
- Età: {2025 - int(profile.get('birth_year', 1990))} anni
- Sesso: {profile.get('sex', 'N/D')}
- Peso: {profile.get('weight_kg', 'N/D')} kg  Altezza: {profile.get('height_cm', 'N/D')} cm
- Livello fitness: {profile.get('fitness_level', 'N/D')}
- Obiettivo: {profile.get('goal', 'N/D')}
- Sport principale: {profile.get('sport', 'N/D')}
"""

    prompt = f"""Sei un coach sportivo esperto. Analizza i seguenti dati di allenamento e fornisci una risposta strutturata in italiano.

{profile_text}
Dati allenamento:
- Sport: {sport}
- Durata: {dur} minuti
- Distanza: {dist:.2f} km
- FC Media: {avg_hr} bpm
- FC Massima: {max_hr} bpm
- Calorie bruciate: {cal} kcal
- Dislivello: {elev} m
- Passo medio: {pace}

Rispondi con un JSON valido con questa struttura esatta (niente testo fuori dal JSON):
{{
  "giudizio": "Ottimo|Buono|Nella norma|Da migliorare",
  "voto": 8,
  "punti_forza": ["punto 1", "punto 2"],
  "aree_miglioramento": ["area 1", "area 2"],
  "consiglio_immediato": "Breve consiglio per il prossimo allenamento.",
  "analisi_fc": "Analisi della frequenza cardiaca in 2-3 frasi.",
  "prossimo_obiettivo": "Suggerimento specifico per la prossima sessione.",
  "messaggio_motivazionale": "Frase motivazionale personalizzata."
}}"""
    return prompt


# ---------------------------------------------------------------------------
# Anthropic backend
# ---------------------------------------------------------------------------

def _analyze_with_anthropic(activity: dict, profile: Optional[dict], api_key: str) -> dict:
    try:
        import anthropic  # type: ignore
        client = anthropic.Anthropic(api_key=api_key)
        prompt = _build_prompt(activity, profile)
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text.strip()
        # Prova a parsare JSON
        if raw.startswith("{"):
            data = json.loads(raw)
        else:
            # Estrai JSON se c'è testo attorno
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            data  = json.loads(raw[start:end])
        data["source"] = "Claude AI"
        return {"ok": True, "data": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Fallback locale
# ---------------------------------------------------------------------------

def _analyze_local(activity: dict, profile: Optional[dict]) -> dict:
    dur    = activity.get("duration_min", 0) or 0
    dist   = activity.get("distance_km", 0) or 0
    avg_hr = activity.get("avg_hr", 0) or 0
    cal    = activity.get("calories", 0) or 0

    # Calcola voto semplice
    voto = 6
    punti_forza = []
    aree = []

    if dur >= 45:
        punti_forza.append(f"Durata ottimale ({dur:.0f} min)")
        voto += 1
    else:
        aree.append("Aumenta la durata a 45+ minuti")

    if dist > 5:
        punti_forza.append(f"Buona distanza percorsa ({dist:.1f} km)")
        voto += 1
    elif dist > 0:
        aree.append("Prova ad aumentare gradualmente la distanza")

    if 120 <= avg_hr <= 160:
        punti_forza.append(f"FC in zona aerobica ideale ({avg_hr} bpm)")
    elif avg_hr > 170:
        aree.append("FC molto alta: considera sessioni più moderate")
    elif avg_hr > 0:
        aree.append("FC nella zona di recupero: puoi aumentare l'intensità")

    if cal > 400:
        punti_forza.append(f"Buon dispendio calorico ({cal} kcal)")

    if not punti_forza:
        punti_forza.append("Hai completato l'allenamento!")
    if not aree:
        aree.append("Continua così e mantieni la costanza")

    voto = min(10, max(4, voto))
    giudizi = {10: "Eccellente", 9: "Ottimo", 8: "Buono", 7: "Buono",
               6: "Nella norma", 5: "Da migliorare", 4: "Da migliorare"}
    giudizio = giudizi.get(voto, "Nella norma")

    data = {
        "giudizio": giudizio,
        "voto": voto,
        "punti_forza": punti_forza,
        "aree_miglioramento": aree,
        "consiglio_immediato": "Mantieni la costanza: 3-4 sessioni a settimana sono l'ideale.",
        "analisi_fc": f"La frequenza cardiaca media di {avg_hr} bpm indica un allenamento " +
                      ("ben calibrato in zona aerobica." if 120 <= avg_hr <= 155
                       else "che potrebbe essere ottimizzato con variazioni di intensità."),
        "prossimo_obiettivo": "Prova ad aumentare volume o intensità del 5-10% rispetto a questa sessione.",
        "messaggio_motivazionale": "Ogni chilometro percorso è un passo verso la versione migliore di te!",
        "source": "Analisi locale"
    }
    return {"ok": True, "data": data}


# ---------------------------------------------------------------------------
# Entry point pubblico
# ---------------------------------------------------------------------------

def analyze_workout(activity: dict, profile: Optional[dict] = None) -> dict:
    """
    Analizza un allenamento con AI.

    Returns dict:
      {"ok": True,  "data": {...}}
      {"ok": False, "error": "...", "data": {...}}  # fallback locale
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    if api_key:
        result = _analyze_with_anthropic(activity, profile, api_key)
        if result["ok"]:
            return result
        # Fallback se chiamata API fallisce
        fallback = _analyze_local(activity, profile)
        fallback["api_error"] = result.get("error", "Errore sconosciuto")
        return fallback
    else:
        return _analyze_local(activity, profile)


def get_weekly_ai_advice(activities_summary: dict, profile: Optional[dict] = None) -> str:
    """
    Genera un consiglio settimanale personalizzato tramite LLM.
    Restituisce testo in italiano (stringa).
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    total_km   = activities_summary.get("total_km", 0)
    total_min  = activities_summary.get("total_min", 0)
    sessions   = activities_summary.get("sessions", 0)
    avg_hr     = activities_summary.get("avg_hr", 0)
    sports     = activities_summary.get("sports", [])
    goal       = profile.get("goal", "Mantenersi in forma") if profile else "Mantenersi in forma"

    if not api_key:
        return (f"Questa settimana hai completato {sessions} sessioni per un totale di "
                f"{total_km:.1f} km in {total_min:.0f} minuti. "
                f"Continua con questa frequenza per raggiungere il tuo obiettivo: {goal}.")

    prompt = f"""Sei un coach sportivo esperto. Genera un consiglio settimanale personalizzato in italiano (massimo 150 parole).

Riepilogo settimana:
- Sessioni completate: {sessions}
- Distanza totale: {total_km:.1f} km
- Tempo totale: {total_min:.0f} minuti
- FC media: {avg_hr} bpm
- Sport praticati: {', '.join(sports) if sports else 'vari'}
- Obiettivo atleta: {goal}

Fornisci un consiglio motivante, specifico e pratico per la prossima settimana. Solo testo, niente JSON."""

    try:
        import anthropic  # type: ignore
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()
    except Exception:
        return (f"Questa settimana hai completato {sessions} sessioni per un totale di "
                f"{total_km:.1f} km. Ottimo lavoro! Continua così per il tuo obiettivo: {goal}.")
