#    Gcode display / edit widget for QT_VCP
#    Copyright 2016 Chris Morley
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# This was based on
# QScintilla sample with PyQt
# Eli Bendersky (eliben@gmail.com)
# Which is code in the public domain
#
# See also:
# http://pyqt.sourceforge.net/Docs/QScintilla2/index.html
# https://qscintilla.com/
#
# Additions/Contributions by:
# Donb9261 (Don Bozarth - Linuxcnc Forums): many lexer improvements
# Joco (James Walker - james.walker.nz@me.com)
"""
Gcode editor/viewer widget.

Exposed QSS properties than can be used for style control.

GcodeEditor {
    qproperty-backgroundColor:          #303030;
    qproperty-marginBackgroundColor:    #D9DADB;
    qproperty-activeLineBackgroundColor: darkgray;
    qproperty-editorDefaultFont:        "Ubuntu Mono";

    qproperty-syntaxColorDefault:       #EFFBEF;
    qproperty-syntaxColorComment:       #fcf803;
    qproperty-syntaxColorKey:           #52ceff;
    qproperty-syntaxColorAssignment:    #fa5f5f;
    qproperty-syntaxColorValue:         #00CC00;
    qproperty-syntaxColorMcode:         #f736d7;
    qproperty-syntaxColorMsg:           #03fc20;
    qproperty-syntaxColorScode:         #03fcc2;
    qproperty-syntaxColorPcode:         #be4dff;
    qproperty-syntaxColorTcode:         #ff8fdb;
    qproperty-syntaxColorHcode:         #87b3ff;
}
"""
import sys
import os

from qtpy.QtCore import Property, Slot, Signal
from qtpy.QtCore import QObject, QFile, QFileInfo, QTextStream
from qtpy.QtGui import QFont, QFontMetrics, QColor
from qtpy.QtWidgets import QInputDialog, QFileDialog, QDialog, QWidget
from qtpy.QtWidgets import QLineEdit, QLabel, QPushButton, QCheckBox
from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout

from qtpyvcp.utilities import logger
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.info import Info
from qtpyvcp.widgets.base_widgets.base_widget import VCPBaseWidget

from qtpyvcp.actions.program_actions import load as loadProgram
from qtpyvcp.actions.program_actions import reload as reLoadProgram


LOG = logger.getLogger(__name__)

try:
    from PyQt5.Qsci import QsciScintilla, QsciLexerCustom
except ImportError as e:
    LOG.critical("Can't import QsciScintilla - is package python-pyqt5.qsci installed?", exc_info=e)
    sys.exit(1)

STATUS = getPlugin('status')
INFO = Info()

DEFAULT_FONT = QFont()
DEFAULT_COLOR = QColor('black')
DEFAULT_PAPER = QColor('white')  # transparent

DEFAULT_STYLES = {
    'default': {
        'color': 'black',
    },
    'comment': {
        'color': '#fcf803',
    },
    'assigment': {
        'color': '#fa5f5f',
    },
    'key': {
        'color': '#52ceff',
    },
    'value': {
        'color': '#00CC00',
    },
    'Gcode': {
        'color': '#f736d7',
    },
    'Mcode': {
        'color': '#f736d7',
    },
    'Fcode': {
        'color': '#f7ce36',
    },
    'Scode': {
        'color': '#03fcc2',
    },
}


class ColorProperty(Property):
    def __init__(self, style, color='black', doc="Testing"):
        """Syntax color property.

        Args:
            style (str) : The name of the style the color is used for.
            color (str) : The default color. Defaults to black.
        """
        super(ColorProperty, self).__init__(QColor, fget=self.getter,
                                            fset=self.setter, freset=self.reset,
                                            doc=doc)

        self._style = style
        self._color = QColor(color)

    def setter(self, widget, color):
        if isinstance(color, QColor):
            self._color = color
        else:
            self._color = QColor(color)

        widget.updateLexer()

    def getter(self, widget):
        return self._color
        # if self._color is not None:
        #     return self._color
        # return widget.property('defaultColor') or DEFAULT_COLOR

    # def reset(self, widget):
    #     """Set color to None to use default color."""
    #     self._color = None


class PaperProperty(Property):
    def __init__(self, style, color=None, doc="Testing"):
        """Syntax color property.

        Args:
            style (str) : The name of the style the color is used for.
            color (str) : The default color. Defaults to black.
        """
        super(PaperProperty, self).__init__(QColor, fget=self.getter,
                                            fset=self.setter, freset=self.reset,
                                            doc=doc)

        self._style = style
        self._color = None

        if color is not None:
            self._color = QColor(color)

    def setter(self, widget, color):
        if isinstance(color, QColor):
            self._color = color
        else:
            self._color = QColor(color)

        widget.updateLexer()

    def getter(self, widget):
        if self._color is not None:
            return self._color
        return widget.property('defaultPaper') or DEFAULT_PAPER

    def reset(self, widget):
        """Set paper to None to use default paper."""
        self._color = None


class FontProperty(Property):
    def __init__(self, style, font=None):
        """Style font property.

        Args:
            style (str) : The name of the style the color is used for.
            color (str) : The default color. Defaults to black.
        """
        super(FontProperty, self).__init__(QFont, fget=self.getter,
                                           fset=self.setter, freset=self.reset)

        self._style = style
        self._font = None

        if font is not None:
            self._font = QFont(font)

    def setter(self, widget, font):
        if isinstance(font, QFont):
            self._font = font
        else:
            self._font = QColor(font)

        widget.updateLexer()

    def getter(self, widget):
        if self._font is None:
            return widget.property('defaultFont') or DEFAULT_FONT
        return self._font

    def reset(self, widget):
        """Set font to None to use default font."""
        self._font = None

# ==============================================================================
# Simple custom lexer for Gcode
# ==============================================================================
class GcodeLexer(QsciLexerCustom):
    def __init__(self, parent=None, standalone=False):
        super(GcodeLexer, self).__init__(parent)

        self._style_counter = 0
        self._style_to_id_maping = {}

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None and not standalone:
            return

    def description(self, style):
        return "Style " + str(style)

    # def defaultColor(self, style):
    #     return QsciLexerCustom.defaultColor(self, style)

    def styleText(self, start, end):
        editor = self.editor()
        if editor is None:
            return

        # scintilla works with encoded bytes, not decoded characters.
        # this matters if the source contains non-ascii characters and
        # a multi-byte encoding is used (e.g. utf-8)
        source = ''
        if end > editor.length():
            end = editor.length()
        if end > start:
            if sys.hexversion >= 0x02060000:
                # faster when styling big files, but needs python 2.6
                source = bytearray(end - start)
                editor.SendScintilla(
                    editor.SCI_GETTEXTRANGE, start, end, source)
            else:
                source = unicode(editor.text()).encode('utf-8')[start:end]
        if not source:
            return

        # the line index will also be needed to implement folding
        index = editor.SendScintilla(editor.SCI_LINEFROMPOSITION, start)
        if index > 0:
            # the previous state may be needed for multi-line styling
            pos = editor.SendScintilla(editor.SCI_GETLINEENDPOSITION, index - 1)
            state = editor.SendScintilla(editor.SCI_GETSTYLEAT, pos)
        else:
            state = 0

        self.startStyling(start, 0x1f)

        # scintilla always asks to style whole lines
        for line in source.splitlines(True):
            # print line
            length = len(line)
            graymode = False
            msg = ('msg' in line.lower() or 'debug' in line.lower())
            for char in str(line):
                # print char
                if char == '(':
                    graymode = True
                    self.setCharStyle('comment')
                    continue
                elif char == ')':
                    graymode = False
                    self.setCharStyle('comment')
                    continue
                elif graymode:
                    if msg and char.lower() in ('m', 's', 'g', ',', 'd', 'e', 'b', 'u'):
                        self.setCharStyle('assignment')
                        if char == ',':
                            msg = False
                    else:
                        self.setCharStyle('comment')
                    continue
                elif char == 'MSG':
                    graymode = True
                    self.setCharStyle('message')
                    continue
                elif char == 'M':
                    graymode = False
                    self.setCharStyle('Mcode')
                    continue
                elif char == 'F':
                    graymode = False
                    self.setCharStyle('Fcode')
                    continue
                elif char == 'S':
                    graymode = False
                    self.setCharStyle('Scode')
                    continue
                elif char == 'P':
                    graymode = False
                    self.setCharStyle('Pcode')
                    continue
                elif char == 'T':
                    graymode = False
                    self.setCharStyle('Tcode')
                    continue
                elif char == 'H':
                    graymode = False
                    self.setCharStyle('Hcode')
                    continue
                elif char in ('%', '<', '>', '#', '='):
                    self.setCharStyle('assignment')
                elif char in ('[', ']'):
                    self.setCharStyle('value')
                elif char.isalpha():
                    self.setCharStyle('key')
                elif char.isdigit():
                    self.setCharStyle('default')
                else:
                    self.setCharStyle('default')

            # folding implementation goes here
            index += 1

    def setCharStyle(self, style):
        style_id = self._style_to_id_maping.get(style)
        if style_id is not None:
            self.setStyling(1, style_id)

    def addStyles(self, styles):
        for style, style_spec in styles.items():
            self.addStyle(style, **style_spec)

    def addStyle(self, style, color=None, paper=None, font=None):
        self._style_to_id_maping[style] = self._style_counter

        if color:
            self.setColor(color, self._style_counter)
        if paper:
            self.setPaper(paper, self._style_counter)
        if font:
            self.setFont(font, self._style_counter)

        # increment the style counter
        self._style_counter += 1


class GcodeEditor(QsciScintilla, VCPBaseWidget):
    ARROW_MARKER_NUM = 8

    locals()['defaultColor'] = ColorProperty('color', DEFAULT_COLOR)
    locals()['defaultPaper'] = PaperProperty('paper', DEFAULT_PAPER)
    locals()['defaultFont'] = FontProperty('font', DEFAULT_FONT)

    for style, style_spec in DEFAULT_STYLES.items():

        if style == 'default':
            continue

        prop_name = style + 'Color'
        locals()[prop_name] = ColorProperty(style, style_spec.get('color'))

        prop_name = style + 'Paper'
        locals()[prop_name] = PaperProperty(style, style_spec.get('paper'))

        prop_name = style + 'Font'
        locals()[prop_name] = FontProperty(style, style_spec.get('font'))

    def __init__(self, parent=None):
        super(GcodeEditor, self).__init__(parent)

        # self.colors = DEFAULT_SYNTAX_COLORS.copy()

        # supress certain events until the vcp initalize event
        self._framework_initalize = False

        #back grounds
        self._background = QColor('#2e3436')
        self._margin_background = QColor('#D9DADB')
        self._current_line_background = QColor('gray')

        # linuxcnc defaults
        self.idle_line_reset = False
        # don't allow editing by default
        self.setReadOnly(True)

        # Set the default font
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(14)

        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width("0") + 6)
        self.setMarginLineNumbers(0, True)

        # Clickable margin 1 for showing markers
        self.setMarginSensitivity(1, True)
        # setting marker margin width to zero make the marker highlight line
        self.setMarginWidth(1, 10)
        self.marginClicked.connect(self.on_margin_clicked)
        self.markerDefine(QsciScintilla.RightTriangle,
                          self.ARROW_MARKER_NUM)
        #  #ffe4e4
        self.setMarkerBackgroundColor(QColor("slate"),
                                      self.ARROW_MARKER_NUM)

        # Brace matching: enable for a brace immediately before or after
        # the current position
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#ffe4e4"))

        self.highlit = None

        # ------- from higher level class ------
        self.filename = ""
        self._last_filename = None
        self.auto_show_mdi = True
        self.last_line = None
        # self.setEolVisibility(True)

        self.is_editor = False

        self.dialog = FindReplaceDialog(parent=self)

        self.linesChanged.connect(self.linesHaveChanged)

        # register with the status:task_mode channel to
        # drive the mdi auto show behaviour
        #STATUS.task_mode.notify(self.onMdiChanged)
        #self.prev_taskmode = STATUS.task_mode

        #self.cursorPositionChanged.connect(self.line_changed)

    # def setProperty(self, *args, **kwargs):
    #     print args, kwargs

    # @Property(QColor)
    # def backgroundColor(self):
    #     """Property to set the background color of the GCodeEditor (str).
    #     sets the background color of the GCodeEditor
    #     """
    #     return self._background
    #
    # @backgroundColor.setter
    # def backgroundColor(self, color):
    #     self._background = color
    #
    #     self.SendScintilla(QsciScintilla.SCI_STYLESETBACK,
    #                        QsciScintilla.STYLE_DEFAULT, color)
    #
    #     self.updateLexer()

    @Property(QColor)
    def marginBackgroundColor(self):
        """Property to set the background color of the GCodeEditor margin (str).
        sets the background color of the GCodeEditor margin
        """
        return self._margin_background

    @marginBackgroundColor.setter
    def marginBackgroundColor(self, color):
        self._margin_background = color
        self.updateLexer()

    @Property(QColor)
    def activeLineBackgroundColor(self):
        """Property to set the background color of the active line.
        The active line is where the caret is within the file.
        """
        return self._current_line_background

    @activeLineBackgroundColor.setter
    def activeLineBackgroundColor(self, color):
        self._current_line_background = color
        self.updateLexer()

    @Slot()
    def updateLexer(self):
        """Taking the new default font and build a new lexer instance.
        Apply the new lexer to the editor.
        """

        # Note that if you do not create a new lexer the
        # the font does not get applied/used.

        self.lexer = GcodeLexer(self)

        for style in DEFAULT_STYLES:
            color = self.property(style + 'Color')
            paper = self.property(style + 'Paper')
            font = self.property(style + 'Font')

            self.lexer.addStyle(style, color, paper, font)

        self.setLexer(self.lexer)

        # rebuild gutter for new font
        self.setNumberGutter(self.lines())
        # set the gutter font to be aligned to main font
        self.setMarginsBackgroundColor(self._margin_background)
        self.setMarginsFont(self.property('defaultFont') or DEFAULT_FONT)

        self.setCaretLineBackgroundColor(self._current_line_background)

        self.SendScintilla(QsciScintilla.SCI_STYLESETBACK,
                           QsciScintilla.STYLE_DEFAULT,
                           self.property('defaultPaper') or DEFAULT_PAPER)


    def find_text_occurences(self, text):
        """Return byte positions of start and end of all 'text' occurences in the document"""

        text_len = len(text)
        end_pos = self.SendScintilla(QsciScintilla.SCI_GETLENGTH)
        self.SendScintilla(QsciScintilla.SCI_SETTARGETSTART, 0)
        self.SendScintilla(QsciScintilla.SCI_SETTARGETEND, end_pos)

        occurences = []

        match = self.SendScintilla(QsciScintilla.SCI_SEARCHINTARGET, text_len, text)
        print(match)
        while match != -1:
            match_end = self.SendScintilla(QsciScintilla.SCI_GETTARGETEND)
            occurences.append((match, match_end))
            # -- if there's a match, the target is modified so we shift its start
            # -- and restore its end --
            self.SendScintilla(QsciScintilla.SCI_SETTARGETSTART, match_end)
            self.SendScintilla(QsciScintilla.SCI_SETTARGETEND, end_pos)
            # -- find it again in the new (reduced) target --
            match = self.SendScintilla(QsciScintilla.SCI_SEARCHINTARGET, text_len, text)

        return occurences

    def highlight_occurences(self, text):

        occurences = self.find_text_occurences(text)
        text_len = len(text)
        self.SendScintilla(QsciScintilla.SCI_SETSTYLEBITS, 8)
        for occs in occurences:
            self.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 0)
            self.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE,
                               occs[0], text_len)

            # -- this is somewhat buggy : it was meant to change the color
            # -- but somewhy the colouring suddenly changes colour.

            # self.SendScintilla(Qsci.QsciScintilla.SCI_STARTSTYLING, occs[0], 0xFF)
            # self.SendScintilla(Qsci.QsciScintilla.SCI_SETSTYLING,
            #                    textLen,
            #                    styles["HIGHLIGHT"][0])

        self.highlit = occurences

    def clear_highlights(self):
        if self.highlit is None:
            return

        for occs in self.highlit:
            self.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 0)
            self.SendScintilla(QsciScintilla.SCI_INDICATORCLEARRANGE,
                               occs[0], occs[1] - occs[0])
        self.highlit = None

    def text_search(self, text, from_start, highlight_all, re=False,
                    cs=True, wo=False, wrap=True, forward=True,
                    line=-1, index=-1, show=True):

        if text is not None:
            if highlight_all:
                self.clear_highlights()
                self.highlight_occurences(text)

            if from_start:
                self.setCursorPosition(0, 0)

            match = self.findFirst(text, re, cs, wo, wrap, forward, line, index, show)

    def text_replace(self, text, sub, from_start, re=False,
                     cs=True, wo=False, wrap=True, forward=True,
                     line=-1, index=-1, show=True):

        if text is not None and sub is not None:
            self.clear_highlights()
            self.highlight_occurences(text)

            if from_start:
                self.setCursorPosition(0, 0)

            match = self.findFirst(text, re, cs, wo, wrap, forward, line, index, show)
            if match:
                self.replace(sub)

    def text_replace_all(self, text, sub, from_start, re=False,
                         cs=True, wo=False, wrap=True, forward=True,
                         line=-1, index=-1, show=True):

        if text is not None and sub is not None:
            self.clear_highlights()

            self.SendScintilla(QsciScintilla.SCI_SETTARGETSTART, 0)
            end_pos = self.SendScintilla(QsciScintilla.SCI_GETLENGTH)
            self.SendScintilla(QsciScintilla.SCI_SETTARGETEND, end_pos)

            print(self.SendScintilla(QsciScintilla.SCI_SEARCHINTARGET, len(text), text))

            # match = self.findFirst(text, re, cs, wo, wrap, forward, line, index, show)
            # if match:
            #     self.replace(sub)

    def on_margin_clicked(self, nmargin, nline, modifiers):
        # Toggle marker for the line the margin was clicked on
        if self.markersAtLine(nline) != 0:
            self.markerDelete(nline, self.ARROW_MARKER_NUM)
        else:
            self.markerAdd(nline, self.ARROW_MARKER_NUM)

    @Slot(bool)
    def setEditable(self, state):
        if state:
            self.setReadOnly(False)
        else:
            self.setReadOnly(True)

    @Slot(str)
    def setFilename(self, path):
        self.filename = path

    @Slot()
    def save(self):
        reload_file = True
        self.filename = str(STATUS.file)
        # determine of have a file name
        if self.filename == '':
            reload_file = False
            self.filename = '/tmp/gcode_tmp.ngc'

        # save out the file
        save_file = QFile(self.filename)
        result = save_file.open(QFile.WriteOnly)
        if result:
            save_stream = QTextStream(save_file)
            save_stream << self.text()
            save_file.close()
            # file save worked, now either load fresh or reload
            if reload_file:
                reLoadProgram()
            else:
                loadProgram(self.filename)

        else:
            print("save error")

    @Slot()
    def saveAs(self):
        #file_name = self.save_as_dialog(self.filename)
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self,"Save As","","All Files (*);;NGC Files (*.ngc)", options=options)

        if file_name is False:
            print("saveAs file name error")
            return
        self.filename = str(STATUS.file)

        original_file = QFileInfo(self.filename)
        path = original_file.path()

        new_absolute_path = os.path.join(path, file_name)
        new_file = QFile(new_absolute_path)

        result = new_file.open(QFile.WriteOnly)
        if result:
            save_stream = QTextStream(new_file)
            save_stream << self.text()
            new_file.close()

    @Slot()
    def find_replace(self):
        self.dialog.show()

    def search_text(self, find_text, highlight_all):
        from_start = False
        if find_text != "":
            self.text_search(find_text, from_start, highlight_all)

    def replace_text(self, find_text, replace_text):
        from_start = False
        if find_text != "" and replace_text != "":
            self.text_replace(find_text, replace_text, from_start)

    def replace_all_text(self, find_text, replace_text):
        from_start = True
        if find_text != "" and replace_text != "":
            self.text_replace_all(find_text, find_text, from_start)

    @Property(bool)
    def is_editor(self):
        return self._is_editor

    @is_editor.setter
    def is_editor(self, enabled):
        self._is_editor = enabled
        if not self._is_editor:
            STATUS.file.notify(self.load_program)
            STATUS.motion_line.onValueChanged(self.highlight_line)

            # STATUS.connect('line-changed', self.highlight_line)
            # if self.idle_line_reset:
            #     STATUS.connect('interp_idle', lambda w: self.set_line_number(None, 0))

    def setNumberGutter(self, lines=1):
        """Set the gutter width based on the number of lines in the text"""
        font = self.lexer.defaultFont()
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width(str(lines)) + 6)

    def load_program(self, fname=None):
        if fname is None:
            fname = self._last_filename
        else:
            self._last_filename = fname
        self.load_text(fname)
        # self.zoomTo(6)
        self.setCursorPosition(0, 0)

    def load_text(self, fname):
        try:
            fp = os.path.expanduser(fname)
            self.setText(open(fp).read())
        except:
            LOG.error('File path is not valid: {}'.format(fname))
            self.setText('')
            return

        # get the number of lines in the file and set new gutter width
        self.setNumberGutter(self.lines())

        self.last_line = None
        self.ensureCursorVisible()
        self.SendScintilla(QsciScintilla.SCI_VERTICALCENTRECARET)

    def highlight_line(self, line):
        # if STATUS.is_auto_running():
        #     if not STATUS.old['file'] == self._last_filename:
        #         LOG.debug('should reload the display')
        #         self.load_text(STATUS.old['file'])
        #         self._last_filename = STATUS.old['file']
        self.markerAdd(line, self.ARROW_MARKER_NUM)
        if self.last_line:
            self.markerDelete(self.last_line, self.ARROW_MARKER_NUM)
        self.setCursorPosition(line, 0)
        self.ensureCursorVisible()
        self.SendScintilla(QsciScintilla.SCI_VERTICALCENTRECARET)
        self.last_line = line

    def set_line_number(self, line):
        pass

    def linesHaveChanged(self):
        """When new lines are detected assess if the number
        column margin needs to be increased to accommodate a
        potentially larger number width.
        """
        # get the number of lines in the file and set new gutter width
        self.setNumberGutter(self.lines())

    def select_lineup(self):
        line, col = self.getCursorPosition()
        LOG.debug(line)
        self.setCursorPosition(line - 1, 0)
        self.highlight_line(line - 1)

    def select_linedown(self):
        line, col = self.getCursorPosition()
        LOG.debug(line)
        self.setCursorPosition(line + 1, 0)
        self.highlight_line(line + 1)

    def save_as_dialog(self, filename):
    # simple input dialog for save as
        text, ok_pressed = QInputDialog.getText(self, "Save as", "New name:", QLineEdit.Normal, filename)

        if ok_pressed and text != '':
            return text
        else:
            return False

    def initialize(self):
        # Refresh the lexer font after everything is loaded.
        # This allows the setting from Designer to be properly applied.
        #print 'gcode_editor initalize start'
        self._framework_initalize = True
        self.updateLexer()

# more complex dialog required by find replace


# ==============================================================================
# Find and replace Dialog
# ==============================================================================
class FindReplaceDialog(QDialog):
    def __init__(self, parent):
        super(FindReplaceDialog, self).__init__(parent)

        self.parent = parent
        self.setWindowTitle("Find Replace")
        self.setFixedSize(400, 200)

        main_layout = QVBoxLayout()

        find_layout = QHBoxLayout()
        replace_layout = QHBoxLayout()
        options_layout = QHBoxLayout()
        buttons_layout = QHBoxLayout()

        find_label = QLabel()
        find_label.setText("Find:")

        self.find_input = QLineEdit()

        find_layout.addWidget(find_label)
        find_layout.addWidget(self.find_input)

        replace_label = QLabel()
        replace_label.setText("Replace:")

        self.replace_input = QLineEdit()

        replace_layout.addWidget(replace_label)
        replace_layout.addWidget(self.replace_input)

        self.close_button = QPushButton()
        self.close_button.setText("Close")

        self.find_button = QPushButton()
        self.find_button.setText("Find")

        self.replace_button = QPushButton()
        self.replace_button.setText("Replace")

        self.all_button = QPushButton()
        self.all_button.setText("Replace All")

        buttons_layout.addWidget(self.close_button)
        buttons_layout.addWidget(self.find_button)
        buttons_layout.addWidget(self.replace_button)
        buttons_layout.addWidget(self.all_button)

        self.highlight_result = QCheckBox()
        self.highlight_result.setText("highlight results")

        options_layout.addWidget(self.highlight_result)

        main_layout.addLayout(find_layout)
        main_layout.addLayout(replace_layout)
        main_layout.addLayout(options_layout)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

        self.find_button.clicked.connect(self.find_text)
        self.replace_button.clicked.connect(self.replace_text)
        self.all_button.clicked.connect(self.replace_all_text)
        self.close_button.clicked.connect(self.hide_dialog)

    def find_text(self):
        find_text = self.find_input.text()
        highlight = self.highlight_result.isChecked()

        self.parent.search_text(find_text, highlight)

    def replace_text(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()

        self.parent.replace_text(find_text, replace_text)

    def replace_all_text(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()

        if find_text == "":
            return

        self.parent.replace_all_text(find_text, replace_text)

    def hide_dialog(self):
        self.hide()

# ==============================================================================
# For testing
# ==============================================================================
# if __name__ == "__main__":
#     from qtpy.QtGui import QApplication
#
#     app = QApplication(sys.argv)
#     editor = GcodeEditor(standalone=True)
#     editor.show()
#
#     editor.setText(open(sys.argv[0]).read())
#     app.exec_()
