# coding=utf-8
"""Merge a classic LinuxCNC .tbl file and a Fusion 360 tool library export
into one COMPLETE schema-v1 tool database.

Each source alone is only a starting point; merged, they complete each
other:

* The .tbl carries the machine-setup data a Fusion export doesn't have --
  X/Z offsets, front/back angles (I/J), lathe orientation (Q), pocket.
* The Fusion library carries what the .tbl doesn't -- each tool's TYPE plus
  insert/holder/threading data. The type is also what makes the .tbl's D
  column safe to interpret at all: legacy D means nose RADIUS for
  turning-family tools but plain DIAMETER for drills/taps, and only the
  Fusion type can say which (the whole reason the plain .tbl importer
  deliberately leaves tools untyped).

Tools match by number: .tbl T <-> Fusion post-process number. The merge
rules are the ratified schema-v1 seed-generator rules
(pb_lathe_conv docs/schema_v1/generate_seed.py, frozen 2026-07-03):

* core offsets/angles/orientation/pocket: from the .tbl (0 defaults when
  the tool is Fusion-only)
* remark: .tbl remark, falling back to the Fusion description
* diameter: 2 x tbl-D for the turning family / tbl-D for drill+tap; when
  the .tbl row is missing or carried D=0 (threading tools usually did),
  derived from Fusion geometry instead (2 x RE / thread-tip-radius, or
  DC / SFDM)
* tool_lathe extras: from Fusion (tbl-only tools import untyped, exactly
  like the plain .tbl importer)

Usage:
    merge2db lathe.tbl library.tools output.db
    merge2db lathe.tbl library.json output.db --units mm
"""

import argparse
import os
import sys

from sqlalchemy.orm import sessionmaker

from .import_legacy_tbl import parse_tbl
from .import_fusion_tools import (
    _Numbers, _make_standalone_engine, extras_from_fusion,
    load_fusion_library, map_type,
)
from .migrate import run_migrations
from .tool_table import Meta, Tool, ToolLathe

TURNING_FAMILY = ("turning", "boring", "grooving", "parting", "threading")


def _fusion_tools_by_number(entries, skipped):
    """{tool_no: fusion_tool} from raw library entries; bare holders,
    number-less tools, and duplicate numbers land in `skipped`."""
    by_number = {}
    for tool in entries:
        description = str(tool.get('description') or '').strip()
        fusion_type = str(tool.get('type') or '').strip()
        label = description or fusion_type or 'unnamed entry'

        if fusion_type.lower() == 'holder':
            skipped.append((label, 'bare holder entry, not a tool'))
            continue

        raw_num = (tool.get('post-process') or {}).get('number')
        try:
            tool_no = int(raw_num)
        except (TypeError, ValueError):
            tool_no = 0
        if tool_no <= 0:
            skipped.append((label, 'no post-process tool number'))
            continue
        if tool_no in by_number:
            skipped.append((label, 'duplicate tool number T%d (first kept)' % tool_no))
            continue
        by_number[tool_no] = tool
    return by_number


def import_merged_to_db(tbl_path, fusion_path, db_path, units='inch',
                        overwrite=False):
    """Create a complete schema-v1 tool database at db_path by merging a
    legacy .tbl and a Fusion 360 library export (.tools or .json).

    Returns (imported_tool_numbers, notes) where notes is a list of
    (label, reason) pairs: Fusion entries that couldn't become tools, plus
    per-tool merge caveats (tbl-only tools imported untyped, Fusion-only
    tools starting with zeroed offsets/angles/orientation).

    Same file-safety guarantees as the other importers: refuses an
    existing db_path unless overwrite=True, and runs on its own standalone
    engine so it never touches a database a running GUI has open.
    """
    if units not in ('inch', 'mm'):
        raise ValueError("units must be 'inch' or 'mm', got %r" % units)

    if os.path.exists(db_path):
        if not overwrite:
            raise FileExistsError(
                "%s already exists -- pass overwrite=True (or --overwrite) "
                "to replace it. This creates a new starting-point database, "
                "it does not merge into an existing one." % db_path)
        os.remove(db_path)

    tbl_rows = parse_tbl(tbl_path)

    notes = []
    fusion_by_number = _fusion_tools_by_number(load_fusion_library(fusion_path), notes)

    tool_numbers = sorted(set(tbl_rows) | set(fusion_by_number))
    if not tool_numbers:
        raise ValueError("No usable tools found in %s + %s -- nothing to import"
                          % (tbl_path, fusion_path))

    records = {}
    for tool_no in tool_numbers:
        row = tbl_rows.get(tool_no)          # Tool-ORM-keyed dict, or None
        ftool = fusion_by_number.get(tool_no)

        ttype = map_type(ftool.get('type')) if ftool else None
        num = _Numbers(ftool.get('unit'), units) if ftool else None
        geo = (ftool.get('geometry') or {}) if ftool else {}

        # D per schema section 5.1 -- the merge's whole reason to exist:
        # the Fusion type disambiguates what the .tbl's D meant. .tbl wins
        # when it carried a real value (it's the machine's measured data);
        # Fusion geometry fills the gaps (threading tools historically
        # carried D=0 in the .tbl).
        tbl_d = float(row.get('diameter', 0.0)) if row else 0.0
        if ttype is None:
            d_val = tbl_d  # untyped: keep raw legacy value, same as tbl2db
        elif ttype in ('drill', 'tap'):
            d_val = tbl_d if tbl_d > 0.0 else (
                num.first_positive(geo.get('DC'), geo.get('SFDM')) or 0.0)
        else:
            d_val = 2.0 * tbl_d if tbl_d > 0.0 else 2.0 * (
                num.first_positive(geo.get('RE'), geo.get('thread-tip-radius')) or 0.0)

        remark = (row.get('remark', '') if row else '') or \
                 (str(ftool.get('description') or '') if ftool else '')

        core = dict(row) if row else {'pocket': -1}
        core['tool_no'] = tool_no
        core['diameter'] = d_val
        core['remark'] = remark

        extras = extras_from_fusion(ftool, ttype, num) if ftool else None
        records[tool_no] = {'core': core, 'extras': extras}

        if ftool is None:
            notes.append((f'T{tool_no} {remark}'.strip(),
                          'no Fusion match -- imported untyped (set type/insert/'
                          'holder data in the tool table editor)'))
        elif row is None:
            notes.append((f'T{tool_no} {remark}'.strip(),
                          'no .tbl match -- offsets/angles/orientation start at 0 '
                          '(set by touch-off and the tool table editor)'))

    engine = _make_standalone_engine(db_path)
    run_migrations(engine)

    session = sessionmaker(bind=engine)()
    try:
        meta = session.query(Meta).first()
        meta.units = units

        for tool_no in tool_numbers:
            record = records[tool_no]
            tool_row = Tool(**record['core'])
            if record['extras'] is not None:
                tool_row.lathe = ToolLathe(**record['extras'])
            session.add(tool_row)

        session.commit()
    finally:
        session.close()
        engine.dispose()

    return tool_numbers, notes


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Merge a legacy LinuxCNC .tbl and a Fusion 360 tool "
                     "library export (.tools or .json) into one complete "
                     "schema-v1 tool database: machine-setup data (offsets, "
                     "angles, orientation) from the .tbl, tool types and "
                     "insert/holder data from Fusion, matched by tool "
                     "number.")
    parser.add_argument('tbl_file', help="Path to the legacy .tbl file")
    parser.add_argument('fusion_file', help="Path to the .tools or .json export")
    parser.add_argument('db_file', help="Path to write the new .db file")
    parser.add_argument('--units', choices=('inch', 'mm'), default='inch',
                         help="Unit system for the new database (default: inch)")
    parser.add_argument('--overwrite', action='store_true',
                         help="Replace db_file if it already exists")
    args = parser.parse_args(argv)

    try:
        imported, notes = import_merged_to_db(
            args.tbl_file, args.fusion_file, args.db_file,
            units=args.units, overwrite=args.overwrite)
    except (ValueError, FileExistsError) as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 1

    print("Merged %d tool(s) from %s + %s -> %s (%s)" %
          (len(imported), args.tbl_file, args.fusion_file, args.db_file,
           args.units))
    print("Tool numbers: %s" % ', '.join(str(t) for t in imported))
    for label, reason in notes:
        print("Note: %s -- %s" % (label, reason))
    return 0


if __name__ == '__main__':
    sys.exit(main())
