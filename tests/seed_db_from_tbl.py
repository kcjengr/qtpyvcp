#!/usr/bin/env python3
"""Quick-seed a schema-v1 tool database from a LinuxCNC .tbl file.

Usage:
    python3 seed_db_from_tbl.py [tbl_file] [db_file]

Defaults to the Probe Basic lathe sim config:
    tbl: ~/dev/probe_basic/configs/probe_basic_lathe/lathe.tbl
    db:  ~/dev/probe_basic/configs/probe_basic_lathe/tool_table.db

Note: D values are imported VERBATIM (no radius/diameter conversion, no
tool_lathe extras). For the ratified D = diameter conversion (plan §5.1) and
real lathe-extras data, use pb_lathe_conv's
docs/schema_v1/generate_seed.py -> seed.sql instead; this script is a quick,
core-columns-only seed for backend/protocol testing.
"""

import os
import sys

sys.path.insert(0, os.path.expanduser('~/dev/qtpyvcp/src'))

from qtpyvcp.lib.db_tool.base import Session, configure_database, get_engine
from qtpyvcp.lib.db_tool.tool_table import Tool
from qtpyvcp.lib.db_tool.migrate import run_migrations

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
            'front_angle': float(tokens.get('I', 0.0)),
            'back_angle': float(tokens.get('J', 0.0)),
            'orientation': int(float(tokens.get('Q', 0))),
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
    run_migrations(get_engine())
    session = Session()
    for row in rows:
        session.add(Tool(**row))
    session.commit()
    session.close()

    print('seeded %d tools from %s into %s' % (len(rows), tbl, db))
    return 0


if __name__ == '__main__':
    sys.exit(main())
