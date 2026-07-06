-- Persists which tool-table columns the user currently has checked visible
-- (core, extras, and custom alike) so a widget restart shows the same
-- columns the user last left checked, instead of always reverting to a
-- hardcoded default. One row per currently-visible column key (e.g. 'T',
-- 'type', 'custom:weight'); the whole table is replaced atomically
-- whenever the visible set changes (see DBToolTable.setVisibleColumns).

BEGIN;

CREATE TABLE ui_visible_column (
  column_key TEXT PRIMARY KEY
);

UPDATE meta SET schema_version = 2;

COMMIT;
