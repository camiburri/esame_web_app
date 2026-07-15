import sqlite3

def get_db_connection():
    conn = sqlite3.connect('fantasy_adventure.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_sessions():
    query = """
            SELECT s.id AS id,
                   s.day AS day,
                   s.start_time AS start_time,
                   s.location AS location,
                   q.id AS quest_id,
                   q.title AS title,
                   q.duration AS duration,
                   q.type AS quest_type,
                   q.difficulty AS difficulty,
                   q.description AS description,
                   q.image AS image
            FROM Sessions s
            JOIN Quests q ON s.quest_id = q.id
            ORDER BY s.start_time
            """
    db = get_db_connection()
    sessions = db.execute(query).fetchall()
    db.close()
    return sessions

def get_all_quests():
    query = "SELECT * FROM Quests ORDER BY title"
    db = get_db_connection()
    quests = db.execute(query).fetchall()
    db.close()
    return quests


def get_session_by_id(p_session_id):
    query = """
            SELECT s.id AS id,
                   s.day AS day,
                   s.start_time AS start_time,
                   s.location AS location,
                   q.id AS quest_id,
                   q.title AS title,
                   q.duration AS duration,
                   q.type AS quest_type,
                   q.difficulty AS difficulty,
                   q.description AS description,
                   q.image AS image
            FROM Sessions s
            JOIN Quests q ON s.quest_id = q.id
            WHERE s.id = ?
            """
    db = get_db_connection()
    session = db.execute(query, (p_session_id,)).fetchone()
    db.close()
    return session

def create_quest(title, duration, quest_type, difficulty, description, image):
    query = """
        INSERT INTO Quests (title, duration, type, difficulty, description, image) 
        VALUES (?, ?, ?, ?, ?, ?)
    """
    db = get_db_connection()
    db.execute(query, (title, duration, quest_type, difficulty, description, image))
    db.commit()
    db.close()

def create_session(quest_id, day, start_time, location):
    query = "INSERT INTO Sessions (quest_id, day, start_time, location) VALUES (?, ?, ?, ?)"
    db = get_db_connection()
    db.execute(query, (quest_id, day, start_time, location))
    db.commit()
    db.close()

def delete_session(session_id):
    query = "DELETE FROM Sessions WHERE id = ?"
    db = get_db_connection()
    db.execute(query, (session_id,))
    db.commit()
    db.close()

def get_quest_by_id(quest_id):
    query = "SELECT * FROM Quests WHERE id = ?"
    db = get_db_connection()
    quest = db.execute(query, (quest_id,)).fetchone()
    db.close()
    return quest

def update_session(session_id, day, start_time, location):
    query = """
        UPDATE Sessions
        SET day = ?, start_time = ?, location = ?
        WHERE id = ?
    """
    db = get_db_connection()
    db.execute(query, (day, start_time, location, session_id))
    db.commit()
    db.close()