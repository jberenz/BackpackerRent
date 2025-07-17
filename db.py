import os  #https://docs.python.org/3/library/os.html 
import sqlite3
import click
from flask import current_app, g
#https://flask.palletsprojects.com/en/stable/appcontext/

def get_db_con(pragma_foreign_keys: bool = True) -> sqlite3.Connection:
    """
    Liefert eine SQLite-Verbindung aus dem App-Context-G-Objekt.
    Aktiviert optional Foreign-Key-Pragmas.
    """
    if "db_con" not in g:
        g.db_con = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db_con.row_factory = sqlite3.Row

        if pragma_foreign_keys:
            # Sichere Fremdschlüssel-Prüfung in SQLite
            g.db_con.execute("PRAGMA foreign_keys = ON;")
    return g.db_con


def close_db_con(e=None) -> None:
    """
    Schließt die Datenbankverbindung am Ende des App-Kontexts.
    """
    db_con = g.pop("db_con", None)
    if db_con is not None:
        db_con.close()


@click.command("init-db")
def init_db() -> None:
    """
    CLI-Befehl: Initialisiert die Datenbank.
    Führt zuerst drop_tables, dann create_tables aus.
    """
    try:
        os.makedirs(current_app.instance_path, exist_ok=True)
    except OSError:
        pass

    db_con = get_db_con()
    # Tabellen löschen
    with current_app.open_resource("sql/drop_tables.sql") as f:
        db_con.executescript(f.read().decode("utf8"))
    # Tabellen neu anlegen
    with current_app.open_resource("sql/create_tables.sql") as f:
        db_con.executescript(f.read().decode("utf8"))
    # Änderungen speichern
    db_con.commit()
    click.echo("Datenbank wurde initialisiert.")


@click.command("insert-sample")
def insert_sample_data() -> None:
    """
    CLI-Befehl: Fügt Sample-Daten in die Tabellen category, region etc. ein.
    Erwartet, dass in sql/insert_sample.sql die passenden INSERT-Statements stehen.
    """
    db_con = get_db_con()
    with current_app.open_resource("sql/insert_sample.sql") as f:
        db_con.executescript(f.read().decode("utf8"))
    # Änderungen speichern
    db_con.commit()
    click.echo("Sample-Daten wurden eingefügt.")


def init_app(app) -> None:
    """
    Registriert die Teardown- und CLI-Befehle in der Flask-App.
    """
    app.teardown_appcontext(close_db_con)
    app.cli.add_command(init_db)
    app.cli.add_command(insert_sample_data)
