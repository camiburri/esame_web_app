import sqlite3
from werkzeug.security import generate_password_hash

def populate_db():
    conn = sqlite3.connect('fantasy_adventure.db')
    cursor = conn.cursor()

    print("Wiping existing data from the database...")
    cursor.execute('DELETE FROM Registrations')
    cursor.execute('DELETE FROM Sessions')
    cursor.execute('DELETE FROM Quests')
    cursor.execute('DELETE FROM Users')

    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('Registrations', 'Sessions', 'Quests', 'Users')")
    except sqlite3.OperationalError:
        pass

    print("Inserting 6 sample users...")

    users_data = [
        ('Rhysand', 'rhysand@nightcourt.com', generate_password_hash('password123'), 'guild_master'),
        ('Feyre', 'feyre@nightcourt.com', generate_password_hash('password123'), 'adventurer'),
        ('Cassian', 'cassian@nightcourt.com', generate_password_hash('password123'), 'adventurer'),
        ('Azriel', 'azriel@nightcourt.com', generate_password_hash('password123'), 'adventurer'),
        ('Nesta', 'nesta@nightcourt.com', generate_password_hash('password123'), 'adventurer'),
        ('Cauldron', 'cauldron@prythian.com', generate_password_hash('password123'), 'guild_council_administrator')
    ]
    cursor.executemany('''
        INSERT INTO Users (username, email, password, role)
        VALUES (?, ?, ?, ?)
    ''', users_data)

    print("Inserting 7 thematic Quests...")
    quests_data = [
        
        ('Infiltration Under the Mountain', 180, 'stealth', 'legendary', 
         'Bypass Amarantha\'s elite patrols to recover an ancient Spring Court artifact. The slightest distraction will be fatal.', 'under_mountain.png'),
        
        ('Blood Rite Survival Challenge', 240, 'survival', 'hard', 
         'Scale the slopes of Mount Ramiel without active magic or guild weapons. Only your raw physical endurance and team cooperation will allow you to reach the monolith.', 'blood_rite.png'),
        
        ('Hunting the Weaver in the Wood', 120, 'combat', 'legendary', 
         'Retrieve the ancestral ring of the Night Court from the Weaver\'s cottage. A single misstep will awaken her lethal melody.', 'weaver_cottage.png'),
        
        ('Riddle of the Book of Breathings', 90, 'puzzle', 'medium', 
         'Decode the hidden symbols of the Book of Leshon within the Summer Court vaults. Beware of the structural illusion traps.', 'breath_of_life.png'),
        
        ('Shadowing the Court of Nightmares', 60, 'exploration', 'easy', 
         'Map the secret pathways and tunnels within the dark faction of the Nightmare Court. Gather critical intel on Keir\'s political moves.', 'nightmare_court.png'),
        
        ('Sealing Velaris Magic Anomalies', 100, 'magic', 'medium', 
         'Seal the volatile rifts opening in the protective ward of the City of Starlight before continent scouts can track its position.', 'velaris_magic.png'),
        
        ('Containment of the Library Shadows', 120, 'combat', 'hard', 
         'The dark entities confined in the lower levels are stirring in Bryaxis\'s absence. Descend into the depths, team up with your companions, and fend off the nameless horrors before they reach the upper floors and the priestesses.', '1783960249.png')
    ]
    cursor.executemany('''
        INSERT INTO Quests (title, duration, type, difficulty, description, image)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', quests_data)

    print("Scheduling 14 weekly Sessions (2 sessions per day)...")
    sessions_data = [
        
        (1, 'Monday', '10:00', 'The middle'),
        (2, 'Monday', '15:00', 'Velaris'),
        
        (3, 'Tuesday', '09:00', 'The mountain of Ramiel'),
        (4, 'Tuesday', '16:00', 'The middle'),
        
        (5, 'Wednesday', '11:00', 'Velaris'),
        (6, 'Wednesday', '18:00', 'The mountain of Ramiel'),
        
        (1, 'Thursday', '14:00', 'The middle'),
        (2, 'Thursday', '20:00', 'Velaris'),
        
        (3, 'Friday', '10:00', 'The mountain of Ramiel'),
        (4, 'Friday', '17:00', 'The middle'),
        
        (5, 'Saturday', '15:00', 'Velaris'),
        (6, 'Saturday', '21:00', 'The mountain of Ramiel'),
        
        (1, 'Sunday', '08:00', 'The middle'),
        (5, 'Sunday', '17:00', 'The mountain of Ramiel')
    ]
    cursor.executemany('''
        INSERT INTO Sessions (quest_id, day, start_time, location)
        VALUES (?, ?, ?, ?)
    ''', sessions_data)

    print("Adding mock test Registrations...")
    registrations_data = [
        
        (2, 1, 'Warrior', 2),  # Feyre reserves 2 spots as a Warrior (2/4)
        (3, 1, 'Warrior', 2),  # Cassian reserves 2 spots as a Warrior (4/4 )
        
        (4, 2, 'Mage', 1),     # Azriel joins as a Mage in Session 2
        (5, 3, 'Healer', 1)    # Nesta joins as a Healer in Session 3
    ]
    cursor.executemany('''
        INSERT INTO Registrations (user_id, session_id, role_category, places)
        VALUES (?, ?, ?, ?)
    ''', registrations_data)

    conn.commit()
    conn.close()
    
    print("\n Database 'fantasy_adventure.db' successfully populated")
    print("Test Accounts generated (Password for all accounts: 'password123'):")
    print("   - Guild Master: Rhysand (rhysand@nightcourt.com)")
    print("   - Adventurers: Feyre, Cassian, Azriel, Nesta")

if __name__ == '__main__':
    populate_db()