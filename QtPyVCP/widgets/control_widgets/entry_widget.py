#!/usr/bin/env python

import os

from PyQt5 import Qt

from QtPyVCP.core import Status, Action, Info
STATUS = Status()
ACTION = Action()
INFO = Info()

class EntryWidget(Qt.QLineEdit):
    def __init__(self, parent=None):
        super(EntryWidget, self).__init__(parent)

        self.returnPressed.connect(self.submit)

    def submit(self):
        cmd = str(self.text()).strip()
        ACTION.issueMDI(cmd)
        self.setText('')

    def keyPressEvent(self, event):
        super(EntryWidget, self).keyPressEvent(event)
        if event.key() == Qt.Qt.Key_Up:
            print 'Move up'
        if event.key() == Qt.Qt.Key_Down:
            print 'Move down'


if __name__ == "__main__":
    import sys
    app = Qt.QApplication(sys.argv)
    led = EntryWidget()
    led.show()
    sys.exit(app.exec_())
