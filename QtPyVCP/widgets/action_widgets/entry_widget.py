#!/usr/bin/env python

import os
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt, QEvent

class EntryWidget(QLineEdit):
    def __init__(self, parent=None):
        super(EntryWidget, self).__init__(parent)

        self.returnPressed.connect(self.submit)

    def submit(self):
        text = str(self.text()).strip()
        print text
        self.setText('')

    def keyPressEvent(self, event):
        super(EntryWidget, self).keyPressEvent(event)
        if event.key() == Qt.Key_Up:
            print 'Move up'
        if event.key() == Qt.Key_Down:
            print 'Move down'


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    led = EntryWidget()
    led.show()
    sys.exit(app.exec_())
