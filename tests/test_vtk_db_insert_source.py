#!/usr/bin/env python3
"""VTK insert geometry: database-native pipeline (plan §6 Phase 5).

Ratified 2026-07-08: in probe_basic there is exactly ONE source of truth
for insert geometry -- the tool database. qtpyvcp contains no tool
library file readers at all; ``lib/db_tool/insert_profile`` flattens a
core row + extras into a schema-named record and dispatches directly
into the shape builders. These checks drive the actual tool_actor
resolution functions against a real seeded DB plugin, without
constructing VTK render objects.

Chris found the motivating bug live: a mistyped nose radius rendered
(honestly, wrong-looking) in the QML preview but VTK looked "correct"
because it was reading a stale library file. Same store now -- a bad
entry is visibly bad everywhere, immediately.

Run directly: QT_QPA_PLATFORM=offscreen python3 tests/test_vtk_db_insert_source.py
"""

import os
import sys

os.environ.setdefault('DESIGNER', '1')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

HERE = os.path.dirname(os.path.abspath(__file__))
# central dev scratch area outside the repo (~/dev/scratch/README.md)
SCRATCH = os.path.expanduser('~/dev/scratch/qtpyvcp')
QTPYVCP_SRC = os.path.abspath(os.path.join(HERE, '..', 'src'))
sys.path.insert(0, QTPYVCP_SRC)

failures = []


def expect(desc, cond):
    print(('PASS  ' if cond else 'FAIL  ') + desc)
    if not cond:
        failures.append(desc)


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    db = os.path.join(SCRATCH, 'vtk_insert_source.db')
    for suffix in ('', '-wal', '-shm'):
        p = db + suffix
        if os.path.exists(p):
            os.remove(p)

    from qtpyvcp.lib.db_tool.base import configure_database, get_engine
    from qtpyvcp.lib.db_tool.migrate import run_migrations
    from qtpyvcp.plugins import registerPlugin
    from qtpyvcp.plugins.db_tool_table import DBToolTable

    configure_database(db)
    run_migrations(get_engine())
    plugin = DBToolTable(db_file=db)
    plugin.loadToolTable()

    # T4: the real-world case -- a 35-degree diamond (V) turning insert.
    # T20: a drill (diameter must pass through unhalved).
    table = plugin.getToolTable()
    table[4] = plugin.newTool(tnum=4)
    table[4].update({'D': 0.0625, 'I': 107.5, 'J': 72.5, 'Q': 2,
                     'R': 'VNMG 35deg'})
    table[20] = plugin.newTool(tnum=20)
    table[20].update({'D': 0.25, 'Q': 0, 'R': 'quarter inch drill'})
    plugin.saveToolTable(table)
    plugin.saveToolExtras(4, {'type': 'turning', 'insert_shape': 'V',
                              'insert_size_mode': 'IC', 'insert_size': 0.375,
                              'insert_thickness': 0.1875,
                              'holder_style': 'SVJBR'})
    plugin.saveToolExtras(20, {'type': 'drill', 'drill_point_angle': 118.0,
                               'flute_length': 2.0})
    registerPlugin('tooltable', plugin)

    from qtpyvcp.widgets.display_widgets.vtk_backplot import tool_actor
    from qtpyvcp.lib.db_tool.insert_profile import (insert_record,
                                                    compute_insert_profile,
                                                    holder_style_code)

    # ---- record composition (schema-named, typed)
    core4 = plugin.getToolTable()[4]
    record4 = insert_record(core4, plugin.getToolExtras(4))
    expect('record carries schema-named insert fields',
           record4['insert_shape'] == 'V' and record4['insert_size'] == 0.375)
    expect('nose radius derived per plan §5.1 (D/2 for turning family)',
           abs(record4['nose_radius'] - 0.03125) < 1e-9)
    expect('ISO holder code reduces to its style letter (SVJBR -> j)',
           holder_style_code(record4) == 'j')

    profile4 = compute_insert_profile(record4)
    expect('DB-native pipeline renders the V-style insert (family = the '
           'ISO style key, as downstream orientation logic expects)',
           profile4.get('family') == 'v'
           and len(profile4.get('insert_polygon_xz') or []) >= 3)

    # ---- tool_actor resolution against the live plugin
    class _FakeStat:
        tool_in_spindle = 4

    class _FakeStatus:
        stat = _FakeStat()

    class _FakeDataSource:
        _status = _FakeStatus()

    rec = tool_actor._resolve_active_insert_record(None, _FakeDataSource())
    expect('tool_actor resolves the in-spindle tool record from the DB '
           'plugin', isinstance(rec, dict) and rec['tool_no'] == 4)

    drill_record = insert_record(plugin.getToolTable()[20],
                                 plugin.getToolExtras(20))
    drill_profile = compute_insert_profile(drill_record)
    expect('drill renders as a drill with its diameter unhalved',
           drill_profile.get('family') == 'drill'
           and abs(drill_profile['dimensions'].get('diameter', 0) - 0.25)
           < 1e-9)

    # ---- the tool-4 regression: a bad nose radius must change VTK's
    # polygon too (same store as QML -- visibly wrong in both, immediately)
    table = plugin.getToolTable()
    table[4]['D'] = 0.625  # the typo: 0.3125 radius on a 3/8 IC insert
    plugin.saveToolTable(table)
    bad_profile = compute_insert_profile(
        insert_record(plugin.getToolTable()[4], plugin.getToolExtras(4)))
    expect('a bad nose-radius entry changes the VTK-side polygon (no '
           'stale-source rendering possible)',
           bad_profile.get('insert_polygon_xz')
           != profile4.get('insert_polygon_xz'))

    # ---- no DB plugin -> no record (generic tool marker path)
    class _NoStat:
        tool_in_spindle = 0

    class _NoStatus:
        stat = _NoStat()

    class _NoToolSource:
        _status = _NoStatus()

    expect('no active tool resolves to None (generic marker fallback)',
           tool_actor._resolve_active_insert_record(None, _NoToolSource())
           is None)

    # ---- the fusion purge is total
    actor_src = open(tool_actor.__file__.replace('.pyc', '.py')).read().lower()
    geom_path = os.path.join(QTPYVCP_SRC, 'qtpyvcp', 'lib',
                             'lathe_insert_geometry.py')
    profile_path = os.path.join(QTPYVCP_SRC, 'qtpyvcp', 'lib', 'db_tool',
                                'insert_profile.py')
    expect('zero fusion references anywhere in the VTK insert pipeline',
           'fusion' not in actor_src
           and 'fusion' not in open(geom_path).read().lower()
           and 'fusion' not in open(profile_path).read().lower())

    for suffix in ('', '-wal', '-shm'):
        p = db + suffix
        if os.path.exists(p):
            os.remove(p)

    print()
    print('ALL CHECKS PASSED' if not failures else 'FAILURES: %s' % failures)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
