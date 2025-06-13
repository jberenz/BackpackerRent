from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import uuid

from db import get_db_con, insert_sample_data, init_app

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY="dev",
    DATABASE=os.path.join(app.instance_path, "backpacker.sqlite"),
    UPLOAD_FOLDER=os.path.join("static", "uploads")
)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.instance_path, exist_ok=True)

# initialize DB CLI and teardown
init_app(app)

@app.route("/")
def index():
    db = get_db_con()
    offers = db.execute("""
        SELECT o.offer_id, o.title, o.price_per_night, o.photo_path,
               c.category_name, r.region_name
        FROM offers o
        JOIN category c ON o.category_id = c.category_id
        JOIN region r   ON o.region_id   = r.region_id
        ORDER BY o.created_at DESC
    """).fetchall()
    return render_template("home.html", offers=offers)

@app.route("/anmelden", methods=["GET", "POST"])
def anmelden():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        db = get_db_con()
        user = db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["user_id"]
            flash(f"Willkommen zurück, {user['first_name']}!", "success")
            return redirect(url_for("index"))
        else:
            return render_template("anmelden.html", error="Ungültige Anmeldedaten")

    return render_template("anmelden.html")

@app.route("/registrieren", methods=["GET", "POST"])
def registrieren():
    db = get_db_con()
    regionen = db.execute("SELECT * FROM region").fetchall()

    if request.method == "POST":
        first_name = request.form["first_name"].strip()
        last_name  = request.form["last_name"].strip()
        email      = request.form["email"].strip()
        password   = request.form["password"].strip()
        region_id  = request.form["region_id"].strip()
        phone      = request.form.get("phone", "").strip() or None

        existing_user = db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        if existing_user:
            return render_template(
                "registrieren.html",
                error="E-Mail bereits registriert",
                regionen=regionen
            )

        hashed_pw = generate_password_hash(password)
        db.execute(
            """
            INSERT INTO users (
                first_name, last_name, email,
                password, region_id, phone
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (first_name, last_name, email, hashed_pw, region_id, phone)
        )
        db.commit()
        flash("Registrierung erfolgreich!", "success")
        return redirect(url_for("anmelden"))

    return render_template("registrieren.html", regionen=regionen)

@app.route("/angebot_erstellen", methods=["GET", "POST"])
def add_offer():
    db = get_db_con()
    categories = db.execute("SELECT * FROM category").fetchall()
    regionen   = db.execute("SELECT * FROM region").fetchall()

    if request.method == "POST":
        title           = request.form["title"].strip()
        description     = request.form.get("description", "").strip()
        category_id     = request.form["category"]
        region_id       = request.form["region_id"]
        price_per_night = float(request.form["price_per_night"])
        user_id         = session.get("user_id")

        if not user_id:
            flash("Bitte melde dich zuerst an.", "warning")
            return redirect(url_for("anmelden"))

        photo = request.files.get("photo")
        photo_path = None
        if photo and photo.filename:
            filename = secure_filename(f"{uuid.uuid4()}_{photo.filename}")
            full_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            photo.save(full_path)
            photo_path = os.path.join("uploads", filename)

        db.execute(
            """
            INSERT INTO offers (
                user_id, title, description,
                category_id, region_id,
                price_per_night, photo_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, title, description,
                category_id, region_id,
                price_per_night, photo_path
            )
        )
        db.commit()
        flash("Angebot erfolgreich erstellt!", "success")
        return redirect(url_for("index"))

    return render_template(
        "angebot_erstellen.html",
        categories=categories,
        regionen=regionen
    )

@app.route("/insert/sample")
def insert_sample():
    insert_sample_data()
    return "Sample-Daten wurden eingefügt."

if __name__ == "__main__":
    app.run(debug=True)
