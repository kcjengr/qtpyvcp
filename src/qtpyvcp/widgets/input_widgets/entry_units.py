"""
Entry Units
-----------

Unit handling shared by the number entry fields (VCPSettingsLineEdit and
VCPVarLineEdit).

Every value with a unit is a length (a feed or a surface speed is a length
per minute or per rev), so a field only needs to know what size its number
is. That is set by ticking one of two checkboxes in Designer:

* ``unitsInMm`` -- the value is in mm on a metric machine, in on an inch one
* ``unitsFtM`` -- the value is in m on a metric machine, ft on an inch one

The machine is metric or inch by its ``[TRAJ] LINEAR_UNITS``. A bare number
is taken as the field's unit; a number typed with any unit (``38mm``,
``1.5in``, ``600ft``) is converted into it by cnc_eval.

A settings field always stores its value in the machine's units. A screen
can show it in the other system with ``setDisplayUnitsSource`` -- a lathe
conversational page, for one, shows its numbers in the page's own INCH/MM.
That changes only what is shown and typed; the stored value is the same size
either way.

A whole-number field with a box ticked, such as a surface speed, rounds the
converted value: 600ft into a metric one is 182.88 m, stored as 183.

The two are exclusive, ticking one clears the other, and both start clear, so
a field takes plain numbers only until one is ticked. They are checkboxes
rather than text because a checkbox cannot be misspelt, and PySide6 cannot
give a Python widget an enum (drop-down) property that Designer and the
runtime loader both understand.

While a number is being typed, the field's ``entryState`` property says
whether Enter would accept it, for the stylesheet to show:

* ``editing`` -- the entry would be accepted
* ``error`` -- it would not; Enter leaves it in place with the text selected
* empty -- not being edited

    QLineEdit[entryState="editing"] { border-bottom: 3px solid blue; }
    QLineEdit[entryState="error"] { border-bottom: 3px solid red;
                                    selection-background-color: red; }

It is its own property, not ``style``: rules set ``style`` (e.g. a "bad"
class when a value is out of range), and the two must not overwrite each
other.
"""

import math

from qtpyvcp.utilities.misc import (CNC_EXPRESSION_PATTERN, CNC_UNIT_EXPRESSION_PATTERN,
                                    CNC_UNITS_IN_METRES)

# Each unit scale and the unit a field holds its value in on a metric and on
# an inch machine.
UNIT_SCALES = {
    'in_mm': ('mm', 'in'),
    'ft_m': ('m', 'ft'),
}


def unit_system_is_metric():
    """True for a metric machine, False for inch, None if it can't be told.

    Read from [TRAJ] LINEAR_UNITS through Info, the same reading the rest of
    qtpyvcp uses.
    """
    try:
        from qtpyvcp.utilities.info import Info
        return Info().getIsMachineMetric()
    except Exception:
        # Designer, or no INI loaded: no unit system, so no unit suffixes
        return None


def entry_base_unit(scale, metric=None):
    """Return the unit a field with this scale holds its value in, or None.

    metric says which system the field is in; left as None it is the
    machine's, from the INI. None back means the field takes plain numbers
    only: it has no scale, or its unit system can't be told.
    """
    if scale not in UNIT_SCALES:
        return None
    if metric is None:
        metric = unit_system_is_metric()
    if metric is None:
        return None
    return UNIT_SCALES[scale][0 if metric else 1]


# A value converted between inch and metric is rounded to take off the
# conversion's float noise: to STORED_FIGURES significant figures when it is
# stored, to SHOWN_FIGURES when it is shown or handed out. Shown coarser than
# stored, a value always converts back to exactly the number typed (3 mm is
# stored as 0.118110236220472 in and shows 3 again). Rounded the same both
# ways the last figure can drift, and rounded to decimal places a small inch
# value loses figures.
STORED_FIGURES = 15
SHOWN_FIGURES = 12


def round_figures(value, figures):
    """value to this many significant figures."""
    return float('%.*g' % (figures, value))


def to_unit_system(value, scale, from_metric, to_metric=None):
    """value, a number of this scale's kind given in metric (True) or inch
    (False) units, in the other system's -- the machine's (INI) when to_metric
    is None -- to be stored. Back unchanged if either system can't be told.
    Not rounded to a whole number; a whole-number setting does that with
    round_whole."""
    source = entry_base_unit(scale, from_metric) if from_metric is not None else None
    target = entry_base_unit(scale, to_metric)
    if not source or not target or source == target:
        return value
    return round_figures(float(value) * CNC_UNITS_IN_METRES[source] / CNC_UNITS_IN_METRES[target],
                         STORED_FIGURES)


def round_whole(value):
    """Round to the nearest whole number, halves away from zero (182.5 -> 183).

    Python's round() sends halves to the even number (182.5 -> 182), which is
    not what anyone reading the field expects.
    """
    return int(math.copysign(math.floor(abs(value) + 0.5), value))


def entry_pattern(scale):
    """Keyboard pattern for a field: unit letters allowed only if it has a scale."""
    return CNC_UNIT_EXPRESSION_PATTERN if scale in UNIT_SCALES else CNC_EXPRESSION_PATTERN


ENTRY_STATE_PROPERTY = 'entryState'


def set_entry_state(widget, state):
    """Set a field's entryState ('', 'editing' or 'error') and restyle it."""
    if (widget.property(ENTRY_STATE_PROPERTY) or '') == state:
        return
    widget.setProperty(ENTRY_STATE_PROPERTY, state)
    # A stylesheet only re-reads a dynamic property when the widget is polished again
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()
