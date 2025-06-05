# db.py
import os
import sqlite3
import click
from flask import current_app, g

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
        # Damit die Abfragen als dict-through-row_factory zurückkommen
        g.db_con.row_factory = sqlite3.Row

        if pragma_foreign_keys:
            g.db_con.execute("PRAGMA foreign_keys = ON;")
    return g.db_con

def close_db_con(e=None) -> None:
    """
    Schließt die SQLite-Verbindung am Ende der HTTP-Request-Verarbeitung,
    sofern sie geöffnet war.
    """
    db_con = g.pop("db_con", None)
    if db_con is not None:
        db_con.close()

@click.command("init-db")
def init_db() -> None:
    """
    CLI-Command, um die Datenbank neu aufzusetzen:
    1) drop_tables.sql ausführen
    2) create_tables.sql ausführen
    """
    # Stelle sicher, dass der instance-Ordner existiert
    try:
        os.makedirs(current_app.instance_path, exist_ok=True)
    except OSError:
        # Falls der Ordner bereits existiert, ignorieren
        pass

    db_con = get_db_con()
    # DROP aller Tabellen
    with current_app.open_resource("sql/drop_tables.sql") as f:
        db_con.executescript(f.read().decode("utf8"))
    # CREATE aller Tabellen
    with current_app.open_resource("sql/create_tables.sql") as f:
        db_con.executescript(f.read().decode("utf8"))
    click.echo("Datenbank wurde initialisiert.")

def insert_sample() -> None:
    """
    Optionales Einfügen von Beispieldaten aus insert_sample.sql
    """
    db_con = get_db_con()
    with current_app.open_resource("sql/insert_sample.sql") as f:
        db_con.executescript(f.read().decode("utf8"))

def init_app(app) -> None:
    """
    In dieser Funktion registrieren wir teardown-Handler und CLI-Command
    bei der Flask-App. Diese Funktion müssen wir in app.py (bzw. in create_app)
    aufrufen, damit alles korrekt verbunden wird.
    """
    # 1) Verbindung am Ende jeder Request schließen
    app.teardown_appcontext(close_db_con)
    # 2) CLI-Command "flask init-db" registrieren
    app.cli.add_command(init_db)
