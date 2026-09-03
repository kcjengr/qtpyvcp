-- Spindle direction, per tool.
--
-- A wrong direction is the one setup error a toolpath preview cannot show. The
-- motion looks perfect: every diameter, every Z, every approach is correct, and
-- the insert still rubs its own flank instead of cutting because the work is
-- turning the wrong way.
--
-- It belongs on the tool because for a given machine it IS a property of the
-- tool. A right-hand turning tool on a rear post wants one direction and will
-- always want it. Left-hand tooling wants the other. That is true before any
-- operation exists.
--
-- Drills and taps are included, not exempt. On a lathe they are held stationary
-- and the WORK rotates, so a left-hand drill or tap needs the spindle reversed
-- exactly as a left-hand turning tool does -- the tool not spinning is what
-- makes the direction a fact about the work, not about the tool's own rotation.
--
-- FWD/REV rather than M3/M4 or CW/CCW: it matches what the operation pages
-- already show in the cutting column, so the tool table and the operation speak
-- the same word and the check between them compares like with like.
--
-- Nullable with no default. Nothing can infer this: a Fusion library does not
-- carry it, and guessing from holder hand would be wrong the moment someone
-- runs a front post. Existing rows go amber until the direction is entered,
-- which is the honest outcome -- the same call 006 made about thread_pitch_min.

BEGIN;

ALTER TABLE tool_lathe ADD COLUMN spindle_direction TEXT
  CHECK (spindle_direction IN ('FWD','REV') OR spindle_direction IS NULL);

UPDATE meta SET schema_version = 7;

COMMIT;
