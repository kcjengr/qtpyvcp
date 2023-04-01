
from qtpy.QtCore import Qt, Slot, Property, QStringListModel
from qtpy.QtGui import QValidator
from qtpy.QtWidgets import QLineEdit, QListWidgetItem, QCompleter

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.info import Info
from qtpyvcp.actions.machine_actions import issue_mdi
from qtpyvcp.widgets.base_widgets.base_widget import CMDWidget

STATUS = getPlugin('status')
INFO = Info()


class Validator(QValidator):
    def validate(self, string, pos):
        # eventually could do some actual validating here
        inputVal = string
        if not(inputVal.startswith(";") or inputVal.startswith("(")):
            inputVal = inputVal.upper();
        return QValidator.Acceptable, inputVal, pos


class MDIEntry(QLineEdit, CMDWidget):
    """MDI Entry

    Input any valid g Code. Enter sends the g Code.
    """
    def __init__(self, parent=None):
        super(MDIEntry, self).__init__(parent)

        self.mdi_rtnkey_behaviour_supressed = False
        self.mdi_history_size = 100

        self.validator = Validator(self)
        self.setValidator(self.validator)
        
        # The completer is what creates the visual list mdi history
        # that can be selected from. This is useful when mdientry is used
        # stand alone but can get in the way when using this widget in
        # conjunction with mdihistory widget and a rich on-screen data
        # entry UI. So this designer exposed setting allows this to be enabled
        # or disabled as needed.
        self._completer_enabled = True

        self.returnPressed.connect(self.submit)

    @Property(int)
    def mdi_history_size(self):
        return self._mdi_history_size

    @mdi_history_size.setter
    def mdi_history_size(self, size):
        self._mdi_history_size = size

    @Property(bool)
    def completerEnabled(self):
        return self._completer_enabled
    
    @completerEnabled.setter
    def completerEnabled(self, flag):
        self._completer_enabled = flag

    @Slot()
    def submit(self):
        # Only support submit from Return Key if not suppressed
        # This is used to stop standalone behaviour by the MDIHistory widget.
        # MDIHisttory uses its handle to this widget to set
        # mdi_rtnkey_behaviour_supressed = True.
        # MDIHistory will now manage the MDILine submission process
        if not self.mdi_rtnkey_behaviour_supressed:
            cmd = str(self.text()).strip()
            issue_mdi(cmd)
            self.setText('')
            STATUS.mdi_history.setValue(cmd)

    @Slot(QListWidgetItem)
    def setMDIText(self, listItem):
        if listItem is not None:
            self.setText(listItem.text())

    def keyPressEvent(self, event):
        if (    self._completer_enabled
             and
             (  event.key() == Qt.Key_Up
              or event.key() == Qt.Key_Down
             )
           ):
            self.completer().complete()
        else:
            super(MDIEntry, self).keyPressEvent(event)

    def focusInEvent(self, event):
        super(MDIEntry, self).focusInEvent(event)
        if self._completer_enabled:
            self.completer().complete()

    def supress_rtn_key_behaviour(self):
        self.mdi_rtnkey_behaviour_supressed = True

    def enable_rtn_key_behaviour(self):
        self.mdi_rtnkey_behaviour_supressed = False

    def initialize(self):
        history = STATUS.mdi_history.value
        if self._completer_enabled:
            completer = QCompleter()
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.model = QStringListModel()
            completer.setModel(self.model)
            self.setCompleter(completer)
            self.model.setStringList(history)
            STATUS.mdi_history.notify(self.model.setStringList)

        STATUS.max_mdi_history_length = self.mdi_history_size

    def terminate(self):
        pass
