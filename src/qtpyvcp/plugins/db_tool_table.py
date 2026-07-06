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

from qtpyvcp.lib.db_tool.base import Base, Session, configure_database, get_engine
from qtpyvcp.lib.db_tool.tool_table import (Tool, ToolTable, ToolModel,
                                            ToolLathe, CustomFieldDef,
                                            CustomFieldValue, VisibleColumn)
from qtpyvcp.lib.db_tool.migrate import run_migrations
from qtpyvcp.lib.db_tool.tool_data_sub import (generate_tool_data_ngc,
                                               NUMBER_KEY, SUB_FILE_NAME)

from sqlalchemy import Text as _SAText

CUSTOM_FIELD_VALUE_TYPES = ('float', 'int', 'text', 'bool')

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


def _default_sub_path():
    """tool_data.ngc under the ini's first SUBROUTINE_PATH entry, or None
    when that can't be resolved (Designer, tests, no ini) -- generation is
    simply skipped then; there is no interpreter around to read it anyway."""
    config_dir = getattr(INFO, 'CONFIG_DIR', None)
    sub_dirs = None
    try:
        sub_dirs = INFO.ini.find('RS274NGC', 'SUBROUTINE_PATH')
    except Exception:
        pass
    if not (config_dir and sub_dirs):
        return None
    first = str(sub_dirs).split(':')[0].strip()
    if not os.path.isabs(first):
        first = os.path.join(config_dir, first)
    if not os.path.isdir(first):
        return None
    return os.path.join(os.path.abspath(first), SUB_FILE_NAME)


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

    def __init__(self, columns='TPXZDIJQR', db_file=None, sub_file=None,
                 **kwargs):
        super(DBToolTable, self).__init__()

        self.columns = self.validateColumns(columns) or [c for c in 'TPXZDIJQR']
        self.db_file = db_file
        self.sub_file = sub_file  # tool_data.ngc override (tests); else ini
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
        self.regenerateToolDataSub()  # file exists and is current from boot

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
        self.regenerateToolDataSub()

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
        self.regenerateToolDataSub()

    # ------------------------------------------------------------ extras
    # (tool_lathe: consumed by the UI/VTK/conversational; never sent to
    # LinuxCNC, so no machine-reload/interp-idle guard applies here.)

    _EXTRAS_COLUMNS = [c.name for c in ToolLathe.__table__.columns
                       if c.name != 'tool_id']
    # G-code-representable extras (RS274 has no strings): drives which
    # columns tool_data.ngc publishes as #<_tool_*> parameters.
    _NUMERIC_EXTRAS = [c.name for c in ToolLathe.__table__.columns
                       if c.name != 'tool_id'
                       and not isinstance(c.type, _SAText)]

    def regenerateToolDataSub(self):
        """Regenerate subroutines/tool_data.ngc from the database.

        Called after every GUI-side mutation (save/renumber/extras/custom
        edits, column add/remove) -- all of which the widget locks to
        interp-idle, so the file can never change under a running program
        (whose interpreter holds byte offsets into it; see the module
        docstring of lib.db_tool.tool_data_sub). Machine-driven writes
        (G10/touch-off) are core-only and core is deliberately not
        mirrored in the file, so they never require regeneration.

        Never raises: a file-write problem must not break the save that
        triggered it (worst case is stale G-code parameters, logged)."""
        path = self.sub_file or _default_sub_path()
        if not path:
            return
        try:
            tool_nos = [t for t in self.TOOL_TABLE if t != 0]
            text = generate_tool_data_ngc(
                tool_nos,
                {t: self.getToolExtras(t) for t in tool_nos},
                self.getCustomFieldDefs(),
                {t: self.getCustomFieldValues(t) for t in tool_nos},
                self._NUMERIC_EXTRAS)
            tmp = path + '.tmp'
            with open(tmp, 'w') as fh:
                fh.write(text)
            os.replace(tmp, path)  # atomic: never a half-written file
        except Exception:
            LOG.exception("tool_data.ngc regeneration failed (%s); G-code "
                          "tool parameters may be stale until the next "
                          "successful save", path)

    def getToolExtras(self, tool_no):
        """Return the tool_lathe extras dict for tool_no, or None if the
        tool has no extras row (a bare core-only tool is valid, §4)."""
        session = Session()
        try:
            tool = session.query(Tool).filter(
                Tool.tool_no == int(tool_no)).one_or_none()
            if tool is None or tool.lathe is None:
                return None
            return {name: getattr(tool.lathe, name)
                    for name in self._EXTRAS_COLUMNS}
        finally:
            session.close()

    def saveToolExtras(self, tool_no, extras):
        """Upsert the tool_lathe extras row for tool_no."""
        self.saveAllToolExtras({int(tool_no): extras})

    def saveAllToolExtras(self, extras_by_tool):
        """Upsert tool_lathe extras rows for many tools in one transaction.

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
                if tool.lathe is None:
                    tool.lathe = ToolLathe()
                extras = extras_by_tool[tool_no]
                for name in self._EXTRAS_COLUMNS:
                    if name in extras:
                        setattr(tool.lathe, name, extras[name])
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        for tool_no in extras_by_tool:
            self.extras_changed.emit(int(tool_no))
        self.regenerateToolDataSub()

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
        # The machine key becomes a G-code parameter name (#<_tool_<name>>,
        # tool_data.ngc) shared with the extras columns -- a colliding key
        # would silently shadow the built-in column's parameter.
        if name in self._EXTRAS_COLUMNS or name == NUMBER_KEY:
            raise ValueError(
                'the name %r is already a built-in tool parameter '
                '(#<_tool_%s>) -- pick a different machine key' % (name, name))
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
        self.regenerateToolDataSub()

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
        self.regenerateToolDataSub()

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
        self.regenerateToolDataSub()

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
