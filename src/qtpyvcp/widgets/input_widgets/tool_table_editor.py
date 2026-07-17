# coding=utf-8
"""ToolTableEditor -- unified tool table widget.

One editing surface for core tool-table columns, machine-flavor "extras"
columns (see ``qtpyvcp.plugins.db_tool_table``'s per-machine extras
tables), and user-defined custom columns. Keeps the same public slot
surface as this package's stock ``tool_table.ToolTable`` widget
(saveToolTable/loadToolTable/addTool/deleteSelectedTool/...) so a VCP can
promote this widget in place of the stock one without changing any `.ui`
signal/slot wiring -- only the promoted class changes.

Machine-flavor configuration (which extras columns exist, their labels,
which are strict enums vs. open-vocabulary vs. free text, default
visibility, ...) is hoisted to class attributes -- this class only
implements the mechanism that reads them; a subclass overrides the data.
Any column key listed in ``OPEN_VOCAB_SEED_OPTIONS`` must have its choices
supplied by overriding :meth:`ToolTableEditorModel.openVocabOptionsFor`.
See probe_basic's ``LatheToolModel``/``MillToolModel`` for real per-machine
subclasses (lathe insert/holder vocabulary, mill's ATC bool extra).

Works against either qtpyvcp tooltable plugin, adapting at runtime to
whichever one a config actually wires up (duck-typed via
``getCustomFieldDefs``) rather than requiring a second copy of the `.ui`
with a different widget class promoted:

- ``qtpyvcp.plugins.tool_table:ToolTable`` -- classic file-based .tbl,
  core columns only, no extras/custom concept.
- ``qtpyvcp.plugins.db_tool_table:DBToolTable`` -- SQLite-backed, adds
  per-machine extras and user-defined custom columns.
"""

from PySide6.QtCore import (Qt, Slot, Signal, Property, QModelIndex, QTimer,
                            QSortFilterProxyModel)
from PySide6.QtGui import QStandardItemModel, QColor, QBrush
from PySide6.QtWidgets import (QTableView, QHeaderView, QAbstractItemView,
                               QStyledItemDelegate, QDoubleSpinBox, QSpinBox,
                               QLineEdit, QComboBox, QMessageBox, QMenu,
                               QInputDialog)

from qtpyvcp.actions.machine_actions import issue_mdi
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.actions import IN_DESIGNER
from qtpyvcp.plugins import getPlugin

LOG = getLogger(__name__)

CUSTOM_PREFIX = 'custom:'

# Custom-column display, by the field's own value_type -- text reads like
# the other text-ish columns (left), float/int/bool read like data rather
# than prose (right for float since that's the numeric-column convention
# everywhere else in this table; centered for int/bool since they're
# short, discrete values rather than magnitudes to compare).
CUSTOM_FIELD_ALIGNMENT = {
    'text': Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
    'float': Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
    'int': Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter,
    'bool': Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter,
}
# Single source of truth for float display precision, table-wide (core
# columns, extras, and custom float fields alike) -- named and centralized
# rather than a bare "4" repeated wherever a float gets formatted, so
# every float column stays uniform on purpose, not by coincidence.
FLOAT_DECIMALS = 4

MAX_COLUMNS = 200  # generous fixed capacity; mirrors the row model's
                   # existing fixed setRowCount(1000)/max-1000-tools limit

GROUP_LABELS = {'core': 'Core', 'extras': 'Extras', 'custom': 'Custom'}

# Qt's QComboBox default (10) puts a scrollbar inside the popup well before
# any of this table's real option lists are long enough to need one (e.g.
# a lathe's holder_style already has 14+ distinct real values) -- a
# scrollable list popped out of a table cell is one nested-scroll-region
# too many. Generous enough that realistic option counts just show in full
# instead.
COMBO_MAX_VISIBLE_ITEMS = 25

# Dynamic property tagging the bool-valued combo editor (both extras bools,
# e.g. a mill's ATC flag, and bool-typed custom fields), so
# setEditorData/setModelData can special-case it without relying on Qt's
# built-in QVariant(bool)->QString marshaling (confirmed live: it lowercases
# to "true"/"false", not "True"/"False" -- matching combo item text against
# that silently mismatches and leaves the wrong item pre-selected) -- easier
# to just own the round-trip as a real Python bool throughout.
BOOL_EDITOR_PROP = '_tool_table_bool_editor'

# Imported after the constants above (not at module top): both dialogs
# import CUSTOM_PREFIX back from this module, which would be a circular
# import (this module not yet finished defining it) if these imports ran
# before that line.
from .add_column_dialog import AddColumnDialog
from .parameter_names_dialog import parameter_entries, ParameterNamesDialog


class ToolTableEditorModel(QStandardItemModel):

    # Machine-flavor configuration, hoisted to class attributes so a
    # machine variant is a subclass overriding data, not a fork of the
    # logic. Neutral/empty defaults here; the model methods (and
    # ToolTableEditorDelegate, via self._model) consult these regardless
    # of what a subclass sets them to.
    EXTRAS_LABELS = {}                       # column key -> header label, in display order
    TEXT_EXTRAS = frozenset()                # extras rendered/edited as free text
    BOOL_EXTRAS = frozenset()                # extras rendered/edited as True/False
    EXTRAS_DEFAULTS = {}                     # value shown when a tool has no extras row
    DEFAULT_VISIBLE_EXTRAS = []
    STRICT_ENUM_OPTIONS = {}                 # DB CHECK-constrained: non-editable pick-lists
    OPEN_VOCAB_SEED_OPTIONS = frozenset()    # editable combo; see openVocabOptionsFor()
    EXTRAS_GROUP_LABEL = 'Extras'            # header-menu section title
    # Core columns forced to render AFTER extras/custom instead of in their
    # normal core position -- e.g. a wide free-text Remark column, so
    # machine extras sit between the numeric offsets and it. Empty by
    # default (keeps Remark in its normal core position); membership
    # only -- these stay 'core' for grouping, only their column position
    # moves.
    TRAILING_CORE_COLUMNS = ()
    # Designer-canvas placeholder columns (see _initEmptyStub) -- cosmetic
    # only, real columns always come from the live plugin's self.tt.columns.
    DESIGNER_STUB_COLUMNS = ['T', 'X', 'Z', 'D', 'R']

    dirtyChanged = Signal(bool)

    def __init__(self, parent=None):
        super(ToolTableEditorModel, self).__init__(parent)
        self._dirty = False

        if IN_DESIGNER:
            self._initEmptyStub()
            return

        try:
            self.status = getPlugin('status')
            self.stat = self.status.stat
            self.tt = getPlugin('tooltable')

            required = ('columns', 'COLUMN_LABELS', 'getToolTable',
                       'saveToolTable', 'newTool', 'tool_table_changed')
            missing = [attr for attr in required if not hasattr(self.tt, attr)]
            if missing:
                # Something fundamentally incompatible -- not even the base
                # (machine-flavor-shared) tool-table interface every
                # 'tooltable' plugin is expected to implement. A plugin
                # merely lacking the DB extras (see _db_backed below) is
                # not this case -- that's a normal, supported backend, not
                # an error.
                raise TypeError(
                    "'tooltable' plugin (%s) doesn't implement the base "
                    "tool-table interface -- missing: %s"
                    % (type(self.tt).__name__, ', '.join(missing)))

            # True for qtpyvcp.plugins.db_tool_table:DBToolTable; False for
            # the classic file-based qtpyvcp.plugins.tool_table:ToolTable.
            # Both are first-class, supported backends for this one widget
            # -- it adapts at runtime to whichever 'tooltable' plugin the
            # .ini/yaml config actually wires up, rather than requiring a
            # second copy of the .ui with a different widget class
            # promoted (Designer bakes the promoted class into the .ui
            # statically, so two backends would mean two .ui files that
            # inevitably drift out of sync on any unrelated edit).
            self._db_backed = hasattr(self.tt, 'getCustomFieldDefs')

            self.current_tool_color = QColor(Qt.darkGreen)
            self.current_tool_bg = None

            self._core_columns = list(self.tt.columns)
            self._core_labels = dict(self.tt.COLUMN_LABELS)
            if self._db_backed and self._pluginServesOurExtras():
                self._extras_columns = list(self.EXTRAS_LABELS)
                self._extras_labels = dict(self.EXTRAS_LABELS)
            else:
                self._extras_columns = []
                self._extras_labels = {}
            self._custom_columns = []
            self._custom_labels = {}
            self._custom_value_types = {}

            self.row_offset = 1
            self._interp_idle = True
            self._tool_table = {}

            if self._db_backed:
                self._refresh_custom_columns()

            # Restore whatever the user last had checked visible -- core,
            # extras, and custom columns alike -- so a widget restart
            # shows the same columns instead of always reverting to the
            # hardcoded default. No persisted preference yet (fresh DB, or
            # classic file-based backend, which has nowhere to persist
            # this at all) falls back to the default set.
            persisted = self.tt.getVisibleColumns() if self._db_backed else None
            self._visible_columns = (self._filterToKnownColumns(persisted) if persisted
                                     else self._default_visible_columns())
            # Fixed capacity, set once, before any view/proxy is attached --
            # never touched again (see MAX_COLUMNS and setVisibleColumns
            # below for why: calling setColumnCount() again later, after a
            # proxy is watching, races its own columnsInserted signal
            # against our columnCount() override still reporting the
            # pre-growth count).
            self.setColumnCount(MAX_COLUMNS)
            self.setRowCount(1000)

            self._load_full_table()

            self.status.tool_in_spindle.notify(self.refreshModel)
            self.status.interp_state.notify(self._onInterpStateChanged)
            self._reload_signals_suppressed = False
            self.tt.tool_table_changed.connect(lambda *_: self._load_full_table())
            if self._db_backed:
                self.tt.extras_changed.connect(self._onExtrasChanged)
                self.tt.fields_changed.connect(self._onFieldsChanged)
        except Exception:
            # A Python exception escaping this constructor would propagate
            # up through QUiLoader's C++ widget-tree building (this widget
            # gets built via .ui customwidget promotion) -- PySide6 segfaults
            # instead of raising cleanly there, rather than just failing this
            # one widget. Fail soft into an empty, read-only stub instead;
            # see ToolTableEditor.__init__ for the matching self.tt is-None
            # guard.
            LOG.exception(
                "ToolTableEditorModel: failed to initialize against the "
                "'tooltable' plugin -- falling back to an empty table "
                "instead of crashing. This means the plugin is missing even "
                "the base tool-table interface (columns/getToolTable/"
                "saveToolTable/...) -- a DB backend is not required (both "
                "qtpyvcp.plugins.tool_table:ToolTable and "
                "qtpyvcp.plugins.db_tool_table:DBToolTable work), so check "
                "'tooltable' is wired to one of those two, not something "
                "else entirely.")
            self._initEmptyStub()

    def _initEmptyStub(self):
        self.status = None
        self.stat = None
        self.tt = None
        self._db_backed = False
        self._reload_signals_suppressed = False
        # Real-path defaults for ToolTableEditor's currentToolColor/
        # currentToolBackground @Property getters, which read these
        # unconditionally. Missing here meant Qt Designer's startup widget-
        # database scan (grabs every registered custom widget's default
        # property values, on a freshly-constructed instance -- independent
        # of which .ui is even open) hit an AttributeError from inside a
        # C++-invoked property getter and segfaulted instead of raising.
        self.current_tool_color = QColor(Qt.darkGreen)
        self.current_tool_bg = None
        self._core_columns = list(self.DESIGNER_STUB_COLUMNS)
        self._extras_columns = []
        self._custom_columns = []
        self._visible_columns = list(self._core_columns)
        self._core_labels = {c: c for c in self._core_columns}
        self._extras_labels = {}
        self._custom_labels = {}
        self._custom_value_types = {}
        # _tool_table must exist before setColumnCount/setRowCount below --
        # both synchronously invoke our overridden rowCount(), which reads it.
        self._tool_table = {}
        self.setColumnCount(len(self._visible_columns))
        self.setRowCount(10)
        self.row_offset = 1
        self._interp_idle = True

    # ------------------------------------------------------------ columns

    def _pluginServesOurExtras(self):
        """True when the DB plugin's configured extras table carries every
        column this model wants to show. A mismatch (e.g. this .ui promotes
        a mill-flavored widget but the config's yaml left the plugin on
        `extras: lathe`) would otherwise stage edits into attributes the
        plugin never persists -- silently. Hide the extras columns and say
        so instead; core and custom columns keep working either way."""
        plugin_extras = getattr(self.tt, '_EXTRAS_COLUMNS', [])
        missing = [c for c in self.EXTRAS_LABELS if c not in plugin_extras]
        if missing:
            LOG.error(
                "The 'tooltable' plugin serves extras columns %s, but this "
                "widget (%s) renders %s -- missing %s. Check the config "
                "yaml's data_plugins.tooltable.kwargs.extras matches the "
                "promoted tool table widget. Hiding the extras columns.",
                plugin_extras, type(self).__name__,
                list(self.EXTRAS_LABELS), missing)
            return False
        return True

    def _refresh_custom_columns(self):
        defs = self.tt.getCustomFieldDefs()
        self._custom_columns = [CUSTOM_PREFIX + d['name'] for d in defs]
        self._custom_labels = {CUSTOM_PREFIX + d['name']: d['label'] for d in defs}
        self._custom_value_types = {CUSTOM_PREFIX + d['name']: d['value_type'] for d in defs}

    def _order_columns(self, cols):
        """Move any TRAILING_CORE_COLUMNS to the end (after extras/custom),
        preserving their relative order -- everything else keeps its order.
        No-op when TRAILING_CORE_COLUMNS is empty."""
        if not self.TRAILING_CORE_COLUMNS:
            return list(cols)
        trailing = [c for c in cols if c in self.TRAILING_CORE_COLUMNS]
        head = [c for c in cols if c not in self.TRAILING_CORE_COLUMNS]
        return head + trailing

    def _default_visible_columns(self):
        extras = [c for c in self.DEFAULT_VISIBLE_EXTRAS if c in self._extras_columns]
        return self._order_columns(list(self._core_columns) + extras)

    def allColumns(self):
        """Every known column key, in display order: core, then extras, then
        custom -- with any TRAILING_CORE_COLUMNS moved to the very end so
        "Show All Columns" and the default order agree.

        Capped at MAX_COLUMNS -- the model's real (fixed) column count; see
        setVisibleColumns. An overflow here would mean ~150+ custom fields
        defined, at which point the newest ones are silently unavailable
        rather than crashing; raising MAX_COLUMNS is the fix if that's ever
        a real shop's use case.
        """
        cols = self._order_columns(
            list(self._core_columns) + list(self._extras_columns)
            + list(self._custom_columns))
        return cols[:MAX_COLUMNS]

    def visibleColumns(self):
        return list(self._visible_columns)

    def _filterToKnownColumns(self, columns):
        """columns, minus any key that no longer exists (a removed custom
        column, or one from a differently-configured core set) -- falls
        back to just the core columns if that leaves nothing at all.

        Also normalizes to allColumns()' own canonical order regardless of
        what order `columns` arrives in, so a column that gets hidden and
        re-shown always lands back in its original position instead of at
        the end (the header menu's re-show path builds the list in toggle
        order via cols.append(key), not display order)."""
        all_cols = self.allColumns()
        wanted = set(columns)
        ordered = [c for c in all_cols if c in wanted]
        return ordered or list(self._core_columns)

    def setVisibleColumns(self, columns):
        # Toggling column *visibility* only ever changes _visible_columns
        # (what columnCount() reports) -- it never touches the model's real
        # (fixed, MAX_COLUMNS) column count. An earlier version grew the
        # real count here via setColumnCount() as new custom fields showed
        # up; calling that *after* a proxy/view was already attached raced
        # its columnsInserted signal against our columnCount() override
        # still reporting the pre-growth total ("QSortFilterProxyModel:
        # invalid inserted rows reported by source model"). Fixed capacity
        # sidesteps this the same way the row model already does.
        visible = self._filterToKnownColumns(columns)
        self.beginResetModel()
        self._visible_columns = visible
        self.endResetModel()
        if self._db_backed:
            # Persist every change, not just user-initiated ones (e.g. a
            # custom column disappearing out from under an existing
            # selection): the persisted set should always mirror what's
            # actually currently shown, with no special-casing over who
            # triggered the change.
            self.tt.setVisibleColumns(visible)

    def columnLabel(self, key):
        if key in self._core_labels:
            return self._core_labels[key]
        if key in self._extras_labels:
            return self._extras_labels[key]
        return self._custom_labels.get(key, key)

    def columnGroup(self, key):
        if key in self._core_columns:
            return 'core'
        if key in self._extras_columns:
            return 'extras'
        return 'custom'

    def openVocabOptionsFor(self, key, row_data):
        """Choices to seed an OPEN_VOCAB_SEED_OPTIONS combo editor for
        `key`, given the row's other already-entered data (e.g. a lathe's
        insert-shape choices depend on the row's tool type). No-op base --
        any subclass that lists columns in OPEN_VOCAB_SEED_OPTIONS must
        override this to supply their choices."""
        return []

    # ------------------------------------------------------------ loading

    def _load_full_table(self):
        core = self.tt.getToolTable()  # {0: NO_TOOL, tnum: {letter: value}}
        table = {}
        for tnum, core_row in core.items():
            row = dict(core_row)
            if tnum != 0 and self._db_backed:
                extras = self.tt.getToolExtras(tnum) or {}
                for key in self._extras_columns:
                    value = extras.get(key)
                    if value is None:
                        # no extras row yet (or an unset cell): show the
                        # machine flavor's default (e.g. mill atc = True)
                        # instead of a blank that reads as "no value".
                        value = self.EXTRAS_DEFAULTS.get(key)
                    row[key] = value
                values = self.tt.getCustomFieldValues(tnum)
                for key in self._custom_columns:
                    row[key] = values.get(key[len(CUSTOM_PREFIX):])
            table[tnum] = row

        self.beginResetModel()
        self._tool_table = table
        self.endResetModel()
        self._set_dirty(False)
        LOG.debug("ToolTableEditorModel reload: tools=%s", len(table) - 1)

    def _onExtrasChanged(self, tool_no):
        # saveAllToolExtras() emits this once per tool in the batch (a
        # correct, real per-tool signal -- kept that way in case anything
        # ever wants that granularity). But saveToolTable() below already
        # does its own single authoritative _load_full_table() right after
        # the whole batch commits, so reacting here too, once per tool,
        # would turn one Save into N redundant full reloads -- suppressed
        # for the duration of that batch call.
        if not self._reload_signals_suppressed:
            self._load_full_table()

    def _onFieldsChanged(self):
        self._refresh_custom_columns()
        # keep whatever core/extras columns were visible; drop any custom
        # column that no longer exists, but don't force newly-added ones
        # into view (the user picks those from the header menu).
        # setVisibleColumns() grows column capacity itself, atomically, if
        # a new custom field means there's more room needed.
        kept = [c for c in self._visible_columns
                if not c.startswith(CUSTOM_PREFIX) or c in self._custom_columns]
        self.setVisibleColumns(kept)
        self._load_full_table()

    def refreshModel(self):
        self.beginResetModel()
        self.endResetModel()

    def _onInterpStateChanged(self, interp_state):
        import linuxcnc
        was_idle = self._interp_idle
        self._interp_idle = (interp_state == linuxcnc.INTERP_IDLE)
        if was_idle != self._interp_idle:
            self.beginResetModel()
            self.endResetModel()

    # ------------------------------------------------------------ Qt model

    def columnCount(self, parent=None):
        return len(self._visible_columns)

    def rowCount(self, parent=None):
        return max(0, len(self._tool_table) - 1)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.columnLabel(self._visible_columns[section])
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Vertical:
            # Row header shows the tool number instead of a plain row
            # index -- it's Qt's own always-visible-through-horizontal-
            # scroll widget, so this is what keeps T in view without
            # needing a frozen/pinned column.
            return self.toolDataFromRow(section)['T']
        return QStandardItemModel.headerData(self, section, orientation, role)

    def _tool_no_for_row(self, row):
        return sorted(self._tool_table)[row + self.row_offset]

    def flags(self, index):
        col_key = self._visible_columns[index.column()]

        if col_key == 'T':
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

        if not self._interp_idle:
            # Every column locks while a program runs, not just core --
            # a custom/extras value could still be referenced by a
            # subroutine or other mid-program logic, so editing any of it
            # during machine operation is unsafe practice regardless of
            # whether LinuxCNC's own interpreter reads that column live.
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

        return (Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable |
                Qt.ItemFlag.ItemIsEditable)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        row, col = index.row(), index.column()
        key = self._visible_columns[col]
        tnum = self._tool_no_for_row(row)

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return self._tool_table[tnum].get(key)

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self.columnGroup(key) == 'custom':
                value_type = self._custom_value_types.get(key)
                return CUSTOM_FIELD_ALIGNMENT.get(
                    value_type, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            if key in ('R',) or key in self.TEXT_EXTRAS:
                return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
            elif key in ('T', 'P', 'Q') or key in self.BOOL_EXTRAS:
                return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter
            else:
                return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight

        elif role == Qt.ItemDataRole.ForegroundRole:
            if self.stat.tool_in_spindle == tnum:
                return QBrush(self.current_tool_color)
            return QStandardItemModel.data(self, index, role)

        elif role == Qt.ItemDataRole.BackgroundRole and self.current_tool_bg is not None:
            if self.stat.tool_in_spindle == tnum:
                return QBrush(self.current_tool_bg)
            return QStandardItemModel.data(self, index, role)

        return QStandardItemModel.data(self, index, role)

    def setData(self, index, value, role):
        key = self._visible_columns[index.column()]
        tnum = self._tool_no_for_row(index.row())
        self._tool_table[tnum][key] = value
        self._set_dirty(True)
        return True

    def _set_dirty(self, dirty):
        """Track unsaved edits staged in memory since the last save/reload;
        emits only on an actual state change so listeners (the Save button's
        color indicator) aren't hit on every single keystroke."""
        dirty = bool(dirty)
        if dirty == self._dirty:
            return
        self._dirty = dirty
        self.dirtyChanged.emit(self._dirty)

    # ------------------------------------------------------------ actions

    def toolDataFromRow(self, row):
        tnum = self._tool_no_for_row(row)
        return self._tool_table[tnum]

    def distinctColumnValues(self, key):
        """Distinct non-empty values currently loaded for `key`, sorted --
        used to seed open-vocabulary combo editors with whatever this
        shop's own data already uses, alongside a fixed seed list."""
        values = set()
        for tnum, row in self._tool_table.items():
            if tnum == 0:
                continue
            value = row.get(key)
            if value:
                values.add(value)
        return sorted(values)

    def distinctColumnValuesForType(self, key, tool_type):
        """Like distinctColumnValues, but scoped to rows whose `type`
        matches `tool_type` -- e.g. only holder_style values this shop has
        actually used on grooving tools, not every holder_style value ever
        used on any tool."""
        t = (tool_type or '').strip().lower()
        values = set()
        for tnum, row in self._tool_table.items():
            if tnum == 0:
                continue
            if (row.get('type') or '').strip().lower() != t:
                continue
            value = row.get(key)
            if value:
                values.add(value)
        return sorted(values)

    def addTool(self):
        try:
            tnum = max(k for k in self._tool_table if k != 0) + 1
        except ValueError:
            tnum = 1

        row = len(self._tool_table) - 1
        if row == 1000:
            return False  # max 1000 tools, matches the core widget's limit

        self.beginInsertRows(QModelIndex(), row, row)
        new_row = self.tt.newTool(tnum=tnum)
        for key in self._extras_columns:
            new_row.setdefault(key, self.EXTRAS_DEFAULTS.get(key))
        for key in self._custom_columns:
            new_row.setdefault(key, None)
        self._tool_table[tnum] = new_row
        self.endInsertRows()
        return True

    def removeTool(self, row):
        tnum = self._tool_no_for_row(row)
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._tool_table[tnum]
        self.endRemoveRows()
        return True

    def renumberTool(self, row, new_tool_no):
        """Commits immediately (unlike core-column edits, which stage in
        memory until Save) -- the DB backend makes this a single UPDATE
        that can't lose extras/custom data, so there's no reason to defer
        it.

        The classic file-based ToolTable plugin has no equivalent atomic
        op -- but also no extras/custom data that a delete+recreate could
        lose, so that's exactly what it falls back to here.
        """
        tnum = self._tool_no_for_row(row)
        new_tool_no = int(new_tool_no)
        if hasattr(self.tt, 'renumberTool'):
            self.tt.renumberTool(tnum, new_tool_no)
        else:
            table = self.tt.getToolTable()
            if new_tool_no != 0 and new_tool_no in table:
                raise ValueError('tool %s already exists' % new_tool_no)
            core = dict(table[tnum])
            core['T'] = new_tool_no
            del table[tnum]
            table[new_tool_no] = core
            self.tt.saveToolTable(table)
        self._load_full_table()
        return True

    def saveToolTable(self):
        # Snapshot before the core save: self.tt.saveToolTable() below emits
        # tool_table_changed synchronously, which our own _load_full_table
        # slot (connected in __init__) reacts to immediately -- that would
        # overwrite self._tool_table with freshly-reloaded (pre-extras-save)
        # data before the extras/custom loop below ever runs, silently
        # discarding those in-memory edits.
        snapshot = {tnum: dict(row) for tnum, row in self._tool_table.items()}

        if self._db_backed:
            # `row` here is core+extras+custom all flattened into one dict
            # (see _load_full_table) -- filter down to just the core subset
            # before handing it to the core-only saveToolTable() call.
            core_table = {tnum: {k: v for k, v in row.items() if k in self._core_columns}
                          for tnum, row in snapshot.items()}
        else:
            # Nothing to filter out here: with no extras/custom columns in
            # this mode, `row` already *is* the classic plugin's own tool
            # dict, untouched -- which includes keys beyond
            # self._core_columns that the *configured display columns*
            # don't cover but the plugin's own saveToolTable() still
            # unconditionally requires (e.g. 'P', inserted into its column
            # list internally regardless of what's configured, for the
            # .tbl file format). Filtering to self._core_columns here
            # stripped 'P' right back out and crashed with KeyError('P').
            core_table = snapshot
        self.tt.saveToolTable(core_table)

        if not self._db_backed:
            # The classic plugin's saveToolTable() only writes the .tbl
            # file and tells the LinuxCNC *task* to reload it
            # (CMD.load_tool_table(), an NML command) -- it does not
            # refresh its own Python-side self.TOOL_TABLE cache (what
            # getToolTable() below actually returns). That only happens
            # asynchronously, ~50ms later, via a QFileSystemWatcher
            # noticing the file changed -- relying on that alone races
            # _load_full_table() below, which could read stale (pre-save)
            # data if it runs first. Force the refresh synchronously
            # instead, the same way the DB-backed plugin's own
            # saveToolTable() already does internally (it calls its own
            # loadToolTable() as part of the same method).
            self.tt.loadToolTable()

        # One batched transaction each for extras/custom values, not one
        # commit per tool (or per tool per custom column) -- see
        # saveAllToolExtras/setCustomFieldValues docstrings: the per-tool
        # loop this replaced made a single-cell edit take ~1.6s against a
        # real 23-tool fixture (47 individual disk-sync'd commits). N/A at
        # all for the classic file-based backend -- no extras/custom
        # concept there, core_table above is the whole save.
        if self._db_backed:
            extras_by_tool = {}
            custom_by_tool = {}
            for tnum, row in snapshot.items():
                if tnum == 0:
                    continue
                extras_by_tool[tnum] = {k: row.get(k) for k in self._extras_columns}
                if self._custom_columns:
                    custom_by_tool[tnum] = {key[len(CUSTOM_PREFIX):]: row.get(key)
                                            for key in self._custom_columns}

            self._reload_signals_suppressed = True
            try:
                if extras_by_tool:
                    self.tt.saveAllToolExtras(extras_by_tool)
                if custom_by_tool:
                    self.tt.setCustomFieldValues(custom_by_tool)
            finally:
                self._reload_signals_suppressed = False

        self._load_full_table()  # authoritative final state after everything committed

        # Writing the table and telling LinuxCNC to re-read it (self.tt.
        # saveToolTable() above) does NOT, on its own, re-apply the
        # *currently active* tool's offset -- LinuxCNC only recomputes that
        # on a tool change or an explicit G43, not just because the
        # underlying table file/row changed. If the tool actually in the
        # spindle is what got edited, the DRO keeps showing its old offset
        # until G43 is reissued. Same recipe qtpyvcp's own classic
        # ToolTable plugin already uses after homing (reload_tool():
        # "M61 Q<n> G43") -- just not currently wired to fire after a
        # table save the way it is after homing.
        if self._interp_idle:
            tnum = self.stat.tool_in_spindle
            if tnum:
                issue_mdi("M61 Q%s G43" % tnum)

        return True

    def clearToolTable(self):
        self.beginRemoveRows(QModelIndex(), 0, 100)
        self._tool_table = {0: self._tool_table[0]}
        self.endRemoveRows()
        return True

    def loadToolTable(self):
        self._load_full_table()
        return True


class ToolTableEditorDelegate(QStyledItemDelegate):

    def __init__(self, model, table=None):
        super(ToolTableEditorDelegate, self).__init__()
        self._model = model
        self._table = table
        self._padding = ' ' * 2

    def _sourceRowForIndex(self, index):
        """Map a (possibly proxy) row index back to the model's own row
        numbering. Needed because some editors' choices depend on the
        row's *data* (type/insert_shape), not just the column: index.row()
        is the view's visual (post-sort) row, which only matches the
        model's internal row order when the table isn't currently sorted
        by some other column."""
        proxy = getattr(self._table, 'proxy_model', None)
        if proxy is not None and index.model() is proxy:
            index = proxy.mapToSource(index)
        return index.row()

    def displayText(self, value, locale):
        if isinstance(value, float):
            # Explicit, named setting (not a bare magic number) so every
            # float column -- core, extras, or a custom float field --
            # displays at the same precision on purpose, not by accident.
            return f"{value:.{FLOAT_DECIMALS}f}"
        if value is None:
            return ''
        return f"{self._padding}{value}"

    def sizeHint(self, option, index):
        # ResizeToContents sizes columns off this; the base implementation
        # has no margin, so content butts right up against the divider.
        size = super(ToolTableEditorDelegate, self).sizeHint(option, index)
        size.setWidth(size.width() + 10)  # 5px each side
        return size

    def createEditor(self, parent, option, index):
        key = self._model._visible_columns[index.column()]
        group = self._model.columnGroup(key)

        if key in self._model.STRICT_ENUM_OPTIONS:
            # DB CHECK-constrained: a strict pick-list, not editable free
            # text -- the user cannot enter a value the database would
            # reject on save.
            editor = QComboBox(parent)
            editor.setFrame(False)
            editor.setMaxVisibleItems(COMBO_MAX_VISIBLE_ITEMS)
            editor.addItems(self._model.STRICT_ENUM_OPTIONS[key])
            self._popOpenOnceShown(editor)
            return editor

        if key in self._model.BOOL_EXTRAS:
            # Boolean extras (e.g. a mill's ATC storable flag): same
            # owned-round-trip True/False combo as bool custom fields --
            # see BOOL_EDITOR_PROP for why this isn't a bare checkbox
            # relying on Qt's QVariant(bool) marshaling.
            editor = QComboBox(parent)
            editor.setFrame(False)
            editor.addItems(['True', 'False'])
            editor.setProperty(BOOL_EDITOR_PROP, True)
            self._popOpenOnceShown(editor)
            return editor

        if key in self._model.OPEN_VOCAB_SEED_OPTIONS:
            # Open vocabulary in practice -- editable combo, but *which*
            # choices are offered is discriminated by this row's own data
            # rather than dumping every value ever used for any tool into
            # one list -- see ToolTableEditorModel.openVocabOptionsFor.
            row_data = self._model.toolDataFromRow(self._sourceRowForIndex(index))
            options = self._model.openVocabOptionsFor(key, row_data)
            current_value = row_data.get(key)

            if not options:
                # e.g. a lathe's drill/tap rows have no insert-shape/holder
                # concept at all -- a combo with nothing valid to offer is
                # worse than plain free text.
                editor = QLineEdit(parent)
                editor.setFrame(False)
                return editor

            editor = QComboBox(parent)
            editor.setFrame(False)
            editor.setEditable(True)
            # Qt auto-attaches a QCompleter to every editable combobox, which
            # pops its own inline autocomplete list -- a second popup
            # mechanism fighting our explicit showPopup() below for focus
            # (the seeded item list below is already the intended picker;
            # there's no free-text-filter feature here to complete against).
            editor.setCompleter(None)
            editor.setMaxVisibleItems(COMBO_MAX_VISIBLE_ITEMS)
            seen = set()
            for value in options + ([current_value] if current_value else []):
                if value and value not in seen:
                    seen.add(value)
                    editor.addItem(value)
            # 200ms, not 0: opening the popup this way (rather than Qt's own
            # native double-click handling, which non-editable combos like
            # a strict-enum column get for free) races the initiating
            # double-click's own trailing mouse-release event still
            # draining through the queue if fired too soon (confirmed live
            # -- 60ms wasn't enough, 200ms is stable).
            self._popOpenOnceShown(editor, delay_ms=200)
            return editor

        if group == 'custom':
            # Typing "3.5" into an int-typed custom column would otherwise
            # be accepted at the cell (plain QLineEdit for every custom
            # column regardless of its declared value_type), only to blow
            # up later -- qtpyvcp's _cast_custom_value() does int(raw) on
            # the next load, which raises ValueError on a non-integer
            # string instead of truncating. Guard at entry instead: pick
            # the editor widget from the field's own value_type so an
            # invalid entry can't be typed in the first place.
            value_type = self._model._custom_value_types.get(key)
            if value_type == 'int':
                editor = QSpinBox(parent)
                editor.setFrame(False)
                editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
                editor.setRange(-999999, 999999)
                return editor
            if value_type == 'float':
                editor = QDoubleSpinBox(parent)
                editor.setFrame(False)
                editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
                editor.setDecimals(FLOAT_DECIMALS)
                editor.setRange(-100000, 100000)
                return editor
            if value_type == 'bool':
                editor = QComboBox(parent)
                editor.setFrame(False)
                editor.addItems(['True', 'False'])
                editor.setProperty(BOOL_EDITOR_PROP, True)
                self._popOpenOnceShown(editor)
                return editor
            # text (or an unrecognized/future value_type): free text, same
            # as always.
            editor = QLineEdit(parent)
            editor.setFrame(False)
            return editor

        if key == 'R' or key in self._model.TEXT_EXTRAS:
            editor = QLineEdit(parent)
            editor.setFrame(False)
            return editor

        if key in ('T', 'P', 'Q'):
            editor = QSpinBox(parent)
            editor.setFrame(False)
            editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
            editor.setMaximum(9 if key == 'Q' else 99999)
            return editor

        # everything else (X/Z/D/I/J offsets, numeric extras) is a float
        editor = QDoubleSpinBox(parent)
        editor.setFrame(False)
        editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        editor.setDecimals(4)
        editor.setRange(-100000, 100000)
        return editor

    def setEditorData(self, editor, index):
        if isinstance(editor, QComboBox) and editor.property(BOOL_EDITOR_PROP):
            value = bool(index.data(Qt.ItemDataRole.EditRole))
            editor.setCurrentIndex(editor.findText('True' if value else 'False'))
            return
        super(ToolTableEditorDelegate, self).setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox) and editor.property(BOOL_EDITOR_PROP):
            model.setData(index, editor.currentText() == 'True',
                          Qt.ItemDataRole.EditRole)
            return
        super(ToolTableEditorDelegate, self).setModelData(editor, model, index)

    @staticmethod
    def _popOpenOnceShown(combo, delay_ms=0):
        """Open the dropdown the instant the editor appears, instead of
        requiring a second tap on the (tiny, easy-to-miss on a touchscreen)
        arrow button after the first double-click/tap creates it.

        delay_ms matters for editable combos specifically: non-editable
        ones (e.g. a strict-enum column) open fine at 0ms because Qt's own
        native mouseDoubleClickEvent handling opens those synchronously as
        part of the same double-click, which correctly accounts for the
        initiating click's mouse button still being logically "down".
        Editable combos never auto-open natively, so *our* showPopup()
        call is the only thing opening them -- firing it before that
        button-down state has fully drained through the event queue races
        Qt's popup grab into treating the eventual release as "dismiss",
        closing it almost immediately (confirmed live; see callers for the
        delay each editor type actually needs).
        """
        def _fire():
            # The popup defaults to the combo's own width (i.e. the cell/
            # column's width), which the item padding above then eats into --
            # long entries were getting elided even though the column
            # itself is wide enough to show them as plain (non-editing)
            # cell text. Widen the popup to actually fit its widest item
            # instead of inheriting the cell's (possibly narrower) width.
            view = combo.view()
            if view is not None:
                hint = view.sizeHintForColumn(0)
                if hint > 0:
                    view.setMinimumWidth(hint + 24)
            combo.showPopup()
        QTimer.singleShot(delay_ms, _fire)


class ToolTableEditor(QTableView):
    toolSelected = Signal(int)
    dirtyChanged = Signal(bool)

    # Machine variants subclass and point this at their model (see
    # probe_basic's LatheToolTable/MillToolTable) -- everything else in
    # this widget consults the model's own class attributes.
    MODEL_CLASS = ToolTableEditorModel

    def __init__(self, parent=None):
        super(ToolTableEditor, self).__init__(parent)

        self.clicked.connect(self.onClick)
        self.doubleClicked.connect(self.onDoubleClick)

        self.tool_model = self.MODEL_CLASS(self)
        self.tool_model.dirtyChanged.connect(self.dirtyChanged.emit)

        if not IN_DESIGNER and self.tool_model.tt is not None:
            self.tool_model.tt.tool_table_changed.connect(self._onToolTableChanged)

        self.item_delegate = ToolTableEditorDelegate(self.tool_model, self)
        self.setItemDelegate(self.item_delegate)

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setFilterKeyColumn(0)
        self.proxy_model.setSourceModel(self.tool_model)
        self.setModel(self.proxy_model)

        self._confirm_actions = False
        self._current_tool_color = QColor('sage')
        self._current_tool_bg = None

        self.setSortingEnabled(True)
        self.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        # Center the tool numbers (the styled default is left/vcenter) and
        # give them 3px of breathing room on the right -- ResizeToContents
        # sizes the header to the text alone, which left the numbers
        # touching the right border edge. Padding-only stylesheet, scoped
        # to this header instance: the theme's global QHeaderView rule
        # (background/color/font) still cascades in for everything not set
        # here, so this can't repeat a solid-black regression (that would
        # come from overriding background-color itself).
        self.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verticalHeader().setStyleSheet(
            'QHeaderView::section { padding-right: 3px; }')
        # Double-clicking a cell in the (permanently non-editable) T column
        # already opens the renumber dialog (see onDoubleClick) -- now that
        # the row header is *also* effectively a pinned tool-number label
        # (it stays put through horizontal scrolling, unlike the real T
        # column), give it the same affordance.
        self.verticalHeader().sectionDoubleClicked.connect(
            self._onRowHeaderDoubleClicked)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setWordWrap(False)
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        # NOT unconditionally setStretchLastSection(True): it forces the
        # last visible column to exactly fill whatever space remains after
        # the others take their content-sized width -- shrinking it *below*
        # its own content's needed width if the rest already fill the
        # viewport (e.g. a "Holder" column showing "GROOVE EXTERNAL" got
        # clipped this way). But leaving it permanently off left a bare gap
        # after the last column for the classic (core-columns-only, fewer/
        # narrower columns) backend, which rarely fills the viewport at
        # all. _updateLastColumnStretch() below toggles it dynamically:
        # stretch only when there's genuinely leftover width to fill.
        self.horizontalHeader().setSortIndicator(0, Qt.AscendingOrder)

        # Per-item vertical scrolling (Qt's default) stops short of the
        # last row whenever the viewport height isn't an exact multiple of
        # row height -- the remaining sliver isn't enough to trigger one
        # more scroll step, so the last row sits half (or fully) clipped at
        # the bottom. Per-pixel scrolling has no such quantization.
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        # per-column visibility menu
        header = self.horizontalHeader()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self._onHeaderContextMenu)

        # cell context menu: copyable G-code/Rules access names for the
        # clicked cell's column (tool_data.ngc params, Rules channel)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._onCellContextMenu)

        self._updateLastColumnStretch()

    def resizeEvent(self, event):
        super(ToolTableEditor, self).resizeEvent(event)
        self._updateLastColumnStretch()

    def _updateLastColumnStretch(self):
        """Stretch the last visible column to fill any leftover viewport
        width -- but only when there actually is leftover width. Whether
        that's true depends on the current viewport size *and* how many/
        how wide the visible columns are (e.g. the classic core-columns-
        only backend rarely fills the viewport at all; the full DB-backed
        table with several extras/custom columns visible often already
        exceeds it) -- not fixed, so this recomputes on every resize
        rather than being decided once from the backend alone."""
        header = self.horizontalHeader()
        count = header.count()
        if count == 0:
            return

        if header.stretchLastSection():
            # Un-stretch first to measure the last column's own actual
            # content-based width -- while stretching is on, sectionSize()
            # for it reports the stretched size, not its natural one.
            header.setStretchLastSection(False)
            self.resizeColumnToContents(count - 1)

        total_width = sum(header.sectionSize(i) for i in range(count))
        header.setStretchLastSection(total_width < self.viewport().width())

    def _refreshDelegate(self):
        """Shared tail for anything that changes the visible/available
        column set (Add/Remove Column, visibility toggles): the delegate
        caches column info that needs rebuilding, and whether the last
        column should stretch can change along with the column set."""
        self.item_delegate = ToolTableEditorDelegate(self.tool_model, self)
        self.setItemDelegate(self.item_delegate)
        self._updateLastColumnStretch()

    # ------------------------------------------------------------ sync

    @Slot(dict)
    def _onToolTableChanged(self, table):
        if not table or len(table) <= 1:
            return
        self.proxy_model.invalidate()
        self.sortByColumn(0, Qt.AscendingOrder)

    # ------------------------------------------------------- column menu

    def _onHeaderContextMenu(self, position):
        header = self.horizontalHeader()
        menu = QMenu(self)

        clicked_idx = header.logicalIndexAt(position)
        visible_cols = self.tool_model.visibleColumns()
        clicked_key = (visible_cols[clicked_idx]
                       if 0 <= clicked_idx < len(visible_cols) else None)

        # Custom columns are a DB-backed-only concept (qtpyvcp.plugins.
        # tool_table:ToolTable, the classic file-based backend, has no
        # custom-field storage) -- offering "Add Column..." against that
        # backend would just crash in AddColumnDialog. remove_column never
        # needs the same guard: _custom_columns is always empty without a
        # DB backend, so there's never a custom column to right-click.
        add_column = None
        if self.tool_model._db_backed:
            add_column = menu.addAction('Add Column...')
        remove_column = None
        if clicked_key and self.tool_model.columnGroup(clicked_key) == 'custom':
            remove_column = menu.addAction(
                'Remove Column "%s"...' % self.tool_model.columnLabel(clicked_key))
        menu.addSeparator()
        show_all = menu.addAction('Show All Columns')
        reset_default = menu.addAction('Reset Default Columns')
        menu.addSeparator()

        visible = set(self.tool_model.visibleColumns())
        sections = {'core': [], 'extras': [], 'custom': []}
        for key in self.tool_model.allColumns():
            sections[self.tool_model.columnGroup(key)].append(key)

        group_labels = dict(GROUP_LABELS,
                            extras=self.tool_model.EXTRAS_GROUP_LABEL)
        toggles = {}
        for group in ('core', 'extras', 'custom'):
            keys = sections[group]
            if not keys:
                continue
            section_menu = menu.addMenu(group_labels[group])
            for key in keys:
                action = section_menu.addAction(self.tool_model.columnLabel(key))
                action.setCheckable(True)
                action.setChecked(key in visible)
                toggles[action] = key

        selected = menu.exec(header.mapToGlobal(position))
        if selected is None:
            return

        if selected == add_column:
            self.showAddColumnDialog()
        elif remove_column is not None and selected == remove_column:
            self._removeCustomColumn(clicked_key)
            return  # column set already refreshed via fields_changed
        elif selected == show_all:
            self.tool_model.setVisibleColumns(self.tool_model.allColumns())
        elif selected == reset_default:
            self.tool_model.setVisibleColumns(self.tool_model._default_visible_columns())
        elif selected in toggles:
            key = toggles[selected]
            cols = self.tool_model.visibleColumns()
            if selected.isChecked():
                if key not in cols:
                    cols.append(key)
            else:
                cols = [c for c in cols if c != key]
                if not cols:
                    QMessageBox.warning(self, 'Tool Table',
                                        'At least one column must remain visible.')
                    return
            self.tool_model.setVisibleColumns(cols)
        else:
            return

        self._refreshDelegate()

    def _onCellContextMenu(self, position):
        index = self.indexAt(position)
        if not index.isValid():
            return
        menu = QMenu(self)
        params_action = menu.addAction('Parameter Names (G-code / Rules)...')
        if menu.exec(self.viewport().mapToGlobal(position)) is params_action:
            source = self.proxy_model.mapToSource(index)
            self._showParameterNamesDialog(
                source.row(),
                self.tool_model.visibleColumns()[source.column()])

    def _showParameterNamesDialog(self, source_row, col_key):
        """Copyable access names for one cell -- what to paste into a
        subroutine (tool_data.ngc params) or a widget rule."""
        group = self.tool_model.columnGroup(col_key)
        if group == 'custom':
            is_text = (self.tool_model._custom_value_types.get(col_key)
                       == 'text')
        else:
            is_text = col_key in self.tool_model.TEXT_EXTRAS or col_key == 'R'
        tool_no = self.tool_model.toolDataFromRow(source_row)['T']
        entries, note = parameter_entries(col_key, group, is_text, tool_no)
        dialog = ParameterNamesDialog(
            'Access Names -- %s (T%s)' % (self.tool_model.columnLabel(col_key),
                                          tool_no),
            entries, note, self)
        dialog.exec()

    @Slot()
    def showAddColumnDialog(self):
        """Define a new custom column -- grows the table immediately; no
        schema migration, no restart."""
        dialog = AddColumnDialog(self.tool_model.tt, self)
        before_all = set(self.tool_model.allColumns())
        if dialog.exec() == AddColumnDialog.DialogCode.Accepted:
            # fields_changed (emitted by addCustomField) already refreshed
            # tool_model's column bookkeeping; make the newly-defined column
            # visible too, so the user sees it land without a second trip
            # to this menu.
            new_keys = set(self.tool_model.allColumns()) - before_all
            if new_keys:
                self.tool_model.setVisibleColumns(
                    self.tool_model.visibleColumns() + list(new_keys))
            self._refreshDelegate()

    def _removeCustomColumn(self, key):
        """Delete a custom column definition -- and every tool's value in
        it -- permanently (cascades via the DB's FK)."""
        name = key[len(CUSTOM_PREFIX):]
        label = self.tool_model.columnLabel(key)
        if not self.confirmAction(
                'Delete custom column "%s"?\n'
                'This removes it, and every tool\'s value in it, '
                'permanently.' % label):
            return
        self.tool_model.tt.removeCustomField(name)
        self._refreshDelegate()

    # ------------------------------------------------------------ slots

    @Slot()
    def saveToolTable(self):
        if not self.confirmAction("Do you want to save changes and\n"
                                  "load tool table into LinuxCNC?"):
            return
        self.tool_model.saveToolTable()

    @Slot()
    def loadToolTable(self):
        if not self.confirmAction("Do you want to re-load the tool table?\n"
                                  "All unsaved changes will be lost."):
            return
        self.tool_model.loadToolTable()

    @Slot()
    def deleteSelectedTool(self):
        current_row = self.selectedRow()
        if current_row == -1:
            return

        tdata = self.tool_model.toolDataFromRow(current_row)
        tnum = tdata['T']

        if tnum == self.tool_model.stat.tool_in_spindle:
            box = QMessageBox(QMessageBox.Warning,
                              "Can't delete current tool!",
                              "Tool #{} is currently loaded in the spindle.\n"
                              "Please remove tool from spindle and try again.".format(tnum),
                              QMessageBox.StandardButton.Ok,
                              parent=self)
            box.show()
            return False

        if not self.confirmAction('Are you sure you want to delete T{tdata[T]}?\n'
                                  '"{tdata[R]}"'.format(tdata=tdata)):
            return

        self.tool_model.removeTool(current_row)

    @Slot()
    def renumberSelectedTool(self):
        """Renumber the selected tool in place (extras/custom data follow --
        this is not a delete+recreate; see ToolTableEditorModel.renumberTool)."""
        current_row = self.selectedRow()
        if current_row == -1:
            return
        tdata = self.tool_model.toolDataFromRow(current_row)
        old_tnum = tdata['T']

        new_tnum, ok = QInputDialog.getInt(
            self, 'Renumber Tool', 'New tool number for T%s:' % old_tnum,
            value=old_tnum, minValue=1, maxValue=99999)
        if not ok or new_tnum == old_tnum:
            return

        try:
            self.tool_model.renumberTool(current_row, new_tnum)
        except (LookupError, ValueError) as exc:
            QMessageBox.warning(self, 'Renumber Tool', str(exc))

    @Slot()
    def selectPrevious(self):
        self.selectRow(self.selectedRow() - 1)
        return True

    @Slot()
    def selectNext(self):
        self.selectRow(self.selectedRow() + 1)
        return True

    @Slot()
    def clearToolTable(self, confirm=True):
        if confirm:
            if not self.confirmAction("Do you want to delete the whole tool table?"):
                return
        self.tool_model.clearToolTable()

    @Slot()
    def addTool(self):
        self.tool_model.addTool()
        self.selectRow(self.tool_model.rowCount() - 1)

    @Slot()
    def loadSelectedTool(self):
        current_row = self.selectedRow()
        if current_row == -1:
            return
        tnum = self.tool_model.toolDataFromRow(current_row)['T']
        issue_mdi("T%s M6" % tnum)

    def selectedRow(self):
        return self.selectionModel().currentIndex().row()

    def onClick(self, index):
        row = index.row()
        tnum = self.tool_model.toolDataFromRow(row)['T']
        self.toolSelected.emit(tnum)

    def onDoubleClick(self, index):
        """The T column is never directly editable (see
        ToolTableEditorModel.flags: a raw cell edit can't re-key the outer
        table dict), so double-clicking it doesn't open the normal
        in-place editor. Route it to renumberSelectedTool() instead -- same
        dialog the (also existing, but otherwise unreachable in the UI)
        Renumber action opens."""
        source_index = self.proxy_model.mapToSource(index)
        col_key = self.tool_model.visibleColumns()[source_index.column()]
        if col_key == 'T':
            self.renumberSelectedTool()

    def _onRowHeaderDoubleClicked(self, logical_row):
        """logical_row is already in view (proxy/sorted) row space -- same
        numbering QHeaderView uses for any row header, since rows (unlike
        columns) can't be drag-reordered independently of sort order."""
        self.selectRow(logical_row)
        self.renumberSelectedTool()

    def confirmAction(self, message):
        if not self._confirm_actions:
            return True
        box = QMessageBox.question(self, 'Confirm Action', message,
                                   QMessageBox.StandardButton.Yes,
                                   QMessageBox.StandardButton.No)
        return box == QMessageBox.StandardButton.Yes

    # Explicit setFoo()/foo() pairs alongside each @Property below: uic-
    # generated setupUi() code calls the conventional Qt Designer accessor
    # names directly (e.g. self.tooltable.setConfirmActions(True)), not the
    # Python property descriptor -- confirmed by compiling a scratch .ui
    # with these properties set and finding AttributeError without these.
    # (The stock qtpyvcp ToolTable widget has the same @Property-only gap;
    # it's just never been exercised because no .ui sets those properties
    # on it today.)

    @Property(bool)
    def confirmActions(self):
        return self._confirm_actions

    @confirmActions.setter
    def confirmActions(self, confirm):
        self._confirm_actions = confirm

    def setConfirmActions(self, confirm):
        self._confirm_actions = confirm

    @Property(QColor)
    def currentToolColor(self):
        return self.tool_model.current_tool_color

    @currentToolColor.setter
    def currentToolColor(self, color):
        self.tool_model.current_tool_color = color

    def setCurrentToolColor(self, color):
        self.tool_model.current_tool_color = color

    @Property(QColor)
    def currentToolBackground(self):
        return self.tool_model.current_tool_bg or QColor()

    @currentToolBackground.setter
    def currentToolBackground(self, color):
        self.tool_model.current_tool_bg = color

    def setCurrentToolBackground(self, color):
        self.tool_model.current_tool_bg = color

    @Property(int)
    def currentRow(self):
        return self.selectedRow()

    @currentRow.setter
    def currentRow(self, row):
        self.selectRow(row)

    def setCurrentRow(self, row):
        self.selectRow(row)
