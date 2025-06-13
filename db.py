import os
import sqlite3
import click
from flask import current_app, g

def get_db_con(pragma_foreign_keys: bool = True) -> sqlite3.Connection:
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
    db_con = g.pop("db_con", None)
    if db_con is not None:
        db_con.close()

@click.command("init-db")
def init_db() -> None:
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
    db_con = get_db_con()
    with current_app.open_resource("sql/insert_sample.sql") as f:
        db_con.executescript(f.read().decode("utf8"))

def init_app(app) -> None:
    app.teardown_appcontext(close_db_con)
    app.cli.add_command(init_db)
