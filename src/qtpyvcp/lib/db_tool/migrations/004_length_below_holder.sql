-- Length below holder (Fusion "LB") gets its own column on round tools.
--
-- It was previously folded into flute_length, which reads LCF first and fell
-- back to LB. They are different measurements: LCF is the fluted portion,
-- LB is how far the tool protrudes from the holder. On a drill they are often
-- equal, which is why the conflation went unnoticed; on a tap they are not --
-- a tap with 1.2 flute can sit 2.0 below the holder.
--
-- LB is what bounds how deep a round tool can be driven before the holder
-- reaches the work, so the reach check needs it directly rather than a value
-- that may or may not be it.
--
-- Nullable with no default: an existing row genuinely does not know its LB,
-- and a fabricated number here would be indistinguishable from a measured
-- one. Callers treat blank as "not recorded" and say so.

BEGIN;

ALTER TABLE tool_lathe ADD COLUMN length_below_holder REAL;

UPDATE meta SET schema_version = 4;

COMMIT;
