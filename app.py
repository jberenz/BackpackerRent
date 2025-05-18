from flask import Flask, render_template, request, redirect, url_for
import db  # falls du das oben schon nutzt
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

# Startseite weiterleiten
@app.route('/')
def index():
    return redirect(url_for('lists'))

# TODO-Listen anzeigen
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
    else:
        return render_template('lists.html', lists=lists)

# Einzelne Liste anzeigen
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
    else:
        return render_template('list.html', list=list_obj)

# Beispieldaten einfügen
@app.route('/insert/sample')
def run_insert_sample():
    db.insert_sample()
    return 'Datenbank mit Beispieldaten gefüllt.'

# =============================
# Login / Registrierung
# =============================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        country = request.form['country']
        phone = request.form['phone']
        # Hier könntest du später z.B. SMS-Code-Login machen
        return redirect(url_for('lists'))  # Weiterleitung nach "Login"
    return render_template('login.html')

@app.route('/login/email')
def login_email():
    return 'Hier kommt das E-Mail Login hin (später implementieren)'

@app.route('/register/email')
def register_email():
    return 'Hier kommt die E-Mail Registrierung hin (später implementieren)'
