BEGIN TRANSACTION;

-- Alte To-Do- und List-Daten löschen
DELETE FROM todo_list;
DELETE FROM todo;
DELETE FROM list;

-- Alte Offer-Daten löschen
DELETE FROM offers;

-- Sequenzen zurücksetzen (Autoincrement)
DELETE FROM sqlite_sequence;

-- Beispiel-Todos
INSERT INTO todo (complete, description) VALUES (1, "Get some food");
INSERT INTO todo (description) VALUES ("Drive the bike more often");
INSERT INTO todo (description) VALUES ("Implement web app");
INSERT INTO todo (complete, description) VALUES (1, "Call mom");
INSERT INTO todo (complete, description) VALUES (1, "Clean up");

-- Beispiel-Listen
INSERT INTO list (name) VALUES ("Life");
INSERT INTO list (name) VALUES ("Work");
INSERT INTO list (name) VALUES ("Family");

-- Zuordnungen
INSERT INTO todo_list (list_id, todo_id) VALUES (1, 1);
INSERT INTO todo_list (list_id, todo_id) VALUES (1, 2);
INSERT INTO todo_list (list_id, todo_id) VALUES (2, 2);
INSERT INTO todo_list (list_id, todo_id) VALUES (2, 3);
INSERT INTO todo_list (list_id, todo_id) VALUES (3, 4);
INSERT INTO todo_list (list_id, todo_id) VALUES (3, 5);

-- Beispiel-Offers
INSERT INTO offers (
  title, category, description, region,
  price_per_night, rating, photo, features
) VALUES (
  'Basic Tent',
  'Zelt',
  'Einfaches 2-Personen-Zelt',
  'Bayern',
  12.5,
  4.2,
  NULL,
  '{"kapazitaet":"2 Personen","gewicht":"2000g"}'
);

INSERT INTO offers (
  title, category, description, region,
  price_per_night, rating, photo, features
) VALUES (
  'Deluxe Backpack',
  'Rucksack',
  'Großer 60L-Rucksack mit Regenschutz',
  'Brandenburg',
  15.0,
  4.8,
  NULL,
  '{"volumen":"60L","gewicht":"1500g"}'
);

COMMIT;
