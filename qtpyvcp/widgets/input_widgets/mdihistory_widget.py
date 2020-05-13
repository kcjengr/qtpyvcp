
from qtpy.QtCore import Qt, Slot, Property
from qtpy.QtGui import QValidator
from qtpy.QtWidgets import QListWidget, QListWidgetItem

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.info import Info
from qtpyvcp.actions.machine_actions import issue_mdi
from qtpyvcp.widgets.base_widgets.base_widget import CMDWidget

STATUS = getPlugin('status')
INFO = Info()



class MDIHistory(QListWidget, CMDWidget):
    """MDI History

    Xxxxxx.
    """
    def __init__(self, parent=None):
        super(MDIHistory, self).__init__(parent)

        #self.returnPressed.connect(self.submit)


    @Slot()
    def submit(self):
        cmd = str(self.text()).strip()
        issue_mdi(cmd)
        self.setText('')
        STATUS.mdi_history.setValue(cmd)

    def rowClicked(self):
        print('item clicked in list: {}'.format(self.currentItem().text()))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up or event.key() == Qt.Key_Down:
            pass
        else:
            super(MDIHistory, self).keyPressEvent(event)

    def focusInEvent(self, event):
        super(MDIHistory, self).focusInEvent(event)
        pass

    def setHistory(self, stringList):
        print('Clear and load history to list')

    def initialize(self):
        history = STATUS.mdi_history.value
        self.addItems(history)
        self.clicked.connect(self.rowClicked)
        STATUS.mdi_history.notify(self.setHistory)

    def terminate(self):
        pass
