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
          extras: lathe    # which per-machine extras table this config
                           # serves: 'lathe' (tool_lathe, the default) or
                           # 'mill' (tool_mill, schema v3)
"""

import os
import re
import shutil
import time

import linuxcnc

from PySide6.QtCore import QTimer, Signal

from qtpyvcp.lib.db_tool.base import Base, Session, configure_database, get_engine
from qtpyvcp.lib.db_tool.tool_table import (Tool, ToolTable, ToolModel,
                                            ToolLathe, ToolMill,
                                            CustomFieldDef,
                                            CustomFieldValue, VisibleColumn,
                                            Meta)
from qtpyvcp.lib.db_tool.migrate import run_migrations

CUSTOM_FIELD_VALUE_TYPES = ('float', 'int', 'text', 'bool')

# Per-machine extras table this plugin instance serves ('extras' kwarg):
# (ORM model, Tool relationship attribute). One flavor per config -- the
# widget promoted in that config's .ui (LatheToolTable/MillToolTable) must
# match, it renders these columns by name.
EXTRAS_TABLES = {
    'lathe': (ToolLathe, 'lathe'),
    'mill': (ToolMill, 'mill'),
}

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
    ('I', 'front_angle'),
    ('J', 'back_angle'),
    ('Q', 'orientation'),
    ('R', 'remark'),
)

INT_LETTERS = ('T', 'P', 'Q')


def _default_db_path():
    """DB path from the INI: [EMCIO] TOOL_DB_FILE if set, else a DB_PROGRAM
    argument (legacy convention -- some db_program scripts take the path as
    a CLI arg), else config dir default.

    Kept in sync with tool_db.sh's own INI lookup and
    tool_db_backend.resolve_db_path(): all must agree on the same file, or
    the GUI and the LinuxCNC-spawned backend silently disagree about which
    database is "live". TOOL_DB_FILE is the documented way to name/swap
    tool database files (backups, per-job variants, ...) without touching
    DB_PROGRAM itself -- switch which one is active by changing this one
    line and restarting; nothing is "the" database except by this explicit
    reference, so nothing can be clobbered by picking a different name.
    """
    config_dir = getattr(INFO, 'CONFIG_DIR', None) or os.getcwd()

    def _resolve(value):
        if not os.path.isabs(value):
            value = os.path.join(config_dir, value)
        return os.path.abspath(os.path.expanduser(value))

    def _strip_inline_comment(value):
        # ini.find() returns the raw rest of the line -- it does no comment
        # handling itself. Strip a trailing "# ..." the same way tool_db.sh's
        # own ini_get does, so a config author who annotates a line (quite
        # likely once they're naming multiple backup/variant files) can't
        # produce a value here that disagrees with what the LinuxCNC-spawned
        # backend actually opens.
        return re.sub(r'\s*#.*$', '', value).strip()

    try:
        tool_db_file = INFO.ini.find('EMCIO', 'TOOL_DB_FILE')
    except Exception:
        tool_db_file = None
    if tool_db_file:
        tool_db_file = _strip_inline_comment(str(tool_db_file))
        if tool_db_file:
            return _resolve(tool_db_file)

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
            return _resolve(arg)

    return os.path.join(config_dir, 'tool_table.db')


_EMCIO_SECTION_RE = re.compile(r'^\s*\[EMCIO\]\s*$')
_SECTION_RE = re.compile(r'^\s*\[')
_TOOL_DB_FILE_KEY_RE = re.compile(r'^\s*TOOL_DB_FILE\s*=')
_DB_PROGRAM_KEY_RE = re.compile(r'^\s*DB_PROGRAM\s*=')


def set_tool_db_file(ini_path, db_path):
    """Write/update [EMCIO] TOOL_DB_FILE in ini_path so it points at
    db_path, as the write-side counterpart of _default_db_path() -- same
    section, same key, so a value written here is guaranteed to be read
    back identically by both the GUI and tool_db.sh.

    A surgical line-level edit, NOT a generic ini-parser rewrite: every
    other line in the file (including every comment, which these configs
    carry heavily) is left byte-for-byte untouched. Existing TOOL_DB_FILE
    line gets replaced in place; otherwise a new one is inserted right
    after DB_PROGRAM (or after the [EMCIO] header if DB_PROGRAM isn't
    found) so the two lines that determine "which database is live" stay
    visually adjacent, matching the documented convention.

    Writes db_path as a bare filename when it lives directly in the same
    directory as the ini file (the common case, and the cleanest to read),
    else as a full absolute path.

    Backs up ini_path first (this edits a file LinuxCNC reads at machine
    startup) -- same pattern as migrate.py's pre-migration db backup.
    Returns (action, backup_path) where action is 'replaced' or 'inserted'.
    """
    ini_path = os.path.abspath(os.path.expanduser(ini_path))
    if not os.path.isfile(ini_path):
        raise FileNotFoundError("INI file not found: %s" % ini_path)

    ini_dir = os.path.dirname(ini_path)
    db_path = os.path.abspath(os.path.expanduser(db_path))
    if os.path.dirname(db_path) == ini_dir:
        value = os.path.basename(db_path)
    else:
        value = db_path

    with open(ini_path, 'r') as fh:
        lines = fh.readlines()

    backup_path = '%s.pre-tool-db-file-edit-%s.bak' % (
        ini_path, time.strftime('%Y%m%d-%H%M%S'))
    shutil.copy2(ini_path, backup_path)

    new_line = 'TOOL_DB_FILE = %s\n' % value

    in_emcio = False
    emcio_start = None
    replace_idx = None
    db_program_idx = None
    for idx, line in enumerate(lines):
        if _EMCIO_SECTION_RE.match(line):
            in_emcio = True
            emcio_start = idx
            continue
        if in_emcio and _SECTION_RE.match(line):
            break  # next section -- stop scanning
        if in_emcio and _TOOL_DB_FILE_KEY_RE.match(line):
            replace_idx = idx
            break
        if in_emcio and _DB_PROGRAM_KEY_RE.match(line):
            db_program_idx = idx

    if emcio_start is None:
        raise ValueError("No [EMCIO] section found in %s" % ini_path)

    if replace_idx is not None:
        lines[replace_idx] = new_line
        action = 'replaced'
    else:
        insert_at = (db_program_idx + 1) if db_program_idx is not None else (emcio_start + 1)
        lines.insert(insert_at, new_line)
        action = 'inserted'

    with open(ini_path, 'w') as fh:
        fh.writelines(lines)

    return action, backup_path


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

    # Per-tool/extras/custom-field change signals (plan §6 Phase 2). Narrower
    # than tool_table_changed: a widget interested in only one tool's extras,
    # or only the set of custom columns, doesn't need to re-render on every
    # core-table reload.
    tool_changed = Signal(int)     # tool_no whose core row was added/edited/removed
    extras_changed = Signal(int)   # tool_no whose tool_lathe row changed
    fields_changed = Signal()      # a custom_field_def or *_value changed

    def __init__(self, columns='TPXZDIJQR', db_file=None, extras='lathe',
                 **kwargs):
        super(DBToolTable, self).__init__()

        self.columns = self.validateColumns(columns) or [c for c in 'TPXZDIJQR']
        self.db_file = db_file
        try:
            self._extras_model, self._extras_attr = EXTRAS_TABLES[extras]
        except KeyError:
            raise ValueError("invalid extras %r (must be one of %s)"
                             % (extras, ', '.join(sorted(EXTRAS_TABLES))))
        self._EXTRAS_COLUMNS = [c.name for c in self._extras_model.__table__.columns
                                if c.name != 'tool_id']
        self._pending_reload = False
        self._refresh_scheduled = False

        # Composed record served by the current_tool channel: core letters
        # + extras (bare column names) + custom values ('custom:<name>').
        # Cached and refreshed on change signals rather than recomposed on
        # every channel read -- Rules expressions poll getValue() freely.
        self._current_tool_no = 0
        self._current_tool_record = dict(NO_TOOL)
        self.tool_table_changed.connect(self._refreshCurrentToolRecord)
        self.fields_changed.connect(self._refreshCurrentToolRecord)
        self.extras_changed.connect(self._onExtrasChangedRefreshCurrent)

    # ------------------------------------------------------------ lifecycle

    def initialise(self):
        db_path = self.db_file or _default_db_path()
        LOG.info("Tool database: %s", db_path)
        configure_database(db_path)
        run_migrations(get_engine())
        # ToolTable/ToolModel (mill per-tool STL reference) aren't part of the
        # versioned lathe schema; create them here if absent (no-op once they
        # exist -- create_all checks first).
        Base.metadata.create_all(get_engine(), tables=[
            ToolTable.__table__, ToolModel.__table__])

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

        The full composed record for the tool in the spindle: core columns
        (letter keys), lathe extras (their column names), and custom
        columns ('custom:' + machine key). Refreshed on tool change and on
        every table/extras/custom edit.

        Rules channel syntax::

            tooltable:current_tool
            tooltable:current_tool?X
            tooltable:current_tool?groove_width
            tooltable:current_tool?custom:coating

        Single-letter core items keep their historical behavior (anything
        starting with the letter works: ?X, ?xoffset); extras/custom items
        must match the machine key exactly.
        """
        record = self._current_tool_record
        if item is None:
            return record
        if item in record:
            return record[item]
        return record.get(item[0].upper())

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
            self._current_tool_no = int(tool_num)
        except (TypeError, ValueError):
            return
        self._refreshCurrentToolRecord()

    def _onExtrasChangedRefreshCurrent(self, tool_no):
        # extras_changed fires once per tool in a batch save; only the
        # current tool's row affects the channel record.
        if int(tool_no) == self._current_tool_no:
            self._refreshCurrentToolRecord()

    def _refreshCurrentToolRecord(self, *_args):
        """*_args: connected to signals with varying payloads
        (tool_table_changed passes the table dict, fields_changed nothing);
        the payload is never needed -- the record recomposes from the DB."""
        self._current_tool_record = self._composeCurrentToolRecord()
        self.current_tool.setValue(self._current_tool_record)

    def _composeCurrentToolRecord(self):
        tool_no = self._current_tool_no
        record = dict(self.TOOL_TABLE.get(tool_no, NO_TOOL))
        if tool_no and tool_no in self.TOOL_TABLE:
            try:
                extras = self.getToolExtras(tool_no)
                if extras:
                    record.update(extras)
                for name, value in self.getCustomFieldValues(tool_no).items():
                    record['custom:' + name] = value
            except Exception:
                # DB not configured yet (early startup) -- core-only record.
                LOG.debug("current_tool extras/custom compose skipped",
                          exc_info=True)
        return record

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

    def getUnits(self):
        """The database's single canonical unit system ('inch' or 'mm',
        meta.units) -- one system for every tool by design (plan §5.5)."""
        session = Session()
        try:
            meta = session.query(Meta).first()
            return meta.units if meta is not None else 'inch'
        finally:
            session.close()

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
        changed = set()
        try:
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
                    tool = Tool(tool_no=tnum, in_use=0)
                    session.add(tool)
                    self._apply_dict_to_tool(tool, tdata)
                    changed.add(tnum)
                else:
                    before = self._tool_to_dict(tool)
                    self._apply_dict_to_tool(tool, tdata)
                    if self._tool_to_dict(tool) != before:
                        changed.add(tnum)

            # delete removed tools
            for tnum, tool in existing.items():
                if tnum not in wanted:
                    session.delete(tool)
                    changed.add(tnum)

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        self.loadToolTable()
        self._request_machine_reload()
        for tnum in changed:
            self.tool_changed.emit(tnum)

    def renumberTool(self, old_tool_no, new_tool_no):
        """Change a tool's number in place -- a single UPDATE on `tool.id`'s
        row, not a delete+recreate.

        Schema v1 keys `tool_lathe`/`custom_field_value` off `tool.id`, not
        `tool_no`, specifically so renumbering is safe (§4): going through
        the generic add/delete path in :meth:`saveToolTable` instead (i.e.
        removing old_tool_no and adding new_tool_no as if it were a brand
        new tool) would give the new row a new `id`, and ON DELETE CASCADE
        would silently wipe that tool's extras and custom-field values.
        """
        old_tool_no, new_tool_no = int(old_tool_no), int(new_tool_no)
        if old_tool_no == new_tool_no:
            return
        if new_tool_no == 0:
            raise ValueError("T0 is reserved (no tool); can't renumber to it")

        session = Session()
        try:
            tool = session.query(Tool).filter(
                Tool.tool_no == old_tool_no).one_or_none()
            if tool is None:
                raise LookupError('tool %s not in database' % old_tool_no)
            if session.query(Tool).filter(
                    Tool.tool_no == new_tool_no).first() is not None:
                raise ValueError('tool %s already exists' % new_tool_no)
            tool.tool_no = new_tool_no
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        self.loadToolTable()
        self._request_machine_reload()
        self.tool_changed.emit(old_tool_no)
        self.tool_changed.emit(new_tool_no)

    # ------------------------------------------------------------ extras
    # (tool_lathe/tool_mill per the 'extras' kwarg: consumed by the UI/
    # VTK/conversational/machine macros; never sent to LinuxCNC, so no
    # machine-reload/interp-idle guard applies here.)

    def getToolExtras(self, tool_no):
        """Return the extras dict for tool_no, or None if the tool has no
        extras row (a bare core-only tool is valid, §4)."""
        session = Session()
        try:
            tool = session.query(Tool).filter(
                Tool.tool_no == int(tool_no)).one_or_none()
            if tool is None:
                return None
            extras_row = getattr(tool, self._extras_attr)
            if extras_row is None:
                return None
            return {name: getattr(extras_row, name)
                    for name in self._EXTRAS_COLUMNS}
        finally:
            session.close()

    def saveToolExtras(self, tool_no, extras):
        """Upsert the extras row for tool_no."""
        self.saveAllToolExtras({int(tool_no): extras})

    def saveAllToolExtras(self, extras_by_tool):
        """Upsert extras rows for many tools in one transaction.

        A per-tool loop calling saveToolExtras() (one SQLAlchemy session +
        commit each) turns a single "Save" click into as many disk-sync'd
        commits as there are rows in the table -- 23 tools alone made a
        small single-cell edit take ~1.6s (measured: 35ms/commit average).
        One session/commit for the whole batch instead.
        """
        session = Session()
        try:
            tool_nos = [int(t) for t in extras_by_tool]
            tools = {t.tool_no: t for t in session.query(Tool).filter(
                Tool.tool_no.in_(tool_nos)).all()}
            for tool_no in tool_nos:
                tool = tools.get(tool_no)
                if tool is None:
                    raise LookupError('tool %s not in database' % tool_no)
                extras_row = getattr(tool, self._extras_attr)
                if extras_row is None:
                    extras_row = self._extras_model()
                    setattr(tool, self._extras_attr, extras_row)
                extras = extras_by_tool[tool_no]
                for name in self._EXTRAS_COLUMNS:
                    if name in extras:
                        setattr(extras_row, name, extras[name])
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        for tool_no in extras_by_tool:
            self.extras_changed.emit(int(tool_no))

    # ------------------------------------------------------------ custom fields
    # (plan §5.7: definition + typed EAV value tables; UI/DB-only by design.)

    @staticmethod
    def _cast_custom_value(raw, value_type):
        if raw is None:
            return None
        if value_type == 'float':
            return float(raw)
        if value_type == 'int':
            return int(raw)
        if value_type == 'bool':
            return str(raw).strip().lower() in ('1', 'true', 'yes', 'y')
        return raw  # text

    def getCustomFieldDefs(self):
        """List of custom field definitions, in display order."""
        session = Session()
        try:
            defs = session.query(CustomFieldDef).order_by(
                CustomFieldDef.display_order, CustomFieldDef.id).all()
            return [{'name': d.name, 'label': d.label,
                     'value_type': d.value_type, 'unit': d.unit,
                     'default_value': d.default_value,
                     'display_order': d.display_order} for d in defs]
        finally:
            session.close()

    def addCustomField(self, name, label, value_type, unit=None,
                       default_value=None, display_order=None):
        """Define a new custom column. Grows the table immediately -- no
        schema migration, no restart (plan §5.7)."""
        if value_type not in CUSTOM_FIELD_VALUE_TYPES:
            raise ValueError('invalid value_type %r (must be one of %s)' %
                             (value_type, CUSTOM_FIELD_VALUE_TYPES))
        # The machine key becomes a G-code parameter name
        # (#<_current_tool_<name>>, written by change_epilog in
        # probe_basic's python/stdglue.py) shared with the extras
        # columns -- a colliding key would silently shadow the built-in
        # column's parameter.
        if name in self._EXTRAS_COLUMNS:
            raise ValueError(
                'the name %r is already a built-in tool parameter '
                '(#<_current_tool_%s>) -- pick a different machine key'
                % (name, name))
        session = Session()
        try:
            if session.query(CustomFieldDef).filter(
                    CustomFieldDef.name == name).first() is not None:
                raise ValueError('custom field %r already exists' % name)
            session.add(CustomFieldDef(
                name=name, label=label, value_type=value_type, unit=unit,
                default_value=default_value, display_order=display_order))
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        self.fields_changed.emit()

    def removeCustomField(self, name):
        """Remove a custom field definition and all its values (cascades)."""
        session = Session()
        try:
            field = session.query(CustomFieldDef).filter(
                CustomFieldDef.name == name).one_or_none()
            if field is not None:
                session.delete(field)
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        self.fields_changed.emit()

    def getCustomFieldValues(self, tool_no):
        """dict of {field_name: typed value} for every custom value set on
        tool_no (fields with no value set for this tool are omitted)."""
        session = Session()
        try:
            tool = session.query(Tool).filter(
                Tool.tool_no == int(tool_no)).one_or_none()
            if tool is None:
                return {}
            return {cv.field.name: self._cast_custom_value(cv.value, cv.field.value_type)
                    for cv in tool.custom_values}
        finally:
            session.close()

    def setCustomFieldValue(self, tool_no, field_name, value):
        self.setCustomFieldValues({int(tool_no): {field_name: value}})

    def setCustomFieldValues(self, values_by_tool):
        """Upsert custom_field_value rows for many tools/fields in one
        transaction -- see saveAllToolExtras for why this matters (a
        per-tool-per-field loop calling setCustomFieldValue() one at a time
        made every custom column multiply the cost of a Save by however
        many tools are in the table)."""
        values_by_tool = {int(t): v for t, v in values_by_tool.items()}
        session = Session()
        try:
            tool_nos = list(values_by_tool)
            tools = {t.tool_no: t for t in session.query(Tool).filter(
                Tool.tool_no.in_(tool_nos)).all()}
            field_names = {name for fields in values_by_tool.values() for name in fields}
            field_defs = {f.name: f for f in session.query(CustomFieldDef).filter(
                CustomFieldDef.name.in_(field_names)).all()}
            existing_values = {
                (cv.tool_id, cv.field_id): cv
                for cv in session.query(CustomFieldValue).filter(
                    CustomFieldValue.tool_id.in_(t.id for t in tools.values()))}

            for tool_no, fields in values_by_tool.items():
                tool = tools.get(tool_no)
                if tool is None:
                    raise LookupError('tool %s not in database' % tool_no)
                for field_name, value in fields.items():
                    field = field_defs.get(field_name)
                    if field is None:
                        raise LookupError('custom field %r not defined' % field_name)
                    cv = existing_values.get((tool.id, field.id))
                    if cv is None:
                        cv = CustomFieldValue(tool_id=tool.id, field_id=field.id)
                        session.add(cv)
                        existing_values[(tool.id, field.id)] = cv
                    cv.value = None if value is None else str(value)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        self.fields_changed.emit()

    # ------------------------------------------------------- UI preferences
    # (schema v2, plan §6 Phase 3 follow-up: which columns are checked
    # visible -- core, extras, custom alike -- so a widget restart shows
    # the same columns the user last left checked.)

    def getVisibleColumns(self):
        """Column keys the user last had checked visible, or None if never
        explicitly set (caller should fall back to its own default -- a
        fresh/never-touched database has no opinion here)."""
        session = Session()
        try:
            rows = session.query(VisibleColumn).all()
            return [r.column_key for r in rows] or None
        finally:
            session.close()

    def setVisibleColumns(self, columns):
        """Persist exactly this set of column keys as visible -- replaces
        whatever was stored before, atomically."""
        session = Session()
        try:
            session.query(VisibleColumn).delete()
            session.add_all(VisibleColumn(column_key=c) for c in columns)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

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
