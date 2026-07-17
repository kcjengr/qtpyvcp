# coding=utf-8
"""MillToolModel/MillToolTable -- mill flavor of the unified tool table
editor (see tool_table_editor.ToolTableEditorModel/ToolTableEditor for the
mechanism this configures). A sibling of LatheToolModel/LatheToolTable (not
a subclass of them) -- the mill has no use for the lathe's insert/holder
vocabulary or its OPEN_VOCAB_SEED_OPTIONS-driven combo lookups, so it
inherits directly from the generic base instead of dragging lathe-only
methods along unused.

Pairs with the ``mill`` extras flavor ``qtpyvcp.plugins.db_tool_table``
already ships (``EXTRAS_TABLES['mill'] -> ToolMill``): a single column,
ATC (tool_mill.atc, schema v3) -- a per-tool boolean for whether the tool
is physically storable in an automatic tool changer. False marks an
oversize tool a carousel-driving M6 remap should never auto-stow into (or
auto-fetch from); a VCP with that kind of remap can use it to fall back to
a manual tool change dialog instead. Every tool imports/creates as
ATC-storable (the tool_mill.atc schema default) -- mark oversize
exceptions in the tool table editor afterward.

This is a ratified default (built to cover a real gap the stock LinuxCNC
tool table has no data for) not a hardcoded ceiling: hide it via the
header's column-visibility menu if a VCP has no ATC concept at all, or add
further columns via the DB backend's custom-field support.
"""

from .tool_table_editor import ToolTableEditorModel, ToolTableEditor


class MillToolModel(ToolTableEditorModel):

    EXTRAS_LABELS = {'atc': 'ATC'}
    TEXT_EXTRAS = frozenset()
    BOOL_EXTRAS = frozenset(('atc',))
    # A tool with no tool_mill row yet reads as storable -- matches the
    # schema default (003_tool_mill.sql: atc DEFAULT 1) and the established
    # all-tools-automatic behavior: only the oversize exceptions get
    # unchecked, a blank cell never silently means "manual only".
    EXTRAS_DEFAULTS = {'atc': True}
    DEFAULT_VISIBLE_EXTRAS = ['atc']
    EXTRAS_GROUP_LABEL = 'Mill Extras'
    # Remark renders last, so ATC (and any future mill extras) sit between
    # the numeric offset columns and the wide free-text Remark column.
    TRAILING_CORE_COLUMNS = ('R',)


class MillToolTable(ToolTableEditor):

    MODEL_CLASS = MillToolModel
