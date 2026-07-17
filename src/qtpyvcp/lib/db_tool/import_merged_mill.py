# coding=utf-8
"""Merge a classic LinuxCNC .tbl file and a Fusion 360 tool library export
into one tool database, mill flavor.

The mill counterpart of import_merged (lathe-flavored). Tools match by
number (.tbl T <-> Fusion post-process number); each source fills what the
other lacks:

* The .tbl carries the machine-setup data a Fusion export doesn't have --
  X/Y/Z offsets and pocket.
* The Fusion library carries tool identity for tools not yet in the .tbl --
  cutting diameter and description.

Diameter handling is where this differs from the lathe merge. A mill tool's
D is a plain cutting diameter in BOTH sources, so there is no nose-radius
reinterpretation: the .tbl's D wins when it carried a real value (it is the
machine's measured data), and Fusion's DC fills in only when the .tbl had
no row or D=0. (The lathe merge exists largely to reinterpret a legacy .tbl
D as 2 x nose radius using the Fusion type; a mill needs none of that, so
this merge is a straightforward field-level union.)

Mill extras (tool_mill.atc) import as the schema default -- every tool
storable in the ATC -- exactly like the mill Fusion and plain .tbl
importers. Mark oversize exceptions in the tool table editor afterward.

Usage:
    merge2db-mill mill.tbl library.tools output.db
    merge2db-mill mill.tbl library.json output.db --units mm
"""

import argparse
import os
import sys

from sqlalchemy.orm import sessionmaker

from .import_legacy_tbl import parse_tbl
from .import_fusion_tools import _Numbers, _make_standalone_engine, load_fusion_library
from .import_fusion_mill import fusion_mill_diameter
from .import_merged import _fusion_tools_by_number
from .migrate import run_migrations
from .tool_table import Meta, Tool


def import_merged_to_db_mill(tbl_path, fusion_path, db_path, units='inch',
                             overwrite=False):
    """Create a tool database at db_path by merging a legacy .tbl and a
    Fusion 360 library export (.tools or .json), mill flavor (core columns
    only).

    Returns (imported_tool_numbers, notes) where notes is a list of
    (label, reason) pairs: Fusion entries that couldn't become tools, plus
    per-tool caveats (Fusion-only tools starting with zeroed offsets/
    pocket). Same file-safety guarantees as the other importers.
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
        num = _Numbers(ftool.get('unit'), units) if ftool else None
        geo = (ftool.get('geometry') or {}) if ftool else {}

        # Plain diameter in both sources for a mill: .tbl wins when it
        # carried a real value (measured machine data), Fusion DC fills the
        # gap. No 2x nose-radius doubling -- that is a lathe-only concern.
        tbl_d = float(row.get('diameter', 0.0)) if row else 0.0
        if tbl_d > 0.0:
            d_val = tbl_d
        elif ftool is not None:
            d_val = fusion_mill_diameter(geo, num)
        else:
            d_val = 0.0

        remark = (row.get('remark', '') if row else '') or \
                 (str(ftool.get('description') or '') if ftool else '')

        core = dict(row) if row else {'pocket': -1}
        core['tool_no'] = tool_no
        core['diameter'] = d_val
        core['remark'] = remark
        records[tool_no] = core

        if ftool is None:
            # tbl-only tools are already complete for a mill (core-only) --
            # no note needed, unlike the lathe merge where a tbl-only tool
            # is missing its type/insert data.
            continue
        if row is None:
            notes.append((f'T{tool_no} {remark}'.strip(),
                          'no .tbl match -- offsets and pocket start at 0 '
                          '(set by touch-off and the tool table editor)'))

    engine = _make_standalone_engine(db_path)
    run_migrations(engine)

    session = sessionmaker(bind=engine)()
    try:
        meta = session.query(Meta).first()
        meta.units = units

        for tool_no in tool_numbers:
            session.add(Tool(**records[tool_no]))

        session.commit()
    finally:
        session.close()
        engine.dispose()

    return tool_numbers, notes


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Merge a legacy LinuxCNC .tbl and a Fusion 360 tool "
                     "library export (.tools or .json) into one tool "
                     "database, mill flavor: machine-setup data (offsets, "
                     "pocket) from the .tbl, tool identity (diameter, "
                     "description) from Fusion, matched by tool number.")
    parser.add_argument('tbl_file', help="Path to the legacy .tbl file")
    parser.add_argument('fusion_file', help="Path to the .tools or .json export")
    parser.add_argument('db_file', help="Path to write the new .db file")
    parser.add_argument('--units', choices=('inch', 'mm'), default='inch',
                         help="Unit system for the new database (default: inch)")
    parser.add_argument('--overwrite', action='store_true',
                         help="Replace db_file if it already exists")
    args = parser.parse_args(argv)

    try:
        imported, notes = import_merged_to_db_mill(
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
