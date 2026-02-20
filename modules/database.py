"""
Database module — SQLite backend for the Live Coach app.
Tables: users, profiles, activities, coach_notes
"""
import sqlite3
import hashlib
from pathlib import Path

DB_PATH = Path("data/coach.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        PRAGMA journal_mode=WAL;

        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            email         TEXT,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL DEFAULT 'user',
            coach_id      INTEGER,
            active        INTEGER NOT NULL DEFAULT 1,
            created_at    TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (coach_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS profiles (
            user_id      INTEGER PRIMARY KEY,
            name         TEXT,
            surname      TEXT,
            height_cm    REAL,
            weight_kg    REAL,
            sex          TEXT,
            birth_year   INTEGER,
            goal         TEXT,
            sport        TEXT,
            fitness_level TEXT DEFAULT 'principiante',
            target_notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS activities (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            date          TEXT,
            sport         TEXT,
            duration_min  REAL,
            distance_km   REAL,
            avg_hr        INTEGER,
            max_hr        INTEGER,
            calories      INTEGER,
            elevation_m   REAL,
            avg_pace      REAL,
            file_name     TEXT,
            notes         TEXT,
            created_at    TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS coach_notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            coach_id   INTEGER NOT NULL,
            user_id    INTEGER NOT NULL,
            date       TEXT,
            note       TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (coach_id) REFERENCES users(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    # Default admin
    admin_hash = hash_password("admin123")
    c.execute(
        "INSERT OR IGNORE INTO users (username, email, password_hash, role) VALUES (?,?,?,?)",
        ("admin", "admin@livecoach.app", admin_hash, "admin"),
    )
    conn.commit()
    conn.close()


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


# ── User helpers ──────────────────────────────────────────────────────────────

def get_user(username: str) -> sqlite3.Row | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username=? AND active=1", (username,)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id: int) -> sqlite3.Row | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return row


def create_user(username: str, email: str, password: str,
                role: str = "user", coach_id: int | None = None) -> bool:
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO users (username, email, password_hash, role, coach_id) VALUES (?,?,?,?,?)",
            (username, email, hash_password(password), role, coach_id),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_all_users() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT id, username, email, role, coach_id, created_at, active FROM users ORDER BY role, username").fetchall()
    conn.close()
    return rows


def update_user_role(user_id: int, role: str):
    conn = get_connection()
    conn.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
    conn.commit()
    conn.close()


def assign_coach(user_id: int, coach_id: int | None):
    conn = get_connection()
    conn.execute("UPDATE users SET coach_id=? WHERE id=?", (coach_id, user_id))
    conn.commit()
    conn.close()


def toggle_user_active(user_id: int, active: bool):
    conn = get_connection()
    conn.execute("UPDATE users SET active=? WHERE id=?", (1 if active else 0, user_id))
    conn.commit()
    conn.close()


def get_coach_clients(coach_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT u.id, u.username, u.email, u.created_at FROM users u WHERE u.coach_id=? AND u.active=1",
        (coach_id,)
    ).fetchall()
    conn.close()
    return rows


def get_coaches() -> list:
    conn = get_connection()
    rows = conn.execute("SELECT id, username FROM users WHERE role='coach' AND active=1").fetchall()
    conn.close()
    return rows


# ── Profile helpers ───────────────────────────────────────────────────────────

def get_profile(user_id: int) -> sqlite3.Row | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row


def upsert_profile(user_id: int, data: dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO profiles (user_id, name, surname, height_cm, weight_kg, sex, birth_year, goal, sport, fitness_level, target_notes)
        VALUES (:user_id,:name,:surname,:height_cm,:weight_kg,:sex,:birth_year,:goal,:sport,:fitness_level,:target_notes)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name, surname=excluded.surname,
            height_cm=excluded.height_cm, weight_kg=excluded.weight_kg,
            sex=excluded.sex, birth_year=excluded.birth_year,
            goal=excluded.goal, sport=excluded.sport,
            fitness_level=excluded.fitness_level, target_notes=excluded.target_notes
    """, {"user_id": user_id, **data})
    conn.commit()
    conn.close()


# ── Activity helpers ──────────────────────────────────────────────────────────

def insert_activity(user_id: int, data: dict) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO activities
            (user_id, date, sport, duration_min, distance_km, avg_hr, max_hr, calories, elevation_m, avg_pace, file_name, notes)
        VALUES
            (:user_id,:date,:sport,:duration_min,:distance_km,:avg_hr,:max_hr,:calories,:elevation_m,:avg_pace,:file_name,:notes)
    """, {"user_id": user_id, **data})
    activity_id = cur.lastrowid
    conn.commit()
    conn.close()
    return activity_id


def get_activities(user_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM activities WHERE user_id=? ORDER BY date DESC", (user_id,)
    ).fetchall()
    conn.close()
    return rows


def delete_activity(activity_id: int, user_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM activities WHERE id=? AND user_id=?", (activity_id, user_id))
    conn.commit()
    conn.close()


# ── Coach notes helpers ───────────────────────────────────────────────────────

def insert_coach_note(coach_id: int, user_id: int, note: str, date: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO coach_notes (coach_id, user_id, note, date) VALUES (?,?,?,?)",
        (coach_id, user_id, note, date),
    )
    conn.commit()
    conn.close()


def get_coach_notes(user_id: int) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT cn.date, cn.note, u.username as coach_name
        FROM coach_notes cn
        JOIN users u ON u.id = cn.coach_id
        WHERE cn.user_id=?
        ORDER BY cn.created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return rows


# ── Admin stats helpers ───────────────────────────────────────────────────────

def get_system_stats() -> dict:
    conn = get_connection()
    c = conn.cursor()
    total_users   = c.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0]
    total_coaches = c.execute("SELECT COUNT(*) FROM users WHERE role='coach'").fetchone()[0]
    total_admins  = c.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
    total_acts    = c.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
    total_notes   = c.execute("SELECT COUNT(*) FROM coach_notes").fetchone()[0]
    active_users  = c.execute("SELECT COUNT(*) FROM users WHERE active=1").fetchone()[0]
    conn.close()
    return {
        "total_users": total_users,
        "total_coaches": total_coaches,
        "total_admins": total_admins,
        "total_activities": total_acts,
        "total_notes": total_notes,
        "active_users": active_users,
    }


def update_user_password(user_id: int, new_password: str):
    conn = get_connection()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?",
                 (hash_password(new_password), user_id))
    conn.commit()
    conn.close()


def get_all_activities_admin() -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT a.*, u.username
        FROM activities a
        JOIN users u ON u.id = a.user_id
        ORDER BY a.date DESC LIMIT 100
    """).fetchall()
    conn.close()
    return rows
