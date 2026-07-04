#!/usr/bin/env python3
"""LinuxCNC tool database program (tooldb protocol v2.1) backed by SQLite.

Configured in the INI; the database path is the first argument so the GUI
plugin and this program share one file (single source of truth):

    [EMCIO]
    DB_PROGRAM = tool_db_backend /path/to/machine/config/tool_table.db

Falls back to $CONFIG_DIR/tool_table.db, then legacy ./db.sqlite.
Pass ``debug`` as a later argument for verbose stderr logging (LinuxCNC's
DB_DEBUG environment variable is honored as well).

Protocol notes (docs/src/tooldatabase/tooldatabase.adoc):
  - 'g'  get all tools: one tool-table-format line per tool, FINI-terminated.
  - 'p'  put: LinuxCNC pushes a full tool line after G10 L1/L10/L11.
  - 'l'/'u'  spindle load/unload: T and P only; maintains tool.in_use.
The tool list registered with tooldb_tools() is a live view that re-queries
the database on every iteration, so tools added/removed by the GUI are
visible to LinuxCNC at the next 'g' (G10 L0 or load_tool_table()) without
restarting this program.
"""

import os
import re
import sys

import tooldb as _tooldb
from tooldb import tooldb_callbacks  # functions (g,p,l,u)
from tooldb import tooldb_tools      # list of tool numbers

from qtpyvcp.lib.db_tool.base import Base, Session, configure_database, get_engine
from qtpyvcp.lib.db_tool.tool_table import Tool, ToolTable, ToolModel
from qtpyvcp.lib.db_tool.migrate import run_migrations

DEBUG = bool(os.getenv('DB_DEBUG'))

TOKEN_RE = re.compile(r'([TPXYZABCUVWDIJQ])\s*([-+]?[0-9.]+)')

# Tool model columns keyed by tool-table letter (schema v1).
LETTER_TO_ATTR = {
    'T': 'tool_no',
    'P': 'pocket',
    'X': 'x_offset',
    'Y': 'y_offset',
    'Z': 'z_offset',
    'A': 'a_offset',
    'B': 'b_offset',
    'C': 'c_offset',
    'U': 'u_offset',
    'V': 'v_offset',
    'W': 'w_offset',
    'D': 'diameter',
    'I': 'front_angle',
    'J': 'back_angle',
    'Q': 'orientation',
}

INT_LETTERS = ('T', 'P', 'Q')


def log(msg):
    sys.stderr.write('tool_db_backend: %s\n' % msg)
    sys.stderr.flush()


def dbg(msg):
    if DEBUG:
        log(msg)


def resolve_db_path(argv):
    """First non-flag argument wins; then $CONFIG_DIR; then legacy CWD file."""
    for arg in argv[1:]:
        if arg.lower() in ('debug', '-d', '--debug'):
            continue
        return os.path.abspath(os.path.expanduser(arg))
    config_dir = os.getenv('CONFIG_DIR')
    if config_dir:
        return os.path.join(os.path.abspath(os.path.expanduser(config_dir)),
                            'tool_table.db')
    return os.path.abspath('db.sqlite')


def fmt_num(value):
    return ('%.6f' % float(value or 0.0)).rstrip('0').rstrip('.') or '0'


class LiveToolNumbers:
    """Sequence of tool numbers that re-queries the DB on every use.

    tooldb's get_cmd iterates (and tool_cmd membership-tests) the registered
    list at command time, so this makes GUI-side add/remove visible without
    restarting the backend.
    """

    def _numbers(self):
        session = Session()
        try:
            rows = session.query(Tool.tool_no).order_by(Tool.tool_no).all()
            return [int(r[0]) for r in rows if r[0] is not None]
        finally:
            session.close()

    def __iter__(self):
        return iter(self._numbers())

    def __contains__(self, tool_no):
        try:
            return int(tool_no) in self._numbers()
        except (TypeError, ValueError):
            return False

    def __len__(self):
        return len(self._numbers())


class DataBaseManager(object):

    def __init__(self):
        self.spindle_tool_no = None

        tooldb_tools(LiveToolNumbers())
        tooldb_callbacks(self.user_get_tool,
                         self.user_put_tool,
                         self.user_load_spindle,
                         self.user_unload_spindle)

    # ------------------------------------------------------------ g
    def user_get_tool(self, tool_no):
        dbg('GET tool %s' % tool_no)
        session = Session()
        try:
            tool = session.query(Tool).filter(
                Tool.tool_no == int(tool_no)).one()
            parts = [
                'T%d' % int(tool.tool_no),
                'P%d' % int(tool.pocket or 0),
                'X%s' % fmt_num(tool.x_offset),
                'Y%s' % fmt_num(tool.y_offset),
                'Z%s' % fmt_num(tool.z_offset),
            ]
            # secondary axes only when set (keeps lathe lines readable)
            for letter in ('A', 'B', 'C', 'U', 'V', 'W'):
                val = getattr(tool, LETTER_TO_ATTR[letter], None)
                if val:
                    parts.append('%s%s' % (letter, fmt_num(val)))
            parts.append('D%s' % fmt_num(tool.diameter))
            parts.append('I%s' % fmt_num(tool.front_angle))
            parts.append('J%s' % fmt_num(tool.back_angle))
            parts.append('Q%d' % int(tool.orientation or 0))
            remark = (tool.remark or '').strip()
            line = ' '.join(parts)
            if remark:
                line += ' ;%s' % remark
            return line
        finally:
            session.close()

    # ------------------------------------------------------------ p
    def user_put_tool(self, tool_no, params):
        dbg('PUT tool %s <%s>' % (tool_no, params))
        # params is the full tool line, uppercased by tooldb; the remark
        # (after ';') is NOT updated here -- G10 does not change remarks.
        body = params.split(';', 1)[0]
        updates = {}
        for letter, raw in TOKEN_RE.findall(body):
            attr = LETTER_TO_ATTR.get(letter)
            if attr is None:
                continue
            updates[attr] = int(float(raw)) if letter in INT_LETTERS else float(raw)

        session = Session()
        try:
            tool = session.query(Tool).filter(
                Tool.tool_no == int(tool_no)).one_or_none()
            if tool is None:
                raise LookupError('tool %s not in database' % tool_no)
            for attr, value in updates.items():
                setattr(tool, attr, value)
            session.commit()
        finally:
            session.close()

    # ------------------------------------------------------------ l / u
    def user_load_spindle(self, tool_no, params):
        dbg('LOAD SPINDLE %s <%s>' % (tool_no, params))
        self._set_in_use(int(tool_no))

    def user_unload_spindle(self, tool_no, params):
        dbg('UNLOAD SPINDLE %s <%s>' % (tool_no, params))
        self._set_in_use(None)

    def _set_in_use(self, tool_no):
        session = Session()
        try:
            session.query(Tool).filter(Tool.in_use == 1).update(
                {Tool.in_use: 0})
            if tool_no:
                session.query(Tool).filter(Tool.tool_no == tool_no).update(
                    {Tool.in_use: 1})
            session.commit()
            self.spindle_tool_no = tool_no
        finally:
            session.close()


def serve_forever():
    """tooldb_loop with a clean EOF exit.

    Upstream tooldb_loop never returns when stdin reaches EOF (readline()
    yields '' forever), leaving an orphaned backend busy-looping if LinuxCNC
    exits. This reuses tooldb's protocol machinery but shuts down instead.
    """
    _tooldb.startup_ack()
    while True:
        try:
            raw = sys.stdin.readline()
            if raw == '':  # EOF: host closed the pipe
                log('stdin closed (host exited) - shutting down')
                return
            line = raw.strip()
            _tooldb.saveline(line)
            if line == '':
                _tooldb.nak_reply('empty_line')
            else:
                _tooldb.do_cmd(line)
        except BrokenPipeError:
            log('stdout pipe broken (host exited) - shutting down')
            return
        except Exception as exc:
            _tooldb.nak_reply('_exception=%s' % exc)


def main():
    global DEBUG
    if any(a.lower() in ('debug', '-d', '--debug') for a in sys.argv[1:]):
        DEBUG = True

    db_path = resolve_db_path(sys.argv)
    log('database: %s' % db_path)
    configure_database(db_path)
    run_migrations(get_engine())
    # ToolTable/ToolModel (mill per-tool STL reference) aren't part of the
    # versioned lathe schema; create them here if absent, same as the GUI
    # plugin, so either process can be first to touch a fresh DB file.
    Base.metadata.create_all(get_engine(), tables=[
        ToolTable.__table__, ToolModel.__table__])

    DataBaseManager()

    try:
        serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception as exc:  # never die silently: LinuxCNC loses all tools
        log('FATAL: %s' % exc)
        raise


if __name__ == '__main__':
    main()
