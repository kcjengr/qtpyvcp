-- ============================================================
-- Unified Lathe Tool Table -- schema v1 (FROZEN 2026-07-03)
-- Canonical DDL, home per plan §5.3. Mirrored (not duplicated-as-truth) by
-- the ORM Column definitions in qtpyvcp/lib/db_tool/tool_table.py, and by
-- the frozen fixture in pb_lathe_conv docs/schema_v1/001_initial.sql.
--
-- D column semantics (plan §5.1, ratified):
--   turning / boring / grooving / parting / threading:
--       diameter = 2 x nose (tip/corner) radius  [LinuxCNC convention]
--   drill: diameter = drill diameter
--   tap:   diameter = major diameter
--   The type column in tool_lathe disambiguates.
-- ============================================================

BEGIN;

-- one row only
CREATE TABLE meta (
  schema_version INTEGER NOT NULL,                      -- loader refuses newer-than-known
  units TEXT NOT NULL CHECK (units IN ('inch','mm'))    -- one canonical system per DB
);

-- core: exactly what LinuxCNC sees via the tooldb line protocol
CREATE TABLE tool (
  id INTEGER PRIMARY KEY,
  tool_no INTEGER NOT NULL UNIQUE CHECK (tool_no > 0),  -- T; the join key everywhere
  pocket INTEGER NOT NULL DEFAULT -1,                   -- P
  x_offset REAL NOT NULL DEFAULT 0,                     -- X
  y_offset REAL NOT NULL DEFAULT 0,                     -- Y (mill/plasma compat)
  z_offset REAL NOT NULL DEFAULT 0,                     -- Z
  a_offset REAL NOT NULL DEFAULT 0,
  b_offset REAL NOT NULL DEFAULT 0,
  c_offset REAL NOT NULL DEFAULT 0,
  u_offset REAL NOT NULL DEFAULT 0,
  v_offset REAL NOT NULL DEFAULT 0,
  w_offset REAL NOT NULL DEFAULT 0,
  diameter REAL NOT NULL DEFAULT 0,                     -- D (see header for semantics)
  front_angle REAL NOT NULL DEFAULT 0,                  -- I
  back_angle REAL NOT NULL DEFAULT 0,                   -- J
  orientation INTEGER NOT NULL DEFAULT 0
    CHECK (orientation BETWEEN 0 AND 9),                -- Q
  remark TEXT NOT NULL DEFAULT '',                      -- R
  in_use INTEGER NOT NULL DEFAULT 0                     -- maintained by l/u pushes
);

-- lathe extras: consumed by the UI, VTK insert display, and the
-- conversational; never sent to LinuxCNC.
CREATE TABLE tool_lathe (
  tool_id INTEGER PRIMARY KEY REFERENCES tool(id) ON DELETE CASCADE,

  type TEXT CHECK (type IN ('turning','boring','grooving','parting',
                            'threading','drill','tap','custom')),

  -- insert identity (ISO turning inserts; VTK profile inputs)
  insert_shape TEXT,          -- ISO shape letter: C,D,V,W,T,R,S,...
  insert_size_mode TEXT CHECK (insert_size_mode IN ('IC','edge_length') OR insert_size_mode IS NULL),
  insert_size REAL,           -- IC diameter or edge length per size_mode
  insert_thickness REAL,      -- S

  -- holder (ISO turning/boring/grooving holders)
  holder_style TEXT,          -- full ISO code, e.g. SCLCR; THSC letter derived
  holder_hand TEXT CHECK (holder_hand IN ('R','L') OR holder_hand IS NULL),
  holder_shank_width REAL,    -- W
  holder_cut_width REAL,      -- CW; internal-groove max depth = CW - W/2
  holder_oal REAL,            -- holder overall length

  -- grooving / parting
  groove_width REAL,          -- cutting edge width
  max_depth_of_cut REAL,      -- groove insert usable depth (display length)

  -- drills / taps (round tools; no holder rows apply)
  drill_point_angle REAL,     -- SIG, e.g. 118 / 135
  flute_length REAL,          -- LCF/LB; drill body & tap flute display length
  overall_length REAL,        -- tool OAL (tap/drill; thread insert length)
  shaft_diameter REAL,        -- SFDM; tap/drill shank
  chamfer_threads REAL,       -- tap lead/chamfer threads (e.g. 2.5)

  -- threading
  thread_pitch_max REAL,      -- TPX/TP; tap pitch reuses this column
  thread_angle REAL,          -- profile angle, default 60
  thread_tip_type TEXT,       -- point | flat | radius

  -- feeds & speeds defaults (conversational autofill)
  surface_speed REAL,         -- SFM / SMM per meta.units
  feed_per_rev REAL,
  depth_of_cut REAL,

  notes TEXT NOT NULL DEFAULT ''
);

-- user-defined custom columns (plan §5.7, ratified: typed EAV)
CREATE TABLE custom_field_def (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,          -- machine-readable key (remap helper queries by this)
  label TEXT NOT NULL,                -- column header in the UI
  value_type TEXT NOT NULL CHECK (value_type IN ('float','int','text','bool')),
  unit TEXT,
  default_value TEXT,
  display_order INTEGER
);

CREATE TABLE custom_field_value (
  tool_id INTEGER NOT NULL REFERENCES tool(id) ON DELETE CASCADE,
  field_id INTEGER NOT NULL REFERENCES custom_field_def(id) ON DELETE CASCADE,
  value TEXT,
  PRIMARY KEY (tool_id, field_id)
);

CREATE INDEX idx_tool_tool_no ON tool(tool_no);
CREATE INDEX idx_custom_value_field ON custom_field_value(field_id);

INSERT INTO meta (schema_version, units) VALUES (1, 'inch');

COMMIT;
