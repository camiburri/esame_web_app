import sqlite3

def get_db_connection():
    conn = sqlite3.connect('fantasy_adventure.db')
    conn.row_factory = sqlite3.Row
    return conn


def new_registration(p_user_id, p_session_id, p_role_category, p_places):
    query = "INSERT INTO Registrations (user_id, session_id, role_category, places) VALUES (?, ?, ?, ?)"
    db = get_db_connection()
    db.execute(query, (p_user_id, p_session_id, p_role_category, p_places))
    db.commit()
    db.close()


def get_registrations_by_user(p_user_id):
    query = """
            SELECT r.*, s.day, s.start_time, s.location, q.title, q.duration, q.type AS quest_type
            FROM Registrations r
            JOIN Sessions s ON r.session_id = s.id
            JOIN Quests q ON s.quest_id = q.id
            WHERE r.user_id = ?
            """
    db = get_db_connection()
    registrations = db.execute(query, (p_user_id,)).fetchall()
    db.close()
    return registrations


def get_registration_for_user_session(p_user_id, p_session_id):
    query = "SELECT * FROM Registrations WHERE user_id = ? AND session_id = ?"
    db = get_db_connection()
    registration = db.execute(query, (p_user_id, p_session_id)).fetchone()
    db.close()
    return registration


def get_places_taken(p_session_id):
    """Restituisce quanti posti sono occupati per sessione, per ogni ruolo."""
    query = """
            SELECT role_category, SUM(places) as places
            FROM Registrations
            WHERE session_id = ?
            GROUP BY role_category
            """
    db = get_db_connection()
    rows = db.execute(query, (p_session_id,)).fetchall()
    db.close()

    places = {"warrior": 0, "mage": 0, "healer": 0}
    for r in rows:
        role_raw = r["role_category"]

        if role_raw:
            role = role_raw.lower()
        else:
            role = ""

        if role in places:
            places[role] = r["places"]
    return places


def get_total_places_by_role():
    query = """
            SELECT role_category, SUM(places) as places
            FROM Registrations
            GROUP BY role_category
            """
    db = get_db_connection()
    rows = db.execute(query).fetchall()
    db.close()

    totals = {"warrior": 0, "mage": 0, "healer": 0}
    for r in rows:
        role_raw = r["role_category"]
        
        if role_raw:
            role = role_raw.lower()

        else:
            role = ""

        if role in totals:
            totals[role] = r["places"]    
    return totals


def get_registration_by_id(p_id):
    query = "SELECT * FROM Registrations WHERE id = ?"
    db = get_db_connection()
    registration = db.execute(query, (p_id,)).fetchone()
    db.close()
    return registration


def get_all_registrations():
    db = get_db_connection()
    registrations = db.execute("SELECT * FROM Registrations").fetchall()
    db.close()
    return registrations


def update_registration(p_id, p_role_category, p_places):
    query = "UPDATE Registrations SET role_category = ?, places = ? WHERE id = ?"
    db = get_db_connection()
    db.execute(query, (p_role_category, p_places, p_id))
    db.commit()
    db.close()


def delete_registration(p_id):
    db = get_db_connection()
    db.execute("DELETE FROM Registrations WHERE id = ?", (p_id,))
    db.commit()
    db.close()