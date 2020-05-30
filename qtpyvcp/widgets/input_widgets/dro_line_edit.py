"""
DROLineEdit
-----------

"""

from qtpy.QtCore import Property
from qtpy.QtWidgets import QLineEdit

from qtpyvcp.widgets.base_widgets.dro_base_widget import DROBaseWidget
from qtpyvcp.actions.machine_actions import issue_mdi

from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)


class DROLineEdit(QLineEdit, DROBaseWidget):
    """DROLineEdit

    DRO that supports typing in desired position to set work coordinate offset.
    """

    def __init__(self, parent=None):
        super(DROLineEdit, self).__init__(parent)

        self.returnPressed.connect(self.onReturnPressed)
        self.editingFinished.connect(self.onEditingFinished)

        issue_mdi.bindOk(widget=self)

    def onReturnPressed(self):
        try:
            val = float(self.text().strip().replace('mm', '').replace('in', ''))
            g5x_index = self.status.stat.g5x_index
            axis = 'XYZABCUVW'[self._anum]

            cmd = 'G10 L20 P{0:d} {1}{2:.12f}'.format(g5x_index, axis, val)
            issue_mdi(cmd)
        except Exception:
            LOG.exception("Error setting work coordinate offset.")

        self.blockSignals(True)
        self.clearFocus()
        self.blockSignals(False)

    def onEditingFinished(self):
        self.updateValue()

    @Property(str)
    def inputType(self):
        return 'int'
