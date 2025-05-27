from flask import Flask, render_template, request, redirect, url_for
import db
import os

app = Flask(__name__)

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

# =============================
# 📝 TODO-Listen-Logik
# =============================

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

@app.route('/lists/<int:id>')
def show_list(id):
    db_con = db.get_db_con()
    sql_query_1 = 'SELECT name FROM list WHERE id=?'
    sql_query_2 = (
        'SELECT id, complete, description FROM todo '
        'JOIN todo_list ON todo_id=todo.id AND list_id=? '
        'ORDER BY id;'
    )
    row = db_con.execute(sql_query_1, (id,)).fetchone()
    if row is None:
        return 'Liste nicht gefunden', 404

    list_obj = {'name': row['name']}
    list_obj['todos'] = db_con.execute(sql_query_2, (id,)).fetchall()

    if request.args.get('json') is not None:
        list_obj['todos'] = [dict(todo) for todo in list_obj['todos']]
        return list_obj
    return render_template('list.html', list=list_obj)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            db_con = db.get_db_con()
            db_con.execute('INSERT INTO list (name) VALUES (?)', (name,))
            db_con.commit()
        return redirect(url_for('lists'))
    return render_template('add.html')

@app.route('/insert/sample')
def run_insert_sample():
    db.insert_sample()
    return 'Datenbank mit Beispieldaten gefüllt.'

# =============================
# 🔐 Authentifizierung
# =============================

# Neue Login-Seite
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

# Neue Registrierungsseite
@app.route('/registrieren', methods=['GET', 'POST'])
def registrieren():
    if request.method == 'POST':
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        region = request.form.get('region')
        phone = request.form.get('phone')
        # Hier kannst du später in die DB schreiben
        return redirect(url_for('lists'))
    return render_template('registrieren.html')

# 🔁 Alte URL weiterleiten (Fehlervermeidung)
@app.route('/register')
def redirect_register():
    return redirect(url_for('registrieren'))

# Optional: alte E-Mail-Routen (noch nicht verwendet)
@app.route('/login/email')
def login_email():
    return 'Hier kommt das E-Mail Login hin (später implementieren)'

@app.route('/register/email')
def register_email():
    return 'Hier kommt die E-Mail Registrierung hin (später implementieren)'

# =============================
# 🚀 Startpunkt
# =============================

if __name__ == '__main__':
    app.run(debug=True)
