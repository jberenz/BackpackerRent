from flask import Flask, render_template, request, redirect, url_for, flash, session, abort #https://flask.palletsprojects.com/en/stable/api/#flask.flash 
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime #https://docs.python.org/3/library/datetime.html #datetime.datetime.strptime
import os
import uuid

from db import get_db_con, insert_sample_data, init_app

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY="dev",
    DATABASE=os.path.join(app.instance_path, "backpacker.sqlite"),
    UPLOAD_FOLDER=os.path.join("static", "uploads")
)

from flask_wtf import CSRFProtect


app.config['WTF_CSRF_SECRET_KEY'] = 'noch-ein-geheimer-schluessel'
csrf = CSRFProtect(app)


os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True) # https://docs.python.org/3/library/os.html#os.makedirs
os.makedirs(app.instance_path, exist_ok=True)

init_app(app)

@csrf.exempt
@app.route("/")
def index():
    db = get_db_con()

    region_id       = request.args.get("region_id",       type=int) #https://flask.palletsprojects.com/en/stable/api/#flask.Request.args
    category_id     = request.args.get("category_filter", type=int)
    min_price       = request.args.get("min_price",  0.0, type=float)
    max_price       = request.args.get("max_price", 50.0, type=float)
    selected_type   = request.args.get("type", "backpacker")
    start           = request.args.get("start_date")
    end             = request.args.get("end_date")

    # Typabhängige erlaubte Kategorien
    if selected_type == "radtour":
        allowed_categories = ('Radtasche', 'Gaskocher', 'Schlafsack', 'Zelt', 'Luftmatratze', 'Multitool')
    else:
        allowed_categories = ('Rucksack', 'Gaskocher', 'Schlafsack', 'Zelt', 'Luftmatratze', 'Multitool')

    sql = """
        SELECT
            o.offer_id,
            o.title,
            o.price_per_night,
            o.photo_path AS photo,
            c.category_name AS category,
            r.region_name   AS region
        FROM offers o
        JOIN category c ON o.category_id = c.category_id
        JOIN region   r ON o.region_id   = r.region_id
    """
    filters = []
    params  = []

    # Filter: nur erlaubte Kategorien (abhängig vom Typ)
    filters.append("c.category_name IN ({})".format(','.join(['?'] * len(allowed_categories))))
    params.extend(allowed_categories)

    if region_id:
        filters.append("o.region_id = ?")
        params.append(region_id)
    if category_id:
        filters.append("o.category_id = ?")
        params.append(category_id)

    filters.append("o.price_per_night BETWEEN ? AND ?")
    params.extend([min_price, max_price])

    # Zeitraumfilter: Angebote ausschließen, die im Zeitraum vermietet sind
    if start and end:
        filters.append("""
            o.offer_id NOT IN (
                SELECT offer_id FROM rentals
                WHERE start_date <= ? AND end_date >= ?
            )
        """)
        params.extend([end, start])

    if filters:
        sql += " WHERE " + " AND ".join(filters)

    sql += " ORDER BY o.created_at DESC"

    offers = db.execute(sql, params).fetchall()
    regionen = db.execute("SELECT * FROM region").fetchall()

    categories = db.execute(
        "SELECT * FROM category WHERE category_name IN ({})".format(','.join(['?'] * len(allowed_categories))),
        allowed_categories
    ).fetchall()

    return render_template(
        "home.html",
        offers=offers,
        regionen=regionen,
        categories=categories,
        selected_type=selected_type,
        selected_region_id=region_id,
        selected_category_id=category_id,
        start_date=start,
        end_date=end
    )


@csrf.exempt
@app.route("/angebot/<int:offer_id>")
def angebot_details(offer_id):
    db = get_db_con()

    # Das Angebot mit Kategorie und Region laden
    offer = db.execute("""
        SELECT o.*, c.category_name AS category, r.region_name AS region
        FROM offers o
        JOIN category c ON o.category_id = c.category_id
        JOIN region   r ON o.region_id = r.region_id
        WHERE o.offer_id = ?
    """, (offer_id,)).fetchone()

    if offer is None:
        return "Angebot nicht gefunden", 404

    # Features + Werte laden (immer alle Features der Kategorie, auch wenn kein Wert vorhanden)
    features_rows = db.execute("""
        SELECT f.feature_name, f.feature_id, f.category_id, of.value
        FROM features f
        LEFT JOIN offer_features of 
            ON f.feature_id = of.feature_id AND of.offer_id = ?
        WHERE f.category_id = ?
    """, (offer_id, offer["category_id"])).fetchall()

    # Features als Liste von Dicts (leichter fürs Template)
    features = [
        {
            "feature_name": row["feature_name"],
            "value": row["value"]
        }
        for row in features_rows
    ]

    return render_template("offer_detail.html", offer=offer, features=features)


@csrf.exempt
@app.route("/anmelden", methods=["GET", "POST"])
def anmelden():
    if request.method == "POST": # Gibt die HTTP-Methode der aktuellen Anfrage zurück (z.B. "GET" oder "POST"): https://flask.palletsprojects.com/en/stable/api/#flask.Request.method
        email = request.form["email"].strip() # request.form ist ein MultiDict, der die Formulardaten enthält, die per POST gesendet wurden. Mit request.form["email"] greift man auf das Feld email zu: https://flask.palletsprojects.com/en/stable/api/#flask.Request.form
        password = request.form["password"].strip() # strip() entfernt Leerzeichen: https://docs.python.org/3/library/stdtypes.html#str.strip
        db = get_db_con()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user and check_password_hash(user["password"], password): #https://werkzeug.palletsprojects.com/en/stable/utils/#werkzeug.security.check_password_hash 
            session["user_id"] = user["user_id"] # https://flask.palletsprojects.com/en/stable/api/#flask.session
            flash(f"Willkommen zurück, {user['first_name']}!", "success")
            return redirect(url_for("index"))
        else:
            return render_template("anmelden.html", error="Ungültige Anmeldedaten")

    return render_template("anmelden.html")

@csrf.exempt
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
        phone = request.form.get("phone", "").strip() or None # Gibt den Wert für "region_id" zurück, oder den leeren String, falls das Feld nicht existiert: https://werkzeug.palletsprojects.com/en/stable/datastructures/#werkzeug.datastructures.MultiDict.get

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

        hashed_pw = generate_password_hash(password) # https://werkzeug.palletsprojects.com/en/stable/utils/#werkzeug.security.generate_password_hash 
        db.execute("""
            INSERT INTO users (first_name, last_name, email, password, region_id, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, hashed_pw, region_id, phone))
        db.commit()

        flash("Registrierung erfolgreich!", "success")
        return redirect(url_for("anmelden"))

    return render_template("registrieren.html", regionen=regionen)
@csrf.exempt
@app.route("/angebot_erstellen", methods=["GET", "POST"])
def add_offer():
    db = get_db_con()
    categories = db.execute("SELECT * FROM category").fetchall()
    regionen = db.execute("SELECT * FROM region").fetchall()

    selected_category_id = None
    features = []

    if request.method == "POST":
        user_id = session.get("user_id")
        if not user_id:
            flash("Bitte melde dich zuerst an.", "warning")
            return redirect(url_for("anmelden"))

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category_id = int(request.form.get("category_id", 0))
        region_id = int(request.form.get("region_id", 0))
        price_str = request.form.get("price_per_night", "").strip()

        selected_category_id = category_id
        features = db.execute("SELECT feature_id, feature_name FROM features WHERE category_id = ?", (category_id,)).fetchall()

        if not title or not price_str:
            flash("Bitte fülle alle Pflichtfelder aus.", "warning")
            return render_template("angebot_erstellen.html", categories=categories, regionen=regionen,
                                   features=features, selected_category_id=selected_category_id)

        price_per_night = float(price_str)

        # Foto
        photo = request.files.get("photo") #https://flask.palletsprojects.com/en/stable/api/#flask.Request.files
        photo_path = None #request.files ist ein MultiDict mit allen hochgeladenen Dateien. Mit .get("photo") wird die Datei mit dem Feldnamen "photo" abgerufen.
        if photo and photo.filename:
            filename = secure_filename(f"{uuid.uuid4()}_{photo.filename}") # secure_filename(filename) sichert Dateinamen, indem es unerwünschte oder gefährliche Zeichen entfernt, um sichere Dateinamen für das Speichern auf dem Server zu erzeugen. https://werkzeug.palletsprojects.com/en/stable/utils/#werkzeug.utils.secure_filename 
            full_path = os.path.join(app.config["UPLOAD_FOLDER"], filename) # uuid.uuid4() erzeugt eine zufällige UUID (Universally Unique Identifier), die hier genutzt wird, um Dateinamen eindeutig zu machen und Kollisionen zu vermeiden.https://docs.python.org/3/library/uuid.html#uuid.uuid4 
            # os.path.join verbindet mehrere Pfadbestandteile zu einem vollständigen Pfad, passend zum Betriebssystem. #https://docs.python.org/3/library/os.path.html#os.path.join
            photo.save(full_path) #photo ist ein FileStorage-Objekt, das eine hochgeladene Datei repräsentiert. Die Methode .save(path) speichert die Datei im angegebenen Pfad. https://flask.palletsprojects.com/en/stable/api/#flask.Request.files

            photo_path = os.path.join("uploads", filename).replace("\\", "/") #Ersetzen von Backslashes durch Slashes sorgt für plattformunabhängige Pfadangaben, insbesondere für Webpfade

        # Angebot
        cursor = db.execute("""
            INSERT INTO offers (
                user_id, title, description, category_id,
                region_id, price_per_night, photo_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, title, description, category_id, region_id, price_per_night, photo_path))
        db.commit()
        offer_id = cursor.lastrowid

        # Features
        for feature in features:
            value = request.form.get(f"feature_{feature['feature_id']}", "").strip()
            if value:
                db.execute("""
                    INSERT INTO offer_features (offer_id, feature_id, value)
                    VALUES (?, ?, ?)
                """, (offer_id, feature["feature_id"], value))
        db.commit()

        flash("Angebot erfolgreich erstellt!", "success")
        return redirect(url_for("index"))

    return render_template("angebot_erstellen.html", categories=categories, regionen=regionen, features=features, selected_category_id=selected_category_id)

@csrf.exempt
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
        abort(404) #https://flask.palletsprojects.com/en/stable/api/#flask.abort

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
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
        except ValueError:
            flash("Ungültiges Datum", "danger")
            return redirect(request.url)

        if end_date <= start_date:
            flash("Enddatum muss nach dem Startdatum liegen.", "warning")
            return redirect(request.url)

        # ✅ Konfliktprüfung
        conflict = db.execute("""
            SELECT 1 FROM rentals
            WHERE offer_id = ?
            AND start_date <= ?
            AND end_date >= ?
        """, (offer_id, end_date, start_date)).fetchone()

        if conflict:
            flash("Dieses Produkt ist im gewählten Zeitraum bereits gebucht.", "danger")
            return redirect(request.url)

        num_days = (end_date - start_date).days
        total_price = num_days * offer["price_per_night"]

        if action == "book":
            db.execute("""
                INSERT INTO rentals (offer_id, user_id, start_date, end_date, total_price)
                VALUES (?, ?, ?, ?, ?)
            """, (offer_id, session["user_id"], start_date, end_date, total_price))
            db.commit()

            return render_template("rental_confirm.html", offer=offer, start_date=start,
                                   end_date=end, address=address, name_on_card=name,
                                   total_price=total_price, num_days=num_days)

        # Preis berechnen
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
    own_offers = []

    if section == "booked":
        rentals = db.execute("""
            SELECT r.*, o.title, o.photo_path
            FROM rentals r
            JOIN offers o ON r.offer_id = o.offer_id
            WHERE r.user_id = ?
            ORDER BY r.start_date DESC
        """, (user["user_id"],)).fetchall()

    elif section == "own":
        own_offers = db.execute("""
            SELECT o.*, c.category_name AS category, r.region_name AS region
            FROM offers o
            JOIN category c ON o.category_id = c.category_id
            JOIN region   r ON o.region_id = r.region_id
            WHERE o.user_id = ?
            ORDER BY o.created_at DESC
        """, (user["user_id"],)).fetchall()

    return render_template(
        "profil.html",
        user=user,
        section=section,
        rentals=rentals,
        own_offers=own_offers

    )

from forms import EditProfileForm

@app.route('/profil/bearbeiten', methods=['GET','POST'])
def edit_profile():
    if 'user_id' not in session:
        flash("Bitte zuerst anmelden.", "warning")
        return redirect(url_for('anmelden'))

    db = get_db_con()
    user = db.execute("SELECT * FROM users WHERE user_id = ?", (session['user_id'],)).fetchone()

    # Regionsliste abrufen
    regions = db.execute("SELECT region_id, region_name FROM region").fetchall()
    form = EditProfileForm()
    # choices für das Dropdown: List[ (id, name), ... ]
    form.region_id.choices = [(r['region_id'], r['region_name']) for r in regions]

    if request.method == "GET":
        # Form mit aktuellen Werten vorbelegen
        form.first_name.data = user['first_name']
        form.last_name.data  = user['last_name']
        form.phone.data      = user['phone'] or ''
        form.region_id.data  = user['region_id']

    if form.validate_on_submit():
        new_pw = generate_password_hash(form.password.data) if form.password.data else user['password']
        db.execute("""
            UPDATE users 
            SET first_name = ?, last_name = ?, phone = ?, password = ?, region_id = ?
            WHERE user_id = ?
        """, (
            form.first_name.data,
            form.last_name.data,
            form.phone.data or None,
            new_pw,
            form.region_id.data,
            session['user_id']
        ))
        db.commit()
        flash('Profil erfolgreich aktualisiert.', 'success')
        return redirect(url_for('profil', section='about'))

    return render_template('profile_edit.html', form=form)

@csrf.exempt
@app.route("/logout")
def logout():
    session.clear() #Löscht alle Daten aus der aktuellen Benutzersitzung (Session), z.B. um einen Benutzer vollständig abzumelden: https://docs.python.org/3/library/stdtypes.html#dict.clear
    flash("Du wurdest abgemeldet.", "success")
    return redirect(url_for("index"))

@csrf.exempt
@app.route("/angebot_loeschen/<int:offer_id>", methods=["POST"])
def angebot_loeschen(offer_id):
    if "user_id" not in session:
        abort(403)

    db = get_db_con()
    offer = db.execute(
        "SELECT * FROM offers WHERE offer_id = ? AND user_id = ?",
        (offer_id, session["user_id"])
    ).fetchone()

    if not offer:
        return "Nicht erlaubt", 403

    db.execute("DELETE FROM offer_features WHERE offer_id = ?", (offer_id,))
    db.execute("DELETE FROM offers WHERE offer_id = ?", (offer_id,))
    db.commit()
    flash("Angebot erfolgreich gelöscht.", "success")
    return redirect(url_for("profil", section="own"))

@csrf.exempt
@app.route("/angebot_bearbeiten/<int:offer_id>", methods=["GET", "POST"])
def edit_offer(offer_id):
    if "user_id" not in session:
        return redirect(url_for("anmelden"))

    db = get_db_con()
    offer = db.execute(
        "SELECT * FROM offers WHERE offer_id = ? AND user_id = ?",
        (offer_id, session["user_id"])
    ).fetchone()

    if not offer:
        abort(404)

    categories = db.execute("SELECT * FROM category").fetchall()
    regionen = db.execute("SELECT * FROM region").fetchall()

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form.get("description", "").strip()
        category_id = int(request.form["category_id"])
        region_id = int(request.form["region_id"])
        price_per_night = float(request.form["price_per_night"])

        # optional neues Bild hochladen
        photo = request.files.get("photo")
        photo_path = offer["photo_path"]
        if photo and photo.filename:
            filename = secure_filename(f"{uuid.uuid4()}_{photo.filename}")
            full_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            photo.save(full_path)
            photo_path = os.path.join("uploads", filename).replace("\\", "/")

        db.execute("""
            UPDATE offers SET
                title = ?, description = ?, category_id = ?,
                region_id = ?, price_per_night = ?, photo_path = ?
            WHERE offer_id = ? AND user_id = ?
        """, (title, description, category_id, region_id, price_per_night, photo_path, offer_id, session["user_id"]))

        db.execute("DELETE FROM offer_features WHERE offer_id = ?", (offer_id,))
        features = db.execute("SELECT feature_id, feature_name FROM features WHERE category_id = ?", (category_id,)).fetchall()
        for feature in features:
            value = request.form.get(f"feature_{feature['feature_id']}")
            if value:
                db.execute("""
                    INSERT INTO offer_features (offer_id, feature_id, value)
                    VALUES (?, ?, ?)
                """, (offer_id, feature["feature_id"], value))
        db.commit()

        flash("Angebot erfolgreich aktualisiert.", "success")
        return redirect(url_for("profil", section="own"))

    # Lade auch die Features mit vorhandenen Werten
    feature_rows = db.execute("""
        SELECT f.feature_id, f.feature_name, of.value
        FROM features f
        LEFT JOIN offer_features of ON f.feature_id = of.feature_id AND of.offer_id = ?
        WHERE f.category_id = ?
    """, (offer_id, offer["category_id"])).fetchall()

    return render_template("angebot_erstellen.html",
                           categories=categories,
                           regionen=regionen,
                           offer=offer,
                           features=feature_rows)
@csrf.exempt
@app.route("/add_to_cart/<int:offer_id>", methods=["POST"])
def add_to_cart(offer_id):
    cart = session.get("cart", [])
    
    # Füge nur hinzu, wenn nicht schon enthalten
    if offer_id not in cart:
        cart.append(offer_id)
        session["cart"] = cart
        flash("Zum Warenkorb hinzugefügt.", "success")
    else:
        flash("Dieses Produkt ist bereits im Warenkorb.", "info")
    
    return redirect(url_for("warenkorb"))


@csrf.exempt
@app.route("/warenkorb")
def warenkorb():
    cart = session.get("cart", [])
    if not cart:
        flash("Dein Warenkorb ist leer.", "info")
        return render_template("warenkorb.html", offers=[])

    db = get_db_con()
    placeholders = ','.join('?' for _ in cart)
    offers = db.execute(f"""
        SELECT o.*, c.category_name AS category, r.region_name AS region
        FROM offers o
        JOIN category c ON o.category_id = c.category_id
        JOIN region   r ON o.region_id = r.region_id
        WHERE o.offer_id IN ({placeholders})
    """, cart).fetchall()

    return render_template("warenkorb.html", offers=offers)
@csrf.exempt
@app.route("/remove_from_cart/<int:offer_id>", methods=["POST"])
def remove_from_cart(offer_id):
    cart = session.get("cart", [])
    if offer_id in cart:
        cart.remove(offer_id)
        session["cart"] = cart
        flash("Angebot aus dem Warenkorb entfernt.", "success")
    return redirect(url_for("warenkorb"))
@csrf.exempt

@csrf.exempt
@app.route("/mieten", methods=["GET", "POST"])
def mietseite():
    if "user_id" not in session:
        flash("Bitte zuerst anmelden.", "warning")
        return redirect(url_for("anmelden"))

    cart = session.get("cart", [])
    if not cart:
        flash("Dein Warenkorb ist leer.", "info")
        return redirect(url_for("warenkorb"))

    db = get_db_con()
    placeholders = ','.join(['?'] * len(cart))
    offers = db.execute(f"""
        SELECT o.*, r.region_name, c.category_name
        FROM offers o
        JOIN region r ON o.region_id = r.region_id
        JOIN category c ON o.category_id = c.category_id
        WHERE o.offer_id IN ({placeholders})
    """, cart).fetchall()

    if request.method == "GET":
        return render_template("rental_form.html", offers=offers)

    action = request.form.get("action", "calculate")
    start = request.form.get("start_date", "")
    end = request.form.get("end_date", "")
    address = request.form.get("address", "")
    name = request.form.get("name_on_card", "")
    card = request.form.get("card_number", "")
    sec = request.form.get("sec_code", "")

    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    except ValueError:
        flash("Ungültiges Datum", "danger")
        return redirect(request.url)

    if end_date <= start_date:
        flash("Enddatum muss nach dem Startdatum liegen.", "warning")
        return redirect(request.url)

    # ✅ Konfliktprüfung für alle Angebote im Warenkorb
    for offer in offers:
        conflict = db.execute("""
            SELECT 1 FROM rentals
            WHERE offer_id = ?
            AND start_date <= ?
            AND end_date >= ?
        """, (offer["offer_id"], end_date, start_date)).fetchone()

        if conflict:
            flash(f"Das Produkt '{offer['title']}' ist im gewählten Zeitraum nicht verfügbar.", "danger")
            return redirect(request.url)

    num_days = (end_date - start_date).days
    total_price = sum([num_days * offer["price_per_night"] for offer in offers])

    if action == "book":
        for offer in offers:
            einzelpreis = num_days * offer["price_per_night"]
            db.execute("""
                INSERT INTO rentals (offer_id, user_id, start_date, end_date, total_price)
                VALUES (?, ?, ?, ?, ?)
            """, (offer["offer_id"], session["user_id"], start_date, end_date, einzelpreis))
        db.commit()

        session["cart"] = []  # Warenkorb leeren

        return render_template("rental_confirm.html", offers=offers, start_date=start,
                               end_date=end, address=address, name_on_card=name,
                               total_price=total_price, num_days=num_days)

    # Preis berechnen
    return render_template("rental_form.html", offers=offers, start_date=start,
                           end_date=end, address=address, name_on_card=name,
                           card_number=card, sec_code=sec,
                           total_price=total_price, num_days=num_days)

@app.route('/features_for_category/<int:category_id>')
def features_for_category(category_id):
    db = get_db_con()
    features = db.execute(
        "SELECT feature_id, feature_name FROM features WHERE category_id = ?",
        (category_id,)
    ).fetchall()
    return render_template('partials/_features.html', features=features)




