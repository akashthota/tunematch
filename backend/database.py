import sqlite3
from contextlib import contextmanager

DB_PATH = "tunematch.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyzed_tracks (
            track_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            tempo REAL,
            energy REAL,
            analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_cached_analysis(track_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT tempo, energy FROM analyzed_tracks WHERE track_id = ?",
            (str(track_id),),
        ).fetchone()
        if row:
            return {"tempo": row["tempo"], "energy": row["energy"]}
        return None


def save_analysis(track_id, source, tempo, energy):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO analyzed_tracks (track_id, source, tempo, energy) VALUES (?, ?, ?, ?)",
            (str(track_id), source, tempo, energy),
        )
        conn.commit()