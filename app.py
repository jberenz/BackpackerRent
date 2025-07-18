from flask import Flask, render_template, request, redirect, url_for, flash, session, abort #https://flask.palletsprojects.com/en/stable/api/#flask.flash 
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime #https://docs.python.org/3/library/datetime.html #datetime.datetime.strptime
import os
import uuid
from functools import wraps

def login_required(view): # https://flask.palletsprojects.com/en/latest/tutorial/views/#require-authentication-in-other-views
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Bitte zuerst anmelden.", "warning")
            return redirect(url_for("anmelden", next=request.path))
        return view(*args, **kwargs)
    return wrapped_view

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
os.makedirs(app.instance_path, exist_ok=True) # Erstellt notwendige Ordner (Uploads, Instanzordner), falls sie noch nicht existieren.

init_app(app)

@csrf.exempt # nicht notwendig, weil Home Seite nichts zurückgibt (kein [POST]), aber kein Risiko es drin zu lassen
@app.route("/") #https://flask.palletsprojects.com/en/latest/quickstart/
def index(): # View Funktion: enthält die Logik zum Laden und Filtern von Angeboten
    db = get_db_con() # Verbindung zur SQLite DB, gibt sqlite3.Connection-Objekt zurück ( instance/backpacker.sqlite)

    # Holt GET-Parameter aus der URL
    region_id       = request.args.get("region_id",       type=int) # https://flask.palletsprojects.com/en/stable/api/#flask.Request.args
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
    filters.append("c.category_name IN ({})".format(','.join(['?'] * len(allowed_categories)))) # https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders (Platzhalter)
    params.extend(allowed_categories) # https://docs.python.org/3/tutorial/datastructures.html#more-on-lists

    if region_id:
        filters.append("o.region_id = ?") # Falls region_id gesetzt ist: Filter auf diese Region
        params.append(region_id)
    if category_id:
        filters.append("o.category_id = ?") # Falls category_id gesetzt ist: Filter auf diese Kategorie                                       
        params.append(category_id)

    filters.append("o.price_per_night BETWEEN ? AND ?") # Filtert nur Angebote im Preisbereich
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

    sql += " ORDER BY o.created_at DESC" # (neuste zuerst)

    offers = db.execute(sql, params).fetchall() # Führt die SQL-Abfrage mit den gesetzten Parametern aus
    regionen = db.execute("SELECT * FROM region").fetchall() # fetchall() gibt eine Liste aller passenden Angebote zurück, Quelle: https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.fetchall
    # Lädt alle Regionen für das Dropdown-Menü in der UI

    categories = db.execute(
        "SELECT * FROM category WHERE category_name IN ({})".format(','.join(['?'] * len(allowed_categories))),
        allowed_categories # Lädt Kategorien abhämgig vom Typ Radtour oder Backpacker
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
    ) # ermöglicht Vorbelegen von Filterfeldern im Frontend


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



@app.route("/anmelden", methods=["GET", "POST"])
def anmelden():
    next_url = request.args.get("next", url_for("index"))
    if request.method == "POST": # Gibt die HTTP-Methode der aktuellen Anfrage zurück (z.B. "GET" oder "POST"): https://flask.palletsprojects.com/en/stable/api/#flask.Request.method
        email = request.form["email"].strip() # request.form ist ein MultiDict, der die Formulardaten enthält, die per POST gesendet wurden. Mit request.form["email"] greift man auf das Feld email zu: https://flask.palletsprojects.com/en/stable/api/#flask.Request.form
        password = request.form["password"].strip() # strip() entfernt Leerzeichen: https://docs.python.org/3/library/stdtypes.html#str.strip
        db = get_db_con()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone() # sucht angegebene email in DB

        if user and check_password_hash(user["password"], password): #https://werkzeug.palletsprojects.com/en/stable/utils/#werkzeug.security.check_password_hash 
            session["user_id"] = user["user_id"] # Speichert die Nutzer-ID in der Session für spätere Authentifizierung. https://flask.palletsprojects.com/en/stable/api/#flask.session
            flash(f"Willkommen zurück, {user['first_name']}!", "success")
            return redirect(next_url) # leitet zur Startseite
        else:
            return render_template("anmelden.html", error="Ungültige Anmeldedaten")# teigt login nochmal an mit Fehlermeldung

    return render_template("anmelden.html", next=next_url)


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

        existing_user = db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone() # prüft on email bereits registriert ist
        if existing_user:
            flash("E-Mail bereits registriert.", "warning")
            return render_template("registrieren.html", error="E-Mail bereits registriert.", regionen=regionen)

        hashed_pw = generate_password_hash(password) # Erstellt sicheren hash für Passwort. https://werkzeug.palletsprojects.com/en/stable/utils/#werkzeug.security.generate_password_hash 
        db.execute("""
            INSERT INTO users (first_name, last_name, email, password, region_id, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, hashed_pw, region_id, phone))
        db.commit()

        flash("Registrierung erfolgreich!", "success")
        return redirect(url_for("anmelden")) # Leitete nach Erfolg zum Login

    return render_template("registrieren.html", regionen=regionen)



@app.route("/angebot_erstellen", methods=["GET", "POST"])
@login_required
def add_offer():
    db = get_db_con()
    categories = db.execute("SELECT * FROM category").fetchall() 
    regionen = db.execute("SELECT * FROM region").fetchall() # Lädt Kategorien und Regionen für die Dropdowns

    selected_category_id = None
    features = [] # Initialisiert die Liste der Features

    if request.method == "POST": # Abschicken des Formulars
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

        # Angebot wird in DB gespeichert
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


@app.route("/mieten/<int:offer_id>", methods=["GET", "POST"]) # Diese Route dient dazu, EIN einzelnes Angebot direkt zu mieten, 
#ohne den Warenkorb zu nutzen, indem der Nutzer auf „Jetzt mieten“ auf der Produktseite klickt
def rental_form(offer_id):
    if "user_id" not in session: # Wenn der Nutzer nicht eingeloggt ist, wird er zur Anmeldeseite weitergeleitet
        flash("Bitte zuerst anmelden.", "warning")
        return redirect(url_for("anmelden"))

    db = get_db_con() 
    # Das angefragte Angebot aus der Datenbank abrufen inkl. Kategorie und Region
    offer = db.execute("""
        SELECT o.*, r.region_name, c.category_name
        FROM offers o
        JOIN region r ON o.region_id = r.region_id
        JOIN category c ON o.category_id = c.category_id
        WHERE o.offer_id = ?
    """, (offer_id,)).fetchone()

    if not offer: # Falls das Angebot nicht existiert, Fehlerseite 404 anzeigen
        abort(404) #https://flask.palletsprojects.com/en/stable/api/#flask.abort

    total_price = None # Initialisierung von total_price und num_days, damit sie verfügbar sind, falls benötigt
    num_days = None

    if request.method == "POST": #Wenn der Nutzer das Formular absendet (Button „Preis berechnen“ oder „Jetzt mieten“ in rental_form.html)
        action = request.form.get("action") # „calculate“ oder „book“
        start = request.form["start_date"] # Mietstart-Datum aus Formular
        end = request.form["end_date"] # Mietende-Datum aus Formular 
        address = request.form.get("address") # Lieferadresse
        name = request.form.get("name_on_card") # Name auf der Karte
        card = request.form.get("card_number") # Kartennummer
        sec = request.form.get("sec_code") # Sicherheitscode

        try: # Die Datumsstrings aus dem Formular (z.B. „2025-07-05“) in echte datetime.date-Objekte umwandeln,
            # um mit ihnen rechnen und vergleichen zu können.
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
        except ValueError:
            flash("Ungültiges Datum", "danger")  # Bei ungültigem Datum zurück zur Formularseite
            return redirect(request.url)

        if end_date <= start_date: # Wenn das Enddatum nicht nach dem Startdatum liegt, Fehlermeldung anzeigen
            flash("Enddatum muss nach dem Startdatum liegen.", "warning")
            return redirect(request.url)

        # "Konfliktprüfung" -> Prüfen, ob dieses Produkt im gewählten Zeitraum bereits gebucht ist
        conflict = db.execute("""
            SELECT 1 FROM rentals
            WHERE offer_id = ?
            AND start_date <= ?
            AND end_date >= ?
        """, (offer_id, end_date, start_date)).fetchone()

        if conflict: # Falls das Produkt im gewählten Zeitraum nicht verfügbar ist, Fehlermeldung anzeigen
            flash("Dieses Produkt ist im gewählten Zeitraum bereits gebucht.", "danger")
            return redirect(request.url)

        num_days = (end_date - start_date).days  # Berechnung der Anzahl der gebuchten Nächte
        total_price = num_days * offer["price_per_night"] # Berechnung des Gesamtpreises: Preis pro Nacht * Anzahl Nächte

        if action == "book": #Falls der Nutzer auf „Jetzt mieten“ klickt:
            # # Buchung wird in der rentals-Tabelle gespeichert
            db.execute("""
                INSERT INTO rentals (offer_id, user_id, start_date, end_date, total_price)
                VALUES (?, ?, ?, ?, ?)
            """, (offer_id, session["user_id"], start_date, end_date, total_price))
            db.commit()

            return render_template("rental_confirm.html", offer=offer, start_date=start, # Nach erfolgreicher Buchung wird die Bestätigungsseite rental_confirm.html angezeigt,
                                   end_date=end, address=address, name_on_card=name, # auf der der Nutzer alle Daten nochmals sieht:
                                   total_price=total_price, num_days=num_days) # # Titel, Kategorie, Region, Zeitraum, Adresse, Name auf der Karte, Preis

        # Falls der Nutzer auf „Preis berechnen“ klickt:
        #rental_form.html wird erneut angezeigt, diesmal mit dem berechneten Gesamtpreis und allen eingegebenen Feldern vorausgefüllt
        # Der Button auf der Seite ändert sich jetzt von „Preis berechnen“ zu „Jetzt mieten“,
        #  damit der Nutzer direkt im nächsten Schritt buchen kann
        return render_template("rental_form.html", offer=offer,
                               start_date=start, end_date=end,
                               address=address, name_on_card=name,
                               card_number=card, sec_code=sec,
                               total_price=total_price, num_days=num_days)

    return render_template("rental_form.html", offer=offer) # Zeigt dem Nutzer das Mietformular (rental_form.html) für dieses Angebot an,
# damit er Mietzeitraum, Adresse und Zahlungsdaten eingeben kann



@app.route("/profil")
@login_required
def profil():
    if "user_id" not in session:
        return redirect(url_for("anmelden"))

    db = get_db_con()
    user = db.execute("""
        SELECT u.user_id, u.first_name, u.last_name, u.email, u.phone, r.region_name
        FROM users u
        JOIN region r ON u.region_id = r.region_id
        WHERE u.user_id = ?
    """, (session["user_id"],)).fetchone() # holt alle Daten aus user nur die des jeweiligen users werden zurückgegeben

    section = request.args.get("section", "about") # Standard section ist 'about'

    rentals = []
    own_offers = [] # Listen werden befüllt je nach section

    if section == "booked":
        rentals = db.execute("""
            SELECT r.*, o.title, o.photo_path
            FROM rentals r
            JOIN offers o ON r.offer_id = o.offer_id
            WHERE r.user_id = ?
            ORDER BY r.start_date DESC
        """, (user["user_id"],)).fetchall() # wenn section 'booked' werden alle Mietbuchungen des Users geholt

    elif section == "own":
        own_offers = db.execute("""
            SELECT o.*, c.category_name AS category, r.region_name AS region
            FROM offers o
            JOIN category c ON o.category_id = c.category_id
            JOIN region   r ON o.region_id = r.region_id
            WHERE o.user_id = ?
            ORDER BY o.created_at DESC
        """, (user["user_id"],)).fetchall()# wenn section 'own' alle offers des users geholt

    return render_template(
        "profil.html",
        user=user,
        section=section,
        rentals=rentals,
        own_offers=own_offers # Daten werden an profil.html übergeben

    )

from forms import EditProfileForm

@app.route('/profil/bearbeiten', methods=['GET','POST'])
def edit_profile():
    if 'user_id' not in session:
        flash("Bitte zuerst anmelden.", "warning")
        return redirect(url_for('anmelden'))

    db = get_db_con()
    user = db.execute("SELECT * FROM users WHERE user_id = ?", (session['user_id'],)).fetchone()# holt Daten

    # Regionsliste abrufen
    regions = db.execute("SELECT region_id, region_name FROM region").fetchall()
    form = EditProfileForm() # Erstellt ein neues Formularobjekt
    # choices für das Dropdown: List[ (id, name), ... ]
    form.region_id.choices = [(r['region_id'], r['region_name']) for r in regions]

    if request.method == "GET":
        # Form mit aktuellen Werten gefüllt
        form.first_name.data = user['first_name']
        form.last_name.data  = user['last_name']
        form.phone.data      = user['phone'] or ''
        form.region_id.data  = user['region_id']

    if form.validate_on_submit(): # Ob alle Validierungen erfolgreich sind (z. B. Pflichtfelder ausgefüllt)
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
        db.commit() # Aktualisierung der DB wenn neue Einträge
        flash('Profil erfolgreich aktualisiert.', 'success')
        return redirect(url_for('profil', section='about'))

    return render_template('profile_edit.html', form=form)

@csrf.exempt
@app.route("/logout")
def logout():
    session.clear() #Löscht alle Daten aus der aktuellen Benutzersitzung (Session), z.B. um einen Benutzer vollständig abzumelden: https://docs.python.org/3/library/stdtypes.html#dict.clear
    flash("Du wurdest abgemeldet.", "success")
    return redirect(url_for("index"))


@app.route("/angebot_loeschen/<int:offer_id>", methods=["POST"])
@login_required
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


@app.route("/angebot_bearbeiten/<int:offer_id>", methods=["GET", "POST"])
@login_required
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
        price_per_night = float(request.form["price_per_night"]) # Holt Werte aus dem HTML Formular

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
        """, (title, description, category_id, region_id, price_per_night, photo_path, offer_id, session["user_id"])) # Werte überschieben

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

    # Lädt auch die Features mit vorhandenen Werten
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
def add_to_cart(offer_id): # Diese Route wird aufgerufen, wenn der Nutzer ein Produkt in den Warenkorb legen möchte
    # Sie wird per POST aufgerufen, z.B. wenn der Nutzer auf der Produktseite auf "In den Warenkorb" klickt
    
    cart = session.get("cart", []) # Holt den aktuellen Warenkorb aus der Session
    # Falls der Nutzer zum ersten Mal etwas hinzufügt, wird ein leerer Warenkorb (leere Liste) erstellt

    if offer_id not in cart: # Wenn die offer_id noch nicht im Warenkorb ist:
        cart.append(offer_id) # Fügt die offer_id dem Warenkorb hinzu
        session["cart"] = cart  # Speichert den aktualisierten Warenkorb zurück in die Session -> bleibt drinne im Warenkorb 
        flash("Zum Warenkorb hinzugefügt.", "success") # Zeigt oben eine grüne Erfolgsmeldung an, dass das Produkt hinzugefügt wurde

    else: # Wenn die offer_id bereits im Warenkorb enthalten ist:
        flash("Dieses Produkt ist bereits im Warenkorb.", "info") # Zeigt eine blaue Info-Meldung an, dass das Produkt bereits vorhanden ist

    
    return redirect(url_for("warenkorb"))
    # Nach dem Hinzufügen wird der Nutzer zur Warenkorbseite weitergeleitet
    # In deiner `warenkorb.html` wird dann der aktuelle Warenkorb angezeigt,
    # wo der Nutzer alle hinzugefügten Produkte mit Titel, Kategorie, Region und Preis pro Nacht sehen kann
    # und dort auch die Möglichkeit hat, Produkte zu entfernen oder alle Produkte gleichzeitig zu mieten

@csrf.exempt
@app.route("/warenkorb")
def warenkorb():
    # Diese Route zeigt dem Nutzer den aktuellen Warenkorb an (warenkorb.html),
    # wenn er auf "Warenkorb" in der Navigation klickt
    cart = session.get("cart", [])
    # Holt den aktuellen Warenkorb aus der Session
    # Der Warenkorb enthält eine Liste mit offer_id's der hinzugefügten Produkte
    # Falls noch nichts im Warenkorb liegt, wird eine leere Liste zurückgegeben

    if not cart: # Prüft, ob der Warenkorb leer ist
        flash("Dein Warenkorb ist leer.", "info")
         # Zeigt eine Info-Meldung an, dass der Warenkorb leer ist
        return render_template("warenkorb.html", offers=[])
        # Lädt die Seite warenkorb.html mit einem leeren offers-Array,
        # wodurch in deiner `warenkorb.html` der Text angezeigt wird:
        # "Dein Warenkorb ist leer."
        # und keine Produktkarten angezeigt werden

    db = get_db_con() # Stellt eine Verbindung zur Datenbank her
    placeholders = ','.join('?' for _ in cart) # Diese Zeile erstellt genau so viele Fragezeichen wie Produkte im Warenkorb sind, damit die Datenbank alle auf einmal finden kann
    offers = db.execute(f"""
        SELECT o.*, c.category_name AS category, r.region_name AS region
        FROM offers o
        JOIN category c ON o.category_id = c.category_id
        JOIN region   r ON o.region_id = r.region_id
        WHERE o.offer_id IN ({placeholders})
    """, cart).fetchall()
    # Führt die SQL-Abfrage aus, um alle Produkte aus dem Warenkorb anhand ihrer offer_id abzurufen
    # Holt dabei:
    # - alle Spalten aus offers (inkl. Titel, Preis pro Nacht, etc.)
    # - den Kategorienamen als "category"
    # - den Regionsnamen als "region"
    # Dies wird für die Anzeige in deiner `warenkorb.html` benötigt,
    # um Titel, Kategorie, Region und Preis pro Nacht korrekt anzuzeigen

    return render_template("warenkorb.html", offers=offers)
    # Rendert die Seite warenkorb.html mit den abgerufenen Angeboten (offers)
    # In deiner `warenkorb.html` wird dann eine Liste von Produktkarten angezeigt:
    #    - Titel
    #    - Kategorie und Region
    #    - Preis pro Nacht (mit Komma)
    # Ein roter Button „Entfernen“ pro Produkt wird angezeigt, der es ermöglicht, das Produkt aus dem Warenkorb zu entfernen
    #  Unten wird ein Button „Alle Produkte jetzt mieten“ angezeigt, der den Nutzer zur Mietseite (/mieten) weiterleitet, um alle Produkte im Warenkorb gleichzeitig zu mieten


@csrf.exempt
@app.route("/remove_from_cart/<int:offer_id>", methods=["POST"])
 # Diese Route wird aufgerufen, wenn der Nutzer in der `warenkorb.html` auf den roten „Entfernen“-Button klickt
 # Sie wird per POST aufgerufen, um sicherzustellen, dass der Nutzer aktiv geklickt hat

def remove_from_cart(offer_id): # Funktion, um ein Produkt aus dem Warenkorb zu löschen
    cart = session.get("cart", []) # holt den aktuellen Warenkorb des Nutzers, wenn er noch keine Offers hat, startet es mit einer leeren Liste

    if offer_id in cart: # Prüft, ob die übergebene offer_id überhaupt im Warenkorb vorhanden ist
       
        cart.remove(offer_id) # Entfernt die offer_id aus dem Warenkorb
        session["cart"] = cart # Speichert den aktualisierten Warenkorb wieder in der Session
        flash("Angebot aus dem Warenkorb entfernt.", "success") # Zeigt oben eine grüne Erfolgsmeldung an, dass das Produkt entfernt wurde
    return redirect(url_for("warenkorb"))
# Leitet den Nutzer zurück zur Warenkorbseite, damit er den aktuellen (aktualisierten) Warenkorb direkt sehen kann

@csrf.exempt
 # Diese Route verarbeitet das Mieten mehrerer Angebote aus dem Warenkorb
@app.route("/mieten", methods=["GET", "POST"]) # Sie erlaubt GET (Formularanzeige) und POST (Formularabsendung)
def mietseite(): # Hier werden mehrere Angebote aus dem Warenkorb verarbeitet, falls der Nutzer nicht ein spezifisches Angebot direkt mietet
    if "user_id" not in session: # Prüfen, ob der Nutzer eingeloggt ist. Ansonsten muss der Nutzer sich erstmal anmelden und wird dorthin geleitet 
        flash("Bitte zuerst anmelden.", "warning")
        return redirect(url_for("anmelden"))

    cart = session.get("cart", []) # Falls der Warenkorb leer ist, wird der Nutzer zurück zur Warenkorbseite geleitet
    if not cart:
        flash("Dein Warenkorb ist leer.", "info")
        return redirect(url_for("warenkorb"))

    db = get_db_con() # Verbindung zur Datenbank öffnen
    placeholders = ','.join(['?'] * len(cart)) # Platzhalter für SQL-Abfrage vorbereiten, passend zur Anzahl der Produkte im Warenkorb
    # Holt alle Angebote aus der Datenbank mit deren:
    # Titel, Preis pro Nacht, Region (region_name), Kategorie (category_name)
    # Diese Daten werden für die Anzeige in rental_form.html (für Formular) und rental_confirm.html (Bestätigung) benötigt
    offers = db.execute(f""" 
        SELECT o.*, r.region_name, c.category_name 
        FROM offers o
        JOIN region r ON o.region_id = r.region_id
        JOIN category c ON o.category_id = c.category_id
        WHERE o.offer_id IN ({placeholders})
    """, cart).fetchall() # Alle Angebote aus dem Warenkorb inkl. Kategorie und Region aus der Datenbank abfragen

    if request.method == "GET": # Wenn die Seite per GET aufgerufen wird, wird das Mietformular angezeigt (rental_form.html)
        return render_template("rental_form.html", offers=offers) # Der Nutzer kann hier den Mietzeitraum, Adresse und Zahlungsdaten eingeben
        # offers=offers sorgt dafür, dass im Formular alle Artikel und Titel in der Überschrift angezeigt werden: „Jetzt mieten: Gaskocher, Zelt, Schlafsack …“

    # Formulardaten aus dem POST-Request auslesen
    action = request.form.get("action", "calculate") # Button-Wert: „calculate“ oder „book“
    start = request.form.get("start_date", "") # Mietbeginn
    end = request.form.get("end_date", "") # Mietende
    address = request.form.get("address", "") # Lieferadresse
    name = request.form.get("name_on_card", "") # Name auf der Kreditkarte
    card = request.form.get("card_number", "")  # Kreditkartennummer
    sec = request.form.get("sec_code", "") # Sicherheitscode

    try: #Wandelt Datum von String in datetime.date um.
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    except ValueError:
        flash("Ungültiges Datum", "danger")  # Bei ungültigem Datum zurück zur Formularseite
        return redirect(request.url)

    if end_date <= start_date: # Enddatum muss später oder gleichzeitig als  dem Startdatum liegen
        flash("Enddatum muss nach dem Startdatum liegen.", "warning")
        return redirect(request.url)

    # Verfügbarkeitsprüfung: prüfen, ob jedes Produkt im gewünschten Zeitraum verfügbar ist
    for offer in offers:
        conflict = db.execute("""
            SELECT 1 FROM rentals
            WHERE offer_id = ?
            AND start_date <= ?
            AND end_date >= ?
        """, (offer["offer_id"], end_date, start_date)).fetchone()

        if conflict:  # Falls ein Produkt bereits in diesem Zeitraum gebucht ist, abbrechen
            flash(f"Das Produkt '{offer['title']}' ist im gewählten Zeitraum nicht verfügbar.", "danger") #Falls Konflikt: Nutzer erhält einen Hinweis und kehrt zurück auf das Formular
            return redirect(request.url)

    num_days = (end_date - start_date).days # Berechnung der Mietdauer und des Gesamtpreises
    total_price = sum([num_days * offer["price_per_night"] for offer in offers]) # Berechnet den Gesamtpreis als Summe (Tage x Preis pro Nacht) für alle Artikel im Warenkorb

    if action == "book": # Wenn der Nutzer „Jetzt Mieten“ geklickt hat:
        for offer in offers:
            einzelpreis = num_days * offer["price_per_night"] # Preis für dieses Produkt berechnen
            # Buchung in der rentals-Tabelle speichern bzw. Für jedes Produkt wird ein Eintrag in der rentals-Tabelle erstellt
            # Speichert: offer_id, user_id, Zeitraum, Preis für dieses Produkt.
            db.execute(""" 
                INSERT INTO rentals (offer_id, user_id, start_date, end_date, total_price) 
                VALUES (?, ?, ?, ?, ?)
            """, (offer["offer_id"], session["user_id"], start_date, end_date, einzelpreis))
        db.commit() # Änderungen in der Datenbank speichern

        session["cart"] = []  # Warenkorb nach erfolgreicher Buchung leeren

        return render_template("rental_confirm.html", offers=offers, start_date=start, # Nach erfolgreicher Buchung Bestätigungsseite anzeigen (rental_confirm.html)
                               end_date=end, address=address, name_on_card=name,   # Diese zeigt alle Details: Produkte, Zeitraum, Adresse, Gesamtpreis
                               total_price=total_price, num_days=num_days)

# Wenn der Nutzer „Preis berechnen“ klickt:
# Zeigt rental_form.html erneut an, diesmal mit dem berechneten Gesamtpreis und vorausgefüllten Feldern,
# sodass der Nutzer im nächsten Schritt direkt buchen kann.
# Der Button ändert sich jetzt zu „Jetzt Mieten“, sodass der Nutzer im nächsten Schritt buchen kann
    return render_template("rental_form.html", offers=offers, start_date=start, 
                           end_date=end, address=address, name_on_card=name,
                           card_number=card, sec_code=sec,
                           total_price=total_price, num_days=num_days)

@app.route('/features_for_category/<int:category_id>') # Route wird aufgerufen, wenn im Frontend eine Kategorie ausgewählt wurde
def features_for_category(category_id):
    db = get_db_con()
    features = db.execute(
        "SELECT feature_id, feature_name FROM features WHERE category_id = ?",
        (category_id,)
    ).fetchall() # Holt alle Features-Namen und IDs zur gewählten Kategorie
    return render_template('partials/_features.html', features=features)




