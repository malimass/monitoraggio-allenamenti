"""
File parser module — supports FIT, TCX, GPX file formats.
Returns a dict with extracted activity metrics.
"""
from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


# ── Namespace maps ────────────────────────────────────────────────────────────

TCX_NS = {
    "tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
    "ns3": "http://www.garmin.com/xmlschemas/ActivityExtension/v2",
}
GPX_NS = {
    "gpx": "http://www.topografix.com/GPX/1/1",
    "gpxtpx": "http://www.garmin.com/xmlschemas/TrackPointExtension/v1",
}


def parse_file(file_bytes: bytes, filename: str) -> dict:
    """
    Detect format from filename extension and return a dict with keys:
        date, sport, duration_min, distance_km, avg_hr, max_hr,
        calories, elevation_m, avg_pace, file_name
    Missing values are None.
    """
    ext = Path(filename).suffix.lower()
    if ext == ".fit":
        return _parse_fit(file_bytes, filename)
    elif ext == ".tcx":
        return _parse_tcx(file_bytes, filename)
    elif ext == ".gpx":
        return _parse_gpx(file_bytes, filename)
    else:
        raise ValueError(f"Formato non supportato: {ext}. Usa FIT, TCX o GPX.")


# ── FIT parser ────────────────────────────────────────────────────────────────

def _parse_fit(data: bytes, filename: str) -> dict:
    try:
        import fitparse  # type: ignore
    except ImportError:
        raise ImportError("Installa 'fitparse' per leggere file .fit: pip install fitparse")

    f = fitparse.FitFile(io.BytesIO(data))

    total_distance = None
    total_timer_time = None
    total_calories = None
    total_ascent = None
    avg_hr = None
    max_hr = None
    sport = None
    start_time = None
    hr_samples: list[int] = []

    for record in f.get_messages():
        name = record.name
        if name == "sport":
            sport = _get_val(record, "sport") or sport
        elif name == "session":
            total_distance = _get_val(record, "total_distance") or total_distance
            total_timer_time = _get_val(record, "total_timer_time") or total_timer_time
            total_calories = _get_val(record, "total_calories") or total_calories
            total_ascent = _get_val(record, "total_ascent") or total_ascent
            avg_hr = _get_val(record, "avg_heart_rate") or avg_hr
            max_hr = _get_val(record, "max_heart_rate") or max_hr
            start_time = _get_val(record, "start_time") or start_time
            sport = _get_val(record, "sport") or sport
        elif name == "record":
            hr = _get_val(record, "heart_rate")
            if hr:
                hr_samples.append(int(hr))

    if not avg_hr and hr_samples:
        avg_hr = int(sum(hr_samples) / len(hr_samples))
    if not max_hr and hr_samples:
        max_hr = max(hr_samples)

    duration_min = (total_timer_time / 60) if total_timer_time else None
    distance_km = (total_distance / 1000) if total_distance else None
    avg_pace = _calc_pace(duration_min, distance_km)

    date_str = None
    if start_time:
        if isinstance(start_time, datetime):
            date_str = start_time.strftime("%Y-%m-%d")
        else:
            date_str = str(start_time)[:10]

    return {
        "date": date_str,
        "sport": _normalise_sport(str(sport) if sport else None),
        "duration_min": round(duration_min, 2) if duration_min else None,
        "distance_km": round(distance_km, 3) if distance_km else None,
        "avg_hr": int(avg_hr) if avg_hr else None,
        "max_hr": int(max_hr) if max_hr else None,
        "calories": int(total_calories) if total_calories else None,
        "elevation_m": round(float(total_ascent), 1) if total_ascent else None,
        "avg_pace": round(avg_pace, 2) if avg_pace else None,
        "file_name": filename,
        "notes": None,
    }


def _get_val(record, field_name):
    try:
        return record.get_value(field_name)
    except Exception:
        return None


# ── TCX parser ────────────────────────────────────────────────────────────────

def _parse_tcx(data: bytes, filename: str) -> dict:
    tree = ET.parse(io.BytesIO(data))
    root = tree.getroot()

    def find(elem, path):
        return elem.find(path, TCX_NS)

    activity = find(root, ".//tcx:Activity")
    sport = activity.attrib.get("Sport", "Sconosciuto") if activity is not None else None

    # Date
    start_time_el = find(root, ".//tcx:Activity/tcx:Id")
    date_str = None
    if start_time_el is not None and start_time_el.text:
        date_str = start_time_el.text[:10]

    # Laps aggregate
    total_time = 0.0
    total_dist = 0.0
    total_cals = 0
    total_ascent = 0.0
    hr_values: list[int] = []

    for lap in root.findall(".//tcx:Lap", TCX_NS):
        t = find(lap, "tcx:TotalTimeSeconds")
        d = find(lap, "tcx:DistanceMeters")
        c = find(lap, "tcx:Calories")
        ah = find(lap, "tcx:AverageHeartRateBpm/tcx:Value")
        if t is not None:
            total_time += float(t.text)
        if d is not None:
            total_dist += float(d.text)
        if c is not None:
            total_cals += int(c.text)
        if ah is not None:
            hr_values.append(int(ah.text))

    # Track points for max HR and elevation
    max_hr_val = 0
    prev_alt = None
    for tp in root.findall(".//tcx:Trackpoint", TCX_NS):
        hr_el = find(tp, "tcx:HeartRateBpm/tcx:Value")
        alt_el = find(tp, "tcx:AltitudeMeters")
        if hr_el is not None:
            hr = int(hr_el.text)
            if hr > max_hr_val:
                max_hr_val = hr
        if alt_el is not None:
            alt = float(alt_el.text)
            if prev_alt is not None and alt > prev_alt:
                total_ascent += alt - prev_alt
            prev_alt = alt

    duration_min = (total_time / 60) if total_time else None
    distance_km = (total_dist / 1000) if total_dist else None
    avg_hr = (sum(hr_values) // len(hr_values)) if hr_values else None
    avg_pace = _calc_pace(duration_min, distance_km)

    return {
        "date": date_str,
        "sport": _normalise_sport(sport),
        "duration_min": round(duration_min, 2) if duration_min else None,
        "distance_km": round(distance_km, 3) if distance_km else None,
        "avg_hr": avg_hr,
        "max_hr": max_hr_val if max_hr_val > 0 else None,
        "calories": total_cals if total_cals > 0 else None,
        "elevation_m": round(total_ascent, 1) if total_ascent > 0 else None,
        "avg_pace": round(avg_pace, 2) if avg_pace else None,
        "file_name": filename,
        "notes": None,
    }


# ── GPX parser ────────────────────────────────────────────────────────────────

def _parse_gpx(data: bytes, filename: str) -> dict:
    tree = ET.parse(io.BytesIO(data))
    root = tree.getroot()

    # Strip namespace prefix for easier access
    ns_uri = ""
    if root.tag.startswith("{"):
        ns_uri = root.tag.split("}")[0][1:]
    NS = {"gpx": ns_uri} if ns_uri else {}

    def find_all(elem, tag):
        if NS:
            return elem.findall(f"gpx:{tag}", NS)
        return elem.findall(tag)

    def find_one(elem, tag):
        if NS:
            return elem.find(f"gpx:{tag}", NS)
        return elem.find(tag)

    # Metadata time
    meta = find_one(root, "metadata")
    date_str = None
    if meta is not None:
        time_el = find_one(meta, "time")
        if time_el is not None:
            date_str = time_el.text[:10]

    track_points = root.findall(".//trkpt", NS) or root.findall(".//{http://www.topografix.com/GPX/1/1}trkpt")
    if not track_points:
        # Try without namespace
        track_points = root.findall(".//trkpt")

    times: list[datetime] = []
    elevations: list[float] = []
    hr_values: list[int] = []
    lats: list[float] = []
    lons: list[float] = []

    for tp in track_points:
        # Time
        t_el = tp.find("{http://www.topografix.com/GPX/1/1}time") or tp.find("time")
        if t_el is not None and t_el.text:
            try:
                dt = datetime.fromisoformat(t_el.text.replace("Z", "+00:00"))
                times.append(dt)
            except Exception:
                pass

        # Elevation
        e_el = tp.find("{http://www.topografix.com/GPX/1/1}ele") or tp.find("ele")
        if e_el is not None:
            try:
                elevations.append(float(e_el.text))
            except Exception:
                pass

        # Heart rate (Garmin extension)
        for hr_el in tp.iter("{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}hr"):
            try:
                hr_values.append(int(hr_el.text))
            except Exception:
                pass

        lats.append(float(tp.attrib.get("lat", 0)))
        lons.append(float(tp.attrib.get("lon", 0)))

    # Duration
    duration_min = None
    if len(times) >= 2:
        duration_min = (times[-1] - times[0]).total_seconds() / 60

    if date_str is None and times:
        date_str = times[0].strftime("%Y-%m-%d")

    # Distance (Haversine sum)
    distance_km = _haversine_total(lats, lons)

    # Elevation gain
    total_ascent = sum(
        max(0, elevations[i] - elevations[i - 1]) for i in range(1, len(elevations))
    )

    avg_hr = (sum(hr_values) // len(hr_values)) if hr_values else None
    max_hr = max(hr_values) if hr_values else None
    avg_pace = _calc_pace(duration_min, distance_km)

    return {
        "date": date_str,
        "sport": "Corsa",
        "duration_min": round(duration_min, 2) if duration_min else None,
        "distance_km": round(distance_km, 3) if distance_km else None,
        "avg_hr": avg_hr,
        "max_hr": max_hr,
        "calories": None,
        "elevation_m": round(total_ascent, 1) if total_ascent > 0 else None,
        "avg_pace": round(avg_pace, 2) if avg_pace else None,
        "file_name": filename,
        "notes": None,
    }


# ── Utilities ─────────────────────────────────────────────────────────────────

def _calc_pace(duration_min: float | None, distance_km: float | None) -> float | None:
    if duration_min and distance_km and distance_km > 0:
        return duration_min / distance_km
    return None


def _normalise_sport(sport: str | None) -> str:
    if not sport:
        return "Sconosciuto"
    mapping = {
        "running": "Corsa",
        "cycling": "Ciclismo",
        "swimming": "Nuoto",
        "hiking": "Trekking",
        "walking": "Camminata",
        "generic": "Generico",
        "transition": "Transizione",
        "fitness_equipment": "Palestra",
        "training": "Allenamento",
        "biking": "Ciclismo",
        "bike": "Ciclismo",
    }
    return mapping.get(sport.lower(), sport.capitalize())


def _haversine_total(lats: list[float], lons: list[float]) -> float:
    """Sum of Haversine distances in km."""
    import math
    total = 0.0
    R = 6371.0
    for i in range(1, len(lats)):
        lat1, lon1 = math.radians(lats[i - 1]), math.radians(lons[i - 1])
        lat2, lon2 = math.radians(lats[i]), math.radians(lons[i])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        total += R * 2 * math.asin(min(1, math.sqrt(a)))
    return total
