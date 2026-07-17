-- Mill extras table (schema v3) -- the mill counterpart of tool_lathe:
-- per-tool data consumed by the mill UI and machine macros; never sent to
-- LinuxCNC through the tooldb protocol.
--
-- atc: whether the tool is storable in the ATC carousel. 1 = normal tool,
-- 0 = does not physically fit between carousel pockets (oversize) -- the
-- M6 remap must never auto-stow it into, or auto-fetch it from, the
-- carousel. Default 1 so only the exceptions get unchecked, matching the
-- established all-tools-automatic behavior; a tool with no tool_mill row
-- at all also reads as atc = 1 (rows appear lazily on first save -- see
-- MillToolModel.EXTRAS_DEFAULTS and the tbl importer, which creates
-- core-only tools).

BEGIN;

CREATE TABLE tool_mill (
  tool_id INTEGER PRIMARY KEY REFERENCES tool(id) ON DELETE CASCADE,
  atc INTEGER NOT NULL DEFAULT 1 CHECK (atc IN (0,1))
);

UPDATE meta SET schema_version = 3;

COMMIT;
