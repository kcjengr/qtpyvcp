#!/usr/bin/env python3
"""Seed a tool database from a LinuxCNC .tbl file (Phase 1 spike).

Usage:
    python3 seed_db_from_tbl.py [tbl_file] [db_file]

Defaults to the Probe Basic lathe sim config:
    tbl: ~/dev/probe_basic/configs/probe_basic_lathe/lathe.tbl
    db:  ~/dev/probe_basic/configs/probe_basic_lathe/tool_table.db

Note: D values are imported VERBATIM. The ratified D = diameter convention
(plan §5.1) is applied by the real Phase 7 bootstrap wizard, which knows each
tool's type (radius-doubling applies to turning-family tools only, and type
is not derivable from a bare .tbl). For the Phase 1 gate demo the D semantics
are irrelevant — the gate exercises offsets, touch-off, and add/delete.
"""

import os
import re
import sys

sys.path.insert(0, os.path.expanduser('~/dev/qtpyvcp/src'))

from qtpyvcp.lib.db_tool.base import (Session, Base, configure_database,
                                      get_engine)
from qtpyvcp.lib.db_tool.tool_table import ToolTable, Tool

DEFAULT_TBL = os.path.expanduser(
    '~/dev/probe_basic/configs/probe_basic_lathe/lathe.tbl')
DEFAULT_DB = os.path.expanduser(
    '~/dev/probe_basic/configs/probe_basic_lathe/tool_table.db')


def parse_tbl(path):
    rows = []
    for line in open(path):
        line = line.strip()
        if not line or line.startswith(';'):
            continue
        body, _, remark = line.partition(';')
        tokens = {}
        for tok in body.split():
            tokens[tok[0].upper()] = tok[1:]
        if 'T' not in tokens:
            continue
        rows.append({
            'tool_no': int(float(tokens['T'])),
            'pocket': int(float(tokens.get('P', -1))),
            'x_offset': float(tokens.get('X', 0.0)),
            'y_offset': float(tokens.get('Y', 0.0)),
            'z_offset': float(tokens.get('Z', 0.0)),
            'a_offset': 0.0, 'b_offset': 0.0, 'c_offset': 0.0,
            'u_offset': 0.0, 'v_offset': 0.0, 'w_offset': 0.0,
            'diameter': float(tokens.get('D', 0.0)),
            'i_offset': float(tokens.get('I', 0.0)),
            'j_offset': float(tokens.get('J', 0.0)),
            'q_offset': int(float(tokens.get('Q', 0))),
            'in_use': 0,
            'remark': remark.strip(),
        })
    return rows


def main():
    tbl = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TBL
    db = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_DB

    if os.path.exists(db):
        print('refusing to overwrite existing %s (delete it first)' % db)
        return 1

    rows = parse_tbl(tbl)

    configure_database(db)
    Base.metadata.create_all(get_engine())
    session = Session()
    table = ToolTable(name='Lathe Tool Table')
    session.add(table)
    session.flush()
    for row in rows:
        session.add(Tool(tool_table_id=table.id, **row))
    session.commit()
    session.close()

    print('seeded %d tools from %s into %s' % (len(rows), tbl, db))
    return 0


if __name__ == '__main__':
    sys.exit(main())
