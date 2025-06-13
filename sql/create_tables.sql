-- ===========================================
-- Tabelle: Region
-- ===========================================
CREATE TABLE IF NOT EXISTS region (
  region_id INTEGER PRIMARY KEY AUTOINCREMENT,
  region_name TEXT NOT NULL
);

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

-- ===========================================
-- Tabelle: Features (gehören zu einer Category)
-- ===========================================
CREATE TABLE IF NOT EXISTS features (
  feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
  feature_name TEXT NOT NULL,
  category_id INTEGER NOT NULL,
  FOREIGN KEY (category_id) REFERENCES category(category_id) ON DELETE CASCADE
);

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