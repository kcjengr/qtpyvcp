"""
DROLineEdit
-----------

"""

import os
from PySide6.QtCore import Qt, Property
from qtpyvcp.widgets.base_widgets.eval_line_edit import EvalLineEdit

from qtpyvcp.widgets.base_widgets.dro_base_widget import DROBaseWidget, Axis, LatheMode
from qtpyvcp.actions.machine_actions import issue_mdi

from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

IN_DESIGNER = os.getenv('DESIGNER', False)

class DROLineEdit(EvalLineEdit, DROBaseWidget):
    """DROLineEdit

    DRO that supports typing in desired position to set work coordinate offset.
    """

    def __init__(self, parent=None):
        super(DROLineEdit, self).__init__(parent)
        # Ensure DROBaseWidget initialises (EvalLineEdit.__init__ doesn't chain)
        DROBaseWidget.__init__(self)

        self.returnPressed.connect(self.onReturnPressed)
        self.editingFinished.connect(self.onEditingFinished)
        self.textEdited.connect(self.setCurrentPos)

        #  issue_mdi.bindOk(widget=self)
        if IN_DESIGNER:
            return
        self.last_commanded_pos = self.status.stat.position[self._anum]

    def onReturnPressed(self):
        try:
            val = float(self.text().strip().replace('mm', '').replace('in', ''))
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

            issue_mdi(cmd)
        except Exception:
            LOG.exception("Error setting work coordinate offset.")

        self.blockSignals(True)
        self.clearFocus()
        self.blockSignals(False)

    def onEditingFinished(self):
        self.updateValue()

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
    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            super(DROLineEdit, self).updateValue()
        else:
            super(DROLineEdit, self).keyPressEvent(e)
