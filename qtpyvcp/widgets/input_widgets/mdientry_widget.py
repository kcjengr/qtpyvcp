#!/usr/bin/env python

import os
from qtpy.QtWidgets import QLineEdit, QCompleter
from qtpy.QtCore import Qt, QEvent, QStringListModel
from qtpy.QtGui import QKeySequence, QValidator

from qtpyvcp.plugins import getPlugin
STATUS = getPlugin('status')

from qtpyvcp.core import Info
INFO = Info()

from qtpyvcp.actions.machine_actions import issue_mdi

MDI_HISTORY_FILE = INFO.getMDIHistoryFile()

class Validator(QValidator):
    def validate(self, string, pos):
        # eventually could do some actual validating here
        return QValidator.Acceptable, string.upper(), pos

class MDIEntry(QLineEdit):
    def __init__(self, parent=None):
        super(MDIEntry, self).__init__(parent)

        self.model = QStringListModel()

        completer = QCompleter()
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setModel(self.model)
        self.setCompleter(completer)

        self.validator = Validator(self)
        self.setValidator(self.validator)

        self.loadMDIHystory()

        self.returnPressed.connect(self.submit)

        STATUS.on_shutown.connect(self.saveMDIHistory)

    def submit(self):
        cmd = str(self.text()).strip()
        issue_mdi(cmd)
        self.setText('')
        cmds = self.model.stringList()
        if cmd not in cmds:
            cmds.append(cmd)
            self.model.setStringList(cmds)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up or event.key() == Qt.Key_Down:
            self.completer().complete()
        else:
            super(MDIEntry, self).keyPressEvent(event)

    def focusInEvent(self, event):
        super(MDIEntry, self).focusInEvent(event)
        self.completer().complete()

    def loadMDIHystory(self):
        history = []
        try:
            with open(MDI_HISTORY_FILE, 'r') as fh:
                lines = fh.readlines()
            for line in lines:
                line = line.strip()
                history.append(line)
            self.model.setStringList(history)
        except:
            # file does not exist
            pass

    def saveMDIHistory(self):
        with open(MDI_HISTORY_FILE, 'w') as fh:
            for cmd in self.model.stringList():
                fh.write(cmd + '\n')

if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = MDIEntry()
    w.show()
    sys.exit(app.exec_())
