BEGIN TRANSACTION;
-- Neue Tabelle zuerst droppen
DROP TABLE IF EXISTS offers;
-- Alte To-Do-Tabellen
DROP TABLE IF EXISTS todo_list;
DROP TABLE IF EXISTS todo;
DROP TABLE IF EXISTS list;
COMMIT;
