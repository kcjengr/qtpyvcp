
from qtpy.QtCore import Qt, Slot, Property, QStringListModel
from qtpy.QtGui import QValidator
from qtpy.QtWidgets import QLineEdit, QListWidgetItem, QCompleter
from qtpyvcp.utilities import logger
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.info import Info
from qtpyvcp.actions.machine_actions import issue_mdi
from qtpyvcp.widgets.base_widgets.base_widget import CMDWidget
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

STATUS = getPlugin('status')
INFO = Info()
LOG = logger.getLogger('qtpyvcp.' + __name__)

class Validator(QValidator):
    def validate(self, string, pos):
        # eventually could do some actual validating here
        inputVal = string
        if not(inputVal.startswith(";") or inputVal.startswith("(")):
            inputVal = inputVal.upper();
        return QValidator.Acceptable, inputVal, pos

class MdiCompleter(QCompleter):
    def __init__(self, parent=None):
        super(MdiCompleter, self).__init__(parent)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.model = QStringListModel()
        self.setModel(self.model)

    def setValues(self, values):
        self.model.setStringList(list(dict.fromkeys(values)))
        #self.popup().setItemDelegate(QStyledItemDelegate())


class MDIEntry(QLineEdit, CMDWidget):
    """MDI Entry

    Input any valid g Code. Enter sends the g Code.
    """
    def __init__(self, parent=None):
        super(MDIEntry, self).__init__(parent)

        self.mdi_history_size = 100
        self.mdiCompleter = MdiCompleter()
        self.setCompleter(self.mdiCompleter)

        self.validator = Validator(self)
        self.setValidator(self.validator)

        self.returnPressed.connect(self.submit)

    @Property(int)
    def mdi_history_size(self):
        return self._mdi_history_size

    @mdi_history_size.setter
    def mdi_history_size(self, size):
        self._mdi_history_size = size

    @Slot()
    def submit(self):
        cmd = str(self.text()).strip()
        issue_mdi(cmd)
        self.setText('')
        STATUS.mdi_history.setValue(cmd)

    @Slot(QListWidgetItem)
    def setMDIText(self, listItem):
        if listItem is not None:
            self.setText(listItem.text())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up or event.key() == Qt.Key_Down:
            self.completer().complete()
        else:
            super(MDIEntry, self).keyPressEvent(event)

    def focusInEvent(self, event):
        super(MDIEntry, self).focusInEvent(event)
        self.completer().complete()

    def initialize(self):
        history = STATUS.mdi_history.value
        LOG.debug("------mdi initialize:{} {}".format(type(history), history))
        self.mdiCompleter.setValues(history)
        STATUS.max_mdi_history_length = self.mdi_history_size
        STATUS.mdi_history.notify(self.mdiCompleter.setValues)

    def terminate(self):
        pass
