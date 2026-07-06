import sqlite3

DB_FILE = "morphic.db"

def connect():
    return sqlite3.connect(DB_FILE)

def initialize_db():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS keys (
        location TEXT PRIMARY KEY,
        data TEXT
    )
    """)

    conn.commit()
    conn.close()

def save_key(location, data):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO keys (location, data)
    VALUES (?, ?)
    """, (location, data))

    conn.commit()
    conn.close()

def get_stored_key(location):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT data FROM keys WHERE location=?", (location,))
    result = cursor.fetchone()

    conn.close()

    return result[0] if result else None