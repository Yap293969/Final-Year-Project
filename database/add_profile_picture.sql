-- Is this a scam? -- adds profile pictures to an existing accounts database.
--
-- Run this ONCE if your isthisascam database was created before 26 Oct 2026
-- (before profile pictures existed):
--   Laragon -> Database (opens HeidiSQL) -> File -> Run SQL file... -> pick this file
-- or, from Laragon's Terminal:
--   mysql -u root < database/add_profile_picture.sql
--
-- Running it a second time stops with "Duplicate column name 'avatar_image'".
-- That only means it has already been run; nothing is harmed.
-- A brand-new database made from schema.sql already has these columns.
--
-- The picture is kept inside the database (not as a file in the website folder),
-- so an uploaded file can never be opened or run as a page on the web server.

USE isthisascam;

ALTER TABLE users
  ADD COLUMN avatar_image      MEDIUMBLOB  NULL,   -- the picture itself; NULL = use the default picture
  ADD COLUMN avatar_type       VARCHAR(20) NULL,   -- image/jpeg, image/png or image/webp
  ADD COLUMN avatar_updated_at DATETIME    NULL;   -- when it last changed (stops the browser showing an old one)
