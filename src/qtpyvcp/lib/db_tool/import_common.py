# coding=utf-8
"""Shared bootstrap for the ``import_*_to_db*`` functions
(import_legacy_tbl, import_fusion_tools, import_fusion_mill, import_merged,
import_merged_mill): standalone-engine creation, units validation, the
overwrite guard, and the create-database/set-units/commit/cleanup sequence
every one of those functions needs identically, before doing its own
importer-specific parsing and row-building.

Deliberately kept separate from :mod:`qtpyvcp.lib.db_tool.base` -- that
module's engine/Session is a process-global singleton the SAME connection a
running app's live DBToolTable plugin uses (base.configure_database rebinds
it process-wide). Every import_*_to_db* function is a one-shot write to a
brand new file; using the global here would silently hijack whatever tool
database a caller already has open, whether that's another CLI run or a GUI
action embedded in a live probe_basic session -- see _make_standalone_engine.
"""

import os
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from .migrate import run_migrations
from .tool_table import Meta


def _make_standalone_engine(db_path):
    """A fresh SQLAlchemy engine bound only to db_path -- never the
    process-global one (see module docstring). Same SQLite pragmas as
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


def validate_units(units):
    if units not in ('inch', 'mm'):
        raise ValueError("units must be 'inch' or 'mm', got %r" % units)


def guard_overwrite(db_path, overwrite):
    """Refuse to touch an existing file unless overwrite=True; removes it
    first when permitted. Every import_*_to_db* function always generates a
    NEW starting-point database, it never merges into one that already
    exists -- call this before any importer-specific parsing, matching the
    original per-function ordering (a source file that turns out empty/
    invalid still means an already-permitted overwrite went through first;
    changing that order is a behavior change, not just deduplication, so
    every caller here keeps calling this before it starts parsing, exactly
    like before this helper existed)."""
    if os.path.exists(db_path):
        if not overwrite:
            raise FileExistsError(
                "%s already exists -- pass overwrite=True (or --overwrite) "
                "to replace it. This creates a new starting-point database, "
                "it does not merge into an existing one." % db_path)
        os.remove(db_path)


@contextmanager
def new_tool_db_session(db_path, units):
    """Create a fresh standalone-engine tool database at db_path (already
    validated/overwrite-guarded by the caller -- see validate_units/
    guard_overwrite, called before this) and yield a session with
    Meta.units already set. Commits on a clean exit; always closes the
    session and disposes the engine whether or not the block raised."""
    engine = _make_standalone_engine(db_path)
    run_migrations(engine)
    session = sessionmaker(bind=engine)()
    try:
        meta = session.query(Meta).first()
        meta.units = units
        yield session
        session.commit()
    finally:
        session.close()
        engine.dispose()
