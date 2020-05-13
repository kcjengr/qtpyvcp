
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


    def submit(self):
        cmd = str(self.text()).strip()
        issue_mdi(cmd)
        STATUS.mdi_history.setValue(cmd)


    def rowClicked(self):
        print('item clicked in list: {}'.format(self.currentItem().text()))


    def keyPressEvent(self, event):
        row = self.currentRow()
        if event.key() == Qt.Key_Up:
            if row > 0:
                row -= 1
        elif event.key() == Qt.Key_Down:
            if row < self.count()-1:
                row += 1
        else:
            super(MDIHistory, self).keyPressEvent(event)

        self.setCurrentRow(row)


    def focusInEvent(self, event):
        super(MDIHistory, self).focusInEvent(event)
        pass


    def setHistory(self, stringList):
        print('Clear and load history to list')
        self.clear()
        self.addItems(stringList)



    def initialize(self):
        history = STATUS.mdi_history.value
        self.addItems(history)
        self.clicked.connect(self.rowClicked)
        STATUS.mdi_history.notify(self.setHistory)


    def terminate(self):
        pass
