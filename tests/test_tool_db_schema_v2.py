#!/usr/bin/env python3
"""Phase 2 schema/plugin unit tests.

Covers the plan §6 Phase 2 test list: round-trip (core + extras + custom
fields, through the actual DBToolTable plugin), concurrent writer, version
gate, malformed DB (refuse + backup), orphan tool_lathe rows.

Run directly: python3 tests/test_tool_db_schema_v2.py
"""

import os
import sys
import threading

os.environ.setdefault('DESIGNER', '1')  # plugin usable without a running app/Qt event loop

HERE = os.path.dirname(os.path.abspath(__file__))
QTPYVCP_SRC = os.path.abspath(os.path.join(HERE, '..', 'src'))
sys.path.insert(0, QTPYVCP_SRC)

from sqlalchemy.exc import IntegrityError

from qtpyvcp.lib.db_tool.base import configure_database, get_engine, Session
from qtpyvcp.lib.db_tool.tool_table import Tool, ToolLathe
from qtpyvcp.lib.db_tool.migrate import run_migrations, MigrationError
from qtpyvcp.plugins.db_tool_table import DBToolTable

failures = []


def expect(desc, cond):
    print(('PASS  ' if cond else 'FAIL  ') + desc)
    if not cond:
        failures.append(desc)


def fresh_db(name):
    path = os.path.join(HERE, name)
    for suffix in ('', '-wal', '-shm'):
        p = path + suffix
        if os.path.exists(p):
            os.remove(p)
    return path


# ---------------------------------------------------------------- round-trip
def test_round_trip():
    db = fresh_db('phase2_roundtrip.db')
    configure_database(db)
    run_migrations(get_engine())

    plugin = DBToolTable()
    plugin.loadToolTable()
    table = plugin.getToolTable()
    table[5] = plugin.newTool(tnum=5)
    table[5].update({'D': 0.5, 'I': 10.0, 'J': 20.0, 'Q': 3, 'R': 'Round Trip Tool'})
    plugin.saveToolTable(table)

    plugin.saveToolExtras(5, {'type': 'turning', 'insert_shape': 'C',
                              'holder_style': 'SCLCR', 'holder_hand': 'R'})

    plugin.addCustomField('coating', 'Coating', 'text')
    plugin.setCustomFieldValue(5, 'coating', 'TiAlN')

    # fresh plugin instance -- simulates a second process/restart reading
    # back what the first one wrote, not just re-reading its own cache.
    plugin2 = DBToolTable()
    plugin2.loadToolTable()
    reloaded = plugin2.getToolTable()[5]
    expect('round-trip core columns',
           reloaded['D'] == 0.5 and reloaded['I'] == 10.0 and
           reloaded['J'] == 20.0 and reloaded['Q'] == 3 and
           reloaded['R'] == 'Round Trip Tool')

    extras = plugin2.getToolExtras(5)
    expect('round-trip extras',
           extras is not None and extras['type'] == 'turning' and
           extras['insert_shape'] == 'C' and extras['holder_style'] == 'SCLCR')

    defs = plugin2.getCustomFieldDefs()
    expect('custom field definition round-trips',
           any(d['name'] == 'coating' and d['value_type'] == 'text' for d in defs))

    values = plugin2.getCustomFieldValues(5)
    expect('custom field value round-trips', values.get('coating') == 'TiAlN')


# ------------------------------------------------------------------ renumber
def test_renumber_preserves_extras_and_custom_values():
    db = fresh_db('phase2_renumber.db')
    configure_database(db)
    run_migrations(get_engine())

    plugin = DBToolTable()
    plugin.loadToolTable()
    table = plugin.getToolTable()
    table[7] = plugin.newTool(tnum=7)
    table[7]['D'] = 0.25
    plugin.saveToolTable(table)
    plugin.saveToolExtras(7, {'type': 'drill', 'drill_point_angle': 118.0})
    plugin.addCustomField('vendor', 'Vendor', 'text')
    plugin.setCustomFieldValue(7, 'vendor', 'Sandvik')

    plugin.renumberTool(7, 47)

    reloaded = plugin.getToolTable()
    expect('renumber: old tool number gone', 7 not in reloaded)
    expect('renumber: new tool number present with same core data',
           47 in reloaded and reloaded[47]['D'] == 0.25)

    extras = plugin.getToolExtras(47)
    expect('renumber: extras followed the tool (same id, not delete+recreate)',
           extras is not None and extras['type'] == 'drill' and
           extras['drill_point_angle'] == 118.0)

    values = plugin.getCustomFieldValues(47)
    expect('renumber: custom field value followed the tool',
           values.get('vendor') == 'Sandvik')

    raised_dup, raised_t0 = False, False
    try:
        plugin.renumberTool(47, 47)  # no-op, must not raise
    except Exception:
        raised_dup = True
    try:
        plugin.renumberTool(47, 0)
    except ValueError:
        raised_t0 = True
    expect('renumber to self is a no-op (no exception)', not raised_dup)
    expect('renumber to T0 is rejected', raised_t0)


# ---------------------------------------------------------- concurrent writer
def test_concurrent_writer():
    """Simulates the plugin (GUI process) and db_program writing at once:
    several threads, each its own Session, hammering different tool rows.
    WAL + busy_timeout (base.py) should serialize writers with retries
    rather than raise 'database is locked'."""
    db = fresh_db('phase2_concurrent.db')
    configure_database(db)
    run_migrations(get_engine())

    errors = []

    def writer(tool_no, iterations):
        try:
            for i in range(iterations):
                s = Session()
                tool = s.query(Tool).filter(Tool.tool_no == tool_no).one_or_none()
                if tool is None:
                    tool = Tool(tool_no=tool_no)
                    s.add(tool)
                tool.x_offset = float(i)
                s.commit()
                s.close()
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(100 + n, 20)) for n in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    expect('concurrent writers hit no errors (WAL + busy_timeout absorbed contention)',
           not errors)

    s = Session()
    final = {t.tool_no: t.x_offset
              for t in s.query(Tool).filter(Tool.tool_no >= 100).all()}
    s.close()
    expect('all 4 concurrent tools present with their final write landed',
           final == {100: 19.0, 101: 19.0, 102: 19.0, 103: 19.0})


# --------------------------------------------------------------- version gate
def test_version_gate():
    db = fresh_db('phase2_futureversion.db')
    configure_database(db)
    run_migrations(get_engine())  # bring to the current known version first

    raw = get_engine().raw_connection()
    raw.cursor().execute("UPDATE meta SET schema_version = 999")
    raw.commit()
    raw.close()

    raised = False
    try:
        run_migrations(get_engine())
    except MigrationError:
        raised = True
    expect('run_migrations refuses a DB claiming a future schema_version', raised)


# --------------------------------------------------------------- malformed DB
def test_malformed_db():
    db = fresh_db('phase2_malformed.db')

    configure_database(db)
    raw = get_engine().raw_connection()
    # pre-schema-v1 shape: a `tool` table that conflicts with 001_initial.sql's
    # CREATE TABLE, simulating a database that predates the Phase 2 rename.
    raw.cursor().execute("CREATE TABLE tool (id INTEGER PRIMARY KEY, i_offset REAL)")
    raw.commit()
    raw.close()

    raised = False
    try:
        run_migrations(get_engine())
    except MigrationError:
        raised = True
    expect('run_migrations refuses a pre-v1 (malformed) database', raised)

    backups = [f for f in os.listdir(HERE)
               if f.startswith(os.path.basename(db) + '.pre-migration-')]
    expect('a backup of the malformed DB was made before refusing', bool(backups))
    for f in backups:
        os.remove(os.path.join(HERE, f))


# ------------------------------------------------------------- orphan rows
def test_orphan_tool_lathe():
    db = fresh_db('phase2_orphan.db')
    configure_database(db)
    run_migrations(get_engine())

    s = Session()
    s.add(ToolLathe(tool_id=99999, type='turning'))  # no such tool row exists
    raised = False
    try:
        s.commit()
    except IntegrityError:
        raised = True
        s.rollback()
    finally:
        s.close()
    expect('orphan tool_lathe row (bogus tool_id) rejected by FK enforcement', raised)


if __name__ == '__main__':
    test_round_trip()
    test_renumber_preserves_extras_and_custom_values()
    test_concurrent_writer()
    test_version_gate()
    test_malformed_db()
    test_orphan_tool_lathe()
    print()
    print('ALL CHECKS PASSED' if not failures else 'FAILURES: %s' % failures)
    sys.exit(1 if failures else 0)
