"""Database Tool Table plugin.

DB-backed drop-in for the file-based ``tooltable`` plugin. The SQLite
database is shared with the LinuxCNC-spawned db_program (tooldb protocol,
see ``qtpyvcp.tools.tool_db_backend``); this plugin is the GUI-process side.

Sync model (both directions, no file involved):

* UI -> machine: :meth:`saveToolTable` commits to the DB, then issues an NML
  ``load_tool_table()`` so LinuxCNC re-requests all tools from the
  db_program. If the interpreter is running the reload is deferred until it
  returns to IDLE (LinuxCNC rejects pushes while running).
* machine -> UI: touch-off (G10 L1/L10/L11) updates LinuxCNC internally and
  is pushed to the db_program, which commits to the DB; this plugin watches
  ``status:tool_table`` and reloads from the DB so the screen follows.

The database path comes from the INI (single source shared with the
db_program): the first argument of ``[EMCIO] DB_PROGRAM``, else
``<config dir>/tool_table.db``.

YAML configuration:

.. code-block:: yaml

    data_plugins:
      tooltable:
        provider: qtpyvcp.plugins.db_tool_table:DBToolTable
        kwargs:
          columns: TPXZDIJQR
"""

import os

import linuxcnc

from PySide6.QtCore import QTimer, Signal

from qtpyvcp.lib.db_tool.base import (Session, Base, configure_database,
                                      get_engine)
from qtpyvcp.lib.db_tool.tool_table import ToolTable, Tool

from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import DataPlugin, DataChannel, getPlugin

LOG = getLogger(__name__)
IN_DESIGNER = os.getenv('DESIGNER', False)

STATUS = None
STAT = None
if not IN_DESIGNER:
    STATUS = getPlugin('status')
    STAT = STATUS.stat if STATUS is not None else None

INFO = Info()

try:
    CMD = linuxcnc.command()
except Exception:  # not running under LinuxCNC (Designer, tests, docs)
    CMD = None


def merge(a, b):
    """Shallow merge two dictionaries"""
    r = a.copy()
    r.update(b)
    return r


DEFAULT_TOOL = {
    'A': 0.0,
    'B': 0.0,
    'C': 0.0,
    'D': 0.0,
    'I': 0.0,
    'J': 0.0,
    'P': -1,
    'Q': 0,
    'T': -1,
    'U': 0.0,
    'V': 0.0,
    'W': 0.0,
    'X': 0.0,
    'Y': 0.0,
    'Z': 0.0,
    'R': '',
}

NO_TOOL = merge(DEFAULT_TOOL, {'T': 0, 'R': 'No Tool Loaded'})

COLUMN_LABELS = {
    'A': 'A Offset',
    'B': 'B Offset',
    'C': 'C Offset',
    'D': 'Diameter',
    'I': 'Fnt Ang',
    'J': 'Bak Ang',
    'P': 'Pocket',
    'Q': 'Orient',
    'R': 'Remark',
    'T': 'Tool',
    'U': 'U Offset',
    'V': 'V Offset',
    'W': 'W Offset',
    'X': 'X Offset',
    'Y': 'Y Offset',
    'Z': 'Z Offset',
}

# (letter, Tool model attribute) — single source for both directions.
LETTER_ATTRS = (
    ('T', 'tool_no'),
    ('P', 'pocket'),
    ('X', 'x_offset'),
    ('Y', 'y_offset'),
    ('Z', 'z_offset'),
    ('A', 'a_offset'),
    ('B', 'b_offset'),
    ('C', 'c_offset'),
    ('U', 'u_offset'),
    ('V', 'v_offset'),
    ('W', 'w_offset'),
    ('D', 'diameter'),
    ('I', 'i_offset'),
    ('J', 'j_offset'),
    ('Q', 'q_offset'),
    ('R', 'remark'),
)

INT_LETTERS = ('T', 'P', 'Q')


def _default_db_path():
    """DB path from the INI (DB_PROGRAM first arg), else config dir default.

    Kept in sync with tool_db_backend.resolve_db_path(): both processes must
    open the same file.
    """
    config_dir = getattr(INFO, 'CONFIG_DIR', None) or os.getcwd()

    db_program = None
    try:
        db_program = INFO.ini.find('EMCIO', 'DB_PROGRAM')
    except Exception:
        pass

    if db_program:
        args = str(db_program).split()[1:]  # drop the program itself
        for arg in args:
            if arg.lower() in ('debug', '-d', '--debug'):
                continue
            if not os.path.isabs(arg):
                arg = os.path.join(config_dir, arg)
            return os.path.abspath(os.path.expanduser(arg))

    return os.path.join(config_dir, 'tool_table.db')


class DBToolTable(DataPlugin):

    TOOL_TABLE = {0: NO_TOOL}
    DEFAULT_TOOL = DEFAULT_TOOL
    COLUMN_LABELS = COLUMN_LABELS

    # NOTE: must be Signal(object), not Signal(dict). PySide marshals a
    # `dict`-typed signal through QVariantMap, which requires string keys;
    # this table is keyed by integer tool number, so a Signal(dict) here
    # silently delivers an EMPTY dict to every connected slot (confirmed
    # via direct PySide6 repro). Signal(object) passes the Python dict
    # through untouched. Matches qtpyvcp.plugins.tool_table.ToolTable,
    # which uses Signal(object) for the identical reason.
    tool_table_changed = Signal(object)

    def __init__(self, columns='TPXZDIJQR', db_file=None, **kwargs):
        super(DBToolTable, self).__init__()

        self.columns = self.validateColumns(columns) or [c for c in 'TPXZDIJQR']
        self.db_file = db_file
        self._pending_reload = False
        self._refresh_scheduled = False

    # ------------------------------------------------------------ lifecycle

    def initialise(self):
        db_path = self.db_file or _default_db_path()
        LOG.info("Tool database: %s", db_path)
        configure_database(db_path)
        Base.metadata.create_all(get_engine())

        self.loadToolTable()

        if STATUS is not None:
            # machine -> UI: touch-off etc. lands in the DB via the
            # db_program; the status channel tells us when to re-read it.
            STATUS.tool_table.notify(self._onMachineToolTableChanged)
            STATUS.tool_in_spindle.notify(self.setCurrentToolNumber)
            # flush a deferred UI -> machine reload once the interp is idle
            STATUS.interp_state.notify(self._onInterpStateChanged)

    def terminate(self):
        pass  # no held sessions

    # ------------------------------------------------------------ channels

    @DataChannel
    def current_tool(self, chan, item=None):
        """Current Tool Info

        Available items: T, P, X, Y, Z, A, B, C, U, V, W, I, J, Q, R

        Rules channel syntax::

            tooltable:current_tool
            tooltable:current_tool?X
        """
        tool_no = STAT.tool_in_spindle if STAT is not None else 0
        tool = self.TOOL_TABLE.get(tool_no, NO_TOOL)
        if item is None:
            return tool
        return tool.get(item[0].upper())

    # ------------------------------------------------------------ helpers

    @staticmethod
    def validateColumns(columns):
        """Validate display column specification.

        Args:
            columns (str | list) : column IDs to show in the tool table.

        Returns:
            None if not valid, else a list of uppercase column IDs.
        """
        if not isinstance(columns, (str, list, tuple)):
            return

        return [col for col in [col.strip().upper() for col in columns]
                if col in 'TPXYZABCUVWDIJQR' and not col == '']

    def newTool(self, tnum=None):
        """Get a dict of default tool values for a new tool."""
        if tnum is None:
            tnum = max(self.TOOL_TABLE) + 1 if self.TOOL_TABLE else 1
        new_tool = DEFAULT_TOOL.copy()
        new_tool.update({'T': tnum, 'R': 'New Tool'})
        return new_tool

    def setCurrentToolNumber(self, tool_num):
        try:
            self.current_tool.setValue(
                self.TOOL_TABLE.get(int(tool_num), NO_TOOL))
        except (TypeError, ValueError):
            pass

    @staticmethod
    def _tool_to_dict(tool):
        tool_dict = {}
        for letter, attr in LETTER_ATTRS:
            value = getattr(tool, attr, None)
            if letter == 'R':
                tool_dict[letter] = value or ''
            elif letter in INT_LETTERS:
                tool_dict[letter] = int(value or 0)
            else:
                tool_dict[letter] = float(value or 0.0)
        return tool_dict

    @staticmethod
    def _apply_dict_to_tool(tool, tool_dict):
        for letter, attr in LETTER_ATTRS:
            if letter not in tool_dict:
                continue
            value = tool_dict[letter]
            if letter == 'R':
                setattr(tool, attr, str(value or ''))
            elif letter in INT_LETTERS:
                setattr(tool, attr, int(value or 0))
            else:
                setattr(tool, attr, float(value or 0.0))

    # ------------------------------------------------------------ load

    def reloadToolTable(self):
        self.loadToolTable()

    def loadToolTable(self):
        """Re-read the tool table from the database and notify consumers."""
        session = Session()
        try:
            tools = session.query(Tool).order_by(Tool.tool_no).all()
            table = {0: NO_TOOL}
            for tool in tools:
                if tool.tool_no is None:
                    continue
                table[int(tool.tool_no)] = self._tool_to_dict(tool)
        except Exception:
            LOG.exception("Tool DB read failed; keeping previous tool table")
            return
        finally:
            session.close()

        if len(table) <= 1 and len(self.TOOL_TABLE) > 1:
            # a populated table never legitimately collapses to empty between
            # two reads; treat as a read anomaly, keep showing current data
            LOG.warning("Tool DB read returned no tools (had %d); keeping "
                        "previous tool table. db=%s",
                        len(self.TOOL_TABLE) - 1, get_engine().url)
            return

        LOG.debug("Reloaded %d tools from %s",
                  len(table) - 1, get_engine().url)

        self.TOOL_TABLE = table
        if STAT is not None:
            self.setCurrentToolNumber(STAT.tool_in_spindle)

        self.tool_table_changed.emit(table.copy())

    def getToolTable(self):
        return self.TOOL_TABLE.copy()

    # ------------------------------------------------------------ save

    def saveToolTable(self, tool_table, columns=None):
        """Write tool table data to the DB and sync LinuxCNC.

        Args:
            tool_table (dict) : dict of tool dicts keyed by tool number.
            columns : accepted for interface compat; the DB always stores
                all columns.
        """
        del columns

        session = Session()
        try:
            table_row = session.query(ToolTable).first()
            if table_row is None:
                table_row = ToolTable(name='Tool Table')
                session.add(table_row)
                session.flush()

            existing = {int(t.tool_no): t
                        for t in session.query(Tool).all()
                        if t.tool_no is not None}

            wanted = {int(tnum): tdata
                      for tnum, tdata in tool_table.items()
                      if int(tnum) != 0}  # T0 = no tool, never stored

            # upsert
            for tnum, tdata in wanted.items():
                tool = existing.get(tnum)
                if tool is None:
                    tool = Tool(tool_no=tnum, in_use=0,
                                tool_table_id=table_row.id)
                    session.add(tool)
                self._apply_dict_to_tool(tool, tdata)

            # delete removed tools
            for tnum, tool in existing.items():
                if tnum not in wanted:
                    session.delete(tool)

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        self.loadToolTable()
        self._request_machine_reload()

    # ------------------------------------------------------------ sync

    def _request_machine_reload(self):
        """Ask LinuxCNC to re-request tools from the db_program (NML).

        Deferred until the interpreter is idle -- LinuxCNC rejects tool data
        pushes while a program is running.
        """
        if CMD is None or STAT is None:
            return

        STAT.poll()
        if STAT.interp_state == linuxcnc.INTERP_IDLE:
            LOG.debug("Issuing load_tool_table()")
            self._pending_reload = False
            CMD.load_tool_table()
        else:
            LOG.info("Interp not idle: tool table reload deferred")
            self._pending_reload = True

    def _onInterpStateChanged(self, interp_state):
        if interp_state != linuxcnc.INTERP_IDLE:
            return

        if self._pending_reload:
            self._pending_reload = False
            LOG.debug("Interp idle: issuing deferred load_tool_table()")
            CMD.load_tool_table()

        # every machine-side tool change (touch-off sub, MDI G10, M61,
        # program) runs through the interp, so returning to IDLE is a
        # reliable "tool data may have changed" signal -- refresh from the
        # DB even if the status:tool_table channel missed the change.
        self._schedule_refresh("interp idle")

    def _onMachineToolTableChanged(self, *args, **kwargs):
        """LinuxCNC's in-memory table changed (touch-off, reload, ...)."""
        self._schedule_refresh("status:tool_table changed")

    def _schedule_refresh(self, reason):
        """Debounced DB re-read: coalesces bursts and gives the db_program's
        commit time to land before we query."""
        if self._refresh_scheduled:
            return
        self._refresh_scheduled = True
        LOG.debug("Scheduling tool table re-read (%s)", reason)

        def _do_refresh():
            self._refresh_scheduled = False
            self.loadToolTable()

        QTimer.singleShot(200, _do_refresh)
