from RacePlus import db, login_manager, app
from datetime import datetime
from flask_login import UserMixin
from flask import redirect, url_for
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
#from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))




# Ορισμός  πίνακα many-to-many
user_event = db.Table('user_event',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True),
    db.Column('payment', db.Boolean, nullable=False, default=False),
    db.Column('deletion_requested', db.Boolean, nullable=False, default=False),
    db.Column('tag_id', db.String(24), nullable=False),
    db.Column('start_time', db.String(12)),
    db.Column('end_time', db.String(12))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed = db.Column(db.Boolean, default=False)
    details = db.relationship('UserDetails', backref='parent', lazy=True, uselist=False)
    enroll = db.relationship('Event', secondary=user_event, backref='enrolled')

    def __repr__(self):
        return f'{self.email} : {self.date_created.strftime("%d/%m/%Y, %H:%M:%S")}'

    # Για τον έλεγχο επιβεβαίωσης μέσω email της εγγραφής και της αλλαγής password
    # Ο χρήστης έχει απεριόριστο χρονικό όριο να επιβεβαιώσει
    def get_token(self, expires_sec = None): 
        serial = Serializer(app.config['SECRET_KEY'] ,expires_sec)
        return serial.dumps({'user_id':self.id}).decode('utf-8')

    @staticmethod
    def verify_token(token):
        serial=Serializer(app.config['SECRET_KEY'])
        
        try:
            user_id = serial.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)
    
   

class UserDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(30))
    lastname = db.Column(db.String(30))
    gender = db.Column(db.String(7)) #Άντρας, Γυναίκα, Άλλο
    phone = db.Column(db.String(15))
    year_of_birth = db.Column(db.String(4))
    club = db.Column(db.String(60))
    region = db.Column(db.String(30))
    city = db.Column(db.String(30))
    role = db.Column(db.String(11), default='user')  # "super_admin", "admin", "user"
    image_file = db.Column(db.String(40), default='default.jpg')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)

    def __repr__(self):
        return f'{self.id} - {self.firstname} - {self.lastname}'


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    racename = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time(timezone=False), nullable=False)
    declaration = db.Column(db.String(255), nullable=True)  
    distance = db.Column(db.String(20), nullable=False)  # Πεδίο απόστασης με τις επιλογές
    finalize_date = db.Column(db.Date, nullable=True)
    link = db.Column(db.String(255), nullable=True)
    map = db.Column(db.String(255), nullable=True)
    age_categories = db.Column(db.Integer, nullable=False) 
    provides = db.Column(db.String(255), nullable=False)  #  JSON
    entry_fee = db.Column(db.Integer, nullable=True)

    def __init__(self, racename, date, time, declaration, finalize_date, link, map, age_categories, provides, distance,entry_fee):
        self.racename = racename
        self.date = date
        self.time = time
        self.declaration = declaration
        self.distance = distance
        self.finalize_date = finalize_date
        self.link = link
        self.map = map
        self.age_categories = age_categories
        self.provides = provides
        self.entry_fee = entry_fee
        
class Event_Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

