"""
DROLineEdit
-----------

"""

import os
from PySide6.QtCore import Qt, Property, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QLineEdit

from qtpyvcp.widgets.base_widgets.dro_base_widget import DROBaseWidget, Axis, LatheMode
from qtpyvcp.actions.machine_actions import issue_mdi
from qtpyvcp.utilities.misc import cnc_eval
from qtpyvcp.widgets.input_widgets.entry_units import entry_pattern, set_entry_state

from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

IN_DESIGNER = os.getenv('DESIGNER', False)

class DROLineEdit(QLineEdit, DROBaseWidget):
    """DROLineEdit

    DRO that supports typing in desired position to set work coordinate offset.

    An entry follows the same rules as the number fields (cnc_eval): math,
    fractions, mixed numbers and power (``^`` or ``**``), and on a linear
    axis a unit -- ``25mm``, ``1in``, ``3/4"`` -- converted into the units
    the DRO shows, the active G20/G21. An angular axis (A, B, C) is in
    degrees and takes no unit. An entry can also work on the current
    position: ``+5`` adds, ``-=5`` subtracts, ``*2``, ``/2``, ``^2``, and
    ``-`` alone flips the sign, all on the actual position, never the
    rounded display.

    Enter sets the work offset (G10 L20) so the DRO reads the entry. An entry
    that can't be accepted stays, marked (``entryState``, see entry_units),
    until it is fixed or dropped with Esc. Leaving the field without Enter
    always puts the position back: an offset is only ever set by Enter.
    """

    def __init__(self, parent=None):
        super(DROLineEdit, self).__init__(parent)
        # Makes sure DROBaseWidget initialises if the cooperative chain does
        # not reach it; its own guard stops it running twice
        DROBaseWidget.__init__(self)

        self.returnPressed.connect(self.onReturnPressed)
        self.editingFinished.connect(self.onEditingFinished)
        self.textEdited.connect(self.setCurrentPos)
        self.textEdited.connect(self._onEntryEdited)

        #  issue_mdi.bindOk(widget=self)
        if IN_DESIGNER:
            return
        self.last_commanded_pos = self.status.stat.position[self._anum]

    def _entry_base_unit(self):
        """The unit an entry is in: the units the DRO shows, the active
        G20/G21. None on an angular axis -- degrees, which take no unit."""
        if self._angular_axis:
            return None
        return 'in' if str(self.status.program_units) == 'in' else 'mm'

    def _shows_diameter(self):
        return self._is_lathe and self._anum == Axis.X and (
            self._lathe_mode == LatheMode.Diameter
            or (self._lathe_mode == LatheMode.Auto and self._g7_active))

    def _current_position(self):
        """The position the DRO shows, unrounded: what +5 or /2 works on."""
        pos = getattr(self.pos, self._ref_typ.name).getValue()[self._anum]
        return pos * 2 if self._shows_diameter() else pos

    def _entry_value(self, text):
        """What an entry works out to, in the DRO's own terms (a diameter
        where it shows one), or ValueError if it can't be accepted."""
        return cnc_eval(text, self._entry_base_unit(), self._current_position())

    def _entry_acceptable(self, text):
        if not text.strip():
            # Cleared: Enter sets nothing and shows the position again
            return True
        try:
            self._entry_value(text)
        except ValueError:
            return False
        return True

    def _onEntryEdited(self, text):
        """Show while typing whether Enter would accept the entry."""
        set_entry_state(self, 'editing' if self._entry_acceptable(text) else 'error')

    def focusInEvent(self, event):
        # The keys a DRO takes: math, and unit letters only on a linear axis.
        # Set here rather than once, as the axis is set after construction.
        self.setValidator(QRegularExpressionValidator(QRegularExpression(
            entry_pattern(None if self._angular_axis else 'in_mm')), self))
        super(DROLineEdit, self).focusInEvent(event)

    def onReturnPressed(self):
        set_entry_state(self, '')
        if not self.text().strip():
            # Cleared: nothing to set
            self.blockSignals(True)
            self.clearFocus()
            self.blockSignals(False)
            super(DROLineEdit, self).updateValue()
            return
        try:
            val = self._entry_value(self.text())
            # Show the worked-out value, not what was typed (3/4" -> 19.050);
            # this also ends the edit, so the display follows the position
            self.setText(self._fmt % val)
            g5x_index = self.status.stat.g5x_index
            axis = 'XYZABCUVW'[self._anum]

            entered = val
            if self._is_lathe and self._anum == Axis.X:
                if self._lathe_mode == LatheMode.Diameter and not self._g7_active:
                    val = val / 2
                elif self._lathe_mode == LatheMode.Radius and self._g7_active:
                    val = val * 2

            cmd = 'G10 L20 P{0:d} {1}{2:.12f}'.format(g5x_index, axis, val)

            if self._is_lathe and self._anum == Axis.X:
                # The most useful record when a user reports the X DRO halving
                # what they typed. Logged loudly on mismatch so it is findable
                # in a screen grab of a DEBUG-level terminal.
                if self.latheG7Mismatch():
                    LOG.warning("bgred<==== LATHE-DRO G7 MISMATCH ====>")
                    LOG.warning("bgred<LATHE-DRO> typed=%s sent=%s cmd=%r",
                                entered, val, cmd)
                    LOG.warning("bgred<LATHE-DRO> %s", self.latheStateSummary())
                    LOG.warning("bgred<LATHE-DRO> DRO will display radius while "
                                "the machine is in diameter mode; the stored "
                                "offset is correct")
                else:
                    LOG.info("cyan<LATHE-DRO entry> typed=%s sent=%s cmd=%r  %s",
                             entered, val, cmd, self.latheStateSummary())

            elif self._anum == Axis.X and self.latheUndeclaredG7():
                # The moment the operator is actually bitten, so log it on
                # every entry rather than once -- this is what sits next to
                # the complaint in a submitted log.
                self.warnUndeclaredLatheG7(entered=entered, sent=val)

            issue_mdi(cmd)
        except Exception:
            LOG.exception("Error setting work coordinate offset.")

        self.blockSignals(True)
        self.clearFocus()
        self.blockSignals(False)

    def updateValue(self, pos=None):
        if self.pos.report_actual_pos and self.isModified():
            # Only update if commanded position changes when user is editing.
            if self.last_commanded_pos == self.status.stat.position[self._anum]:
                return None

        super(DROLineEdit, self).updateValue(pos)

    def setCurrentPos(self):
        # Run once user starts editing field.
        self.isEdited = True
        self.last_commanded_pos = self.status.stat.position[self._anum]
    
    def onEditingFinished(self):
        set_entry_state(self, '')
        self.updateValue()

    def keyPressEvent(self, e):
        if (e.key() in (Qt.Key_Return, Qt.Key_Enter)
                and not self._entry_acceptable(self.text())):
            # Refused: nothing is set; the entry stays, selected and marked,
            # until it is fixed, cleared or dropped with Esc
            set_entry_state(self, 'error')
            self.selectAll()
            e.accept()
            return
        if e.key() == Qt.Key_Escape:
            set_entry_state(self, '')
            super(DROLineEdit, self).updateValue()
        else:
            super(DROLineEdit, self).keyPressEvent(e)
