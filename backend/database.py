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