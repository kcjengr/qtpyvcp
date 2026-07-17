# coding=utf-8
"""SQLAlchemy engine/session for the qtpyvcp tool database.

The database location is set with :func:`configure_database`; both the GUI
process (DataPlugin) and the LinuxCNC-spawned db_program must call it with
the same path (single source: the INI, see DB_PROGRAM args).

Until configure_database() is called, a legacy-compatible default engine
bound to ``./db.sqlite`` exists so importing this module has no side effects
and existing callers keep working. SQLite pragmas (WAL, foreign keys, busy
timeout) are applied on every connection — required because two processes
(GUI and db_program) share the file.
"""

import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def _make_engine(db_path):
    eng = create_engine('sqlite:///%s' % db_path, echo=False)

    @event.listens_for(eng, 'connect')
    def _sqlite_pragmas(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.execute('PRAGMA busy_timeout=5000')
        cursor.close()

    return eng


# Legacy default (CWD-relative). Deliberately not connected at import time;
# call configure_database() before first use to bind the real per-machine file.
engine = _make_engine('db.sqlite')
Session = sessionmaker(bind=engine)


def configure_database(db_path):
    """Bind the module engine and Session factory to `db_path`.

    Rebinds the existing Session factory in place, so callers holding
    ``from ...base import Session`` see the new database. Callers that
    captured ``engine`` directly should use :func:`get_engine` instead.
    """
    global engine
    engine = _make_engine(os.path.abspath(os.path.expanduser(str(db_path))))
    Session.configure(bind=engine)
    return engine


def get_engine():
    """Current engine (respects configure_database rebinds)."""
    return engine
