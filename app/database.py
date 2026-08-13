import sqlite3
from pathlib import Path

# Resolve relative to this file, not the process's current working directory,
# so the db path is correct no matter where the app is launched from.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "orbit.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                contact_name TEXT NOT NULL,
                job_title TEXT NOT NULL,
                company_size INTEGER NOT NULL,
                industry TEXT NOT NULL,
                website TEXT,
                intent_signal TEXT NOT NULL,
                score INTEGER NOT NULL,
                classification TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
