from flask_wtf import FlaskForm, RecaptchaField

from flask_wtf.file import FileField, FileAllowed,FileRequired
from wtforms import StringField, PasswordField, SubmitField, HiddenField
from wtforms import  DateField, TimeField, FileField, SelectField, IntegerField, BooleanField
from wtforms.widgets.html5 import DateInput, TimeInput
#from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from wtforms.validators import ValidationError, NumberRange

class LoginForm(FlaskForm):
    recaptcha = RecaptchaField()
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Κωδικός', validators=[DataRequired(), Length(min=6, max=20)])
    submit = SubmitField('Σύνδεση')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Κωδικός', validators=[DataRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField('Επιβεβαίωση Κωδικού', validators=[DataRequired(), EqualTo('password')])
    recaptcha = RecaptchaField()
    submit = SubmitField('Εγγραφή')


class ResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Αλλαγή συνθηματικού')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Κωδικός', validators=[DataRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField('Επιβεβαίωση', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Αλλαγή συνθηματικού')

class AccountUpdateForm(FlaskForm):
    firstname= StringField('Όνομα ', validators=[Length(message="Πλήθος χαρακτήρων [0..30]", min=0, max=30)])
    lastname = StringField('Επώνυμο ', validators=[Length(message="Πλήθος χαρακτήρων [0..30]", min=0, max=30)])
    email = StringField('Email')
    gender = StringField('Φύλο')
    year_of_birth = StringField('Έτος γέννησης')
    club = StringField('Σύλλογος')
    region = StringField('Περιφέρεια')
    city = StringField('Πόλη')
    picture = FileField(label='Ενημέρωση εικόνας', validators=[
        FileAllowed(['jpg', 'png', 'gif'], 'Επιτρέπονται  JPG, PNG, ή GIF εικόνες')
    ])

    
    submit = SubmitField('Ενημέρωση')
    # custom validator για το μέγιστο μήκος αρχείου εικόνας
    def validate_picture(self, picture):
            if picture.data.filename and len(picture.data.filename) > 40:
                raise ValidationError('Μέγιστο μήκος ονόματος αρχείου 40 χαρακτήρες')

class EventForm(FlaskForm):
    racename = StringField('Ονομασία γεγονότος', validators=[DataRequired()])
    date = DateField('Ημερομηνία', format='%Y-%m-%d', validators=[DataRequired()], widget=DateInput())
    time = TimeField('Ώρα', format='%H:%M', validators=[DataRequired()], widget=TimeInput())
    declaration = FileField('Προκήρυξη')  
    distance = SelectField('Απόσταση', choices=[('5ΚΜ', '5ΚΜ'), ('10ΚΜ', '10ΚΜ'), ('21ΚΜ', '21ΚΜ'), ('Μαραθώνιος', 'Μαραθώνιος'), ('Άλλο', 'Άλλο')], validators=[DataRequired()])

    finalize_date = DateField('Ημερομηνία κλειδώματος εγγραφών', format='%Y-%m-%d', validators=[DataRequired()], widget=DateInput())
    link = StringField('Ιστοσελίδα', render_kw={"placeholder": "π.χ. https://www.syrosrunners.gr","class": "form-control form-control-sm"})
    map = StringField('Χάρτης διαδρομής', render_kw={"placeholder": "π.χ. https://www.syrosrunners/maps/syrosrun2024","class": "form-control form-control-sm"})
    
    categories = IntegerField('Ηλικιακές κατηγορίες')

    provides_bib = BooleanField('Αριθμός')
    provides_medal = BooleanField('Μετάλιο')
    provides_certificate = BooleanField('Αναμνηστικό δίπλωμα')
    provides_tshirt = BooleanField('Μπλουζάκι')
    provides_other = StringField('Άλλη παροχή')
    entry_fee = IntegerField('Κόστος συμμετοχής (Βασικό πακέτο)', default=0, 
                render_kw={"placeholder": "Αφήστε το κενό αν το βασικό πακέτο είναι δωρεάν","class": "form-control form-control-sm"}, 
                validators=[NumberRange(min=0, message="Παρακαλώ εισάγετε έναν ακέραιο αριθμό.")])
    submit = SubmitField('Καταχώριση')

class ShowEventForm(FlaskForm):
    start_date = DateField('Από την ημερομηνία', format='%Y-%m-%d', validators=[DataRequired()], widget=DateInput())
    end_date = DateField('Μέχρι την ημερομηνία', format='%Y-%m-%d', validators=[DataRequired()], widget=DateInput())
    options = SelectField('Επιλογή', choices=[('option1', 'Επιλογή 1'), ('option2', 'Επιλογή 2'), ('option3', 'Επιλογή 3')], validators=[DataRequired()])
    my_races = BooleanField('Εμφάνισε μόνο τα γεγονότα που έχω συμμετάσχει')
    submit = SubmitField('Εμφάνισε')

class UploadForm(FlaskForm):
    file = FileField('Επιλέξτε ένα αρχείο', validators=[ FileAllowed(['txt','csv'], 'Αποδεκτοί τύποι αρχείων: .txt και csv')])
    submit = SubmitField('Εισαγωγή δεδομένων στην ΒΔ')
    results = SubmitField('Αποτελέσματα')
    old_file = SubmitField('Εμφάνιση παλιότερων δεδομένων')

class HiddenForm(FlaskForm):
    hidden_tag = HiddenField('hidden_tag', validators=[DataRequired()])
    submit = SubmitField('Submit')