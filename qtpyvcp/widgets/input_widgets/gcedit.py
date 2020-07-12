
import sys, os
from PyQt5.QtWidgets import (QApplication, QPlainTextEdit,
    QTextEdit, QWidget, QMenu)
from PyQt5.QtGui import (QIcon, QFontDatabase, QFont, QColor, QPainter,
    QTextFormat, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QFontInfo)
from PyQt5.QtCore import (QRect, Qt, QRegularExpression)

from qtpy.QtCore import Slot, Signal, Property
from qtpyvcp import actions

from qtpyvcp.plugins import getPlugin
STATUS = getPlugin('status')

import yaml

from qtpyvcp import DEFAULT_CONFIG_FILE
YAML_DIR = os.path.dirname(DEFAULT_CONFIG_FILE)


class gCodeHighlight(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(gCodeHighlight, self).__init__(parent)

        self.rules = []

        self.loadSyntaxFromYAML()

    def loadSyntaxFromYAML(self):

        with open(os.path.join(YAML_DIR, 'gcode_syntax.yml')) as fh:
            syntax_spec = yaml.load(fh, Loader=yaml.FullLoader)

        syntax_spec = syntax_spec['syntaxSpec']
        cio = QRegularExpression.CaseInsensitiveOption

        for name, spec in syntax_spec['definitions'].items():
            char_fmt = QTextCharFormat()

            for option, value in spec.get('textFormat', {}).items():
                if value is None:
                    continue

                if option in ['foreground', 'background']:
                    value = QColor(value)

                if isinstance(value, basestring) and value.startswith('QFont:'):
                    value = getattr(QFont, value.lstrip('QFont:'))

                attr = 'set' + option[0].capitalize() + option[1:]
                getattr(char_fmt, attr)(value)

            patterns = spec.get('match', '')
            for pattern in patterns:
                self.rules.append([QRegularExpression(pattern, cio), char_fmt])

    def highlightBlock(self, text):  # Using QRegularExpression
        for exp, format in self.rules:

            result = exp.match(text)
            index = result.capturedStart()

            count = 0
            while index >= 0:
                count += 1
                start = result.capturedStart()
                end = result.capturedEnd()
                length = result.capturedLength()
                self.setFormat(start, length, format)
                # check again starting at the end of the last match
                result = exp.match(text, end)
                index = result.capturedStart()

        # process any pending events so we don't lock up the GUI
        QApplication.processEvents()

class gCodeEdit(QPlainTextEdit):
    """
    g Code Editor using QPlainTextEdit for speed in loading
    """
    focusLine = Signal(int)

    def __init__(self, parent=None):
        super(gCodeEdit, self).__init__(parent)
        self.status = STATUS
        # if a program is loaded into LinuxCNC display that file
        self.status.file.notify(self.load_program)
        self.status.motion_line.onValueChanged(self.changeCursorPosition)

        self.setGeometry(50, 50, 800, 640)
        self.setWindowTitle("PyQt5 g Code Editor")
        self.setWindowIcon(QIcon('/usr/share/pixmaps/linuxcncicon.png'))
        self._setfont = QFont("DejaVu Sans Mono", 12)
        self.setFont(self._setfont)
        self.lineNumbers = NumberBar(self)
        self.currentLine = None
        self.currentLineColor = self.palette().alternateBase()
        self.cursorPositionChanged.connect(self.highlightLine)
        self.gCodeHighlighter = gCodeHighlight(self.document())

        self._backgroundcolor = QColor(255,255,255)
        self.pallet = self.viewport().palette()
        self.pallet.setColor(self.viewport().backgroundRole(), self._backgroundcolor)
        self.viewport().setPalette(self.pallet)

        # context menu
        self.focused_line = 1
        self.enable_run_action = actions.program_actions._run_ok()
        self.menu = QMenu(self)
        self.menu.addAction(self.tr("run from line {}".format(self.focused_line)), self.run_from_here)
        self.menu.addSeparator()
        self.menu.addAction(self.tr('Cut'), self.cut)
        self.menu.addAction(self.tr('Copy'), self.copy)
        self.menu.addAction(self.tr('Paste'), self.paste)
        # FIXME picks the first action run from here, should not be by index
        self.run_action = self.menu.actions()[0]
        self.run_action.setEnabled(self.enable_run_action)
        self.cursorPositionChanged.connect(self.on_cursor_changed)

        # file operations
        gCodeFileName = ''

    @Slot(bool)
    def EditorReadOnly(self, state):
        """
        Set to Read Only to disable editing
        """
        if state:
            self.setReadOnly(True)
        else:
            self.setReadOnly(False)

    @Property(QFont)
    def setfont(self):
        return self._setfont

    @setfont.setter
    def setfont(self, font):
        self._setfont = font
        print(font.family())
        self.setFont(font)

    @Property(QColor)
    def backgroundcolor(self):
        return self._backgroundcolor

    @backgroundcolor.setter
    def backgroundcolor(self, color):
        self._backgroundcolor = color
        self.pallet.setColor(self.viewport().backgroundRole(), color)
        self.viewport().setPalette(self.pallet)

    def load_program(self, fname=None):
        if fname:
            with open(fname) as f:
                gcode = f.read()
            self.setPlainText(gcode)

    def changeCursorPosition(self, line):
        #print(line)
        cursor = QTextCursor(self.document().findBlockByLineNumber(line))
        self.setTextCursor(cursor)

    def on_cursor_changed(self):
        self.focused_line = self.textCursor().blockNumber() + 1
        self.focusLine.emit(self.focused_line)

    def contextMenuEvent(self, event):
        self.enable_run_action = actions.program_actions._run_ok()
        self.run_action.setText("run from line {}".format(self.focused_line))
        self.run_action.setEnabled(self.enable_run_action)
        self.menu.popup(event.globalPos())
        event.accept()

    def run_from_here(self, *args, **kwargs):
        line, _ = self.getCursorPosition()
        actions.program_actions.run(line + 1)

    def resizeEvent(self, *e):
        cr = self.contentsRect()
        rec = QRect(cr.left(), cr.top(), self.lineNumbers.getWidth(), cr.height())
        self.lineNumbers.setGeometry(rec)
        QPlainTextEdit.resizeEvent(self, *e)

    def highlightLine(self): # highlights current line, find a way not to use QTextEdit
        newCurrentLineNumber = self.textCursor().blockNumber()
        if newCurrentLineNumber != self.currentLine:
            self.currentLine = newCurrentLineNumber
            selectedLine = QTextEdit.ExtraSelection()
            selectedLine.format.setBackground(QColor('#d5d8dc'))
            selectedLine.format.setProperty(QTextFormat.FullWidthSelection, True)
            selectedLine.cursor = self.textCursor()
            selectedLine.cursor.clearSelection()
            self.setExtraSelections([selectedLine])


class NumberBar(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.parent = parent
        # this only happens when lines are added or subtracted
        self.parent.blockCountChanged.connect(self.updateWidth)
        # this happens quite often
        self.parent.updateRequest.connect(self.updateContents)
        self.font = QFont()
        self.numberBarColor = QColor("#e8e8e8")

    def getWidth(self):
        blocks = self.parent.blockCount()
        return self.fontMetrics().width(str(blocks)) + 10

    def updateWidth(self): # check the number column width and adjust
        width = self.getWidth()
        if self.width() != width:
            self.setFixedWidth(width)
            self.parent.setViewportMargins(width, 0, 0, 0)

    def updateContents(self, rect, scroll):
        if scroll:
            self.scroll(0, scroll)
        else:
            self.update(0, rect.y(), self.width(), rect.height())
        if rect.contains(self.parent.viewport().rect()):
            fontSize = self.parent.currentCharFormat().font().pointSize()
            self.font.setPointSize(fontSize)
            self.font.setStyle(QFont.StyleNormal)
            self.updateWidth()

    def paintEvent(self, event): # this puts the line numbers in the margin
        painter = QPainter(self)
        painter.fillRect(event.rect(), self.numberBarColor)
        block = self.parent.firstVisibleBlock()
        while block.isValid():
            blockNumber = block.blockNumber()
            block_top = self.parent.blockBoundingGeometry(block).translated(self.parent.contentOffset()).top()
            # if the block is not visible stop wasting time
            if not block.isVisible() or block_top >= event.rect().bottom():
                break
            if blockNumber == self.parent.textCursor().blockNumber():
                self.font.setBold(True)
                painter.setPen(QColor("#000000"))
            else:
                self.font.setBold(False)
                painter.setPen(QColor("#717171"))
            painter.setFont(self.font)
            paint_rect = QRect(0, block_top, self.width(), self.parent.fontMetrics().height())
            painter.drawText(paint_rect, Qt.AlignRight, str(blockNumber+1))
            block = block.next()
        painter.end()
        QWidget.paintEvent(self, event)

"""
if __name__ == '__main__':
    app = QApplication(sys.argv)
    GUI = gcedit()
    sys.exit(app.exec_())
"""
