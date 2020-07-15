
import os
import yaml

from qtpy.QtCore import (Qt, QRect, QRegularExpression, QEvent, Slot, Signal, Property)
from qtpy.QtGui import (QIcon, QFont, QColor, QPainter, QSyntaxHighlighter,
                        QTextOption, QTextFormat, QTextCharFormat, QTextCursor)
from qtpy.QtWidgets import (QApplication, QPlainTextEdit, QTextEdit, QWidget, QMenu)

from qtpyvcp import actions, DEFAULT_CONFIG_FILE
from qtpyvcp.plugins import getPlugin

STATUS = getPlugin('status')
YAML_DIR = os.path.dirname(DEFAULT_CONFIG_FILE)


class gCodeHighlight(QSyntaxHighlighter):
    def __init__(self, document, parent):
        super(gCodeHighlight, self).__init__(document)

        self._parent = parent

        self.rules = []
        self._char_fmt = QTextCharFormat()

        self.loadSyntaxFromYAML()

    def loadSyntaxFromYAML(self):

        with open(os.path.join(YAML_DIR, 'gcode_syntax.yml')) as fh:
            syntax_specs = yaml.load(fh, Loader=yaml.FullLoader)

        assert isinstance(syntax_specs, dict), \
            "Invalid YAML format for language spec, root item must be a dictionary."

        cio = QRegularExpression.CaseInsensitiveOption

        for lang_name, language in syntax_specs.items():

            definitions = language.get('definitions', {})

            default_fmt_spec = definitions.get('default', {}).get('textFormat', {})

            for context_name, spec in definitions.items():

                base_fmt = default_fmt_spec.copy()
                fmt_spec = spec.get('textFormat', {})

                # update the default fmt spec
                base_fmt.update(fmt_spec)

                char_fmt = self.charFormatFromSpec(fmt_spec)

                patterns = spec.get('match', [])
                for pattern in patterns:
                    self.rules.append([QRegularExpression(pattern, cio), char_fmt])

    def charFormatFromSpec(self, fmt_spec):

        char_fmt = self.defaultCharFormat()

        for option, value in fmt_spec.items():
            if value is None:
                continue

            if option in ['foreground', 'background']:
                value = QColor(value)

            if isinstance(value, basestring) and value.startswith('QFont:'):
                value = getattr(QFont, value[6:])

            attr = 'set' + option[0].capitalize() + option[1:]
            getattr(char_fmt, attr)(value)

        return char_fmt

    def defaultCharFormat(self):
        char_fmt = QTextCharFormat()
        char_fmt.setFont(self._parent.font())
        return char_fmt

    def highlightBlock(self, text):  # Using QRegularExpression

        self.setFormat(0, len(text), self.defaultCharFormat())

        for exp, tex_fmt in self.rules:

            result = exp.match(text)
            index = result.capturedStart()

            while index >= 0:
                start = result.capturedStart()
                end = result.capturedEnd()
                length = result.capturedLength()
                self.setFormat(start, length, tex_fmt)
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
        self.status.file.notify(self.loadProgramFile)
        self.status.motion_line.onValueChanged(self.setCurrentLine)

        self.setGeometry(50, 50, 800, 640)

        self.margin = NumberMargin(self)
        self.current_line = None

        self.current_line_background = QColor(self.palette().alternateBase())

        self.currentLineColor = self.palette().alternateBase()
        self.cursorPositionChanged.connect(self.highlightLine)

        # syntax highlighting
        self.gCodeHighlighter = gCodeHighlight(self.document(), self)

        # context menu
        self.focused_line = 1
        self.enable_run_action = actions.program_actions._run_ok()
        self.menu = QMenu(self)
        self.menu.addAction(self.tr("Run from line {}".format(self.focused_line)), self.runFromHere)
        self.menu.addSeparator()
        self.menu.addAction(self.tr('Cut'), self.cut)
        self.menu.addAction(self.tr('Copy'), self.copy)
        self.menu.addAction(self.tr('Paste'), self.paste)

        # FIXME picks the first action run from here, should not be by index
        self.run_action = self.menu.actions()[0]
        self.run_action.setEnabled(self.enable_run_action)

        self.cursorPositionChanged.connect(self.on_cursor_changed)

        self.setCenterOnScroll(True)
        self.setWordWrapMode(QTextOption.NoWrap)

    def changeEvent(self, event):
        if event.type() == QEvent.FontChange:
            # Update syntax highlighter with new font
            self.gCodeHighlighter = gCodeHighlight(self.document(), self)
        super(gCodeEdit, self).changeEvent(event)

    @Slot(bool)
    def EditorReadOnly(self, state):
        """Set to Read Only to disable editing"""
        if state:
            self.setReadOnly(True)
        else:
            self.setReadOnly(False)

    @Property(QColor)
    def currentLineBackground(self):
        return self.current_line_background

    @currentLineBackground.setter
    def currentLineBackground(self, color):
        self.current_line_background = color
        self.setCurrentLine(2)
        self.setCurrentLine(1)

    @Property(QColor)
    def marginBackground(self):
        return self.margin.background

    @marginBackground.setter
    def marginBackground(self, color):
        self.margin.background = color
        self.margin.update()

    @Property(QColor)
    def marginCurrentLineBackground(self):
        return self.margin.highlight_background

    @marginCurrentLineBackground.setter
    def marginCurrentLineBackground(self, color):
        self.margin.highlight_background = color
        self.margin.update()

    @Property(QColor)
    def marginColor(self):
        return self.margin.color

    @marginColor.setter
    def marginColor(self, color):
        self.margin.color = color
        self.margin.update()

    @Property(QColor)
    def marginCurrentLineColor(self):
        return self.margin.highlight_color

    @marginCurrentLineColor.setter
    def marginCurrentLineColor(self, color):
        self.margin.highlight_color = color
        self.margin.update()

    @Slot(str)
    @Slot(object)
    def loadProgramFile(self, fname=None):
        if fname:
            with open(fname) as f:
                gcode = f.read()
            self.setPlainText(gcode)

    @Slot(int)
    @Slot(object)
    def setCurrentLine(self, line):
        cursor = QTextCursor(self.document().findBlockByLineNumber(line - 1))
        self.setTextCursor(cursor)
        self.centerCursor()

    def on_cursor_changed(self):
        self.focused_line = self.textCursor().blockNumber() + 1
        self.focusLine.emit(self.focused_line)

    def contextMenuEvent(self, event):
        self.enable_run_action = actions.program_actions._run_ok()
        self.run_action.setText("Run from line {}".format(self.focused_line))
        self.run_action.setEnabled(self.enable_run_action)
        self.menu.popup(event.globalPos())
        event.accept()

    def runFromHere(self, *args, **kwargs):
        line, _ = self.getCursorPosition()
        actions.program_actions.run(line + 1)

    def resizeEvent(self, *e):
        cr = self.contentsRect()
        rec = QRect(cr.left(), cr.top(), self.margin.getWidth(), cr.height())
        self.margin.setGeometry(rec)
        QPlainTextEdit.resizeEvent(self, *e)

    def highlightLine(self): # highlights current line, find a way not to use QTextEdit
        line_number = self.textCursor().blockNumber()
        if line_number != self.current_line:
            self.current_line = line_number
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(self.current_line_background)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            self.setExtraSelections([selection])


class NumberMargin(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.parent = parent
        # this only happens when lines are added or subtracted
        self.parent.blockCountChanged.connect(self.updateWidth)
        # this happens quite often
        self.parent.updateRequest.connect(self.updateContents)

        self.background = QColor('#e8e8e8')
        self.highlight_background = QColor('#e8e8e8')
        self.color = QColor('#717171')
        self.highlight_color = QColor('#000000')

    def getWidth(self):
        blocks = self.parent.blockCount()
        return self.parent.fontMetrics().width(str(blocks)) + 5

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
            self.updateWidth()

    def paintEvent(self, event):  # this puts the line numbers in the margin
        painter = QPainter(self)
        painter.fillRect(event.rect(), self.background)
        block = self.parent.firstVisibleBlock()

        font = self.parent.font()

        while block.isValid():
            block_num = block.blockNumber()
            block_top = self.parent.blockBoundingGeometry(block).translated(self.parent.contentOffset()).top()

            # if the block is not visible stop wasting time
            if not block.isVisible() or block_top >= event.rect().bottom():
                break

            if block_num == self.parent.textCursor().blockNumber():
                font.setBold(True)
                painter.setFont(font)
                painter.setPen(self.highlight_color)
                background = self.highlight_background
            else:
                font.setBold(False)
                painter.setFont(font)
                painter.setPen(self.color)
                background = self.background

            text_rec = QRect(0, block_top, self.width(), self.parent.fontMetrics().height())
            painter.fillRect(text_rec, background)
            painter.drawText(text_rec, Qt.AlignRight, str(block_num + 1))
            block = block.next()

        painter.end()
        QWidget.paintEvent(self, event)

"""
if __name__ == '__main__':
    app = QApplication(sys.argv)
    GUI = gcedit()
    sys.exit(app.exec_())
"""
