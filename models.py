# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Ein einziges db-Objekt für alle Models
db = SQLAlchemy()


# ---------------------------------------------------
# (A) Bestehende Tabellen: todo, list, todo_list
# ---------------------------------------------------

class Todo(db.Model):
    __tablename__ = "todo"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text, nullable=False)
    complete = db.Column(db.Boolean, default=False, nullable=False)

    # n-m Beziehung zu List über die Zwischentabelle "todo_list"
    lists = db.relationship(
        "List",
        secondary="todo_list",
        back_populates="todos"
    )

    def __repr__(self):
        return f"<Todo id={self.id} complete={self.complete} description={self.description!r}>"


class List(db.Model):
    __tablename__ = "list"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)

    # n-m Beziehung zu Todo über "todo_list"
    todos = db.relationship(
        "Todo",
        secondary="todo_list",
        back_populates="lists"
    )

    def __repr__(self):
        return f"<List id={self.id} name={self.name!r}>"


class TodoList(db.Model):
    __tablename__ = "todo_list"

    # Zusammengesetzter Primärschlüssel: (list_id, todo_id)
    list_id = db.Column(
        db.Integer,
        db.ForeignKey("list.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    todo_id = db.Column(
        db.Integer,
        db.ForeignKey("todo.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    complete = db.Column(db.Integer, default=0, nullable=False)

    # Back-References, falls man von hier aus navigieren will:
    todo = db.relationship(
        "Todo",
        backref=db.backref("todo_list_entries", cascade="all, delete-orphan")
    )
    list = db.relationship(
        "List",
        backref=db.backref("todo_list_entries", cascade="all, delete-orphan")
    )

    def __repr__(self):
        return f"<TodoList list_id={self.list_id} todo_id={self.todo_id} complete={self.complete}>"


# ---------------------------------------------------
# (B) Neue Tabelle: offers
# ---------------------------------------------------

class Offer(db.Model):
    __tablename__ = "offers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    region = db.Column(db.Text, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False, default=0.0)
    rating = db.Column(db.Float, nullable=False, default=0.0)
    photo = db.Column(db.Text, nullable=True)    # z.B. Dateipfad "uploads/abc.jpg"
    features = db.Column(db.Text, nullable=True) # JSON‐String mit den dynamischen Merkmalen
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<Offer id={self.id} title={self.title!r} category={self.category!r} "
            f"region={self.region!r} price_per_night={self.price_per_night} rating={self.rating} "
            f"photo={self.photo!r} created_at={self.created_at}>"
        )
