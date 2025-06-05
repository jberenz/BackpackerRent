import os
import json
from datetime import datetime

import click
import sqlite3
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    g
)
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

# ---------------------------------------------------
# 1) DB-Hilfsfunktionen (für raw sqlite3 Queries für TODO-Listen)
# ---------------------------------------------------

def get_db_con(pragma_foreign_keys: bool = True) -> sqlite3.Connection:
    """
    Liefert eine SQLite-Verbindung aus dem Flask-Context (g).
    Aktiviert optional PRAGMA foreign_keys = ON.
    """
    if "db_con" not in g:
        g.db_con = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db_con.row_factory = sqlite3.Row
        if pragma_foreign_keys:
            g.db_con.execute("PRAGMA foreign_keys = ON;")
    return g.db_con

def close_db_con(e=None) -> None:
    """
    Schließt die SQLite-Verbindung am Ende der Request-Verarbeitung,
    sofern sie geöffnet war.
    """
    db_con = g.pop("db_con", None)
    if db_con is not None:
        db_con.close()

@click.command("init-db")
def init_db_command() -> None:
    """
    CLI-Command, um die Datenbank neu aufzusetzen:
    1) drop_tables.sql ausführen
    2) create_tables.sql ausführen
    """
    # Stelle sicher, dass der instance-Ordner existiert
    try:
        os.makedirs(current_app.instance_path, exist_ok=True)
    except OSError:
        pass

    db_con = get_db_con()
    # DROP aller Tabellen
    with current_app.open_resource("sql/drop_tables.sql") as f:
        db_con.executescript(f.read().decode("utf8"))
    # CREATE aller Tabellen
    with current_app.open_resource("sql/create_tables.sql") as f:
        db_con.executescript(f.read().decode("utf8"))
    click.echo("Datenbank wurde initialisiert.")

def insert_sample_data() -> None:
    """
    Optionales Einfügen von Beispieldaten aus insert_sample.sql
    """
    db_con = get_db_con()
    with current_app.open_resource("sql/insert_sample.sql") as f:
        db_con.executescript(f.read().decode("utf8"))


# ---------------------------------------------------
# 2) SQLAlchemy-Models (interna)
# ---------------------------------------------------

# Ein einziges SQLAlchemy-Objekt für unsere Modelle
sqla_db = SQLAlchemy()

class Todo(sqla_db.Model):
    __tablename__ = "todo"

    id = sqla_db.Column(sqla_db.Integer, primary_key=True, autoincrement=True)
    description = sqla_db.Column(sqla_db.Text, nullable=False)
    complete = sqla_db.Column(sqla_db.Boolean, default=False, nullable=False)

    # n-m Beziehung zu List über die Zwischentabelle "todo_list"
    lists = sqla_db.relationship(
        "List",
        secondary="todo_list",
        back_populates="todos"
    )

    def __repr__(self):
        return f"<Todo id={self.id} complete={self.complete} description={self.description!r}>"

class List(sqla_db.Model):
    __tablename__ = "list"

    id = sqla_db.Column(sqla_db.Integer, primary_key=True, autoincrement=True)
    name = sqla_db.Column(sqla_db.Text, nullable=False)

    # n-m Beziehung zu Todo über "todo_list"
    todos = sqla_db.relationship(
        "Todo",
        secondary="todo_list",
        back_populates="lists"
    )

    def __repr__(self):
        return f"<List id={self.id} name={self.name!r}>"

class TodoList(sqla_db.Model):
    __tablename__ = "todo_list"

    list_id = sqla_db.Column(
        sqla_db.Integer,
        sqla_db.ForeignKey("list.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    todo_id = sqla_db.Column(
        sqla_db.Integer,
        sqla_db.ForeignKey("todo.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    complete = sqla_db.Column(sqla_db.Integer, default=0, nullable=False)

    todo = sqla_db.relationship(
        "Todo",
        backref=sqla_db.backref("todo_list_entries", cascade="all, delete-orphan")
    )
    list = sqla_db.relationship(
        "List",
        backref=sqla_db.backref("todo_list_entries", cascade="all, delete-orphan")
    )

    def __repr__(self):
        return f"<TodoList list_id={self.list_id} todo_id={self.todo_id} complete={self.complete}>"

class Offer(sqla_db.Model):
    __tablename__ = "offers"

    id = sqla_db.Column(sqla_db.Integer, primary_key=True, autoincrement=True)
    title = sqla_db.Column(sqla_db.Text, nullable=False)
    category = sqla_db.Column(sqla_db.Text, nullable=False)
    description = sqla_db.Column(sqla_db.Text, nullable=True)
    region = sqla_db.Column(sqla_db.Text, nullable=False)
    price_per_night = sqla_db.Column(sqla_db.Float, nullable=False, default=0.0)
    rating = sqla_db.Column(sqla_db.Float, nullable=False, default=0.0)
    photo = sqla_db.Column(sqla_db.Text, nullable=True)    # z.B. "uploads/20230601_zelt.jpg"
    features = sqla_db.Column(sqla_db.Text, nullable=True) # JSON-String mit den dynamischen Merkmalen
    created_at = sqla_db.Column(sqla_db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<Offer id={self.id} title={self.title!r} category={self.category!r} "
            f"region={self.region!r} price_per_night={self.price_per_night} rating={self.rating} "
            f"photo={self.photo!r} created_at={self.created_at}>"
        )


# ---------------------------------------------------
# 3) Flask-App-Setup
# ---------------------------------------------------

app = Flask(__name__, instance_relative_config=True)

# 3a) Basis-Konfiguration: SECRET_KEY & Pfad zur SQLite-Datei (für raw sqlite3)
app.config.from_mapping(
    SECRET_KEY="secret_key_just_for_dev_environment",
    DATABASE=os.path.join(app.instance_path, "todos.sqlite")
)

# 3b) Konfiguration für SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + app.config["DATABASE"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 3c) Ordner für Uploads (Fotos von Angeboten)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# 3d) Registriere raw-sqlite3 CLI-Command und teardown-Funktion
app.cli.add_command(init_db_command)
app.teardown_appcontext(close_db_con)

# 3e) SQLAlchemy initialisieren
sqla_db.init_app(app)

# 3f) Erstelle alle Tabellen (Todo, List, TodoList, Offer) beim ersten Start
with app.app_context():
    sqla_db.create_all()


# ---------------------------------------------------
# 4) 🔀 TODO-Listen-Routen (raw sqlite3)
# ---------------------------------------------------

# Startseite zeigt jetzt home.html (statt redirect auf /lists/)
@app.route("/")
def index():
    # Alle Angebote aus der Datenbank holen, sortiert nach Erstellungszeitpunkt absteigend
    offers = Offer.query.order_by(Offer.created_at.desc()).all()
    return render_template("home.html", offers=offers)

# Alle TODO-Listen anzeigen
@app.route("/lists/")
def lists():
    db_con = get_db_con()
    sql_query = "SELECT * FROM list ORDER BY name"
    lists_temp = db_con.execute(sql_query).fetchall()
    lists = []
    for list_temp in lists_temp:
        list_obj = dict(list_temp)
        sql_query = (
            "SELECT COUNT(complete) = SUM(complete) AS complete FROM todo "
            "JOIN todo_list ON list_id=? AND todo_id=todo.id;"
        )
        complete = db_con.execute(sql_query, (list_obj["id"],)).fetchone()["complete"]
        list_obj["complete"] = complete
        lists.append(list_obj)

    if request.args.get("json") is not None:
        return lists
    return render_template("lists.html", lists=lists)

# Einzelne TODO-Liste und ihre Todos anzeigen
@app.route("/lists/<int:id>")
def show_list(id):
    db_con = get_db_con()
    sql_query_1 = "SELECT name FROM list WHERE id=?"
    sql_query_2 = (
        "SELECT id, complete, description FROM todo "
        "JOIN todo_list ON todo_id=todo.id AND list_id=? "
        "ORDER BY id;"
    )
    row = db_con.execute(sql_query_1, (id,)).fetchone()
    if row is None:
        return "Liste nicht gefunden", 404

    list_obj = {"name": row["name"]}
    list_obj["todos"] = db_con.execute(sql_query_2, (id,)).fetchall()

    if request.args.get("json") is not None:
        list_obj["todos"] = [dict(todo) for todo in list_obj["todos"]]
        return list_obj
    return render_template("list.html", list=list_obj)

# Neue Liste anlegen (Formular und Einfügen)
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form.get("name")
        if name:
            db_con = get_db_con()
            db_con.execute("INSERT INTO list (name) VALUES (?)", (name,))
            db_con.commit()
        return redirect(url_for("lists"))
    return render_template("add.html")

# Beispieldaten einfügen (nur via Browser-Aufruf)
@app.route("/insert/sample")
def run_insert_sample():
    insert_sample_data()
    return "Datenbank mit Beispieldaten gefüllt."


# ---------------------------------------------------
# 5) 🔒 Authentifizierungs-Routen
# ---------------------------------------------------

# Login-Seite
@app.route("/anmelden", methods=["GET", "POST"])
def anmelden():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email == "test@example.com" and password == "pass123":
            return redirect(url_for("lists"))
        else:
            return render_template("anmelden.html", error="Ungültige Anmeldedaten")

    return render_template("anmelden.html")

# Registrierungsseite
@app.route("/registrieren", methods=["GET", "POST"])
def registrieren():
    if request.method == "POST":
        last_name = request.form.get("last_name")
        first_name = request.form.get("first_name")
        region = request.form.get("region")
        phone = request.form.get("phone")
        # TODO: Hier später in die DB schreiben
        return redirect(url_for("lists"))
    return render_template("registrieren.html")

# Alte URL weiterleiten
@app.route("/register")
def redirect_register():
    return redirect(url_for("registrieren"))

# Platzhalter-Routen (noch nicht verwendet)
@app.route("/login/email")
def login_email():
    return "Hier kommt das E-Mail Login hin (später implementieren)"

@app.route("/register/email")
def register_email():
    return "Hier kommt die E-Mail Registrierung hin (später implementieren)"


# ---------------------------------------------------
# 6) 🚀 Angebots-Routen (SQLAlchemy)
# ---------------------------------------------------

@app.route("/offers")
def list_offers():
    """
    Zeigt alle Angebote an (SQLAlchemy-Abfrage).
    """
    offers = Offer.query.order_by(Offer.created_at.desc()).all()
    return render_template("lists_offers.html", offers=offers)

@app.route("/offers/add", methods=["GET", "POST"])
def add_offer():
    """
    Zeigt das Formular zum Anlegen eines neuen Angebots und
    verarbeitet die POST-Daten, um ein Offer-Objekt in die DB zu speichern.
    """
    if request.method == "POST":
        # ----- A) Basis-Felder auslesen -----
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        region = request.form.get("region", "").strip()

        # Momentan fixe Default-Werte für Preis und Rating:
        price_per_night = 0.0
        rating = 0.0

        # ----- B) Foto-Upload verarbeiten -----
        photo_filename = None
        uploaded_file = request.files.get("photo")
        if uploaded_file and uploaded_file.filename:
            filename = secure_filename(uploaded_file.filename)
            ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{ts}_{filename}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            uploaded_file.save(save_path)
            # Speichere nur den relativen Pfad unter /static
            photo_filename = os.path.join("uploads", filename)

        # ----- C) Dynamische Merkmale sammeln -----
        expected_feature_keys = [
            "kapazitaet", "packmass", "gewicht", "wassersaeule", "material",
            "volumen", "masse", "tragesystem",
            "funktionen", "klingenlaenge",
            "temperatur", "fuellmaterial", "form",
            "abmessungen", "dicke", "maxbelast",
            "volumen_rt", "material_rt", "gewicht_rt", "wasserdicht_rt", "tragesystem_rt",
            "leistung_gk", "brennstoff_gk", "durchsatz_gk", "gewicht_gk", "abmessungen_gk"
        ]
        feature_data = {}
        for key in expected_feature_keys:
            value = request.form.get(key)
            if value and value.strip():
                feature_data[key] = value.strip()

        # ----- D) Offer-Instanz anlegen und speichern -----
        new_offer = Offer(
            title=title,
            category=category,
            description=description or None,
            region=region,
            price_per_night=price_per_night,
            rating=rating,
            photo=photo_filename,
            features=json.dumps(feature_data) if feature_data else None
        )
        sqla_db.session.add(new_offer)
        sqla_db.session.commit()

        flash("Angebot erfolgreich erstellt!", "success")
        # Nach dem Speichern zurück zur Startseite (/)
        return redirect(url_for("index"))

    # GET: Formular anzeigen
    return render_template("add_offer.html")

@app.route("/offers/<int:offer_id>")
def offer_detail(offer_id):
    """
    Zeigt ein einzelnes Angebot im Detail an.
    """
    offer = Offer.query.get_or_404(offer_id)

    # Features (JSON) wieder in ein Python-Dict umwandeln
    feature_dict = {}
    if offer.features:
        try:
            feature_dict = json.loads(offer.features)
        except ValueError:
            feature_dict = {}

    return render_template("offer_detail.html", offer=offer, features=feature_dict)


# ---------------------------------------------------
# 7) 🚀 Startpunkt
# ---------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
