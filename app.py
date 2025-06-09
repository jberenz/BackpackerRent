from __future__ import annotations

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
    g,
    abort
)
from werkzeug.utils import secure_filename

# ---------------------------------------------------
# 1) DB-Hilfsfunktionen (für raw sqlite3 Queries)
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
    Schließt die SQLite-Verbindung am Ende jeder Request-Verarbeitung.
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
    try:
        os.makedirs(current_app.instance_path, exist_ok=True)
    except OSError:
        pass
    db_con = get_db_con()
    with current_app.open_resource("sql/drop_tables.sql") as f:
        db_con.executescript(f.read().decode("utf8"))
    with current_app.open_resource("sql/create_tables.sql") as f:
        db_con.executescript(f.read().decode("utf8"))
    click.echo("Datenbank wurde initialisiert.")

def insert_sample_data() -> None:
    """
    Optional: Füllt Beispieldaten aus insert_sample.sql ein.
    """
    db_con = get_db_con()
    with current_app.open_resource("sql/insert_sample.sql") as f:
        db_con.executescript(f.read().decode("utf8"))

# ---------------------------------------------------
# 2) Offer-Klasse mit reinem sqlite3-Zugriff
# ---------------------------------------------------

class Offer:
    TABLE_NAME = "offers"

    def __init__(
        self,
        title: str,
        category: str,
        region: str,
        price_per_night: float = 0.0,
        rating: float = 0.0,
        description: str | None = None,
        photo: str | None = None,
        features: dict | None = None,
        created_at: datetime | None = None,
        id: int | None = None
    ):
        self.id = id
        self.title = title
        self.category = category
        self.region = region
        self.price_per_night = price_per_night
        self.rating = rating
        self.description = description
        self.photo = photo
        self.features = features or {}
        self.created_at = created_at or datetime.utcnow()

    def __repr__(self):
        return (
            f"<Offer id={self.id} title={self.title!r} category={self.category!r} "
            f"region={self.region!r} price_per_night={self.price_per_night} rating={self.rating} "
            f"photo={self.photo!r} created_at={self.created_at}>"
        )

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Offer:
        # Features parsen
        feats: dict = {}
        if row["features"]:
            try:
                feats = json.loads(row["features"])
            except json.JSONDecodeError:
                feats = {}

        # created_at konvertieren
        raw = row["created_at"]
        if isinstance(raw, str):
            created = datetime.fromisoformat(raw)
        else:
            created = raw

        return cls(
            id=row["id"],
            title=row["title"],
            category=row["category"],
            description=row["description"],
            region=row["region"],
            price_per_night=row["price_per_night"],
            rating=row["rating"],
            photo=row["photo"],
            features=feats,
            created_at=created,
        )

    @classmethod
    def all(cls) -> list[Offer]:
        db = get_db_con()
        cur = db.execute(
            f"""
            SELECT id, title, category, description, region,
                   price_per_night, rating, photo, features, created_at
            FROM {cls.TABLE_NAME}
            ORDER BY created_at DESC
            """
        )
        return [cls.from_row(r) for r in cur.fetchall()]

    @classmethod
    def get_by_id(cls, offer_id: int) -> Offer | None:
        db = get_db_con()
        row = db.execute(
            f"SELECT * FROM {cls.TABLE_NAME} WHERE id = ?",
            (offer_id,)
        ).fetchone()
        return cls.from_row(row) if row else None

    def save(self) -> None:
        db = get_db_con()
        data = {
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "region": self.region,
            "price_per_night": self.price_per_night,
            "rating": self.rating,
            "photo": self.photo,
            "features": json.dumps(self.features) if self.features else None,
            "created_at": self.created_at,
        }

        if self.id is None:
            cols = ", ".join(data.keys())
            placeholders = ", ".join("?" for _ in data)
            vals = tuple(data.values())
            cur = db.execute(
                f"INSERT INTO {self.TABLE_NAME} ({cols}) VALUES ({placeholders})",
                vals
            )
            self.id = cur.lastrowid
        else:
            assignments = ", ".join(f"{k}=?" for k in data.keys())
            vals = tuple(data.values()) + (self.id,)
            db.execute(
                f"UPDATE {self.TABLE_NAME} SET {assignments} WHERE id = ?",
                vals
            )
        db.commit()

    def delete(self) -> None:
        if self.id is None:
            return
        db = get_db_con()
        db.execute(
            f"DELETE FROM {self.TABLE_NAME} WHERE id = ?",
            (self.id,)
        )
        db.commit()
        self.id = None

def init_offers_table() -> None:
    """
    Erstellt die offers-Tabelle, falls sie noch nicht existiert.
    """
    db = get_db_con()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS offers (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        title            TEXT    NOT NULL,
        category         TEXT    NOT NULL,
        description      TEXT,
        region           TEXT    NOT NULL,
        price_per_night  REAL    NOT NULL DEFAULT 0.0,
        rating           REAL    NOT NULL DEFAULT 0.0,
        photo            TEXT,
        features         TEXT,
        created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)
    db.commit()

# ---------------------------------------------------
# 3) Flask-App-Setup
# ---------------------------------------------------

app = Flask(__name__, instance_relative_config=True)

# Basis-Konfiguration
app.config.from_mapping(
    SECRET_KEY="secret_key_just_for_dev_environment",
    DATABASE=os.path.join(app.instance_path, "todos.sqlite")
)

# Upload-Ordner
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# CLI-Command & teardown
app.cli.add_command(init_db_command)
app.teardown_appcontext(close_db_con)

# Tabelle initialisieren
with app.app_context():
    init_offers_table()

# ---------------------------------------------------
# 4) TODO-Listen-Routen (raw sqlite3)
# ---------------------------------------------------

@app.route("/lists/")
def lists():
    db_con = get_db_con()
    lists_temp = db_con.execute("SELECT * FROM list ORDER BY name").fetchall()
    lists = []
    for lt in lists_temp:
        obj = dict(lt)
        complete = db_con.execute(
            "SELECT COUNT(complete)=SUM(complete) AS complete "
            "FROM todo JOIN todo_list ON list_id=? AND todo_id=todo.id;",
            (obj["id"],)
        ).fetchone()["complete"]
        obj["complete"] = complete
        lists.append(obj)

    if request.args.get("json"):
        return lists
    return render_template("lists.html", lists=lists)

@app.route("/lists/<int:id>")
def show_list(id):
    db_con = get_db_con()
    row = db_con.execute("SELECT name FROM list WHERE id=?", (id,)).fetchone()
    if not row:
        return "Liste nicht gefunden", 404

    todos = db_con.execute(
        "SELECT id, complete, description FROM todo "
        "JOIN todo_list ON todo_id=todo.id AND list_id=? ORDER BY id;",
        (id,)
    ).fetchall()

    if request.args.get("json"):
        return {"name": row["name"], "todos": [dict(t) for t in todos]}
    return render_template("list.html", list={"name": row["name"], "todos": todos})

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

@app.route("/insert/sample")
def run_insert_sample():
    insert_sample_data()
    return "Datenbank mit Beispieldaten gefüllt."

# ---------------------------------------------------
# 5) Auth-Routen
# ---------------------------------------------------

@app.route("/anmelden", methods=["GET", "POST"])
def anmelden():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if email == "test@example.com" and password == "pass123":
            return redirect(url_for("lists"))
        return render_template("anmelden.html", error="Ungültige Anmeldedaten")
    return render_template("anmelden.html")

@app.route("/registrieren", methods=["GET", "POST"])
def registrieren():
    if request.method == "POST":
        return redirect(url_for("lists"))
    return render_template("registrieren.html")

@app.route("/register")
def redirect_register():
    return redirect(url_for("registrieren"))

@app.route("/login/email")
def login_email():
    return "Email-Login (später)"

@app.route("/register/email")
def register_email():
    return "Email-Registrierung (später)"

# ---------------------------------------------------
# 6) Angebots-Routen (sqlite3-basiert)
# ---------------------------------------------------

@app.route("/")
def index():
    # Filter nach Tab-Typ, Region und Kategorie
    selected_type    = request.args.get("type", "backpacker")
    dest             = request.args.get("dest", type=str)
    category_filter  = request.args.get("category_filter", type=str)

    # Dynamische Kategorien pro Tab
    type_cats = {
        "backpacker": ["zelt","rucksack","multitool","schlafsack","luftmatratze"],
        "radtour":    ["radtasche","gaskocher","schlafsack","zelt","luftmatratze"]
    }
    categories = type_cats.get(selected_type, type_cats["backpacker"])

    # Baue WHERE-Klauseln
    conditions: list[str] = []
    params:     list[str] = []
    if dest:
        conditions.append("region = ?")
        params.append(dest)
    if category_filter:
        conditions.append("category = ?")
        params.append(category_filter)

    sql = "SELECT * FROM offers"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY created_at DESC"

    rows = get_db_con().execute(sql, params).fetchall()
    offers = [Offer.from_row(r) for r in rows]

    return render_template(
        "home.html",
        offers=offers,
        selected_type=selected_type,
        categories=categories
    )

@app.route("/offers")
def list_offers():
    offers = Offer.all()
    return render_template("lists_offers.html", offers=offers)

@app.route("/offers/add", methods=["GET", "POST"])
def add_offer():
    if request.method == "POST":
        title            = request.form.get("title", "").strip()
        category         = request.form.get("category", "").strip()
        description      = request.form.get("description", "").strip() or None
        region           = request.form.get("region", "").strip()
        price_per_night  = float(request.form.get("price_per_night", 0))
        rating           = 0.0

        photo_filename = None
        uploaded_file  = request.files.get("photo")
        if uploaded_file and uploaded_file.filename:
            filename   = secure_filename(uploaded_file.filename)
            ts         = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename   = f"{ts}_{filename}"
            save_path  = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            uploaded_file.save(save_path)
            photo_filename = f"uploads/{filename}"

        expected_keys = [
            "kapazitaet","packmass","gewicht","wassersaeule","material",
            "volumen","masse","tragesystem","funktionen","klingenlaenge",
            "temperatur","fuellmaterial","form","abmessungen","dicke",
            "maxbelast","volumen_rt","material_rt","gewicht_rt",
            "wasserdicht_rt","tragesystem_rt","leistung_gk","brennstoff_gk",
            "durchsatz_gk","gewicht_gk","abmessungen_gk"
        ]
        feature_data: dict = {}
        for key in expected_keys:
            val = request.form.get(key)
            if val and val.strip():
                feature_data[key] = val.strip()

        new_offer = Offer(
            title=title,
            category=category,
            description=description,
            region=region,
            price_per_night=price_per_night,
            rating=rating,
            photo=photo_filename,
            features=feature_data
        )
        new_offer.save()
        flash("Angebot erfolgreich erstellt!", "success")
        return redirect(url_for("index"))

    return render_template("add_offer.html")

@app.route("/offers/<int:offer_id>")
def offer_detail(offer_id):
    offer = Offer.get_by_id(offer_id)
    if not offer:
        abort(404)
    return render_template("offer_detail.html", offer=offer, features=offer.features)

# ---------------------------------------------------
# 7) Startpunkt
# ---------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
