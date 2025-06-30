from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField # https://wtforms.readthedocs.io/en/3.0.x/fields/#wtforms.fields.DateField
from wtforms.validators import DataRequired, Length, Optional # https://wtforms.readthedocs.io/en/3.0.x/validators/

class EditProfileForm(FlaskForm): #https://wtforms.readthedocs.io/en/3.0.x/fields/#wtforms.fields.DateField
    first_name = StringField( 
        'Vorname',
        validators=[DataRequired(), Length(min=1, max=64)]
    )
    last_name = StringField(
        'Nachname',
        validators=[DataRequired(), Length(min=1, max=64)]
    )
    phone = StringField(
        'Telefon',
        validators=[Optional(), Length(max=20)]
    )
    password = PasswordField(
        'Neues Passwort (leer lassen, wenn gleich)',
        validators=[Optional(), Length(max=20)]
    )
    region_id = SelectField(
        'Region',
        coerce=int,
        validators=[DataRequired()]
    )
    submit = SubmitField('Speichern')

class RentalForm(FlaskForm):
    start_date = DateField(
        'Startdatum',
        format='%Y-%m-%d',
        validators=[DataRequired()]
    )
    end_date = DateField(
        'Enddatum',
        format='%Y-%m-%d',
        validators=[DataRequired()]
    )
    submit = SubmitField('Preis berechnen / Jetzt Mieten')
