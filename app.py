from flask import Flask, render_template, request, redirect, url_for
import db
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Ordner für Foto-Uploads
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Konfiguration
app.config.from_mapping(
    SECRET_KEY='secret_key_just_for_dev_environment',
    DATABASE=os.path.join(app.instance_path, 'todos.sqlite')
)

# Flask CLI + DB-Teardown
app.cli.add_command(db.init_db)
app.teardown_appcontext(db.close_db_con)

# Startseite
@app.route('/')
def index():
    return redirect(url_for('lists'))

# Angebotsliste anzeigen
@app.route('/lists/')
def lists():
    db_con = db.get_db_con()
    sql_query = 'SELECT * from list ORDER BY name'
    lists_temp = db_con.execute(sql_query).fetchall()
    lists = []
    for list_temp in lists_temp:
        list_obj = dict(list_temp)
        sql_query = (
            'SELECT COUNT(complete) = SUM(complete) AS complete FROM todo '
            'JOIN todo_list ON list_id=? AND todo_id=todo.id;'
        )
        complete = db_con.execute(sql_query, (list_obj["id"],)).fetchone()['complete']
        list_obj['complete'] = complete
        lists.append(list_obj)

    if request.args.get('json') is not None:
        return lists
    return render_template('lists.html', lists=lists)

# Neues Angebot hinzufügen
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        description = request.form.get('description')
        region = request.form.get('region')

        # Dynamische Felder (z. B. Merkmale)
        dynamic_fields = {
            key: request.form.get(key)
            for key in request.form
            if key not in ['title', 'category', 'description', 'region']
        }
        features_json = json.dumps(dynamic_fields)

        # Bild speichern
        photo = request.files.get('photo')
        filename = None
        if photo and photo.filename != '':
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Zeitstempel erstellen
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # In Datenbank speichern
        db_con = db.get_db_con()
        db_con.execute(
            'INSERT INTO angebote (title, category, description, region, photo, features, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (title, category, description, region, filename, features_json, created_at)
        )
        db_con.commit()
        return redirect(url_for('lists'))

    return render_template('add.html')

# Beispieldaten einfügen
@app.route('/insert/sample')
def run_insert_sample():
    db.insert_sample()
    return 'Datenbank mit Beispieldaten gefüllt.'

# Anmeldung
@app.route('/anmelden', methods=['GET', 'POST'])
def anmelden():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if email == 'test@example.com' and password == 'pass123':
            return redirect(url_for('lists'))
        else:
            return render_template('anmelden.html', error='Ungültige Anmeldedaten')

    return render_template('anmelden.html')

# Registrierung
@app.route('/registrieren', methods=['GET', 'POST'])
def registrieren():
    if request.method == 'POST':
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        region = request.form.get('region')
        phone = request.form.get('phone')
        return redirect(url_for('lists'))
    return render_template('registrieren.html')

# Weiterleitung für alte URL
@app.route('/register')
def redirect_register():
    return redirect(url_for('registrieren'))

@app.route('/login/email')
def login_email():
    return 'Hier kommt das E-Mail Login hin (später implementieren)'

@app.route('/register/email')
def register_email():
    return 'Hier kommt die E-Mail Registrierung hin (später implementieren)'

# Starten
if __name__ == '__main__':
    app.run(debug=True)
