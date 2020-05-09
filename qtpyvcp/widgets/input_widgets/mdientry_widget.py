
from qtpy.QtCore import Qt, QStringListModel, Slot
from qtpy.QtGui import QValidator
from qtpy.QtWidgets import QLineEdit, QCompleter

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.info import Info
from qtpyvcp.actions.machine_actions import issue_mdi
from qtpyvcp.widgets.base_widgets.base_widget import CMDWidget

STATUS = getPlugin('status')
INFO = Info()
MDI_HISTORY_FILE = INFO.getMDIHistoryFile()


class Validator(QValidator):
    def validate(self, string, pos):
        # eventually could do some actual validating here
        return QValidator.Acceptable, string.upper(), pos


class MDIEntry(QLineEdit, CMDWidget):
    """MDI Entry
    
    Input any valid g Code. Enter sends the g Code.
    """
    def __init__(self, parent=None):
        super(MDIEntry, self).__init__(parent)

        self.model = QStringListModel()

        completer = QCompleter()
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setModel(self.model)
        self.setCompleter(completer)

        self.validator = Validator(self)
        self.setValidator(self.validator)

        self.returnPressed.connect(self.submit)

    @Slot()
    def submit(self):
        cmd = str(self.text()).strip()
        issue_mdi(cmd)
        self.setText('')
        STATUS.mdi_history.setValue(cmd)

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
        self.model.setStringList(history)
        STATUS.mdi_history.notify(self.model.setStringList)

    def terminate(self):
        pass
