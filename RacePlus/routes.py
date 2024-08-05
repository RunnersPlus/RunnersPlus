import json, secrets, csv, os, subprocess, re,requests, pathlib, google.auth.transport.requests
from RacePlus import app, db, bcrypt, mail,login_manager
from flask import  url_for, render_template, flash, redirect, request,abort,session
from RacePlus.forms import HiddenForm, RegistrationForm,  LoginForm, ResetRequestForm, ResetPasswordForm, AccountUpdateForm, EventForm, ShowEventForm,UploadForm
from RacePlus.models import User, UserDetails, Event, Event_Category,user_event
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from flask_login import LoginManager
from sqlalchemy import update

from pip._vendor import cachecontrol
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from RacePlus import GOOGLE_CLIENT_ID, CITIES_DATA
from sqlalchemy import asc
from werkzeug.utils import secure_filename
from datetime import datetime

login_manager.init_app(app)

#
#--------------   google login  ---------------------
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)
@app.route('/show_all_results_for_a_user', methods=['POST', 'GET'])
def show_all_results_for_a_user():
    #TODO
    # <th class="small sortable" onclick="sortTable(2)">Διοργανωτής</th>
    # <th class="small sortable" onclick="sortTable(3)">Πόλη</th>
    # <th class="small sortable" onclick="sortTable(4)">Start time</th>
    # <th class="small sortable" onclick="sortTable(5)">End time</th>
    # <th class="small sortable" onclick="sortTable(6)">Net time</th>
    # <th class="small sortable" onclick="sortTable(7)">Θέση γενική</th>
    # <th class="small sortable" onclick="sortTable(8)">Θέση στο φύλο</th>
    # <th class="small sortable" onclick="sortTable(9)">Θέση κατηγορίας</th>


    all_results = []
    for event in current_user.enroll:
        city=''
        for user in event.enrolled:
            if user.details.role=='admin':
                city = user.details.city
                break
                
        for user in event.enrolled:
            if user.id == current_user.id:
                # Query για την ανάκτηση των start_time και end_time
                user_event_record = db.session.query(user_event).filter(
                    user_event.c.user_id == user.id,
                    user_event.c.event_id == event.id
                ).first()

                if user_event_record:
                    net_time = seconds_to_time(time_to_seconds(user_event_record.end_time) - time_to_seconds(user_event_record.start_time))

                    event_data = {
                        "racename": event.racename,
                        "year": event.date.year,
                        "distance": event.distance,
                        "city": city,
                        "start_time": user_event_record.start_time,
                        "end_time": user_event_record.end_time,
                        "net_time": net_time
                    }
            
                    all_results.append(event_data)

    all = []
    for event in current_user.enroll:
            for user in event.enrolled:
                user_event_record = db.session.query(user_event).filter(
                    user_event.c.user_id == user.id,
                    user_event.c.event_id == event.id
                ).first()
                if user_event_record:
                    if user_event_record.end_time!='' and user_event_record.end_time!=None: 
                        net_time = seconds_to_time(time_to_seconds(user_event_record.end_time) - time_to_seconds(user_event_record.start_time))
                        user_data = {
                            "user_id": user.id,  
                            "net_time": net_time,
                            "gender": user.details.gender,
                            "age": int(event.date.year) - int(user.details.year_of_birth)
                        }
                        
                        all.append(user_data)
    
    sorted_all = sorted(all, key=lambda x: time_to_seconds(x['net_time']))
    position_net_time = next((index for index, entry in enumerate(sorted_all, start=1) if entry['user_id'] ==current_user.id), None)
    filtered_by_gender = [entry for entry in all if entry['gender'] == current_user.details.gender]
    sorted_by_gender_and_time = sorted(filtered_by_gender, key=lambda x: x['net_time'])
    position_gender_net_time = next((index for index, entry in enumerate(sorted_by_gender_and_time, start=1) if entry['user_id'] == current_user.id), None)
    # Βρίσκουμε την ηλικιακή κατηγορία του current_user
    age_cat = int(event.date.year) - int(user.details.year_of_birth)
    current_user_age_category_gender = get_age_category(age_cat)
    print('user:',current_user,current_user.id,'current_user_age_category_gender=',current_user_age_category_gender)
    # Φιλτράρισμα της λίστας all ώστε να περιλαμβάνει μόνο τους χρήστες στην ίδια ηλικιακή κατηγορία
    filtered_by_age_category_gender = [
        entry for entry in all 
        if get_age_category(entry['age']) == current_user_age_category_gender and  entry['gender'] == current_user.details.gender
    ]
    sorted_by_age_category_gender = sorted(filtered_by_age_category_gender, key=lambda x: x['net_time'])

    position_age_category_gender = 0
    print('sorted_by_age_category_gender=',sorted_by_age_category_gender)
    for i in sorted_by_age_category_gender:
        position_age_category_gender += 1
        if i['user_id'] == current_user.id:
           break
    print('position_age_category_gender=',position_age_category_gender)

   
    return render_template('show_all_results_for_a_user.html',all_results=all_results,
                           position_net_time=position_net_time,
                           position_gender_net_time=position_gender_net_time,
                           position_age_category_gender=position_age_category_gender, 
                           category=current_user_age_category_gender)

# Ορισμός της ηλικιακής κατηγορίας βάσει της ηλικίας
def get_age_category(age):
    if age < 18:
        return 'Κάτω των 18'
    elif 18 <= age < 30:
        return '18-29'
    elif 30 <= age < 40:
        return '30-39'
    elif 40 <= age < 50:
        return '40-49'
    else:
        return '50+'


@app.route('/assign_athletes_ids/<int:event_id>', methods=['POST', 'GET'])
def assign_athletes_ids(event_id):
    if current_user.is_authenticated  :
        if current_user.details.role == 'admin' or current_user.details.role=='super_admin': 
            # Έχει ήδη ελεγχθεί ότι είναι ο δημιουργός του event είναι ο current_user(admin)

            event = db.session.query(Event).filter_by(id=event_id).first()
            participants = db.session.query(User).join(user_event).join(Event).filter(
                Event.id == event_id,
                User.details.has(UserDetails.role != 'admin'),
                User.details.has(UserDetails.role != 'super_admin')
            ).add_columns(user_event.c.tag_id).all()

            participants_details = [
                {
                    "user_id": participant.details.id,
                    "firstname": participant.details.firstname,
                    "lastname": participant.details.lastname,
                    "club": participant.details.club,
                    "city": participant.details.city,
                    "id_tag": tag_id  #  το tag_id από τον πίνακα user_event
                }
                for participant, tag_id in participants
            ]
            participants_details = sorted(participants_details, key=lambda x: (x['lastname'], x['firstname']))
            if request.method == 'POST': 
                # Ενημέρωση των id_tag με τις τιμές από τη φόρμα
                for index, participant in enumerate(participants):
                    participants_details[index]["id_tag"] = request.form.get(f"id_tag_{index + 1}")
                # Ενημέρωση του πίνακα user_id της  ΒΔ 
                for participant in participants_details:
                    user_id = participant['user_id']
                    id_tag = participant['id_tag']
                    
                    db.session.execute(
                        update(user_event).
                        where(user_event.c.user_id == user_id).
                        values(tag_id=id_tag)
                    )

                # Εφαρμογή των αλλαγών στη βάση δεδομένων
                db.session.commit()
                flash('Τα id tags των συμμετεχόντων αθλητών ενημερώθηκαν.')
            return render_template('assign_athletes_ids.html', event_id=event_id,event_racename=event.racename, participants_details = participants_details, event_fee=event.entry_fee)
           
    
    return redirect("/show_events")


def process_lines_from_list(lines,event_id):
    # Συνάρτηση για επεξεργασία κάθε γραμμής των δεδομένων χρονομέτρησης
    # Επιστρέφει λίστα με τις εγγραφές που βρέθηκαν από 1 φορά (αφαιρεί τις πολλαπλές)
    # πριν και μετά το ALL_PASS_FROM_START_POINT. Επιστρέφει και τις λάθος εγγραφές

   
    pattern = r"\d{2}:\d{2}:\d{2}:\d{2}"  # Προσθήκη του pattern για την αντιστοίχιση του χρόνου
 
    participants = db.session.query(
        user_event.c.tag_id,
        user_event.c.start_time,
        user_event.c.end_time
    ).join(User).join(Event).filter(
        Event.id == event_id,
        User.details.has(UserDetails.role != 'admin'),
        User.details.has(UserDetails.role != 'super_admin')
    ).all()

    # όλα τα ids που έχουν οι συμμετέχοντες (1ο πεδίο εγγραφής)
    tag_ids = [int(participant[0]) for participant in participants]
    all=[]
    for line in lines:
        tag_id = line[0]
        timestamp1 = line[1]
        timestamp2 = line[2]
        # error_type = line[3]

        error_type=''
        if len(tag_id) != 24:
            error_type = 'Το ID πρέπει να έχει 24 ψηφία'
        else:
            try:
                int(tag_id)
                # υπάρχει αυτό το ID?
                if int(tag_id) not in tag_ids:
                    error_type = 'Αυτό το ID δεν έχει αποδοθεί σε δρομέα'
                elif not re.match(pattern, timestamp1):
                    error_type ='Λάθος στο χρόνο εκκίνησης (00:00:00:00)' 
                elif not re.match(pattern, timestamp2):
                    error_type = 'Λάθος στο χρόνο τερματισμού (00:00:00:00)'
            except ValueError:
                error_type = 'Το ID πρέπει να περιέχει μόνο αριθμητικά ψηφία'
        record = [tag_id, timestamp1, timestamp2, error_type]
        all.append(record)

    errors = []
    for entry in all:
        if entry[3] is not None and entry[3] !='':
            errors.append(entry)

    if not errors:

        # αποθήκευση δεδομένων σε αρχείο
        save_data(event_id, all) 
        # Ενημέρωση της βάσης δεδομένων για κάθε participant
        for participant in participants:
            tag_id, start_time, end_time = participant
            start_time = ''
            end_time = ''
            
            for entry in all:
                if entry[0] == tag_id:
                    start_time = entry[1]
                    end_time = entry[2]
                    break

            temp = update(user_event).where(
                (user_event.c.tag_id == tag_id) & 
                (user_event.c.event_id == event_id)
            ).values(start_time=start_time, end_time=end_time)
            db.session.execute(temp)
        db.session.commit()
                    
          
    return all, errors

def process_lines_from_file(lines,event_id):
    # Συνάρτηση για επεξεργασία κάθε γραμμής από το ΑΡΧΕΙΟ δεδομένων χρονομέτρησης
    # Επιστρέφει λίστα με τις εγγραφές που βρέθηκαν από 1 φορά (αφαιρεί τις πολλαπλές)
    # πριν και μετά το ALL_PASS_FROM_START_POINT

    before_all_pass = []
    after_all_pass = []
    all_pass_reached = False
    pattern = r"\d{2}:\d{2}:\d{2}:\d{2}"  # Προσθήκη του pattern για την αντιστοίχιση του χρόνου

    participants = db.session.query(
        user_event.c.tag_id,
        user_event.c.start_time,
        user_event.c.end_time
    ).join(User).join(Event).filter(
        Event.id == event_id,
        User.details.has(UserDetails.role != 'admin'),
        User.details.has(UserDetails.role != 'super_admin')
    ).all()

    # όλα τα ids που έχουν οι συμμετέχοντες (1ο πεδίο εγγραφής)
    tag_ids = [int(participant[0]) for participant in participants]
    for line in lines:
        parts = line.split(',')
        if len(parts) >= 2:
            tag_id = parts[0].strip()
           
            timestamp = parts[1].strip()
            error_type = None

            if len(tag_id) != 24:
                error_type = 'Το ID πρέπει να έχει 24 ψηφία'
            else:
                try:
                    int(tag_id)
                    # υπάρχει αυτό το ID?
                    if int(tag_id) not in tag_ids:
                        error_type = 'Αυτό το ID δεν έχει αποδοθεί σε δρομέα'
                    elif not re.match(pattern, timestamp):
                        error_type = 'Λάθος στο χρόνο εκκίνησης (00:00:00:00)' if not all_pass_reached else 'Λάθος στο χρόνο τερματισμού (00:00:00:00)'
                except ValueError:
                    error_type = 'Το ID πρέπει να περιέχει μόνο αριθμητικά ψηφία'
            record = [tag_id, timestamp, error_type]

            if not all_pass_reached:
                for item in before_all_pass: # καταχωρίζει η τελευταία τιμή του χρόνου εκκίνησης
                    if item[0] == tag_id:
                        item[1] = record[1]
                        break
                else: # for
                    before_all_pass.append(record)
                
            else: 
                if not any(item[0] == tag_id for item in after_all_pass):
                    after_all_pass.append(record) # καταχωρίζει η πρώτη τιμή του χρόνου τερματισμού
        else:
            if line.strip() == 'ALL_PASS_FROM_START_POINT':
                all_pass_reached = True


    before_ids = {entry[0] for entry in before_all_pass}
    after_ids = {entry[0] for entry in after_all_pass}

    # Ενημέρωση της after_all_pass για κάθε id που δεν υπάρχει στην before_all_pass
    for entry in after_all_pass:
        if entry[0] not in before_ids:
            if entry[2] == None: # έχει λάθος id;
                entry[2] = 'DNS'

    # Ενημέρωση της before_all_pass για κάθε id που υπάρχει στην before_all_pass αλλά όχι στην after_all_pass
    for entry in before_all_pass:
        if entry[0] in before_ids and entry[0] not in after_ids:
            if entry[2]==None:
                entry[2] = 'Λάθος στο χρόνο τερματισμού (00:00:00:00)'
            else:
                entry[2] = 'Λάθος στο χρόνο τερματισμού (00:00:00:00)'

    all = []

    for sublist in before_all_pass:
        new_sublist = [sublist[0], sublist[1], '', sublist[2]]
        all.append(new_sublist)    
    
    all = all + [['ALL_PASS_FROM_START_POINT', None, None,None]]
    
    # Ενημέρωση του τρίτου πεδίου της all_data από την after_all_pass
    for sublist in after_all_pass:      
        found = False
        for entry in all: # η all περιέχει όλες τις εγγραφές της before + 1 πεδίο για τον χρόνο τερματισμού
            if entry[0] != 'ALL_PASS_FROM_START_POINT':
                if entry[0] == sublist[0]:
                    entry[2] = sublist[1]
                    found = True
                    break
        if not found:
            if sublist[2]=='DNS':
                new_entry = [sublist[0], "00:00:00:00",sublist[1], None]
                all.append(new_entry)
            else: # λάθος id
                new_entry = [sublist[0], "",sublist[1], sublist[2]]
                all.append(new_entry)

    errors = []
    for entry in all:
        if entry[0] != 'ALL_PASS_FROM_START_POINT':
            if entry[3] is not None or entry[3]=='':
                errors.append(entry)  
    if not errors:   
 
        # Ενημέρωση της βάσης δεδομένων για κάθε participant
        for participant in participants:
            tag_id, start_time, end_time = participant
            start_time = ''
            end_time = ''
            
            for entry in all:
                if entry[0] == tag_id:
                    start_time = entry[1]
                    end_time = entry[2]
                    break

            temp = update(user_event).where(
                (user_event.c.tag_id == tag_id) & 
                (user_event.c.event_id == event_id)
            ).values(start_time=start_time, end_time=end_time)
            db.session.execute(temp)

        db.session.commit()
        # αποθήκευση δεδομένων σε αρχείο

        save_data(event_id, all) 
    return all, errors




def save_data(event_id, all_entries):
    # Δημιουργία του νέου αρχείου χρονομέτρησης που έχει τις σωστές καταχωρίσεις
    new_filename = str(event_id) + '.txt'
    path = os.path.join(app.root_path, 'static/results_files', new_filename)
    with open(path, 'w') as f:
    
        for item in all_entries:
            if item[0]!="ALL_PASS_FROM_START_POINT":
                f.write(f"{item[0]},{item[1]},{item[2]}\n")

def time_to_seconds(time_str):
 
    h, m, s, ms = map(int, time_str.split(':'))
    total_seconds = h * 3600 + m * 60 + s + ms / 100
    return total_seconds

def seconds_to_time(seconds):

    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds * 100) % 100)
    return f"{h:02}:{m:02}:{s:02}:{ms:02}"

@app.route('/upload_results/<int:event_id>', methods=['POST', 'GET'])
def upload_results(event_id):
    all=[]
    errors = []
    form=UploadForm()
    hidden_form = HiddenForm()
  
    event = db.session.query(Event).filter_by(id=event_id).first()
    
   
    participants = db.session.query(
                    user_event.c.tag_id,
                    user_event.c.start_time,
                    user_event.c.end_time
                ).join(User).join(Event).filter(
                    Event.id == event_id,
                    User.details.has(UserDetails.role != 'admin'),
                    User.details.has(UserDetails.role != 'super_admin')
                ).all()
    participants_id_tags = [p.tag_id for p in participants if p.tag_id is not None and p.tag_id != '']
    participants_start_time = [p.start_time for p in participants if p.start_time is not None and p.start_time != '']
    participants_end_time = [p.end_time for p in participants if p.end_time is not None and p.end_time != '']
    f=''
    if not participants_id_tags or not participants_start_time or not participants_end_time:
        crono_ok=False
    else:
        crono_ok=True
        f = str(event_id)+  "_init.txt"
        path = os.path.join(app.root_path, 'static/results_files', f)
        if os.path.exists(path):
            f="results_files/"+f

    if request.method == 'POST': 
        # Eπιλέχθηκε νέο αρχείο δεδομένων
        if request.form['submit'] == 'Εισαγωγή δεδομένων στην ΒΔ': 
            # Προσωρινή αποθήκευση αρχείου δεδομένων κεραίας
            file = request.files['file']
            filename = secure_filename(file.filename) 
            path = os.path.join(app.root_path, 'static/results_files', filename)
            file.save(path)

            with open(path, 'r') as file:
                lines = file.readlines()

            all,errors = process_lines_from_file(lines, event_id)
            
            # Αλλαγή ονόματος αρχείου
            new_filename = str(event_id)+'_init.txt'
            new_path = os.path.join(app.root_path, 'static/results_files', new_filename)
            if os.path.exists(new_path):
                os.remove(new_path)
            os.rename(path, new_path)

            # Δημιουργία του νέου αρχείου χρονομέτρησης που έχει τις σωστές και λάθος καταχωρίσεις από 1 φορά
         
            if not errors:
                
                flash('Τα δεδομένα χρονομέτρησης ανακτήθηκαν με επιτυχία')
       
        # Επιλέχθηκε να γραφούν στη ΒΔ ΜΟΝΟ οι σωστές εγγραφών και να αγνοηθούν οι λάθος
        elif request.form['submit'] == 'Αποδοχή εγγραφών':
            old_all = eval(request.form["old_all"]) # λίστα με τις σωστές εγγραφές
            old_errors = eval(request.form["old_errors"]) # λίστα με τα λάθη πριν την διόρθωση
            all = []
            for entry in old_all:
                if entry[0] != 'ALL_PASS_FROM_START_POINT':
                    id_to_check = entry[0]
                    if not any(error[0] == id_to_check for error in old_errors):
                        all.append(entry)

            all, errors = process_lines_from_list(all, event_id)
            if not errors:
                flash('Τα δεδομένα χρονομέτρησης αποθηκεύτηκαν')
                            

        # Επιλέχθηκε να διορθωθούν οι λάθος εγγραφές
        elif request.form['submit'] == 'Αποθήκευση αλλαγών':
            # Παίρνουμε τις λίστες από την αίτηση φόρμας και τις μετατρέπουμε από JSON strings σε Python dictionaries
            old_errors = eval(request.form["old_errors"]) # λίστα με τα λάθη πριν την διόρθωση
            old_all = eval(request.form["old_all"]) # λίστα με όλες τις εγγραφές πριν την διόρθωση
            ids = request.form.getlist('id[]')
            t1 = request.form.getlist('t1[]')
            t2 = request.form.getlist('t2[]')
            error_types = request.form.getlist('error_type[]')

            # λίστα με τις διορθωμένες εγγραφές
            corrected_errors = [[id, t1,t2, error_type] for id, t1,t2, error_type in zip(ids, t1,t2, error_types)]

            all = []
            for entry in old_all:
                if entry[0] != 'ALL_PASS_FROM_START_POINT':
                    id_to_check = entry[0]
                 
                    if any(error[0] == id_to_check for error in old_errors):
                        for corrected_entry in corrected_errors:
                            if corrected_entry[0] == id_to_check:
                                all.append(corrected_entry)
                                break
                    else:
                        all.append(entry)

            all, errors = process_lines_from_list(all, event_id)

            if not errors:
                flash('Οι διορθώσεις στα δεδομένα χρονομέτρησης αποθηκεύτηκαν')
        elif request.form['submit'] == 'Εμφάνιση αποτελεσμάτων' :
            
            # Λήψη όλων των εγγραφών από τον πίνακα user_event που σχετίζονται με το συγκεκριμένο event
            user_event_entries = db.session.query(user_event).filter_by(event_id=event_id).all()

            # Εμφάνιση των πληροφοριών
            all_results = []
            for entry in user_event_entries:
                user = db.session.query(User).filter_by(id=entry.user_id).first()
                if user.details.role!='super_admin' and user.details.role!='admin':
                    if    entry.end_time !='' and entry.start_time!='':
                        net_time = seconds_to_time(time_to_seconds(entry.end_time) - time_to_seconds(entry.start_time))
                    else:
                        net_time=''
                    all_results.append([user.details.lastname + ' '+ user.details.firstname, 
                                user.details.gender,user.details.year_of_birth,
                                user.details.club, user.details.city,
                                entry.start_time,entry.end_time,
                                net_time,
                                ])
            age_category = db.session.query(Event_Category.name).join(Event, Event.age_categories == Event_Category.id).filter(Event.id == event_id).scalar()

            return render_template('show_results.html', all_results=all_results, racename=event.racename,age_category=age_category, event_year=event.date.year)
            
    return render_template('upload_results.html', form=form, hidden_form=hidden_form, errors=errors, all=all, event_id=event_id, crono_ok=crono_ok, f= f,racename=event.racename)


@app.route('/show_results')
def show_results():
    results = []  

    # Έλεγχος για την ύπαρξη του αρχείου CSV
    if not os.path.exists('results.csv'):
        return "Το αρχείο δεν βρέθηκε."

    # Διάβασμα του αρχείου CSV
    with open('results.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            results.append({
            'firstname': row['firstname'],
            'lastname': row['lastname'],
            'gender': row['gender'],
            'club': row['club'],
            'region': row['region'],
            'city': row['city'],
            'time': row['time']  
        })

    return render_template('results.html', results=results)

def login_with_google_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()
    return wrapper

@app.route("/protected_area")
@login_with_google_is_required
def protected_area():
    user = User.query.filter_by(email=session['email']).first()
    if user == None : 
        # Πρώτη φορά ο χρήστης συνδέεται με χρήση google account
        user = User(email=session['email'], password="")
        db.session.add(user)
        db.session.commit()

        user_details = UserDetails(
                firstname="",
                lastname="",
                gender="",
                year_of_birth="",
                club="",
                region="",
                city="",
                role='user',  # προεπιλεγμένος ρόλος
                image_file='default.jpg',  # προεπιλεγμένη εικόνα
                user_id=user.id  # Συσχέτιση με τον νέο χρήστη
            )
        db.session.add(user_details)
        db.session.commit()
    login_user(user)
    return redirect("/login")


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    # if not session["state"] == request.args["state"]:
    #     abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=10
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    return redirect("/protected_area")

@app.route("/login_with_google")
def login_with_google():
    
    if "google_id" not in session:
        authorization_url, state = flow.authorization_url()
        session["state"] = state
        return redirect(authorization_url)
    else:
        # Ο χρήστης έχει ήδη συνδεθεί μέσω Google, οπότε τον ανακατευθύνουμε στην αρχική σελίδα
        return redirect("/protected_area")
#-----------------------------------



@app.route('/add_event/', methods=['GET', 'POST'])
@login_required
def add_event():
    # Υπάρχει επιλογή γιαυτό το route μόνο στο μενού του admin και super_admin 
    if current_user.details.role == 'user':
        return redirect(url_for('dashboard_user'))
    form = EventForm()
    # Όλες οι κατηγορίες γεγονότων που μπορούν να επιλεγούν
    # μπορούν να οριστούν μόνο από τον χρήστη super_admin
    event_categories = Event_Category.query.all()
    
    if form.validate_on_submit():
        if form.date.data < datetime.now().date():
            flash("Η ημερομηνία πρέπει να είναι μεταγενέστερη από την σημερινή ημερομηνία")
            return render_template('add_event.html', form=form,event_categories=event_categories)

        if form.finalize_date.data > form.date.data:
            flash("Η ημερομηνία πρέπει να είναι μεγαλύτερη από την ημερομηνία κλειδώματος εγγραφών ")
            return render_template('add_event.html', form=form,event_categories=event_categories)
        prefixes = ["http://", "https://"]
        if form.link.data and not any(form.link.data.startswith(prefix) for prefix in prefixes):
            flash("Ενημερώστε τη διεύθυνση ιστοσελίδας με το πρόθεμα https:// ή http://")
            return render_template('add_event.html', form=form,event_categories=event_categories)
        if form.map.data and not any(form.map.data.startswith(prefix) for prefix in prefixes):
            flash("Ενημερώστε τη διεύθυνση για τον χάρτη διαδρομής με το πρόθεμα https:// ή http://")
            return render_template('add_event.html', form=form,event_categories=event_categories)
        # Αποθήκευση των δεδομένων της φόρμας στη βάση δεδομένων
        # Δημιουργία του JSON string με τις πληροφορίες που παρέχει ο αγώνας από τα δεδομένα της φόρμας
        provides_json = json.dumps({
            'bib': form.provides_bib.data,
            'medal': form.provides_medal.data,
            'certificate': form.provides_certificate.data,
            'tshirt': form.provides_tshirt.data,
            'other':form.provides_other.data
        })

        new_event = Event(
            racename=form.racename.data,
            date=form.date.data,
            time=form.time.data,
            declaration=save_declaration(form.declaration.data),
            distance=form.distance.data,
            finalize_date=form.finalize_date.data,
            link=form.link.data,
            map=form.map.data,
            age_categories=int(form.categories.data),
            provides=provides_json,
            entry_fee=int(form.entry_fee.data)
        )
        db.session.add(new_event)
        db.session.commit()


        # Δημιουργία της εγγραφής για τον πίνακα user_event
        temp = user_event.insert().values(
            user_id=current_user.id,
            event_id=new_event.id,
            payment=False,
            deletion_requested=False,
            tag_id='', 
            start_time='', 
            end_time=''  
        )
        db.session.execute(temp)
        db.session.commit()

        return redirect(url_for('show_events'))
  
    return render_template('add_event.html', form=form,event_categories=event_categories)

@app.route('/show_events/', methods=['GET', 'POST'])
def show_events():
    form = ShowEventForm()
    events=db.session.query(Event).first() 
    first_event_date=None
    last_event_date=None
    order=-1 # Εμφάνιση γεγονότων σε συγκριμένο διάστημα ημερομηνιών

    if events:
        first_event_date = db.session.query(Event).order_by(Event.date.asc()).first().date
        last_event_date = db.session.query(Event).order_by(Event.date.desc()).first().date
        if request.method == 'POST':
            #έχει γίνει έλεγχος με javascipt και η start_date<=end_date
            sd = form.data['start_date']
            ed = form.data['end_date']
            if form.options.data=='next_events':
                sd = datetime.now().date() 
                ed = last_event_date
                order = 1
            elif form.options.data=='previous_events':
                sd = first_event_date
                ed = datetime.now().date() 
                order = 2
            elif form.options.data=='all_events':
                sd = first_event_date 
                ed = last_event_date 
                order = 0  
            else: # Εμφάνιση γεγονότων σε συγκριμένο διάστημα ημερομηνιών
                order = -1      
            first_event_date = sd
            last_event_date = ed
            events = Event.query.filter(Event.date.between(sd, ed)).order_by(Event.date.asc()).all()
            
            if not events:
                flash("Δεν υπάρχουν καταχωρίσεις με αυτές τις επιλογές.")
                return redirect(url_for('show_events')) 
            else: 
                if form.data['my_races'] : # Εμφάνισε μόνο τους αγώνες που έχω συμμετάσχει'
                    common_events = [event for event in current_user.enroll if event in events]
                    events = sorted(common_events, key=lambda event: event.date)
  
           
        else: # GET
            events = Event.query.filter(Event.date.between(first_event_date, last_event_date)).order_by(Event.date.asc()).all()

    else:     
        flash("Δεν υπάρχουν καταχωρίσεις γεγονότων.")
    return render_template('show_events.html',events=events,form=form,first_event_date=first_event_date,last_event_date=last_event_date,order=order) 

def save_image(picture_file):
    picture_name = secure_filename(picture_file.filename)
    picture_path = os.path.join(app.root_path,'static/profile_pics',picture_name)
    picture_file.save(picture_path)
    return picture_name

def save_declaration(file):
    filename=""
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.root_path, 'static/declaration_files',  filename)
        file.save(file_path)
    return filename 


@app.route('/account/',methods=['GET','POST'])
@login_required
def account():
    form = AccountUpdateForm()
    current_year = datetime.now().year

    if form.validate_on_submit():
        
        user_details = UserDetails.query.get(current_user.id)
        if user_details:# μάλλον είναι περιττό
            
            user_details.firstname = form.firstname.data
            user_details.lastname = form.lastname.data
            user_details.gender = form.gender.data
            user_details.year_of_birth = form.year_of_birth.data
            user_details.club = form.club.data
            user_details.region = form.region.data
            user_details.city = form.city.data
            if form.picture.data:
                # έλεγχος για το format της εικόνας, αν έχει σωστή επέκταση
                s = form.picture.data.filename
                last_dot_index = s.rfind(".")
                if last_dot_index != -1:  # έχει γίνει ήδη έλεγχος και από τον validator
                     # σβήνεται η παλιά φωτογραφία (εφόσον υπήρχε) εκτός και αν η default.jpg
                    image_file_name = current_user.details.image_file
                    if image_file_name !="default.jpg":
                        image_path = os.path.join(app.root_path, 'static', 'profile_pics', image_file_name)
                        if os.path.exists(image_path):
                            os.remove(image_path)
                    # αποθηκεύεται η καινούργια
                    extension = s[last_dot_index :] 
                    form.picture.data.filename=str(current_user.id) + extension
                    image_file = save_image(form.picture.data)
                    current_user.details.image_file = image_file  
                    
                else:
                    flash("Η εικόνα που επιλέχθηκε δεν είναι κατάλληλη.")
            db.session.commit() 
            return redirect(url_for('account')) 

    return render_template('account.html', title='Πληροφορίες Λογαριασμού', form=form, cities=CITIES_DATA, current_year=current_year)

@app.route('/',methods=['GET','POST'])
@app.route('/index/',methods=['GET','POST'])
@app.route('/login/',methods=['GET','POST'])
def login():
    
    if current_user.is_authenticated  :

        if current_user.details.role =='user':
            return redirect(url_for('dashboard_user'))
        elif current_user.details.role =='admin':
            return redirect(url_for('dashboard_admin'))
        else:
            return redirect(url_for('dashboard_superadmin'))
    
    form = LoginForm() 
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user :
            if user.confirmed: 
                if bcrypt.check_password_hash(user.password, form.password.data): 
                    login_user(user)
                    if user.details.role == 'user':
                        return redirect(url_for('dashboard_user'))
                    elif user.details.role =='admin':
                        return redirect(url_for('dashboard_admin'))
                    else:
                        return redirect(url_for('dashboard_superadmin'))
                else:
                    flash("Δεν υπάρχει χρήστης με αυτά τα στοιχεία.")
            else:
                flash("Δεν έχετε επιβεβαιώσει το email σας.")
        else:
             flash("Δεν υπάρχει χρήστης με αυτά τα στοιχεία.")

    return render_template('login.html',form = form)

@app.route('/logout/')
def logout():
    logout_user()
    session.clear()

    return redirect(url_for('login'))

# αφορά μόνο απλούς χρήστες, τον admin τον έχει γράψει στην ΒΔ ο super_admin
@app.route('/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_user'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            encrypted_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(email=form.email.data, password=encrypted_password, confirmed=False)
            # προσωρινή εγγραφή στην βάση μέχρι να γίνει η επιβεβαίωση δεν θεωρείται ενεργός χρήστης
            db.session.add(user)
            db.session.commit()
            send_mail_confirm_user_email(user)

            flash('Στάλθηκε μήνυμα για την επιβεβαίωση του email σας. Ελέγξτε το email σας.', category='success')
            return redirect(url_for('login'))
            
            # flash(f'Ο λογαριασμός για τον χρήστη {form.email.data} δημιουργήθηκε με επιτυχία')
            # return redirect(url_for('login'))
        else:
            if(user.confirmed==True):
                flash(f'Υπάρχει ήδη χρήστης με το email : {form.email.data}')
            else:
                flash(f'Ο λογαριασμός σας δεν έχει ενεργοποιηθεί. Στο email {form.email.data} σας έχει αποσταλεί σύνδεσμος ενεργοποίησης.')


    return render_template('register.html', title='Εγγραφή', form=form)

@app.route('/crud_event/<int:event_id>', methods=['POST'])
def crud_event(event_id):

    event = Event.query.filter_by(id=event_id).first()
    event_provides_dict = json.loads(event.provides)
    form = EventForm()
    event_categories = Event_Category.query.all() 
    tags_ok =False
    tag_id_current_user=''
    if request.method == 'POST':
       
        if request.form['select_button'] == 'Δήλωση συμμετοχής': # Δήλωση συμμετοχής από χρήστη 
            # Έλεγχος αν ο χρήστης (user) έχει ενημερώσει τις πληροφορίες του λογαριασμού του
            if current_user.details.firstname and current_user.details.lastname and current_user.details.gender and current_user.details.year_of_birth:
                # Έλεγχος αν υπάρχει ήδη εγγραφή για τον current_user και το συγκεκριμένο event
                existing_entry = db.session.query(user_event).filter_by(user_id=current_user.id, event_id=event_id).first()
                canDeclare = True
                if existing_entry:
                    # Αν υπάρχει εγγραφή, ενημερώνουμε το deletion_requested σε False
                    temp = user_event.update().where(
                        (user_event.c.user_id == current_user.id) & (user_event.c.event_id == event_id)
                    ).values(deletion_requested=False)
                    db.session.execute(temp)
                    db.session.commit()

                else:
                    
                    send_mail_confirm_participation(current_user, event)
                    db.session.add(event)
                    db.session.commit()

                    # Δημιουργία της εγγραφής για τον πίνακα user_event
                    temp = user_event.insert().values(
                        user_id=current_user.id,
                        event_id=event.id,
                        payment=False,
                        deletion_requested=False,
                        tag_id='', 
                        start_time='',  
                        end_time=''  
                    )
                    db.session.execute(temp)
                    db.session.commit()
            else:
                canDeclare = False
            return render_template('race_participation.html', canDeclare=canDeclare, event = event)
         
        elif request.form['select_button']=='Ακύρωση συμμετοχής':
            user_event_entry = db.session.query(user_event).filter_by(user_id=current_user.id, event_id=event.id).first()

            current_user_id = current_user.id

            # Δημιουργία του update statement
            temp = update(user_event).where(
                (user_event.c.user_id == current_user_id) & 
                (user_event.c.event_id == event_id)
            ).values(deletion_requested=True)

            # Εκτέλεση του update statement
            db.session.execute(temp)
            db.session.commit()
   
            return redirect(url_for('show_events')) 
        
        elif request.form['select_button'] == 'Οριστικοποίηση': # Οριστικοποίηση αποτελεσμάτων
            print('οριστικοποίηση')
            #TODO
            #return render_template('update_event.html', event=event,event_categories=event_categories, event_provides_dict=event_provides_dict,form=form)
        
        elif request.form['select_button'] == 'Τροποποίηση': # Τροποποίηση από διαχειριστή
            return render_template('update_event.html', event=event,event_categories=event_categories, event_provides_dict=event_provides_dict,form=form)
        elif request.form['select_button'] == 'Εμφάνιση δηλώσεων': # Εμφάνιση δηλώσεων 
             # Όλοι οι εγγραμμένοι στο event
            event_users = db.session.query(
                user_event.c.event_id.label('event_id'),
                user_event.c.user_id.label('user_id')
            ).filter( user_event.c.event_id == event.id ).all()
           
            # list με  dictionaries
            user_details_dict = []
            for x in event_users:
                user = User.query.filter_by(id=x.user_id).first()  # π.χ x=(2,3)
                if user.details.role == 'user':
                    #  event_id στο φίλτρο
                    payment_status, deletion_requested_status = db.session.query(
                        user_event.c.payment, user_event.c.deletion_requested
                    ).filter(
                        user_event.c.user_id == user.id,
                        user_event.c.event_id == x.event_id  # event_id στο φίλτρο
                    ).first()

                    user_details_dict.append({
                        "id": user.id,
                        "Email": user.email,
                        "Επώνυμο": user.details.lastname,
                        "Όνομα": user.details.firstname,
                        "Φύλο": user.details.gender,
                        "Έτος γέννησης": user.details.year_of_birth,
                        "Σύλλογος": user.details.club,
                        "Πόλη": user.details.city,
                        "Πληρωμή": payment_status,
                        "Αίτημα διαγραφής": deletion_requested_status
                    })

            return render_template('crud_users_in_event.html', event=event, user_details_dict = user_details_dict)
        elif request.form['select_button']=='Διαγραφή χρήστη από event':
         
            for key, value in request.form.items():
                    if key=='user_id':
                        user_event_to_delete_id = value
            user = User.query.filter_by(id = user_event_to_delete_id).first()
            user.enroll.remove(event) # διαγραφή χρήστη από το event
            db.session.commit()

        elif request.form['select_button']=='Αποθήκευση': # αλλαγή στην πληρωμή χρήστη
            # αλλαγή του πεδίου payment στον πίνακα user_event

            user_data = json.loads(request.form['user_data'])
            event = Event.query.get(event_id)
            for user_entry in user_data:
                user_id = user_entry.get('user_id')
                payment_status = user_entry.get('payment_status')
                user = User.query.get(user_id)
                stmt = user_event.update().where(
                (user_event.c.user_id == user.id) & (user_event.c.event_id == event.id)
            ).values(payment=(payment_status == 'Ναι'))

                db.session.execute(stmt)
            db.session.commit()
            
            
        elif request.form['select_button'] == 'Διαγραφή': # Διαγραφή event από διαχειριστή
            db.session.delete(event)
            db.session.commit()
            return redirect(url_for('show_events')) 

        elif request.form['select_button'] == 'Εγγραφή χρήστη': # Εγγραφή guest 
            return redirect(url_for('register'))
        
        elif request.form['select_button'] == 'Ανάθεση ID': # Ανάθεση ID στους αθλητές

            return redirect(url_for('assign_athletes_ids',  event_id=event.id))
        
        elif request.form['select_button'] == 'Xρονομέτρηση': # Εισαγωγή δεδομένων χρονομέτρησης 
            return redirect(url_for('upload_results', event_id=event.id))

        elif request.form['select_button'] == 'Αποτελέσματα':
             # Λήψη όλων των εγγραφών από τον πίνακα user_event που σχετίζονται με το συγκεκριμένο event
            user_event_entries = db.session.query(user_event).filter_by(event_id=event_id).all()
            all_results = []
            for entry in user_event_entries:
                user = db.session.query(User).filter_by(id=entry.user_id).first()
                if user.details.role!='super_admin' and user.details.role!='admin':
                    if    entry.end_time !='' and entry.start_time!='':
                        net_time = seconds_to_time(time_to_seconds(entry.end_time) - time_to_seconds(entry.start_time))
                    else:
                        net_time=''
                    all_results.append([user.details.lastname + ' '+ user.details.firstname, 
                                user.details.gender,user.details.year_of_birth,
                                user.details.club, user.details.city,
                                entry.start_time,entry.end_time,
                                net_time,
                                ])
            age_category = db.session.query(Event_Category.name).join(Event, Event.age_categories == Event_Category.id).filter(Event.id == event_id).scalar()
            return render_template('show_results.html', all_results=all_results, racename=event.racename,age_category=age_category, event_year=event.date.year)       
        elif request.form['select_button'] == 'Ενημέρωση': # Έγινε η τροποποίηση -> ενημέρωση DB
            error=False
            if form.date.data < datetime.now().date():
                error=True
                flash("Η ημερομηνία πρέπει να είναι μεταγενέστερη από την σημερινή ημερομηνία")
            if form.finalize_date.data > form.date.data:
                error=True
                flash("Η ημερομηνία πρέπει να είναι μεγαλύτερη από την ημερομηνία κλειδώματος εγγραφών ")
            prefixes = ["http://", "https://"]
            if form.link.data and not any(form.link.data.startswith(prefix) for prefix in prefixes):
                error=True
                flash("Ενημερώστε τη διεύθυνση ιστοσελίδας με το πρόθεμα https:// ή http://")
            if form.map.data and not any(form.map.data.startswith(prefix) for prefix in prefixes):
                error=True
                flash("Ενημερώστε τη διεύθυνση για τον χάρτη διαδρομής με το πρόθεμα https:// ή http://")
            if form.entry_fee.data==None or int(form.entry_fee.data)<0:
                error=True
                flash("Εισάγετε στο κόστος βασικού πακέτου έναν ακέραιο >=0")
            if not error:
                # Ενημέρωση event με τροποποιήσεις από τον admin
                provides_json = json.dumps({
                    'bib': form.provides_bib.data,  
                    'medal': form.provides_medal.data,
                    'certificate': form.provides_certificate.data,
                    'tshirt': form.provides_tshirt.data,
                    'other':form.provides_other.data
                })

                event.racename = form.racename.data
                event.date = form.date.data
                event.time = form.time.data
                event.declaration = save_declaration(form.declaration.data)
                event.distance = form.distance.data
                event.finalize_date = form.finalize_date.data
                event.link = form.link.data
                event.map = form.map.data  
                event.age_categories = int(form.categories.data)
                event.provides = provides_json
                event.entry_fee = int(form.entry_fee.data)
                db.session.commit()
                event = Event.query.filter_by(id=event_id).first()
                event_provides_dict = json.loads(event.provides)
            else:
                return render_template('update_event.html', event=event,event_categories=event_categories, event_provides_dict=event_provides_dict,form=form)
    if current_user.is_authenticated:
        #αν έχει επιλέξει ακύρωση συμμετοχής ο χρήστης σε προηγούμενη ενέργειά του
        deletion_requested = db.session.query(user_event.c.deletion_requested).filter(
                        user_event.c.user_id == current_user.id,
                        user_event.c.event_id == event_id
                    ).scalar()
       
        
        
    else:
        deletion_requested=None

     # έχει αποδοθεί στους συμμετέχοντες id tag και έχουν χρόνους ?
    participants = db.session.query(
                    user_event.c.tag_id,
                    user_event.c.start_time,
                    user_event.c.end_time
                ).join(User).join(Event).filter(
                    Event.id == event_id,
                    User.details.has(UserDetails.role != 'admin'),
                    User.details.has(UserDetails.role != 'super_admin')
                ).all()
    participants_id_tags = [p.tag_id for p in participants if p.tag_id is not None and p.tag_id != '']
    participants_start_time = [p.start_time for p in participants if p.start_time is not None and p.start_time != '']
    participants_end_time = [p.end_time for p in participants if p.end_time is not None and p.end_time != '']

    if not participants_id_tags: # αν δεν υπάρχουν εγγραφές
        tags_ok =False
    else:
        tags_ok =True
        if current_user.is_authenticated:
            if current_user.details.role=='user':
                tag_id_current_user = db.session.query(user_event.c.tag_id).filter(
                                user_event.c.user_id == current_user.id,
                                user_event.c.event_id == event_id
                            ).scalar()
    # έχουν ενημερωθεί οι εγγραφές με τους χρόνους;
    if not participants_start_time or not participants_end_time:
        crono_ok=False
    else:
        crono_ok=True
    return render_template('crud_event.html', event=event,event_categories=event_categories, 
                           event_provides_dict=event_provides_dict,
                           form=form,deletion_requested=deletion_requested, 
                           tags_ok=tags_ok, crono_ok=crono_ok, tag_id_current_user=tag_id_current_user)

@app.route('/crud_users', methods=['GET', 'POST'])
@login_required
def crud_users():
    if current_user.details=='user':
        return redirect(url_for('dashboard_user'))
    elif current_user.details=='admin':
        return redirect(url_for('dashboard_admin'))
    # Αναζήτηση όλων των users 
    # ταξινόμηση με βάση την πόλη 
    all_users = User.query.join(User.details).order_by(asc(UserDetails.city)).all()
    
    if request.method == 'POST':
        for key, value in request.form.items(): # ενημέρωση role χρήστη
            
            if key=='update_button':
                for key, value in request.form.items():
                    if key=='role':
                        user_to_update_role = value
                    if key=='user_id':
                        user_to_update_id = value
                user = User.query.filter_by(id = user_to_update_id).first()
                user.details.role = user_to_update_role
                db.session.commit()
            elif key=='delete_button':
                for key, value in request.form.items():
                    if key=='user_id':
                        user_to_delete_id = value
                user_details_to_delete = UserDetails.query.filter_by(user_id=user_to_delete_id).first()
                db.session.delete(user_details_to_delete)
                user = User.query.filter_by(id = user_to_delete_id).first()
                db.session.delete(user)
                db.session.commit()
                all_users = User.query.join(User.details).order_by(asc(UserDetails.city)).all()

    return render_template('crud_users.html', all_users = all_users)




@app.route('/dashboard_admin/')
@login_required
def dashboard_admin():
    return render_template('dashboard_admin.html')

@app.route('/dashboard_user/')
@login_required
def dashboard_user():
    return render_template('dashboard_user.html')

@app.route('/dashboard_superadmin/')
@login_required
def dashboard_superadmin():
    return render_template('dashboard_superadmin.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def send_mail_confirm_user_email(user):
    token = user.get_token()
    msg = Message('Επιβεβαίωση email', recipients = [user.email], sender='argyroi@gmail.com')
    msg.body  = f'''Για να επιβεβαιώσετε το email σας πατήστε στον παρακάτω σύνδεσμο
                { url_for('reset_token_confirm_user_email',token=token, _external=True) }

                Αν δεν στείλατε αίτημα επιβεβαίωσης του email παρακαλούμε αγνοήστε το παρόν μήνυμα
                '''
    mail.send(msg)

def send_mail_confirm_participation(user, event):
    token = user.get_token()
    msg = Message(
        subject='Ολοκλήρωση συμμετοχής στο ' + event.racename, 
        recipients=[user.email], 
        sender='argyroi@gmail.com'
    )
    if event.entry_fee>0:
        msg.body = f'''Για την ολοκλήρωση της συμμετοχής σας στο αθλητικό γεγονός {event.racename}, πρέπει να καταθέσετε το ποσό των {event.entry_fee} ευρώ.
Παρακαλούμε στο αποδεικτικό κατάθεσης συμπληρώστε το ονοματεπώνυμό σας.

Ευχαριστούμε για την συμμετοχή.'''
    else:
         msg.body = f'''Η εγγραφή σας στο {event.racename} ολοκληρώθηκε. 

Ευχαριστούμε για την συμμετοχή. '''

    mail.send(msg)

def send_mail(user):
    token = user.get_token()
    msg = Message('Τροποποίηση συνθηματικού', recipients = [user.email], sender='argyroi@gmail.com')
    msg.body  = f'''Για να τροποποιήσετε το συνθηματικό σας πατήστε στον παρακάτω σύνδεσμο
                { url_for('reset_token',token=token, _external=True) }

                Αν δεν στείλατε αίτημα τροποποίησης συνθηματικού παρακαλούμε αγνοήστε το παρόν μήνυμα
                '''
    mail.send(msg)

@login_required
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    form = ResetRequestForm()
    if request.method == 'POST':
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_mail(user)
            flash('Στάλθηκε μήνυμα για την επαναφορά του κωδικού. Ελέγξτε το email σας', category='success')
            return redirect(url_for('login'))
        else:
            flash('Δεν υπάρχει αυτό το email', category='danger')

    return render_template('reset_request.html',form=form)

@login_required
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if token !='None':
        user = User.verify_token(token )
        if user is None:
            flash ('Λάθος, πιθανόν πέρασε ο χρόνος για την επιλογή του συνδέσμου τροποποίησης συνθηματικού', 'warning')
            return redirect(url_for('reset_request'))
    else:
        user = current_user

    form = ResetPasswordForm()
    if request.method == 'POST':

        if form.validate_on_submit():

            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user.password = hashed_password
            db.session.commit()
            flash ('Έγινε η αλλαγή του συνθηματικού με επιτυχία', 'success')
            return redirect(url_for('login'))
        else:
            flash ('Δώστε 2 φορές τον ίδιο κωδικό με μήκος από 6 έως 20 σύμβολα.', ' danger')
    return render_template('change_password.html',form=form)


@app.route('/reset_token_confirm_user_email/<token>', methods=['GET', 'POST'])
def reset_token_confirm_user_email(token):
    user = User.verify_token(token)
    if user is None:
        flash ('Λάθος, πιθανόν πέρασε ο χρόνος για την επιλογή του συνδέσμου επιβεβαίωσης email', 'warning')
        return redirect(url_for('register'))
    else:
        
        # Δημιουργία αντικειμένου UserDetails και σύνδεση με τον νέο χρήστη
        user.confirmed = True
        user_details = UserDetails(
            firstname="",lastname="", gender="",  year_of_birth="", club="", region="", city="",
                role='user',  # προεπιλεγμένος ρόλος
                image_file='default.jpg',  # προεπιλεγμένη εικόνα
                user_id=user.id  # Συσχέτιση με τον νέο χρήστη
            )
        db.session.add(user_details)
        db.session.commit()
        session.clear()
        flash ("Το email σας επιβεβαιώθηκε.", 'success')
    return redirect(url_for('login'))

