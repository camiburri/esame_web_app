import sqlite3
import os

# nuovo path 
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'fantasy_adventure.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_id(user_id):
    db = get_db_connection()
    user = db.execute('SELECT * FROM Users WHERE id = ?', (user_id,)).fetchone()
    db.close()
    return user

def get_user_by_username(username):
    db = get_db_connection()
    user = db.execute('SELECT * FROM Users WHERE username = ?', (username,)).fetchone()
    db.close()
    return user

def get_user_by_email(email):
    db = get_db_connection()
    user = db.execute('SELECT * FROM Users WHERE email = ?', (email,)).fetchone()
    db.close()
    return user

def get_all_adventurers():
    """Restituisce tutti gli utenti con ruolo 'adventurer', usato dalla pagina
    del Guild Council administrator per elencare gli avventurieri registrati."""
    db = get_db_connection()
    users = db.execute(
        "SELECT * FROM Users WHERE role = 'adventurer' ORDER BY username"
    ).fetchall()
    db.close()
    return users


def create_user(username, email, password_hash, role="adventurer"):
    db = get_db_connection()
    db.execute(
        'INSERT INTO Users (username, email, password, role) VALUES (?, ?, ?, ?)',
        (username, email, password_hash, role)
    )
    db.commit()
    db.close()