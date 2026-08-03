-- Holder head length (Fusion holder "LH") gets its own column.
--
-- Stickout was being taken from holder_oal (Fusion holder "OAL"), which is the
-- holder's FULL PHYSICAL LENGTH -- most of which is clamped in the tool block
-- and can never enter a bore. LH is the head: the portion that protrudes, and
-- therefore the only part that has anything to do with reach or slenderness.
--
-- Using OAL over-stated reach and under-stated the slender ratio -- wrong in
-- the unsafe direction on both counts.
--
-- Nullable with no default: an existing row does not know its head length, and
-- inventing one would be indistinguishable from a measured value.

BEGIN;

ALTER TABLE tool_lathe ADD COLUMN holder_head_length REAL;

UPDATE meta SET schema_version = 5;

COMMIT;
