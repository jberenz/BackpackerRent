DELETE FROM offer_features;
DELETE FROM offers;
DELETE FROM users;

-- User
INSERT OR IGNORE INTO users (first_name, last_name, email, password, phone, region_id) VALUES
  ('Max', 'Mustermann', 'max@example.com', 'passwort123', '0123456789', 1),
  ('Erika', 'Musterfrau', 'erika@example.com', 'passwort456', '0987654321', 2);

-- Angebote
INSERT OR IGNORE INTO offers (user_id, title, description, category_id, region_id, price_per_night, photo_path) VALUES
  (1, 'Komfortables 2‑Personen Zelt',
   'Unser komfortables 2-Personen-Zelt ist ideal für Campingausflüge, Festivals und Wanderungen.',
   1, 1, 12.50, 'images/Zelt.jpg'),

  (2, 'Großer Trekking Rucksack',
   'Robuster und geräumiger Trekking-Rucksack mit einem Volumen von 70 Litern – ideal für mehrtägige Wanderungen und Abenteuer.',
   2, 2, 9.00, 'images/TrekkingRucksack.jpg');

-- Offer_Features Zelt (Offer_ID = 1)
INSERT OR IGNORE INTO offer_features (offer_id, feature_id, value) VALUES
  (1, 1, '2'),
  (1, 2, '60 × 20 × 15 cm'),
  (1, 3, '2.8'),
  (1, 4, '3000'),
  (1, 5, 'Ripstop-Nylon');

-- Offer_Features Rucksack (Offer_ID = 2)
INSERT OR IGNORE INTO offer_features (offer_id, feature_id, value) VALUES
  (2, 6, '70'),
  (2, 7, '2.5'),
  (2, 8, '75 × 35 × 30 cm'),
  (2, 9, 'Cordura'),
  (2, 10, 'Hüftgurt');

