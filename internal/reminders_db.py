import sqlite3
import logging
import datetime
from internal.logs import logger

DB_PATH = "./internal/data/databases/reminders.db"

def setup():
    """Initializes the database and creates the reminders table if it doesn't exist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                due_time DATETIME NOT NULL,
                reminder_message TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        logger.LogPrint(f"ERROR - Could not initialize reminders database: {e}", logging.ERROR)

def add_reminder(user_id, channel_id, due_time, message):
    """Adds a new reminder to the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO reminders (user_id, channel_id, due_time, reminder_message) VALUES (?, ?, ?, ?)",
                  (user_id, channel_id, due_time, message))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.LogPrint(f"ERROR - Could not add reminder to database: {e}", logging.ERROR)

def get_due_reminders():
    """Fetches all reminders that are due."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        c.execute("SELECT * FROM reminders WHERE due_time <= ?", (now,))
        reminders = c.fetchall()
        conn.close()
        return reminders
    except Exception as e:
        logger.LogPrint(f"ERROR - Could not get due reminders: {e}", logging.ERROR)
        return []

def delete_reminder(reminder_id):
    """Deletes a reminder from the database by its ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.LogPrint(f"ERROR - Could not delete reminder from database: {e}", logging.ERROR)
