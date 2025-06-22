

-- Beispiel-User
INSERT OR IGNORE INTO users (first_name, last_name, email, password, phone, region_id)
VALUES
  ('Max', 'Mustermann', 'max@example.com', 'passwort123', '0123456789', 1),
  ('Erika', 'Musterfrau', 'erika@example.com', 'passwort456', '0987654321', 2);

-- Zwei Beispiel-Angebote
INSERT OR IGNORE INTO offers (user_id, title, description, category_id, region_id, price_per_night, photo_path)
VALUES
  (1, 'Komfortables 2‑Personen Zelt', 'Unser komfortables 2-Personen-Zelt ist ideal für Campingausflüge, Festivals und Wanderungen. Es bietet dank seiner stabilen Konstruktion zuverlässigen Schutz vor Wind und Wetter. Das Zelt lässt sich in wenigen Minuten aufbauen und verfügt über ein leichtes Packmaß. Perfekt für Abenteurer, die Wert auf Komfort und Funktionalität legen.', 1, 1, 12.50, 'images/Draussen Camping.jpg'),
  (2, 'Großer Trekking Rucksack', 'Robuster und geräumiger Trekking-Rucksack mit einem Volumen von 70 Litern – ideal für mehrtägige Wanderungen und Abenteuer. Der Rucksack verfügt über ein komfortables Tragesystem mit gepolsterten Schulter- und Hüftgurten sowie eine integrierte Regenhülle. Zahlreiche Fächer und Befestigungsmöglichkeiten bieten viel Platz für Ausrüstung und persönliche Gegenstände.', 2, 2, 9.00, 'images/Trekking-Rucksack.jpg');
