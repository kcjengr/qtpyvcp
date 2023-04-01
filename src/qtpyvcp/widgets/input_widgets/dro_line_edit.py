"""
DROLineEdit
-----------

"""

from qtpy.QtCore import Qt, Property
from qtpyvcp.widgets.base_widgets.eval_line_edit import EvalLineEdit

from qtpyvcp.widgets.base_widgets.dro_base_widget import DROBaseWidget, Axis, LatheMode
from qtpyvcp.actions.machine_actions import issue_mdi

from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)


class DROLineEdit(EvalLineEdit, DROBaseWidget):
    """DROLineEdit

    DRO that supports typing in desired position to set work coordinate offset.
    """

    def __init__(self, parent=None):
        super(DROLineEdit, self).__init__(parent)

        self.returnPressed.connect(self.onReturnPressed)
        self.editingFinished.connect(self.onEditingFinished)
        self.textEdited.connect(self.setCurrentPos)

        issue_mdi.bindOk(widget=self)
        
        self.last_commanded_pos = self.status.stat.position[self._anum]

    def onReturnPressed(self):
        try:
            val = float(self.text().strip().replace('mm', '').replace('in', ''))
            g5x_index = self.status.stat.g5x_index
            axis = 'XYZABCUVW'[self._anum]

            if self._is_lathe and self._anum == Axis.X:
                if self._lathe_mode == LatheMode.Diameter and not self._g7_active:
                    val = val / 2
                elif self._lathe_mode == LatheMode.Radius and self._g7_active:
                    val = val * 2

            cmd = 'G10 L20 P{0:d} {1}{2:.12f}'.format(g5x_index, axis, val)
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
