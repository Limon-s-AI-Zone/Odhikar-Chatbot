import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "odhikar.db")

def clean_database():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get all table names except sqlite internal tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()

        for (table_name,) in tables:
            cursor.execute(f"DELETE FROM {table_name};")
            print(f"Deleted all rows from table: {table_name}")

        # Reset SQLite sequence / autoincrement counters if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';")
        if cursor.fetchone():
            cursor.execute("DELETE FROM sqlite_sequence;")
            print("Reset autoincrement sequences.")

        conn.commit()
        # Reclaim unused space
        cursor.execute("VACUUM;")
        print("Database successfully cleaned and vacuumed.")
    except Exception as e:
        conn.rollback()
        print(f"Error cleaning database: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    clean_database()
