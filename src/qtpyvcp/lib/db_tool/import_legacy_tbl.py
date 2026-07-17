# coding=utf-8
"""Import a classic LinuxCNC lathe .tbl file into a fresh schema-v1 tool
database -- a starting point for transitioning to the DB-backed tool table,
not a finished migration.

Deliberately minimal (ratified 2026-07-15): every imported tool lands with
only the core LinuxCNC fields (T/P/X/Z/I/J/D/Q/R) and NO tool_lathe row --
type, insert geometry, and holder data are left for the user to fill in via
the tool table editor afterward.

This is the only safe default without guessing. In the legacy .tbl
convention, D means nose radius for turning-family tools but plain diameter
for drill/tap. In schema v1 the `tool.diameter` column means "2 x nose
radius" ONCE A TYPE IS SET (migrations/001_initial.sql, plan §5.1) --
auto-guessing a type wrong would silently double or halve a tool's real
geometry. Leaving type unset sidesteps that risk entirely:
db_tool_provider.DbToolTableAdapter passes an untyped row's D straight
through unchanged at read time, so imported turning tools keep exactly
their old nose-radius meaning and imported drill/tap tools keep their old
diameter meaning -- G-code output identical to the legacy .tbl, immediately,
with zero risk of a silent 2x error. The user assigns each tool's real type
(and gets the richer conversational features -- insert preview, groove-width
checks, min-bore safety -- for that tool) at their own pace afterward.

Usage:
    python3 -m qtpyvcp.lib.db_tool.import_legacy_tbl lathe.tbl output.db
    python3 -m qtpyvcp.lib.db_tool.import_legacy_tbl lathe.tbl output.db --units mm
"""

import argparse
import os
import re
import sys

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from .migrate import run_migrations
from .tool_table import Meta, Tool


def _make_standalone_engine(db_path):
    """A fresh SQLAlchemy engine bound only to db_path.

    Deliberately NOT qtpyvcp.lib.db_tool.base's global engine/Session
    singleton -- that singleton is the SAME connection a running app's live
    DBToolTable plugin uses (base.configure_database rebinds it process-
    wide). Importing a .tbl is a one-shot write to a brand new file; using
    the global here would silently hijack whatever tool database a caller
    already has open, whether that's another CLI run or a GUI action
    embedded in a live probe_basic session. Same SQLite pragmas as
    base._make_engine (WAL + FK + busy timeout) for two-process-safe access
    to the resulting file, applied here since we're deliberately not
    sharing that helper's engine/global state."""
    eng = create_engine('sqlite:///%s' % db_path, echo=False)

    @event.listens_for(eng, 'connect')
    def _sqlite_pragmas(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.execute('PRAGMA busy_timeout=5000')
        cursor.close()

    return eng

# Same field-extraction regex as qtpyvcp.plugins.tool_table.DataPlugin.
# loadToolTable (the live legacy-.tbl loader) -- proven against real files,
# not reimplemented from scratch.
_FIELD_RE = re.compile(r"([A-Z]+[0-9.+-]+)")
_INT_FIELDS = ('P', 'Q')
_FLOAT_FIELDS = ('X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W', 'D', 'I', 'J')

_COLUMN_FOR_FIELD = {
    'P': 'pocket',
    'X': 'x_offset', 'Y': 'y_offset', 'Z': 'z_offset',
    'A': 'a_offset', 'B': 'b_offset', 'C': 'c_offset',
    'U': 'u_offset', 'V': 'v_offset', 'W': 'w_offset',
    'D': 'diameter', 'I': 'front_angle', 'J': 'back_angle',
    'Q': 'orientation',
}


def parse_tbl(tbl_path):
    """Parse a classic LinuxCNC .tbl file into {tool_no: {column: value}}
    dicts keyed by the Tool ORM's column names.

    T<=0 rows (the ``T0``/``T-1`` "no tool" sentinels some .tbl files carry)
    are skipped -- schema v1's ``tool`` table has a hard ``CHECK (tool_no >
    0)`` constraint, and T0 is a synthesized in-memory placeholder even in
    the legacy dict-based loader, never a real row. A duplicate T number
    within the file keeps its LAST occurrence, matching the legacy loader's
    own ``table[tnum] = tool`` last-wins behavior.
    """
    with open(tbl_path, 'r') as fh:
        lines = [line.strip() for line in fh.readlines()]

    tools = {}
    for line in lines:
        if not line or line.startswith(';'):
            continue

        data, _sep, comment = line.partition(';')
        items = _FIELD_RE.findall(data.replace(' ', ''))
        if not items:
            continue

        row = {'pocket': -1, 'remark': comment.strip()}
        tool_no = None
        for item in items:
            descriptor, value = item[0], item[1:]
            if descriptor == 'T':
                try:
                    tool_no = int(value)
                except ValueError:
                    tool_no = None
            elif descriptor in _INT_FIELDS:
                try:
                    row[_COLUMN_FOR_FIELD[descriptor]] = int(value)
                except ValueError:
                    pass
            elif descriptor in _FLOAT_FIELDS:
                try:
                    row[_COLUMN_FOR_FIELD[descriptor]] = float(value)
                except ValueError:
                    pass

        if tool_no is None or tool_no <= 0:
            continue

        tools[tool_no] = row

    return tools


def import_tbl_to_db(tbl_path, db_path, units='inch', overwrite=False):
    """Create a fresh schema-v1 tool database at db_path from a legacy .tbl
    file. Returns the sorted list of imported tool numbers.

    Refuses to touch an existing file unless overwrite=True -- this always
    generates a NEW starting-point database, it never merges into one.

    Uses its own standalone engine/session (see _make_standalone_engine),
    NOT qtpyvcp.lib.db_tool.base's process-global one -- safe to call from
    anywhere, including from inside a running probe_basic GUI process that
    already has a different tool database open; this never touches that
    connection.
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

    tools = parse_tbl(tbl_path)
    if not tools:
        raise ValueError("No tools found in %s -- nothing to import" % tbl_path)

    engine = _make_standalone_engine(db_path)
    run_migrations(engine)

    session = sessionmaker(bind=engine)()
    try:
        meta = session.query(Meta).first()
        meta.units = units

        for tool_no, row in sorted(tools.items()):
            session.add(Tool(tool_no=tool_no, **row))

        session.commit()
    finally:
        session.close()
        engine.dispose()

    return sorted(tools.keys())


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Import a classic LinuxCNC .tbl file into a fresh "
                     "schema-v1 tool database -- a starting point, not a "
                     "finished migration. Every tool comes in untyped "
                     "(core LinuxCNC fields only); use the tool table "
                     "editor afterward to set each tool's type and fill in "
                     "insert/holder data.")
    parser.add_argument('tbl_file', help="Path to the legacy .tbl file")
    parser.add_argument('db_file', help="Path to write the new .db file")
    parser.add_argument('--units', choices=('inch', 'mm'), default='inch',
                         help="Unit system for the new database (default: inch)")
    parser.add_argument('--overwrite', action='store_true',
                         help="Replace db_file if it already exists")
    args = parser.parse_args(argv)

    try:
        imported = import_tbl_to_db(
            args.tbl_file, args.db_file, units=args.units, overwrite=args.overwrite)
    except (ValueError, FileExistsError) as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 1

    print("Imported %d tool(s) from %s -> %s (%s)" %
          (len(imported), args.tbl_file, args.db_file, args.units))
    print("Tool numbers: %s" % ', '.join(str(t) for t in imported))
    print()
    print("These are untyped starting points -- open the tool table editor "
          "and set each tool's Type (turning/boring/grooving/parting/"
          "threading/drill/tap) plus its insert/holder data to unlock "
          "insert previews, groove-width checks, and min-bore safety "
          "validation.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
