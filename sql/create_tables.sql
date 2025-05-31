-- ===========================
-- Tabelle: todo
-- ===========================
CREATE TABLE IF NOT EXISTS todo (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  description TEXT NOT NULL
);

-- ===========================
-- Tabelle: list
-- ===========================
CREATE TABLE IF NOT EXISTS list (
  id   INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);

-- ===========================
-- Verknüpfungstabelle: todo_list
-- ===========================
CREATE TABLE IF NOT EXISTS todo_list (
  list_id   INTEGER NOT NULL,
  todo_id   INTEGER NOT NULL,
  complete  INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (list_id) REFERENCES list (id) ON DELETE CASCADE,
  FOREIGN KEY (todo_id) REFERENCES todo (id) ON DELETE CASCADE,
  PRIMARY KEY (list_id, todo_id)
);

-- ===========================
-- Neue Tabelle: offers
-- ===========================
CREATE TABLE IF NOT EXISTS angebote (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  title            TEXT    NOT NULL,
  category         TEXT    NOT NULL,
  description      TEXT,
  region           TEXT    NOT NULL,
  price_per_night  REAL    NOT NULL DEFAULT 0.0,
  rating           REAL    NOT NULL DEFAULT 0.0,
  photo            TEXT,              -- z.B. uploads/bild.jpg
  features         TEXT,              -- JSON-String für dynamische Felder
  created_at       TEXT    NOT NULL   -- z.B. '2025-05-31 10:45:00'
);
