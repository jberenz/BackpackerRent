
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class EditProfileForm(FlaskForm):
    first_name = StringField('Vorname', validators=[DataRequired(), Length(1,64)])
    last_name  = StringField('Nachname', validators=[DataRequired(), Length(1,64)])
    phone      = StringField('Telefon',    validators=[Length(0,20)])
    password   = PasswordField('Neues Passwort (leer lassen, wenn gleich)', validators=[Length(0,128)])
    submit     = SubmitField('Speichern')
