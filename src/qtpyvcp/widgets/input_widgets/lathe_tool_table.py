# coding=utf-8
"""LatheToolModel/LatheToolTable -- lathe flavor of the unified tool table
editor (see tool_table_editor.ToolTableEditorModel/ToolTableEditor for the
mechanism this configures).

Pairs with the ``lathe`` extras flavor ``qtpyvcp.plugins.db_tool_table``
already ships (``EXTRAS_TABLES['lathe'] -> ToolLathe``, the DB schema's
own first-class lathe columns) -- this is that schema's reference UI
presentation: labels, which columns are strict enums vs. open-vocabulary
vs. free text, and sensible default visibility, plus the insert-shape/
holder-style option lookups an open-vocabulary combo editor needs (see
ToolTableEditorModel.openVocabOptionsFor).

These are ratified defaults (built to cover real gaps the stock LinuxCNC
tool table has no data for -- insert geometry, holder identification,
threading parameters -- not arbitrary choices), not a hardcoded ceiling: a
VCP can hide any of these via the header's column-visibility menu, or add
its own columns entirely via the DB backend's custom-field support. Treat
this as a working starting point most lathe VCPs will want, override by
subclassing where it doesn't fit.

Core columns are the same letter-keyed data (T P X Z D I J Q R ...) served
by ``qtpyvcp.plugins.db_tool_table.DBToolTable``; extras are ``tool_lathe``
attribute names; custom fields are keyed ``custom:<name>``. All three groups
are staged in one in-memory dict per tool and committed together by
:meth:`saveToolTable` -- one widget, one Save action, single-store rule.
Every column (core, extras, custom) locks while a program is running -- not
just the ones LinuxCNC itself reads live: a custom/extras value could still
be referenced by a subroutine or some other mid-program logic, so editing
any of it while the machine is running is unsafe practice regardless of
whether LinuxCNC's own interpreter happens to consume that particular
column.
"""

from .tool_table_editor import ToolTableEditorModel, ToolTableEditor

# tool_lathe columns, in display order -- labels for the header and the
# column-visibility menu.
EXTRAS_LABELS = {
    'type': 'Type',
    'insert_shape': 'Insert Shape',
    'insert_size_mode': 'Size Mode',
    'insert_size': 'Insert Size',
    'insert_thickness': 'Insert Thk',
    'holder_style': 'Holder',
    'holder_hand': 'Hand',
    'holder_shank_width': 'Shank W',
    'holder_cut_width': 'Cut W',
    'holder_head_length': 'Head Length',
    'holder_oal': 'Holder OAL',
    'groove_width': 'Groove W',
    'max_depth_of_cut': 'Max DOC',
    'drill_point_angle': 'Point Angle',
    'flute_length': 'Flute Len',
    'length_below_holder': 'Len Below Holder',
    'overall_length': 'Overall Len',
    'shaft_diameter': 'Shaft Dia',
    'chamfer_threads': 'Chamfer Thds',
    'thread_pitch_max': 'Max Pitch',
    'thread_angle': 'Thread Angle',
    'thread_tip_type': 'Tip Type',
    'surface_speed': 'Surface Speed',
    'feed_per_rev': 'Feed/Rev',
    'depth_of_cut': 'DOC',
    'notes': 'Notes',
}
EXTRAS_ORDER = list(EXTRAS_LABELS)  # dict preserves insertion order (py3.7+)

TEXT_EXTRAS = {'type', 'insert_shape', 'insert_size_mode', 'holder_style',
              'holder_hand', 'thread_tip_type', 'notes'}

# Extras columns that feed real machine-facing behavior somewhere -- the
# VTK insert display and/or conversational-style turning operations (core
# columns cover LinuxCNC itself and are always default-visible) -- are all
# shown by default: a user setting up a tool should see every parameter
# something actually consumes without having to know to unhide it first.
# The others excluded here are reference-only (nothing reads them back --
# same-named values elsewhere are per-operation user inputs, not tool-table
# reads).
#
# holder_oal is reference-only: it is the holder's full physical length,
# most of which is clamped in the tool block. Reach and slenderness are
# calculated from Head Length instead, so OAL feeds nothing and showing it
# by default invited it being read as the stickout -- which is exactly the
# mistake it caused before.
REFERENCE_ONLY_EXTRAS = ('holder_hand', 'thread_tip_type', 'chamfer_threads',
                         'surface_speed', 'feed_per_rev', 'depth_of_cut',
                         'notes', 'holder_oal')
DEFAULT_VISIBLE_EXTRAS = [c for c in EXTRAS_ORDER
                          if c not in REFERENCE_ONLY_EXTRAS]

# Strict, DB-enforced enums (CHECK constraints in migrations/001_initial.sql)
# -- these become non-editable combo pick-lists; the user literally cannot
# enter a value the database would reject.
TYPE_OPTIONS = ['turning', 'boring', 'grooving', 'parting', 'threading',
               'drill', 'tap', 'custom']
INSERT_SIZE_MODE_OPTIONS = ['IC', 'edge_length']
HOLDER_HAND_OPTIONS = ['R', 'L']
# Not DB-enforced, but a documented closed convention:
# "D=0 remains for thread_tip_type='point' inserts and is valid data".
THREAD_TIP_TYPE_OPTIONS = ['point', 'flat', 'radius']

STRICT_ENUM_OPTIONS = {
    'type': TYPE_OPTIONS,
    'insert_size_mode': INSERT_SIZE_MODE_OPTIONS,
    'holder_hand': HOLDER_HAND_OPTIONS,
    'thread_tip_type': THREAD_TIP_TYPE_OPTIONS,
}

# insert_shape and holder_style are open vocabularies in practice -- real
# data mixes plain ISO letters (turning: C/D/V/W) with descriptive codes for
# other tool families (grooving: "GROOVE SQUARE"; threading: "THREAD ISO
# TRIPLE"; holder_style: "GROOVE EXTERNAL", full ISO holder codes like
# "SCLCR", ...). These get an *editable* combo -- not a strict pick-list --
# but which choices are actually offered is discriminated by the row's own
# `type` (and, for holder_style, by the row's already-chosen `insert_shape`)
# rather than dumping every value ever used for any tool into one list --
# see LatheToolModel.insertShapeOptionsForType/holderStyleOptionsForRow.
OPEN_VOCAB_SEED_OPTIONS = {'insert_shape', 'holder_style'}

NO_INSERT_TYPES = {'drill', 'tap'}
GROOVING_TYPES = {'grooving', 'parting'}
THREADING_TYPES = {'threading'}

# turning/boring/custom insert shapes share one ISO-letter vocabulary.
GENERAL_INSERT_SHAPES = ['C', 'D', 'V', 'W', 'T', 'S', 'R']
GROOVING_INSERT_SHAPES = ['GROOVE SQUARE', 'GROOVE ROUND']
THREADING_INSERT_SHAPES = ['THREAD ISO TRIPLE', 'THREAD ISO DOUBLE']

GROOVING_HOLDER_STYLES = ['GROOVE EXTERNAL', 'GROOVE INTERNAL', 'GROOVE FACE']
THREADING_HOLDER_STYLES = ['THREAD STRAIGHT', 'THREAD FACE',
                           'THREAD INTERNAL', 'THREAD OFFSET']


class LatheToolModel(ToolTableEditorModel):

    EXTRAS_LABELS = EXTRAS_LABELS            # column key -> header label, in display order
    TEXT_EXTRAS = TEXT_EXTRAS                # extras rendered/edited as free text
    BOOL_EXTRAS = frozenset()                # extras rendered/edited as True/False
    EXTRAS_DEFAULTS = {}                     # value shown when a tool has no extras row
    DEFAULT_VISIBLE_EXTRAS = DEFAULT_VISIBLE_EXTRAS
    STRICT_ENUM_OPTIONS = STRICT_ENUM_OPTIONS
    OPEN_VOCAB_SEED_OPTIONS = OPEN_VOCAB_SEED_OPTIONS
    EXTRAS_GROUP_LABEL = 'Lathe Extras'      # header-menu section title
    # Core columns forced to render AFTER extras/custom instead of in their
    # normal core position -- empty by default (the lathe keeps Remark in
    # its ratified core position); the mill sets ('R',) so ATC lands just
    # before Remark. Membership only -- these stay 'core' for grouping;
    # only their column position moves.
    TRAILING_CORE_COLUMNS = ()
    DESIGNER_STUB_COLUMNS = ['T', 'P', 'X', 'Z', 'D', 'I', 'J', 'Q', 'R']

    # Shading rules -- REQUIRED_BY_TYPE / USED_BY_TYPE / REQUIRED_ALWAYS
    # and the internal-vs-external rule-key split -- are deliberately NOT
    # defined here. They encode which fields a *consumer* of the tool data
    # reads: a conversational addon's G-code builders and its collision
    # checks. This module cannot verify any of that, and a second copy of
    # rules that live somewhere else is a copy that drifts -- it did, twice,
    # in a single afternoon.
    #
    # The owner registers them instead:
    #
    #     LatheToolModel.registerRules(required_by_type=..., used_by_type=...,
    #                                  required_always=..., rule_key=...)
    #
    # Nothing registered means no shading, which is the correct behaviour for
    # a VCP with no such consumer -- see ToolTableEditorModel.registerRules().
    #
    # REQUIREMENT_KEY stays here: which column selects a rule set is a fact
    # about this schema, not about any consumer of it.
    REQUIREMENT_KEY = 'type'

    # Dead for every tool type -- the same list the default column layout
    # leaves hidden. Tinted whenever they hold a value. A property of the
    # lathe extras schema rather than of any one consumer, so it keeps its
    # default here; registerRules() can still override it.
    UNUSED_COLUMNS = frozenset(REFERENCE_ONLY_EXTRAS)

    def openVocabOptionsFor(self, key, row_data):
        tool_type = row_data.get('type')
        if key == 'insert_shape':
            return self.insertShapeOptionsForType(tool_type)
        if key == 'holder_style':
            return self.holderStyleOptionsForRow(tool_type, row_data.get('insert_shape'))
        return []

    def insertShapeOptionsForType(self, tool_type):
        """insert_shape choices valid for a given tool `type`."""
        t = (tool_type or '').strip().lower()
        if t in NO_INSERT_TYPES:
            return []  # no insert-shape concept for drills/taps

        if t in GROOVING_TYPES:
            seed = list(GROOVING_INSERT_SHAPES)
        elif t in THREADING_TYPES:
            seed = list(THREADING_INSERT_SHAPES)
        else:
            return list(GENERAL_INSERT_SHAPES)  # turning/boring/custom

        for value in self.distinctColumnValuesForType('insert_shape', t):
            if value not in seed:
                seed.append(value)
        return seed

    def holderStyleOptionsForRow(self, tool_type, insert_shape):
        """holder_style choices valid for a given tool `type`, further
        narrowed by the row's already-chosen `insert_shape` for turning/
        boring/custom tools. Full ISO holder codes (e.g. "SCLCR") encode
        their compatible insert shape as the 2nd character of the code --
        insert_shape 'C' pairs only with holder codes like SCLCR/SCLCL/
        SCMCN, never SDJCR -- so an insert shape discriminates which holder
        codes make physical sense."""
        t = (tool_type or '').strip().lower()
        if t in NO_INSERT_TYPES:
            return []  # no holder concept for drills/taps

        if t in GROOVING_TYPES:
            seed = list(GROOVING_HOLDER_STYLES)
            for value in self.distinctColumnValuesForType('holder_style', t):
                if value not in seed:
                    seed.append(value)
            return seed

        if t in THREADING_TYPES:
            seed = list(THREADING_HOLDER_STYLES)
            for value in self.distinctColumnValuesForType('holder_style', t):
                if value not in seed:
                    seed.append(value)
            return seed

        # turning / boring / custom -- one shared pool of full ISO holder
        # codes; narrow to ones compatible with the chosen insert shape.
        shape = (insert_shape or '').strip().upper()
        all_values = self.distinctColumnValues('holder_style')
        if len(shape) == 1:
            matching = [v for v in all_values if len(v) >= 2 and v[1].upper() == shape]
            if matching:
                return matching
        return all_values


class LatheToolTable(ToolTableEditor):

    # Machine variants subclass and point this at their model (see
    # mill_tool_table.MillToolTable).
    MODEL_CLASS = LatheToolModel
