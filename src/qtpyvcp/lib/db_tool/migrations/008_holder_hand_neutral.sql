-- Neutral tooling: holder_hand gains 'N'.
--
-- A neutral insert is symmetric -- it has no hand, and cuts equally well in
-- either direction. Which way the work must turn for it is decided by the
-- orientation instead, since LinuxCNC's orientation numbering is defined
-- against an M3 spindle.
--
-- Until now the column allowed only R and L, so a neutral tool had to be
-- recorded as one or the other. The Fusion import made that concrete: it reads
-- holder.HAND, finds 'N', fails the R/L test, and falls through to setup.HAND
-- -- a BOOLEAN -- where True lands on 'R'. Every neutral tool in a library
-- therefore arrives labelled right-hand. On this machine T8 and T9 are both
-- 'NEUTRAL TURNING TOOL' in their own remarks and both imported as R.
--
-- SQLite cannot alter a CHECK in place, so the table is rebuilt. Column order,
-- types, defaults and the tool_id foreign key are preserved exactly; only the
-- holder_hand constraint changes. No data is transformed -- rows that say R
-- still say R, because which of them are genuinely neutral is a question about
-- the tooling, not something a migration can infer.

PRAGMA foreign_keys=OFF;

BEGIN;

CREATE TABLE tool_lathe_new (
  tool_id INTEGER PRIMARY KEY REFERENCES tool(id) ON DELETE CASCADE,
  type TEXT CHECK (type IN ('turning','boring','grooving','parting',
                            'threading','drill','tap','custom')),
  insert_shape TEXT,
  insert_size_mode TEXT CHECK (insert_size_mode IN ('IC','edge_length') OR insert_size_mode IS NULL),
  insert_size REAL,
  insert_thickness REAL,
  holder_style TEXT,
  holder_hand TEXT CHECK (holder_hand IN ('R','L','N') OR holder_hand IS NULL),
  holder_shank_width REAL,
  holder_cut_width REAL,
  holder_oal REAL,
  groove_width REAL,
  max_depth_of_cut REAL,
  drill_point_angle REAL,
  flute_length REAL,
  overall_length REAL,
  shaft_diameter REAL,
  chamfer_threads REAL,
  thread_pitch_max REAL,
  thread_angle REAL,
  thread_tip_type TEXT,
  surface_speed REAL,
  feed_per_rev REAL,
  depth_of_cut REAL,
  notes TEXT NOT NULL DEFAULT '',
  length_below_holder REAL,
  holder_head_length REAL,
  thread_pitch REAL,
  thread_pitch_min REAL,
  spindle_direction TEXT CHECK (spindle_direction IN ('FWD','REV') OR spindle_direction IS NULL)
);

INSERT INTO tool_lathe_new SELECT
  tool_id, type, insert_shape, insert_size_mode, insert_size, insert_thickness,
  holder_style, holder_hand, holder_shank_width, holder_cut_width, holder_oal,
  groove_width, max_depth_of_cut, drill_point_angle, flute_length,
  overall_length, shaft_diameter, chamfer_threads, thread_pitch_max,
  thread_angle, thread_tip_type, surface_speed, feed_per_rev, depth_of_cut,
  notes, length_below_holder, holder_head_length, thread_pitch,
  thread_pitch_min, spindle_direction
FROM tool_lathe;

DROP TABLE tool_lathe;
ALTER TABLE tool_lathe_new RENAME TO tool_lathe;

UPDATE meta SET schema_version = 8;

COMMIT;

PRAGMA foreign_keys=ON;
