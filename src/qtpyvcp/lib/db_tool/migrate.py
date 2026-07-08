"""Hand-rolled versioned SQL migration runner for the tool database.

Plan §6/§9 decision: a folder of ordered scripts (``NNN_description.sql``),
applied in a transaction, each script bumping ``meta.schema_version`` itself
(see the ``INSERT``/``UPDATE`` at the end of every migration file). No
Alembic: single-file SQLite, one linear history, plain-SQL review.

The DB predating schema v1 (bare ``tool``/``tool_table``/``tool_model``
tables, no ``meta``) cannot be migrated automatically -- the column
renames are breaking (plan §6 Phase 1 note). ``run_migrations`` detects that
case and fails loudly with a clear message instead of leaving a half-applied
schema.
"""

import glob
import os
import shutil
import time

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'migrations')


class MigrationError(Exception):
    pass


def _scripts():
    """Ordered (version, path) pairs from migrations/NNN_*.sql."""
    paths = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, '[0-9][0-9][0-9]_*.sql')))
    return [(int(os.path.basename(p)[:3]), p) for p in paths]


def _backup_db_file(engine):
    """Copy the sqlite file (+ -wal/-shm) aside before refusing a malformed
    or pre-schema-v1 database, so a failed migration is never confused with
    silent data loss. Returns the backup path, or None if there's no file
    (e.g. an in-memory DB) to back up."""
    db_path = engine.url.database
    if not db_path or not os.path.exists(db_path):
        return None
    backup_path = '%s.pre-migration-%s.bak' % (db_path, time.strftime('%Y%m%d-%H%M%S'))
    shutil.copy2(db_path, backup_path)
    for suffix in ('-wal', '-shm'):
        side = db_path + suffix
        if os.path.exists(side):
            shutil.copy2(side, backup_path + suffix)
    return backup_path


def _current_version(cursor):
    has_meta = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='meta'"
    ).fetchone()
    if not has_meta:
        return 0
    row = cursor.execute("SELECT schema_version FROM meta").fetchone()
    return row[0] if row else 0


def run_migrations(engine):
    """Bring the database at `engine` up to the latest known schema version.

    Applies every migrations/NNN_*.sql script newer than the DB's current
    ``meta.schema_version``, in order. Safe to call on every startup: a
    fully up-to-date DB is a no-op.
    """
    scripts = _scripts()
    if not scripts:
        raise MigrationError("no migration scripts found in %s" % MIGRATIONS_DIR)
    latest_known = scripts[-1][0]

    raw = engine.raw_connection()
    try:
        cursor = raw.cursor()
        current = _current_version(cursor)

        if current > latest_known:
            raise MigrationError(
                "database schema_version=%d is newer than this qtpyvcp "
                "build knows about (latest=%d); refusing to touch it. "
                "Update qtpyvcp before opening this database." %
                (current, latest_known))

        pending = [(v, p) for v, p in scripts if v > current]
        for version, path in pending:
            sql = open(path).read()
            try:
                cursor.executescript(sql)
            except Exception as exc:
                raw.rollback()
                raw.close()
                backup_path = _backup_db_file(engine)
                raise MigrationError(
                    "migration %s failed (db may predate schema v1 -- "
                    "the column renames in v1 are not auto-upgradable from "
                    "the pre-Phase-2 schema; delete/re-seed the database "
                    "instead). Original file backed up to %s before "
                    "refusing: %s" % (os.path.basename(path), backup_path, exc)) from exc
        raw.commit()
    finally:
        raw.close()

    return latest_known
