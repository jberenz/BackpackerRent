BEGIN TRANSACTION;

DELETE FROM region;
INSERT INTO region (region_name) VALUES
  ('berlin'),
  ('hamburg'),
  ('frankfurt'),
  ('muenchen');
