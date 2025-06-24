-- ===========================================
-- Tabelle: Region
-- ===========================================
CREATE TABLE IF NOT EXISTS region (
  region_id INTEGER PRIMARY KEY AUTOINCREMENT,
  region_name TEXT NOT NULL
);

INSERT OR IGNORE INTO region (region_name) VALUES
  ('Berlin'),
  ('Hamburg'),
  ('München'),
  ('Frankfurt');

-- ===========================================
-- Tabelle: Users
-- ===========================================
CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  phone TEXT,
  region_id INTEGER NOT NULL,
  FOREIGN KEY (region_id) REFERENCES region(region_id) ON DELETE CASCADE
);

-- ===========================================
-- Tabelle: Category
-- ===========================================
CREATE TABLE IF NOT EXISTS category (
  category_id INTEGER PRIMARY KEY AUTOINCREMENT,
  category_name TEXT NOT NULL
);

INSERT INTO category (category_id, category_name) VALUES
 (1,'Zelt'),
 (2,'Rucksack'),
 (3,'Multitool'),
 (4,'Schlafsack'),
 (5,'Luftmatratze'),
 (6,'Radtasche'),
 (7,'Gaskocher');

-- ===========================================
-- Tabelle: Features (gehören zu einer Category)
-- ===========================================
CREATE TABLE IF NOT EXISTS features (
  feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
  feature_name TEXT NOT NULL,
  category_id INTEGER NOT NULL,
  FOREIGN KEY (category_id) REFERENCES category(category_id) ON DELETE CASCADE
);
-- Zelt (1)
INSERT INTO features (feature_name, category_id) VALUES
('Kapazität (z. B. 1–4 Personen)', 1),
('Packmaß (L × B × H in cm)', 1),
('Gewicht (kg)', 1),
('Wassersäule (mm)', 1),
('Material (z. B. Ripstop-Nylon)', 1);

-- Rucksack (2)
INSERT INTO features (feature_name, category_id) VALUES
('Volumen (l)', 2),
('Gewicht (kg)', 2),
('Maße (H × B × T in cm)', 2),
('Material (z. B. Cordura)', 2),
('Tragesystem (z. B. Hüftgurt)', 2);

-- Multitool (3)
INSERT INTO features (feature_name, category_id) VALUES
('Funktionen (z. B. 12-in-1)', 3),
('Gewicht (g)', 3),
('Material (z. B. Edelstahl)', 3),
('Klingenlänge (cm)', 3),
('Maße zusammengeklappt (L × B × T in cm)', 3);

-- Schlafsack (4)
INSERT INTO features (feature_name, category_id) VALUES
('Temperaturbereich (°C)', 4),
('Füllmaterial (Daune/synt.)', 4),
('Gewicht (kg)', 4),
('Packmaß (L × Ø in cm)', 4),
('Form (Mumie/Decke)', 4);

-- Luftmatratze (5)
INSERT INTO features (feature_name, category_id) VALUES
('Abmessungen (L × B × H in cm)', 5),
('Dicke (cm)', 5),
('Material (z. B. PVC/TPU)', 5),
('Gewicht (kg)', 5),
('Max. Belastung (kg)', 5);

-- Radtasche (6)
INSERT INTO features (feature_name, category_id) VALUES
('Volumen (l)', 6),
('Material (z. B. Cordura)', 6),
('Gewicht (kg)', 6),
('Wasserdicht (ja/nein)', 6),
('Tragesystem (z. B. Schultergurt)', 6);

-- Gaskocher (7)
INSERT INTO features (feature_name, category_id) VALUES
('Leistung (W)', 7),
('Brennstoffart (z. B. Butan)', 7),
('Durchsatz (g/min)', 7),
('Gewicht (g)', 7),
('Abmessungen (B × T × H in cm)', 7);


-- ===========================================
-- Tabelle: Offers (Angebote zur Ausleihe)
-- ===========================================
CREATE TABLE IF NOT EXISTS offers (
  offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  category_id INTEGER NOT NULL,
  region_id INTEGER NOT NULL,
  price_per_night REAL NOT NULL DEFAULT 0.0,
  photo_path TEXT,
  created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES category(category_id) ON DELETE CASCADE,
  FOREIGN KEY (region_id) REFERENCES region(region_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS offer_features (
  offer_id INTEGER NOT NULL,
  feature_id INTEGER NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (offer_id, feature_id),
  FOREIGN KEY (offer_id) REFERENCES offers(offer_id) ON DELETE CASCADE,
  FOREIGN KEY (feature_id) REFERENCES features(feature_id) ON DELETE CASCADE
);


-- ===========================================
-- Tabelle: Rentals (Buchungen / Ausleihen)
-- ===========================================
CREATE TABLE IF NOT EXISTS rentals (
  rental_id INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  total_price REAL NOT NULL,
  created_at DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  FOREIGN KEY (offer_id) REFERENCES offers(offer_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);