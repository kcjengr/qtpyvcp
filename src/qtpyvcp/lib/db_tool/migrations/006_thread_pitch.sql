-- Thread pitch: three Fusion keys that were being collapsed into one column.
--
-- A Fusion export carries TP, TPN and TPX, and they are not the same thing.
-- On a tap, TP is the pitch it cuts -- fixed, because a tap is ground for one
-- thread. On a threading insert, TPN and TPX bound the RANGE of pitches the
-- insert can cut, and they genuinely differ: a SIR-375-H11-11IRA60 exports
-- TPN 0.03 against TPX 0.0625.
--
-- The import wrote first_positive(TPX, TP, TPN) into thread_pitch_max and
-- discarded the rest. Two consequences: the minimum was lost, so nothing
-- could check a programmed pitch against what the insert is rated for; and a
-- tap's pitch ended up in a column labelled "Max Pitch", which is where the
-- confusion that prompted this started.
--
-- So: thread_pitch for the tap's fixed pitch, thread_pitch_min/-_max for the
-- insert's range. thread_pitch_max keeps its name and its data -- for a
-- threading insert it already held TPX and stays correct.
--
-- Nullable with no default. An existing tap row has its pitch sitting in
-- thread_pitch_max, and moving it is the one case we CAN infer safely: a tap
-- has no range, so whatever is in that column is its pitch. Threading rows
-- are left alone -- their max is right and their min was never imported, so
-- it is genuinely unknown rather than something to fabricate.

BEGIN;

ALTER TABLE tool_lathe ADD COLUMN thread_pitch REAL;
ALTER TABLE tool_lathe ADD COLUMN thread_pitch_min REAL;

-- Taps only: relabel the value already stored, since for a tap that column
-- never meant a maximum.
UPDATE tool_lathe
   SET thread_pitch = thread_pitch_max,
       thread_pitch_max = NULL
 WHERE thread_pitch_max IS NOT NULL
   AND lower(coalesce(type, '')) = 'tap';

UPDATE meta SET schema_version = 6;

COMMIT;
