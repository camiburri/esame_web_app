# python -m flask run --debug
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from operator import itemgetter
from models import User
import users_dao, quests_dao, registrations_dao
import os 

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config["SECRET_KEY"] = "la_tua_chiave_segreta_super_sicura_acotar"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    db_user = users_dao.get_user_by_id(user_id)
    if db_user is not None:
        return User(id=db_user["id"], username=db_user["username"], role=db_user["role"])
    return None

DAYS_ORDER = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

def session_sort_key(session):
    """Ordina prima per giorno della settimana, poi per orario di inizio."""
    day_number = DAYS_ORDER.index(session['day'])
    return day_number, session['start_time']

# Posti massimi disponibili per ogni ruolo in una quest session 
MAX_PLACES = {'warrior': 4, 'mage': 3, 'healer': 2}


def time_to_minutes(time_str):
    """Converte una stringa 'HH:MM' nel numero di minuti dalla mezzanotte,
    per poter confrontare facilmente orari di inizio/fine tra sessioni."""
    hours, minutes = time_str.split(':')
    return int(hours) * 60 + int(minutes)


# Giorno e ora "simulati" correnti nella settimana fittizia del gioco.
# Usati per decidere se una partecipazione è ancora modificabile (regola
# delle 8 ore prima dell'inizio della quest session). Valore fisso, comunicato
# agli istruttori insieme alle credenziali di test.
SIMULATED_CURRENT_DAY = 'monday'
SIMULATED_CURRENT_TIME = '19:00'


def day_time_to_week_minutes(day, time_str):
    """Converte una coppia (giorno, orario) in un numero di minuti assoluto
    all'interno della settimana fittizia (Monday 00:00 = 0), così da poter
    confrontare facilmente due momenti anche se cadono in giorni diversi."""
    day_index = DAYS_ORDER.index(day.lower())
    return day_index * 24 * 60 + time_to_minutes(time_str)


@app.route("/")
def home():

    filter_day = request.args.get('day', 'all')
    filter_type = request.args.get('type', 'all')
    filter_difficulty = request.args.get('difficulty', 'all')
    filter_role = request.args.get('role', 'all')

    session_list = quests_dao.get_all_sessions()

    sessions_filtered = []

    for s in session_list:
        # Nel DB il giorno è salvato con l'iniziale maiuscola (es. "Monday"),
        # mentre i filtri arrivano dall'URL in minuscolo (es. "monday").
        session_day = s['day'].lower()

        if filter_day != 'all' and session_day != filter_day:
            continue
        if filter_type != 'all' and s['quest_type'] != filter_type:
            continue
        if filter_difficulty != 'all' and s['difficulty'] != filter_difficulty:
            continue

        taken_places = registrations_dao.get_places_taken(s['id'])

        # Una sessione è disponibile per un ruolo solo se i posti occupati
        # non hanno ancora raggiunto il massimo previsto per quel ruolo.
        if filter_role != 'all' and taken_places[filter_role] >= MAX_PLACES[filter_role]:
            continue

        session_data = dict(s)
        session_data['day'] = session_day
        session_data['taken_places'] = taken_places
        sessions_filtered.append(session_data)

    # crea un dizionario dove ogni chiave è un giorno (es. "monday", "tuesday", ecc.)
    # e il valore associato è una lista vuota che poi riempirai con le sessioni di quel giorno.
    sessions_order_by_day = {}
    for day in DAYS_ORDER:
        sessions_order_by_day[day] = []

    for session_data in sessions_filtered:
        sessions_order_by_day[session_data['day']].append(session_data)

    current_filters = {
        'day': filter_day,
        'type': filter_type,
        'difficulty': filter_difficulty,
        'role': filter_role
    }

    return render_template('index.html', sessions_order_by_day=sessions_order_by_day, filters=current_filters)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db_user = users_dao.get_user_by_username(username)

        if not db_user:
            flash("L'utente non esiste", "danger")
            return redirect(url_for("login"))
        elif not check_password_hash(db_user["password"], password):
            flash("Password errata", "danger")
            return redirect(url_for("login"))
        else:
            new_user_obj = User(id=db_user["id"], username=db_user["username"], role=db_user["role"])
            login_user(new_user_obj)
            flash(f"Welcome {db_user['username']}!", "success")
            return redirect(url_for("home"))

    return redirect(url_for("home"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route('/profile_adventurer')
@login_required
def profile_adventurer():

    if current_user.role != 'adventurer':
        flash("This page is only available to adventurers.", "danger")
        return redirect(url_for('home'))

    pre_registrations = registrations_dao.get_registrations_by_user(current_user.id)

    # Momento "corrente" simulato, usato come riferimento per la regola delle 8 ore
    current_week_minutes = day_time_to_week_minutes(SIMULATED_CURRENT_DAY, SIMULATED_CURRENT_TIME)

    registrations = []
    for reg in pre_registrations:
        reg_data = dict(reg)

        session_week_minutes = day_time_to_week_minutes(reg_data['day'], reg_data['start_time'])
        # Modificabile solo se la quest session inizia più di 8 ore dopo il momento corrente
        reg_data['can_modify'] = (session_week_minutes - current_week_minutes) > 8 * 60

        reg_data['day'] = reg_data['day'].lower()
        registrations.append(reg_data)

    # Ordino le iscrizioni per giorno e orario, come già avviene nella home
    registrations.sort(key=session_sort_key)

    return render_template('profile_adventurer.html', registrations=registrations)

@app.route('/profile_guild')
@login_required
def profile_guild():
    if current_user.role != 'guild_master':
        flash("This page is only available to Guild Master.", "danger")
        return redirect(url_for('home'))

    pre_sessions = quests_dao.get_all_sessions()
    
    all_sessions = []

    for s in pre_sessions:
        session_dict = dict(s)
        # Sfruttiamo la funzione che hai già creato per ottenere i posti occupati per ruolo
        taken_places = registrations_dao.get_places_taken(session_dict['id'])
        session_dict['taken_places'] = taken_places
        
        # Calcoliamo il totale assoluto dei posti occupati (ci serve per bloccare i bottoni nel frontend)
        session_dict['total_taken'] = sum(taken_places.values())
        
        # Assicuriamoci che il giorno sia formattato correttamente in minuscolo per coerenza
        session_dict['day'] = session_dict['day'].lower()
        
        all_sessions.append(session_dict)
        
    # Ordiniamo le sessioni per giorno della settimana e poi per orario, così la griglia è ordinata
    all_sessions.sort(key=session_sort_key)

    # 3. Recuperiamo l'elenco di tutte le quest per popolare il form "Schedule New Session"
    all_quests = quests_dao.get_all_quests()

    return render_template('profile_guild.html', all_sessions=all_sessions, all_quests=all_quests)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash("Username, email e password sono obbligatori", "danger")
            return redirect(url_for('register'))

        if users_dao.get_user_by_username(username):
            flash("Questo username è già in uso", "danger")
            return redirect(url_for('register'))

        if users_dao.get_user_by_email(email):
            flash("Questa email è già registrata", "danger")
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        users_dao.create_user(username, email, password_hash, role="adventurer")

        flash("Registration complete! Now you can login.", "success")
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/session/<int:session_id>')
def quest_session(session_id):
    s = quests_dao.get_session_by_id(session_id)

    if s is None:
        flash("Sessione non trovata", "danger")
        return redirect(url_for('home'))

    taken_places = registrations_dao.get_places_taken(s['id'])

    quest_data = dict(s)
    quest_data['day'] = quest_data['day'].lower()
    quest_data['taken_places'] = taken_places

    return render_template('quest_session.html', quest=quest_data)


@app.route('/session/<int:session_id>/join', methods=['POST'])
@login_required
def join_quest(session_id):

    # 1. Solo gli adventurer possono iscriversi (Guild Master escluso)
    if current_user.role != 'adventurer':
        flash("Only adventurers can participate in quests.", "danger")
        return redirect(url_for('quest_session', session_id=session_id))

    session_row = quests_dao.get_session_by_id(session_id)
    if session_row is None:
        flash("Session not found.", "danger")
        return redirect(url_for('home'))

    # 2. Validazione lato server dei dati arrivati dal form
    #    (il front end limita già le scelte, ma il back end deve
    #    ricontrollare tutto perché il form potrebbe essere manipolato)
    role = request.form.get('role')
    places_raw = request.form.get('places')

    if role not in MAX_PLACES:
        flash("Ruolo non valido.", "danger")
        return redirect(url_for('quest_session', session_id=session_id))

    try:
        places = int(places_raw)
    except (TypeError, ValueError):
        flash("Numero di posti non valido.", "danger")
        return redirect(url_for('quest_session', session_id=session_id))

    if places not in (1, 2):
        flash("Puoi prenotare solo 1 o 2 posti per la stessa quest session.", "danger")
        return redirect(url_for('quest_session', session_id=session_id))

    # 3. Un adventurer non può iscriversi due volte alla stessa sessione
    already_joined = registrations_dao.get_registration_for_user_session(current_user.id, session_id)
    if already_joined:
        flash("You are already signed up for this quest session.", "warning")
        return redirect(url_for('quest_session', session_id=session_id))

    # 4. Il ruolo scelto deve avere posti sufficienti ancora liberi
    taken_places = registrations_dao.get_places_taken(session_id)
    if taken_places[role] + places > MAX_PLACES[role]:
        flash(f"There aren't enough free places as {role.capitalize()}.", "danger")
        return redirect(url_for('quest_session', session_id=session_id))

    # 5. Un adventurer può partecipare al massimo a 3 quest session a settimana
    user_registrations = registrations_dao.get_registrations_by_user(current_user.id)
    if len(user_registrations) >= 3:
        flash("You've already maxed out 3 quest sessions for this week.", "danger")
        return redirect(url_for('quest_session', session_id=session_id))

    # 6. La nuova sessione non deve sovrapporsi ad altre sessioni già
    #    prenotate dallo stesso adventurer nello stesso giorno
    new_start = time_to_minutes(session_row['start_time'])
    new_end = new_start + session_row['duration']

    for reg in user_registrations:
        if reg['day'].lower() != session_row['day'].lower():
            continue  # giorni diversi, nessuna sovrapposizione possibile

        existing_start = time_to_minutes(reg['start_time'])
        existing_end = existing_start + reg['duration']

        # due intervalli si sovrappongono se uno inizia prima che l'altro finisca
        if new_start < existing_end and existing_start < new_end:
            flash("This quest overlaps with\"{reg['title']}\", you're already subscribed to.", "danger")
            return redirect(url_for('quest_session', session_id=session_id))

    # 7. Tutti i controlli superati: registriamo l'iscrizione
    registrations_dao.new_registration(current_user.id, session_id, role.capitalize(), places)
    flash("You have successfully joined the quest!", "success")
    return redirect(url_for('quest_session', session_id=session_id))

@app.route('/registration/<int:registration_id>/modify', methods=['POST'])
@login_required
def modify_registration(registration_id):
    if current_user.role != 'adventurer':
        flash("Only adventurers can edit registrations.", "danger")
        return redirect(url_for('quest_session'))

    registration = registrations_dao.get_registration_by_id(registration_id)

    if not registration:
        flash("Registration not found.", "danger")
        return redirect(url_for('profile_adventurer'))
    
    if registration['user_id'] != current_user.id:
        flash("You can't change another adventurer's registrations.", "danger")
        return redirect(url_for('profile_adventurer'))
    
    session_row = quests_dao.get_session_by_id(registration['session_id'])
    
    current_week_minutes = day_time_to_week_minutes(SIMULATED_CURRENT_DAY, SIMULATED_CURRENT_TIME)
    session_week_minutes = day_time_to_week_minutes(session_row['day'], session_row['start_time'])

    can_modify = (session_week_minutes - current_week_minutes) > 8 * 60

    if not can_modify:
        flash("This quest starts in less than 8 hours, you can't edit it anymore.", "danger")
        return redirect(url_for('profile_adventurer'))
    
    new_role = request.form.get('role').lower()

    try:
        new_places = int(request.form.get('places'))
    except (TypeError, ValueError):
        flash("Invalid number of places.", "danger")
        return redirect(url_for('profile_adventurer'))
    
    if new_role not in MAX_PLACES or new_places not in (1,2):
        flash("Role or number of places invalid.", "danger")
        return redirect(url_for('profile_adventurer'))
    
    taken_places = registrations_dao.get_places_taken(registration['session_id'])
    current_role = registration['role_category'].lower()
    current_places = registration['places']

    # Logica fondamentale: calcoliamo quanti posti sono occupati *dagli altri giocatori* nel ruolo scelto
    places_taken_by_others = taken_places[new_role]
    if current_role == new_role:
        # Se sto rimanendo nello stesso ruolo, tolgo i MIEI posti attuali dal totale calcolato
        places_taken_by_others -= current_places
    
    # Ora posso verificare se aggiungendo i miei nuovi posti supero il limite
    if places_taken_by_others + new_places > MAX_PLACES[new_role]:
        flash(f"There aren't enough free places as {new_role.capitalize()}.", "danger")
        return redirect(url_for('profile_adventurer'))

    # 7. Tutto okay, aggiorno il database
    registrations_dao.update_registration(registration_id, new_role.capitalize(), new_places)
    flash("Successfully edited registration!", "success")
    return redirect(url_for('profile_adventurer'))  

@app.route('/registration/<int:registration_id>/cancel', methods=['POST'])
@login_required
def cancel_registration(registration_id):

    # 1. La registrazione deve esistere
    registration = registrations_dao.get_registration_by_id(registration_id)
    if registration is None:
        flash("Registration not found.", "danger")
        return redirect(url_for('profile_adventurer'))

    # 2. Deve appartenere all'utente attualmente loggato: un adventurer non
    #    può cancellare le iscrizioni di un altro adventurer
    if registration['user_id'] != current_user.id:
        flash("You can't unsubscribe another adventurer.", "danger")
        return redirect(url_for('profile_adventurer'))

    # 3. Recupero la sessione collegata, per sapere quando inizia la quest
    session_row = quests_dao.get_session_by_id(registration['session_id'])
    if session_row is None:
        flash("Session not found.", "danger")
        return redirect(url_for('profile_adventurer'))

    # 4. Regola delle 8 ore: stesso calcolo già usato in profile_adventurer()
    current_week_minutes = day_time_to_week_minutes(SIMULATED_CURRENT_DAY, SIMULATED_CURRENT_TIME)
    session_week_minutes = day_time_to_week_minutes(session_row['day'], session_row['start_time'])
    can_modify = (session_week_minutes - current_week_minutes) > 8 * 60

    if not can_modify:
        flash("This quest starts in less than 8 hours: you can no longer unsubscribe.", "danger")
        return redirect(url_for('profile_adventurer'))

    # 5. Tutti i controlli superati: cancello la registrazione
    registrations_dao.delete_registration(registration_id)
    flash("Registration successfully deleted.", "success")
    return redirect(url_for('profile_adventurer'))

@app.route('/create_quest', methods=['POST'])
@login_required
def create_quest():
    if current_user.role != 'guild_master':
        flash("You don't have permission to create a quest.", "danger")
        return redirect(url_for('home'))

    title = request.form.get('title')
    quest_type = request.form.get('type')
    difficulty = request.form.get('difficulty')
    duration = request.form.get('duration')
    description = request.form.get('description')

    # CORREZIONE 1: Usare request.files per le immagini
    image_file = request.files.get('image')
    
    # CORREZIONE 2: Risolto il typo "filenaame" in "filename"
    if image_file and image_file.filename != '':
        secs = int(datetime.now().timestamp())
        ext = image_file.filename.split(".")[-1]
        img_name = str(secs) + "." + ext
        
        # Salva l'immagine usando il nuovo percorso
        upload_path = os.path.join(BASE_DIR, 'static', 'images', img_name)
        image_file.save(upload_path)
        
        # Salvataggio nel DB con l'immagine personalizzata
        quests_dao.create_quest(title, int(duration), quest_type, difficulty, description, img_name)
    else:
        # CORREZIONE 4: Blocco else nel caso in cui non venga caricata alcuna immagine
        quests_dao.create_quest(title, int(duration), quest_type, difficulty, description, "default_quest.png")
        
    flash("Quest created successfully!", "success")
    return redirect(url_for('profile_guild'))


@app.route('/schedule_session', methods=['POST'])
@login_required
def schedule_session():
    if current_user.role != 'guild_master':
        flash("You do not have permission to schedule a session.", "danger")
        return redirect(url_for('home'))

    quest_id = request.form.get('quest_id')
    day = request.form.get('day')
    start_time = request.form.get('start_time')
    location = request.form.get('location')

    # Recuperiamo la durata della quest per calcolare quando finirà la sessione
    quest = quests_dao.get_quest_by_id(quest_id)
    if not quest:
        flash("Quest non trovata.", "danger")
        return redirect(url_for('profile_guild'))

    new_start = time_to_minutes(start_time)
    new_end = new_start + quest['duration']

    # Controllo Sovrapposizioni (Location, Day, Time)
    all_sessions = quests_dao.get_all_sessions()
    for s in all_sessions:
        if s['location'] == location and s['day'].lower() == day.lower():
            existing_start = time_to_minutes(s['start_time'])
            existing_end = existing_start + s['duration']
            
            # Se la nuova inizia prima che l'altra finisca e viceversa, c'è sovrapposizione
            if new_start < existing_end and existing_start < new_end:
                flash(f"Unable to schedule: The location '{location}' is already occupied in that time slot by another session.", "danger")
                return redirect(url_for('profile_guild'))

    # Se tutti i controlli sono passati, creiamo la sessione
    quests_dao.create_session(quest_id, day, start_time, location)
    flash("New session successfully scheduled!", "success")
    return redirect(url_for('profile_guild'))


@app.route('/session/<int:session_id>/delete', methods=['POST'])
@login_required
def delete_session(session_id):
    if current_user.role != 'guild_master':
        flash("You do not have permission to cancel this session.", "danger")
        return redirect(url_for('home'))

    # Controllo che non ci siano iscritti (total_taken == 0)
    taken_places = registrations_dao.get_places_taken(session_id)
    total_taken = sum(taken_places.values())
    
    if total_taken > 0:
        flash("Cannot be deleted: there are already adventurers registered for this session.", "danger")
        return redirect(url_for('profile_guild'))

    quests_dao.delete_session(session_id)
    flash("Session successfully cancelled..", "success")
    return redirect(url_for('profile_guild'))

@app.route('/session/<int:session_id>/modify_guild', methods=['POST'])
@login_required
def modify_session_guild(session_id):
    if current_user.role != 'guild_master':
        flash("You do not have permission to edit this session.", "danger")
        return redirect(url_for('home'))
    
    taken_places = registrations_dao.get_places_taken(session_id)
    total_taken = sum(taken_places.values())

    if total_taken > 0:
        flash("Unable to edit: There are already adventurers registered for this session.", "danger")
        return redirect(url_for('profile_guild'))
    
    new_day = request.form.get('day').lower()
    new_start_time = request.form.get('start_time')
    new_location = request.form.get('location')

    # 4. Recupera i dettagli attuali per ottenere la durata della quest
    session_to_edit = quests_dao.get_session_by_id(session_id)
    if not session_to_edit:
        flash("Session not found.", "danger")
        return redirect(url_for('profile_guild'))
    
    new_start = time_to_minutes(new_start_time)
    new_end = new_start + session_to_edit['duration']

    # 5. Controllo sovrapposizioni con ALTRE sessioni
    all_sessions = quests_dao.get_all_sessions()
    for s in all_sessions:
        # Escludiamo dal controllo la sessione stessa che stiamo modificando (s['id'] != session_id)
        if s['id'] != session_id and s['location'] == new_location and s['day'].lower() == new_day:
            existing_start = time_to_minutes(s['start_time'])
            existing_end = existing_start + s['duration']
            
            # Se i tempi si accavallano
            if new_start < existing_end and existing_start < new_end:
                flash(f"Unable to change: The location '{new_location}' is already occupied in that time slot by another session.", "danger")
                return redirect(url_for('profile_guild'))
    
    # 6. Salva le modifiche nel database se tutto va bene
    quests_dao.update_session(session_id, new_day, new_start_time, new_location)
    flash("Session updated successfully!", "success")
    return redirect(url_for('profile_guild'))       

@app.route('/administrator')
@login_required
def profile_administrator():
    if current_user.role != 'guild_council_administrator':
        flash("Access denied. This page is for the Guild Council administrator only.", "danger")
        return redirect(url_for('home'))
    
    # 1. Lista di tutti gli adventurer registrati, con il numero di quest a cui partecipano
    pre_adventurers = users_dao.get_all_adventurers()
    all_users = []
    for a in pre_adventurers:
        user_data = dict(a)
        user_data['participations_count'] = len(registrations_dao.get_registrations_by_user(a['id']))
        all_users.append(user_data)

    # 2. Tutte le sessioni della settimana, con posti occupati per ruolo (stessa logica di profile_guild)
    pre_sessions = quests_dao.get_all_sessions()
    all_sessions = []
    for s in pre_sessions:
        session_dict = dict(s)
        taken_places = registrations_dao.get_places_taken(session_dict['id'])
        session_dict['taken_places'] = taken_places
        session_dict['total_taken'] = sum(taken_places.values())
        session_dict['day'] = session_dict['day'].lower()
        all_sessions.append(session_dict)

    all_sessions.sort(key=session_sort_key)

    # 3. Tutte le quest, usate per raggruppare le sessioni per quest nel template
    all_quests = quests_dao.get_all_quests()

    # 4. Statistiche generali della gilda
    places_by_type = {}
    for s in all_sessions:
        places_by_type[s['quest_type']] = places_by_type.get(s['quest_type'], 0) + s['total_taken']
    most_popular_type = max(places_by_type, key=places_by_type.get) if places_by_type else None

    busiest_sessions = []
    max_partecipanti = 0
    for session in all_sessions:
        if session['total_taken'] > max_partecipanti:
            max_partecipanti = session['total_taken']
            busiest_sessions = [session]
        elif session['total_taken'] == max_partecipanti:
            busiest_sessions.append(session)

    stats = {
        'total_adventurers': len(all_users),
        'total_quests': len(all_quests),
        'total_sessions': len(all_sessions),
        'total_participations': len(registrations_dao.get_all_registrations()),
        'places_by_role': registrations_dao.get_total_places_by_role(),
        'most_popular_type': most_popular_type,
        'busiest_sessions': busiest_sessions
    }

    return render_template(
        'profile_administrator.html',
        all_users=all_users,
        all_sessions=all_sessions,
        all_quests=all_quests,
        stats=stats
    )