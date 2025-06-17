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

init_app(app)

@app.route("/")
def index():
    db = get_db_con()

    region_id       = request.args.get("region_id",       type=int)
    category_id     = request.args.get("category_filter", type=int)
    min_price       = request.args.get("min_price",  0.0, type=float)
    max_price       = request.args.get("max_price", 50.0, type=float)
    selected_type   = request.args.get("type", "backpacker")

    sql = """
        SELECT
            o.offer_id,
            o.title,
            o.price_per_night,
            o.photo_path,
            c.category_name AS category,
            r.region_name   AS region
        FROM offers o
        JOIN category c ON o.category_id = c.category_id
        JOIN region   r ON o.region_id   = r.region_id
    """
    filters = []
    params  = []

    if region_id:
        filters.append("o.region_id = ?")
        params.append(region_id)
    if category_id:
        filters.append("o.category_id = ?")
        params.append(category_id)

    filters.append("o.price_per_night BETWEEN ? AND ?")
    params.extend([min_price, max_price])

    if filters:
        sql += " WHERE " + " AND ".join(filters)

    sql += " ORDER BY o.created_at DESC"

    offers    = db.execute(sql, params).fetchall()
    regionen  = db.execute("SELECT * FROM region").fetchall()

    if selected_type == "radtour":
        categories = db.execute("""
            SELECT * FROM category
            WHERE category_name IN ('Radtasche','Gaskocher','Schlafsack','Zelt','Luftmatratze','Multitool')
        """).fetchall()
    else:
        categories = db.execute("""
            SELECT * FROM category
            WHERE category_name IN ('Gaskocher','Schlafsack','Zelt','Luftmatratze','Rucksack','Multitool')
        """).fetchall()

    return render_template(
        "home.html",
        offers=offers,
        regionen=regionen,
        categories=categories,
        selected_type=selected_type,
        selected_region_id=region_id,
        selected_category_id=category_id
    )

@app.route("/angebot/<int:offer_id>")
def angebot_details(offer_id):
    db = get_db_con()

    offer = db.execute("""
        SELECT o.*, c.category_name AS category, r.region_name AS region
        FROM offers o
        JOIN category c ON o.category_id = c.category_id
        JOIN region   r ON o.region_id = r.region_id
        WHERE o.offer_id = ?
    """, (offer_id,)).fetchone()

    if offer is None:
        return "Angebot nicht gefunden", 404

    features_rows = db.execute("""
        SELECT f.feature_name, of.value
        FROM offer_features of
        JOIN features f ON of.feature_id = f.feature_id
        WHERE of.offer_id = ?
    """, (offer_id,)).fetchall()

    features = {row["feature_name"]: row["value"] for row in features_rows} if features_rows else {}

    return render_template("offer_detail.html", offer=offer, features=features)

@app.route("/anmelden", methods=["GET", "POST"])
def anmelden():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        db = get_db_con()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

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
        region_id_str = request.form.get("region_id", "").strip()
        phone = request.form.get("phone", "").strip() or None

        if not region_id_str:
            flash("Bitte wähle eine Region aus.", "warning")
            return render_template("registrieren.html", error="Bitte wähle eine Region aus.", regionen=regionen)

        try:
            region_id = int(region_id_str)
        except ValueError:
            flash("Ungültige Region.", "danger")
            return render_template("registrieren.html", error="Ungültige Region.", regionen=regionen)

        exists = db.execute("SELECT 1 FROM region WHERE region_id = ?", (region_id,)).fetchone()
        if not exists:
            flash("Region existiert nicht.", "danger")
            return render_template("registrieren.html", error="Region existiert nicht.", regionen=regionen)

        existing_user = db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        if existing_user:
            flash("E-Mail bereits registriert.", "warning")
            return render_template("registrieren.html", error="E-Mail bereits registriert.", regionen=regionen)

        hashed_pw = generate_password_hash(password)
        db.execute("""
            INSERT INTO users (first_name, last_name, email, password, region_id, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, hashed_pw, region_id, phone))
        db.commit()

        flash("Registrierung erfolgreich!", "success")
        return redirect(url_for("anmelden"))

    return render_template("registrieren.html", regionen=regionen)

@app.route("/angebot_erstellen", methods=["GET", "POST"])
def add_offer():
    db = get_db_con()
    categories = db.execute("SELECT * FROM category").fetchall()
    regionen = db.execute("SELECT * FROM region").fetchall()

    if request.method == "POST":
        title       = request.form["title"].strip()
        description = request.form.get("description", "").strip()
        category_id = request.form["category_id"]
        region_id   = request.form["region_id"]
        price_per_night = float(request.form["price_per_night"])
        user_id = session.get("user_id")

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

        cursor = db.execute("""
            INSERT INTO offers (
                user_id, title, description, category_id,
                region_id, price_per_night, photo_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, title, description, category_id, region_id, price_per_night, photo_path))
        db.commit()

        offer_id = cursor.lastrowid

        features = db.execute("SELECT feature_id, feature_name FROM features WHERE category_id = ?", (category_id,)).fetchall()
        for feature in features:
            value = request.form.get(feature["feature_name"])
            if value:
                db.execute("""
                    INSERT INTO offer_features (offer_id, feature_id, value)
                    VALUES (?, ?, ?)
                """, (offer_id, feature["feature_id"], value))
        db.commit()

        flash("Angebot erfolgreich erstellt!", "success")
        return redirect(url_for("index"))

    return render_template("angebot_erstellen.html", categories=categories, regionen=regionen)

@app.route("/mieten/<int:offer_id>", methods=["GET", "POST"])
def rental_form(offer_id):
    if "user_id" not in session:
        flash("Bitte zuerst anmelden.", "warning")
        return redirect(url_for("anmelden"))

    db = get_db_con()
    offer = db.execute("""
        SELECT o.*, r.region_name, c.category_name
        FROM offers o
        JOIN region r ON o.region_id = r.region_id
        JOIN category c ON o.category_id = c.category_id
        WHERE o.offer_id = ?
    """, (offer_id,)).fetchone()

    if not offer:
        abort(404)

    total_price = None
    num_days = None

    if request.method == "POST":
        action = request.form.get("action")
        start = request.form["start_date"]
        end = request.form["end_date"]
        address = request.form.get("address")
        name = request.form.get("name_on_card")
        card = request.form.get("card_number")
        sec = request.form.get("sec_code")

        try:
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            flash("Ungültiges Datum", "danger")
            return redirect(request.url)

        if end_date <= start_date:
            flash("Enddatum muss nach dem Startdatum liegen.", "warning")
            return redirect(request.url)

        num_days = (end_date - start_date).days
        total_price = num_days * offer["price_per_night"]

        if action == "book":
            db.execute("""
                INSERT INTO rentals (offer_id, user_id, start_date, end_date, total_price)
                VALUES (?, ?, ?, ?, ?)
            """, (offer_id, session["user_id"], start, end, total_price))
            db.commit()

            return render_template("rental_confirm.html", offer=offer, start_date=start, end_date=end,
                       address=address, name_on_card=name, total_price=total_price, num_days=num_days)


        # Wenn nur "Preis berechnen" gedrückt wurde → einfach Formular anzeigen mit Preis
        return render_template("rental_form.html", offer=offer,
                               start_date=start, end_date=end,
                               address=address, name_on_card=name,
                               card_number=card, sec_code=sec,
                               total_price=total_price, num_days=num_days)

    return render_template("rental_form.html", offer=offer)

@app.route("/profil")
def profil():
    if "user_id" not in session:
        return redirect(url_for("anmelden"))

    db = get_db_con()
    user = db.execute("""
        SELECT u.user_id, u.first_name, u.last_name, u.email, u.phone, r.region_name
        FROM users u
        JOIN region r ON u.region_id = r.region_id
        WHERE u.user_id = ?
    """, (session["user_id"],)).fetchone()

    section = request.args.get("section", "about")

    rentals = []
    if section == "booked":
        rentals = db.execute("""
            SELECT r.*, o.title, o.photo_path
            FROM rentals r
            JOIN offers o ON r.offer_id = o.offer_id
            WHERE r.user_id = ?
            ORDER BY r.start_date DESC
        """, (user["user_id"],)).fetchall()

    return render_template("profil.html", user=user, section=section, rentals=rentals)

@app.route("/insert/sample")
def insert_sample():
    insert_sample_data()
    return "Sample-Daten wurden eingefügt."

if __name__ == "__main__":
    app.run(debug=True)
