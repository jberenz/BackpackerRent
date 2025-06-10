-- ---------------------------------------------------
-- (A) Bestehende Tabellen: todo, list, todo_list
-- ---------------------------------------------------

CREATE TABLE IF NOT EXISTS list (
  id    INTEGER PRIMARY KEY AUTOINCREMENT,
  name  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS todo (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS todo_list (
  list_id  INTEGER NOT NULL,
  todo_id  INTEGER NOT NULL,
  complete INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (list_id, todo_id),
  FOREIGN KEY (list_id) REFERENCES list (id) ON DELETE CASCADE,
  FOREIGN KEY (todo_id) REFERENCES todo (id) ON DELETE CASCADE
);

-- ---------------------------------------------------
-- (B) Tabelle: offers 
-- ---------------------------------------------------

CREATE TABLE IF NOT EXISTS offers (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  title            TEXT    NOT NULL,
  category         TEXT    NOT NULL,
  description      TEXT,
  region           TEXT    NOT NULL,
  price_per_night  REAL    NOT NULL DEFAULT 0.0,
  rating           REAL    NOT NULL DEFAULT 0.0,
  photo            TEXT,              -- Dateipfad zum hochgeladenen Bild, z.B. "uploads/123456_zelt.jpg"
  features         TEXT,              -- JSON-String mit den dynamischen Merkmalen
  created_at       DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);
-- ---------------------------------------------------
-- (C) Tabelle für Benutzer
-- ---------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  region TEXT NOT NULL,
  phone TEXT
);
