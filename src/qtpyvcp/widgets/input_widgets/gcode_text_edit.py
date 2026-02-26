"""
GcodeTextEdit
-------------

QPlainTextEdit based G-code editor with syntax highlighting.
"""

import os
import yaml

from PySide6.QtCore import (Qt, QRect, QRegularExpression, QEvent, Slot, Signal,
                         Property, QFile, QTextStream, QSize)

from PySide6.QtGui import (QFont, QColor, QPainter, QSyntaxHighlighter,
                        QTextDocument, QTextOption, QTextFormat,
                        QTextCharFormat, QTextCursor, QPalette, QKeySequence)

from PySide6.QtWidgets import (QApplication, QInputDialog, QTextEdit, QLineEdit,
                            QPlainTextEdit, QWidget, QMenu,
                            QPlainTextDocumentLayout, QFileDialog,
                            QStyledItemDelegate, QTreeView, QListView)

from dateutil.parser import parse as parse_date

IN_DESIGNER = os.getenv('DESIGNER', False)

class ColumnFormatterDelegate(QStyledItemDelegate):
    """Flexible delegate for column formatting with configurable alignment, padding, and text formatting."""
    
    def __init__(self, parent=None, alignment=None, margin=None, padding=None, formatter=None, text_padding=None):
        """
        Initialize the delegate.
        
        Args:
            parent: Parent QObject
            alignment: Qt alignment flags (e.g., Qt.AlignLeft, Qt.AlignRight | Qt.AlignVCenter)
                      Default is Qt.AlignLeft | Qt.AlignVCenter
            margin: Dict with keys 'top', 'right', 'bottom', 'left' for pixel margins (spacing between items)
            padding: Dict with keys 'top', 'right', 'bottom', 'left' for pixel padding (inset content from highlight)
            formatter: Optional function that takes (value, locale) and returns formatted string
            text_padding: String to add as text padding (e.g., "  " for spaces)
        """
        super().__init__(parent)
        self.alignment = alignment if alignment is not None else (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.margin = margin or {'top': 0, 'right': 0, 'bottom': 0, 'left': 0}
        self.padding = padding or {'top': 0, 'right': 0, 'bottom': 0, 'left': 0}
        self.text_padding = text_padding or ""
        self.formatter = formatter
    
    def displayText(self, value, locale):
        """Format the display text using the custom formatter if provided."""
        if self.formatter:
            text = self.formatter(value, locale)
        else:
            text = str(value)
        
        # Apply text padding if specified
        if self.text_padding:
            text = self.text_padding + text + self.text_padding
            
        return text
    
    def initStyleOption(self, option, index):
        """Set the alignment and padding for this column."""
        super().initStyleOption(option, index)
        option.displayAlignment = self.alignment
        # Apply padding to the rectangle
        if self.padding:
            option.rect = option.rect.adjusted(
                self.padding.get('left', 0),
                self.padding.get('top', 0),
                -self.padding.get('right', 0),
                -self.padding.get('bottom', 0)
            )
    
    def sizeHint(self, option, index):
        """Return size hint including margin and padding."""
        size = super().sizeHint(option, index)
        # Add both margin and padding to the total size
        total_width = size.width() + self.margin.get('left', 0) + self.margin.get('right', 0) + self.padding.get('left', 0) + self.padding.get('right', 0)
        total_height = size.height() + self.margin.get('top', 0) + self.margin.get('bottom', 0) + self.padding.get('top', 0) + self.padding.get('bottom', 0)
        return QSize(total_width, total_height)


# Formatter functions for specific column types
def format_date(value, locale):
    """Format dates as MM/DD/YY   HH:MM  AM/PM"""
    try:
        date = parse_date(str(value))
        return f"{date:%m/%d/%y   %I:%M  %p}"
    except (ValueError, TypeError):
        return str(value)


def format_size(value, locale):
    """Format file sizes with two-letter abbreviations."""
    text = str(value).strip()
    replacements = {
        ' bytes': ' byt',
        ' KB': ' kib',
        ' MB': ' mib',
        ' GB': ' gib',
        ' TB': ' tib',
        ' KiB': ' kib',
        ' MiB': ' mib',
        ' GiB': ' gib',
        ' TiB': ' tib',
    }
    for old, new in replacements.items():
        if text.endswith(old):
            return text[:-len(old)] + new
    return text


from qtpyvcp import DEFAULT_CONFIG_FILE
from qtpyvcp.plugins import getPlugin
from qtpyvcp.actions import program_actions
from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.utilities.encode_utils import encodingDetector

from qtpyvcp.widgets.dialogs.find_replace_dialog import FindReplaceDialog

import linuxcnc

LOG = getLogger(__name__)
INFO = Info()
STATUS = getPlugin('status')
YAML_DIR = os.path.dirname(DEFAULT_CONFIG_FILE)

# Get PROGRAM_PREFIX from INI file for default save location
INI_FILE = linuxcnc.ini(os.getenv('INI_FILE_NAME'))
PROGRAM_PREFIX = INI_FILE.find('DISPLAY', 'PROGRAM_PREFIX') or '~/linuxcnc/nc_files'
PROGRAM_PREFIX = os.path.expandvars(os.path.expanduser(PROGRAM_PREFIX))


class GcodeSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document, font):
        super(GcodeSyntaxHighlighter, self).__init__(document)

        self.font = font

        self.rules = []
        self.char_fmt = QTextCharFormat()

        self._abort = False

        self.loadSyntaxFromYAML()

    def loadSyntaxFromYAML(self):

        if INFO.getGcodeSyntaxFile() is not None:
            YAML_DIR = os.environ['CONFIG_DIR']
            gcode_syntax_file = INFO.getGcodeSyntaxFile()
        else:
            YAML_DIR = os.path.dirname(DEFAULT_CONFIG_FILE)
            gcode_syntax_file = 'gcode_syntax.yml'

        with open(os.path.join(YAML_DIR, gcode_syntax_file)) as fh:
            syntax_specs = yaml.load(fh, Loader=yaml.FullLoader)

        cio = QRegularExpression.CaseInsensitiveOption

        for lang_name, language in list(syntax_specs.items()):

            definitions = language.get('definitions', {})

            default_fmt_spec = definitions.get('default', {}).get('textFormat', {})

            for context_name, spec in list(definitions.items()):

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

        for option, value in list(fmt_spec.items()):
            if value is None:
                continue

            if option in ['foreground', 'background']:
                value = QColor(value)

            if isinstance(value, str) and value.startswith('QFont:'):
                value = getattr(QFont, value[6:])

            attr = 'set' + option[0].capitalize() + option[1:]
            getattr(char_fmt, attr)(value)

        return char_fmt

    def defaultCharFormat(self):
        char_fmt = QTextCharFormat()
        char_fmt.setFont(self.font())
        return char_fmt

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """

        QApplication.processEvents()
        LOG.debug(f'Highlight light block:  {text}')


        for regex, fmt in self.rules:

            nth = 0
            match = regex.match(text, offset=0)
            index = match.capturedStart()

            while index >= 0:

                # We actually want the index of the nth match
                index = match.capturedStart(nth)
                length = match.capturedLength(nth)
                self.setFormat(index, length, fmt)

                # check the rest of the string
                match = regex.match(text, offset=index + length)
                index = match.capturedStart()


class GcodeTextEdit(QPlainTextEdit):
    """G-code Text Edit

    QPlainTextEdit based G-code editor with syntax heightening.
    """
    focusLine = Signal(int)

    def __init__(self, parent=None):
        super(GcodeTextEdit, self).__init__(parent)

        self.parent = parent

        # Set all instance variables with safe defaults first so that
        # @Property getters always have a valid value to return.
        self.block_number = None
        self.focused_line = 1
        self.current_line_background = QColor(self.palette().alternateBase().color())
        self.readonly = False
        self.syntax_highlighting = False
        self.old_docs = []
        self.gCodeHighlighter = None
        self.find_case = None
        self.find_words = None
        self.search_term = ""
        self.replace_term = ""
        self.highlight_selections = []
        self._find_palette_backup = None
        self.menu = None
        self.run_action = None
        self.dialog = None

        # In designer mode use a lightweight placeholder for self.margin so
        # that the margin-related @Property getters work without creating a
        # real QWidget child (which would connect signals and disturb Qt
        # Designer's rendering pipeline).
        class _MarginPlaceholder:
            background = QColor('#e8e8e8')
            highlight_background = QColor('#e8e8e8')
            color = QColor('#717171')
            highlight_color = QColor('#000000')
            def update(self): pass
            def getWidth(self): return 0
            def setGeometry(self, *a): pass
            def updateWidth(self): pass

        if IN_DESIGNER:
            self.margin = _MarginPlaceholder()
            # Still create the real margin for visual display in designer
            self.real_margin = NumberMargin(self)
            self.real_margin.updateWidth()  # Ensure proper positioning
            return

        self.setCenterOnScroll(True)
        self.setGeometry(50, 50, 800, 640)
        self.setWordWrapMode(QTextOption.NoWrap)

        # set the custom margin
        self.margin = NumberMargin(self)

        if parent is not None:
            pass  # find_case / find_words already set above

        # context menu
        self.menu = QMenu(self)
        self.menu.addAction(self.tr("Run from line {}".format(self.focused_line)), self.runFromHere)
        self.menu.addSeparator()
        self.menu.addAction(self.tr('Cut'), self.cut)
        self.menu.addAction(self.tr('Copy'), self.copy)
        self.menu.addAction(self.tr('Paste'), self.paste)
        self.menu.addSeparator()
        self.menu.addAction(self.tr('Find / Replace...'), self.findDialog)

        # FixMe: Picks the first action run from here, should not be by index
        self.run_action = self.menu.actions()[0]
        self.run_action.setEnabled(program_actions.run_from_line.ok())
        program_actions.run_from_line.bindOk(self.run_action)

        self.dialog = FindReplaceDialog(parent=self)

        # connect signals
        self.cursorPositionChanged.connect(self.onCursorChanged)

        # connect status signals
        STATUS.file.notify(self.loadProgramFile)
        STATUS.motion_line.onValueChanged(self.setCurrentLine)

    @Slot(str)
    def set_search_term(self, text):
        LOG.debug(f"Set search term :{text}")
        self.search_term = text

    @Slot(str)
    def set_replace_term(self, text):
        LOG.debug(f"Set replace term :{text}")
        self.replace_term = text

    @Slot()
    def findDialog(self):
        LOG.debug("Show find dialog")
        self.dialog.show()

    @Slot(bool)
    def findCase(self, enabled):
        LOG.debug(f"Find case sensitive :{enabled}")
        self.find_case = enabled

    @Slot(bool)
    def findWords(self, enabled):
        LOG.debug(f"Find whole words :{enabled}")
        self.find_words = enabled

    # ========================================================================
    # Enhanced Find/Replace Methods with Regex Support
    # ========================================================================
    
    def _buildFindFlags(self, case_sensitive, whole_words, backward=False):
        """Build QTextDocument find flags from parameters."""
        flags = QTextDocument.FindFlag(0)
        
        if case_sensitive:
            flags |= QTextDocument.FindCaseSensitively
        if whole_words:
            flags |= QTextDocument.FindWholeWords
        if backward:
            flags |= QTextDocument.FindBackward
            
        return flags
    
    def _findInDocument(self, text, case_sensitive, whole_words, use_regex, backward=False, start_cursor=None):
        """
        Find text in document with support for regex.
        Returns QTextCursor with selection if found, otherwise null cursor.
        """
        if not text:
            return QTextCursor()
        
        cursor = start_cursor if start_cursor else self.textCursor()
        
        if use_regex:
            # Use QRegularExpression for regex search
            pattern_options = QRegularExpression.PatternOption(0)
            if not case_sensitive:
                pattern_options |= QRegularExpression.CaseInsensitiveOption
                
            regex = QRegularExpression(text, pattern_options)
            if not regex.isValid():
                LOG.warning(f"Invalid regex pattern: {text}")
                return QTextCursor()
            
            # Search using regex
            if backward:
                result_cursor = self.document().find(regex, cursor, QTextDocument.FindBackward)
            else:
                result_cursor = self.document().find(regex, cursor)
        else:
            # Plain text search
            flags = self._buildFindFlags(case_sensitive, whole_words, backward)
            result_cursor = self.document().find(text, cursor, flags)
        
        return result_cursor
    
    def findNext(self, text, case_sensitive=False, whole_words=False, use_regex=False, wrap=True):
        """
        Find next occurrence of text.
        Returns True if found, False otherwise.
        """
        if not text:
            return False
        
        # Try to find from current position
        result_cursor = self._findInDocument(text, case_sensitive, whole_words, use_regex, backward=False)
        
        if not result_cursor.isNull():
            self.setTextCursor(result_cursor)
            self.ensureCursorVisible()
            return True
        elif wrap:
            # Wrap around to beginning
            cursor = QTextCursor(self.document())
            cursor.movePosition(QTextCursor.Start)
            result_cursor = self._findInDocument(text, case_sensitive, whole_words, use_regex, 
                                                 backward=False, start_cursor=cursor)
            if not result_cursor.isNull():
                self.setTextCursor(result_cursor)
                self.ensureCursorVisible()
                return True
        
        return False
    
    def findPrevious(self, text, case_sensitive=False, whole_words=False, use_regex=False, wrap=True):
        """
        Find previous occurrence of text.
        Returns True if found, False otherwise.
        """
        if not text:
            return False
        
        # Try to find from current position
        result_cursor = self._findInDocument(text, case_sensitive, whole_words, use_regex, backward=True)
        
        if not result_cursor.isNull():
            self.setTextCursor(result_cursor)
            self.ensureCursorVisible()
            return True
        elif wrap:
            # Wrap around to end
            cursor = QTextCursor(self.document())
            cursor.movePosition(QTextCursor.End)
            result_cursor = self._findInDocument(text, case_sensitive, whole_words, use_regex, 
                                                 backward=True, start_cursor=cursor)
            if not result_cursor.isNull():
                self.setTextCursor(result_cursor)
                self.ensureCursorVisible()
                return True
        
        return False
    
    def replaceCurrent(self, search_text, replace_text, case_sensitive=False, whole_words=False, use_regex=False):
        """
        Replace the currently selected text if it matches the search text.
        Returns True if replaced, False otherwise.
        """
        if not search_text:
            return False
        
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return False
        
        selected_text = cursor.selectedText()
        
        # Check if selection matches search text
        matches = False
        if use_regex:
            pattern_options = QRegularExpression.PatternOption(0)
            if not case_sensitive:
                pattern_options |= QRegularExpression.CaseInsensitiveOption
            regex = QRegularExpression(search_text, pattern_options)
            if regex.isValid():
                match = regex.match(selected_text)
                matches = match.hasMatch() and match.capturedStart() == 0 and match.capturedLength() == len(selected_text)
                if matches and match.lastCapturedIndex() > 0:
                    # Handle regex capture groups in replacement
                    for i in range(match.lastCapturedIndex() + 1):
                        replace_text = replace_text.replace(f"\\{i}", match.captured(i))
        else:
            if case_sensitive:
                matches = selected_text == search_text
            else:
                matches = selected_text.lower() == search_text.lower()
        
        if matches:
            cursor.beginEditBlock()
            cursor.insertText(replace_text)
            cursor.endEditBlock()
            return True
        
        return False

    def replaceCurrentWithUndo(self, search_text, replace_text, case_sensitive=False, whole_words=False, use_regex=False):
        """
        Replace the current selection and return undo data for that replacement.
        Returns a dict with position and text info, or None if no replacement.
        """
        if not search_text:
            return None

        cursor = self.textCursor()
        if not cursor.hasSelection():
            return None

        original_text = cursor.selectedText()
        matches = False
        new_text = replace_text

        if use_regex:
            pattern_options = QRegularExpression.PatternOption(0)
            if not case_sensitive:
                pattern_options |= QRegularExpression.CaseInsensitiveOption
            regex = QRegularExpression(search_text, pattern_options)
            if regex.isValid():
                match = regex.match(original_text)
                matches = match.hasMatch() and match.capturedStart() == 0 and match.capturedLength() == len(original_text)
                if matches and match.lastCapturedIndex() > 0:
                    new_text = replace_text
                    for i in range(match.lastCapturedIndex() + 1):
                        new_text = new_text.replace(f"\\{i}", match.captured(i))
        else:
            if case_sensitive:
                matches = original_text == search_text
            else:
                matches = original_text.lower() == search_text.lower()

        if not matches:
            return None

        start_pos = cursor.selectionStart()
        cursor.beginEditBlock()
        cursor.insertText(new_text)
        cursor.endEditBlock()

        return {
            "pos": start_pos,
            "original": original_text,
            "new_text": new_text,
        }

    def replaceAllWithUndo(self, search_text, replace_text, case_sensitive=False, whole_words=False, use_regex=False):
        """
        Replace all occurrences and return undo data for those replacements.
        Returns a list of dicts with position and text info.
        """
        if not search_text:
            return []

        records = []
        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.Start)

        while True:
            if use_regex:
                pattern_options = QRegularExpression.PatternOption(0)
                if not case_sensitive:
                    pattern_options |= QRegularExpression.CaseInsensitiveOption
                regex = QRegularExpression(search_text, pattern_options)
                if not regex.isValid():
                    break
                result_cursor = self.document().find(regex, cursor)
            else:
                flags = self._buildFindFlags(case_sensitive, whole_words)
                result_cursor = self.document().find(search_text, cursor, flags)

            if result_cursor.isNull():
                break

            original_text = result_cursor.selectedText()
            new_text = replace_text
            if use_regex and result_cursor.hasSelection():
                pattern_options = QRegularExpression.PatternOption(0)
                if not case_sensitive:
                    pattern_options |= QRegularExpression.CaseInsensitiveOption
                regex = QRegularExpression(search_text, pattern_options)
                match = regex.match(original_text)
                if match.hasMatch() and match.lastCapturedIndex() > 0:
                    new_text = replace_text
                    for i in range(match.lastCapturedIndex() + 1):
                        new_text = new_text.replace(f"\\{i}", match.captured(i))

            start_pos = result_cursor.selectionStart()
            result_cursor.insertText(new_text)
            records.append({
                "pos": start_pos,
                "original": original_text,
                "new_text": new_text,
            })

            cursor = result_cursor

        cursor.endEditBlock()
        self.clearHighlights()

        return records
    
    def replaceAll(self, search_text, replace_text, case_sensitive=False, whole_words=False, use_regex=False):
        """
        Replace all occurrences of search_text with replace_text.
        Returns the count of replacements made.
        """
        if not search_text:
            return 0
        
        count = 0
        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()
        
        # Start from beginning
        cursor.movePosition(QTextCursor.Start)
        
        while True:
            if use_regex:
                pattern_options = QRegularExpression.PatternOption(0)
                if not case_sensitive:
                    pattern_options |= QRegularExpression.CaseInsensitiveOption
                regex = QRegularExpression(search_text, pattern_options)
                if not regex.isValid():
                    break
                result_cursor = self.document().find(regex, cursor)
            else:
                flags = self._buildFindFlags(case_sensitive, whole_words)
                result_cursor = self.document().find(search_text, cursor, flags)
            
            if result_cursor.isNull():
                break
            
            # Handle regex capture groups if needed
            actual_replace = replace_text
            if use_regex and result_cursor.hasSelection():
                selected = result_cursor.selectedText()
                pattern_options = QRegularExpression.PatternOption(0)
                if not case_sensitive:
                    pattern_options |= QRegularExpression.CaseInsensitiveOption
                regex = QRegularExpression(search_text, pattern_options)
                match = regex.match(selected)
                if match.hasMatch() and match.lastCapturedIndex() > 0:
                    actual_replace = replace_text
                    for i in range(match.lastCapturedIndex() + 1):
                        actual_replace = actual_replace.replace(f"\\{i}", match.captured(i))
            
            result_cursor.insertText(actual_replace)
            cursor = result_cursor
            count += 1
        
        cursor.endEditBlock()
        
        # Clear any highlights
        self.clearHighlights()
        
        return count
    
    def getMatchCount(self, text, case_sensitive=False, whole_words=False, use_regex=False):
        """
        Count the total number of matches in the document.
        """
        if not text:
            return 0
        
        count = 0
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.Start)
        
        while True:
            if use_regex:
                pattern_options = QRegularExpression.PatternOption(0)
                if not case_sensitive:
                    pattern_options |= QRegularExpression.CaseInsensitiveOption
                regex = QRegularExpression(text, pattern_options)
                if not regex.isValid():
                    break
                cursor = self.document().find(regex, cursor)
            else:
                flags = self._buildFindFlags(case_sensitive, whole_words)
                cursor = self.document().find(text, cursor, flags)
            
            if cursor.isNull():
                break
            count += 1
        
        return count
    
    def getCurrentMatchIndex(self, text, case_sensitive=False, whole_words=False, use_regex=False):
        """
        Get the index of the current match (1-based).
        Returns 0 if no current selection or selection doesn't match.
        """
        if not text:
            return 0
        
        current_cursor = self.textCursor()
        if not current_cursor.hasSelection():
            return 0
        
        # Count matches before current position
        index = 0
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.Start)
        
        while True:
            if use_regex:
                pattern_options = QRegularExpression.PatternOption(0)
                if not case_sensitive:
                    pattern_options |= QRegularExpression.CaseInsensitiveOption
                regex = QRegularExpression(text, pattern_options)
                if not regex.isValid():
                    break
                cursor = self.document().find(regex, cursor)
            else:
                flags = self._buildFindFlags(case_sensitive, whole_words)
                cursor = self.document().find(text, cursor, flags)
            
            if cursor.isNull():
                break
            
            index += 1
            
            # Check if this match is the current selection
            if cursor.selectionStart() == current_cursor.selectionStart() and \
               cursor.selectionEnd() == current_cursor.selectionEnd():
                return index
        
        return 0
    
    def highlightAllMatches(self, text, case_sensitive=False, whole_words=False, use_regex=False, highlight_current=True):
        """
        Highlight all matches in the document, with an optional distinct highlight
        for the current match.
        """
        self.clearHighlights()
        
        if not text:
            return
        
        # Create highlight formats
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#8691FF"))
        current_format = QTextCharFormat()
        current_format.setBackground(QColor("#1402FC"))
        current_format.setForeground(QColor("#FFFFFF"))
        current_format.setFontWeight(QFont.Weight.Bold)
        
        # Find all matches
        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.Start)
        
        selections = []
        match_found = False
        while True:
            if use_regex:
                pattern_options = QRegularExpression.PatternOption(0)
                if not case_sensitive:
                    pattern_options |= QRegularExpression.CaseInsensitiveOption
                regex = QRegularExpression(text, pattern_options)
                if not regex.isValid():
                    break
                cursor = self.document().find(regex, cursor)
            else:
                flags = self._buildFindFlags(case_sensitive, whole_words)
                cursor = self.document().find(text, cursor, flags)
            
            if cursor.isNull():
                break
            
            # Create selection for this match
            selection = QTextEdit.ExtraSelection()
            selection.format = highlight_format
            selection.cursor = cursor
            selections.append(selection)
            match_found = True
        
        if highlight_current and match_found:
            current_cursor = self.textCursor()
            if current_cursor.hasSelection():
                selected_text = current_cursor.selectedText()
                matches_selection = False
                if use_regex:
                    pattern_options = QRegularExpression.PatternOption(0)
                    if not case_sensitive:
                        pattern_options |= QRegularExpression.CaseInsensitiveOption
                    regex = QRegularExpression(text, pattern_options)
                    if regex.isValid():
                        match = regex.match(selected_text)
                        matches_selection = match.hasMatch() and match.capturedStart() == 0 and match.capturedLength() == len(selected_text)
                else:
                    if case_sensitive:
                        matches_selection = selected_text == text
                    else:
                        matches_selection = selected_text.lower() == text.lower()

                if matches_selection:
                    if self._find_palette_backup is None:
                        self._find_palette_backup = self.palette()
                    find_palette = self.palette()
                    find_palette.setColor(QPalette.ColorRole.Highlight, QColor("#1402FC"))
                    find_palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
                    self.setPalette(find_palette)

                    current_selection = QTextEdit.ExtraSelection()
                    current_selection.format = current_format
                    current_selection.cursor = current_cursor
                    selections.append(current_selection)

        if not selections:
            self.clearHighlights()
            return

        self.highlight_selections = selections
        self.setExtraSelections(selections)
    
    def clearHighlights(self):
        """Clear all search highlights."""
        self.highlight_selections = []
        self.setExtraSelections([])  # Explicitly clear editor's extra selections
        if self._find_palette_backup is not None:
            self.setPalette(self._find_palette_backup)
            self._find_palette_backup = None
        self.onCursorChanged()

    # ========================================================================
    # Legacy Methods (kept for backward compatibility)
    # ========================================================================
    
    def findAllText(self, text=None):
        if text is None:
            text = self.search_term
        flags = QTextDocument.FindFlag(0)

        if self.find_case:
            flags |= QTextDocument.FindCaseSensitively
        if self.find_words:
            flags |= QTextDocument.FindWholeWords

        searching = True
        cursor = self.textCursor()

        while searching:
            found = self.find(text, flags)
            if found:
                cursor = self.textCursor()
            else:
                searching = False

        if cursor.hasSelection():
            self.setTextCursor(cursor)

    def findAll(self):
        """Find all occurrences - UI compatibility method."""
        self.findAllText()

    def findForward(self):
        """Find forward - UI compatibility method."""
        self.findForwardText()

    def replaceAll(self):
        """Replace all - UI compatibility method."""
        self.replaceAllText()

    def replace(self):
        """Replace current - UI compatibility method."""
        self.replaceText()

    def findForwardText(self, text=None):
        if text is None:
            text = self.search_term
        flags = QTextDocument.FindFlag()

        if self.find_case:
            flags |= QTextDocument.FindCaseSensitively
        if self.find_words:
            flags |= QTextDocument.FindWholeWords

        found = self.find(text, flags)

        # if found:
        #     cursor = self.document().find(text, flags)
        #     if cursor.position() > 0:
        #         self.setTextCursor(cursor)

    def findForward(self):
        """Alias for findForwardText to maintain compatibility with UI files."""
        self.findForwardText()

    def findBackwardText(self, text=None):
        if text is None:
            text = self.search_term
        flags = QTextDocument.FindFlag()
        flags |= QTextDocument.FindBackward

        if self.find_case:
            flags |= QTextDocument.FindCaseSensitively
        if self.find_words:
            flags |= QTextDocument.FindWholeWords

        found = self.find(text, flags)

        # if found:
        #     cursor = self.document().find(text, flags)
        #     if cursor.position() > 0:
        #         self.setTextCursor(cursor)

    def replaceText(self, search=None, replace=None):
        if search is None:
            search = self.search_term
        if replace is None:
            replace = self.replace_term

        flags = QTextDocument.FindFlag()

        if self.find_case:
            flags |= QTextDocument.FindCaseSensitively
        if self.find_words:
            flags |= QTextDocument.FindWholeWords

        found = self.find(search, flags)
        if found:
            cursor = self.textCursor()
            cursor.beginEditBlock()
            if cursor.hasSelection():
                cursor.insertText(replace)
            cursor.endEditBlock();

    def replace(self):
        """Alias for replaceText to maintain compatibility with UI files."""
        self.replaceText()

    def replaceAllText(self, search=None, replace=None):
        if search is None:
            search = self.search_term
        if replace is None:
            replace = self.replace_term

        flags = QTextDocument.FindFlag()

        if self.find_case:
            flags |= QTextDocument.FindCaseSensitively
        if self.find_words:
            flags |= QTextDocument.FindWholeWords

        searching = True
        while searching:
            found = self.find(search, flags)
            if found:
                cursor = self.textCursor()
                cursor.beginEditBlock()
                if cursor.hasSelection():
                    cursor.insertText(replace)
                cursor.endEditBlock();
            else:
                searching = False

    def replaceAll(self):
        """Alias for replaceAllText to maintain compatibility with UI files."""
        self.replaceAllText()

    @Slot()
    def saveFile(self, save_file_name = None):
        if save_file_name == None:
            save_file = QFile(str(STATUS.file))
        else:
            save_file = QFile(str(save_file_name))

        result = save_file.open(QFile.WriteOnly)
        if result:
            LOG.debug(f'---Save file: {save_file.fileName()}')
            save_stream = QTextStream(save_file)
            save_stream << self.toPlainText()
            save_file.close()
        else:
            LOG.debug("---save error")

    # File save dialog for save as
    def save_as_dialog(self, filename):
        # Use QFileDialog to allow directory browsing
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        directory = os.path.dirname(filename) if filename else ""
        basename = os.path.basename(filename) if filename else ""

        dialog = QFileDialog(self, "Save G-code File", directory,
                             "G-code Files (*.ngc *.nc *.tap);;All Files (*)")
        dialog.setOptions(options)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setViewMode(QFileDialog.Detail)
        dialog.setLabelText(QFileDialog.FileType, "File Type:")
        
        # Clear file dialog history to prevent showing cached paths from other machines
        # This is especially important when using sync tools like Syncthing that may sync Qt settings
        dialog.setHistory([])
        
        # Always use static system locations for consistency across all machines
        # This prevents synced Qt settings from causing issues with Syncthing
        from qtpy.QtCore import QUrl, QStandardPaths
        
        static_urls = []
        
        # Home directory (user's home as first entry)
        home_dir = os.path.expanduser('~')
        if os.path.isdir(home_dir):
            static_urls.append(QUrl.fromLocalFile(home_dir))
        
        # Desktop
        desktop_paths = QStandardPaths.standardLocations(QStandardPaths.DesktopLocation)
        if desktop_paths and os.path.isdir(desktop_paths[0]):
            static_urls.append(QUrl.fromLocalFile(desktop_paths[0]))
        
        # Documents
        doc_paths = QStandardPaths.standardLocations(QStandardPaths.DocumentsLocation)
        if doc_paths and os.path.isdir(doc_paths[0]):
            static_urls.append(QUrl.fromLocalFile(doc_paths[0]))
        
        # PROGRAM_PREFIX (LinuxCNC nc_files)
        if os.path.isdir(PROGRAM_PREFIX):
            static_urls.append(QUrl.fromLocalFile(PROGRAM_PREFIX))
        
        # Set the static sidebar URLs
        dialog.setSidebarUrls(static_urls)

        if basename:
            dialog.selectFile(basename)

        # Configure column formatting
        # Column configuration: alignment, margin (item spacing), padding (text inset), and formatter function
        # Alignment options: Qt.AlignLeft, Qt.AlignRight, Qt.AlignCenter, Qt.AlignHCenter
        # Combine with Qt.AlignVCenter for vertical centering
        # Margin: spacing between items (affects clickable/highlight area size)
        # Padding: insets text within the highlight area
        
        column_configs = {
            0: {  # Name column
                'alignment': Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                'margin': {'top': 3, 'right': 0, 'bottom': 3, 'left': 0},  # Space between items
                'padding': {'top': 0, 'right': 2, 'bottom': 0, 'left': 12},  # Text inset from highlight
                'text_padding': None,  # String for text padding like "  "
                'formatter': None,
                'min_width': 300  # Minimum width in pixels
            },
            1: {  # Size column
                'alignment': Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                'margin': {'top': 8, 'right': 0, 'bottom': 8, 'left': 0},
                'padding': {'top': 0, 'right': 0, 'bottom': 0, 'left': 0},
                'text_padding': None,
                'formatter': format_size,
                'min_width': 80
            },
            2: {  # Type column
                'alignment': Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                'margin': {'top': 8, 'right': 0, 'bottom': 8, 'left': 0},
                'padding': {'top': 0, 'right': 0, 'bottom': 0, 'left': 0},
                'text_padding': None,
                'formatter': None,
                'min_width': 80
            },
            3: {  # Date column
                'alignment': Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                'margin': {'top': 8, 'right': 0, 'bottom': 8, 'left': 0},
                'padding': {'top': 0, 'right': 12, 'bottom': 0, 'left': 0},
                'text_padding': None,
                'formatter': format_date,
                'min_width': 180
            }
        }
        
        # View configuration - shared settings for both tree and list views
        view_font = QFont("sans", 10)
        view_font.setWeight(QFont.Weight.Normal)
        
        view_min_width = 200  # Minimum width for the view widget
        
        # Sidebar (directory tree) configuration
        # Note: Sidebar item padding is controlled in probe_basic.qss 
        # via QFileDialog QTreeView#sidebar::item { padding: ... }
        sidebar_config = {
            'min_width': 200,
            'max_width': 300
        }
        
        # Create delegates for each column
        delegates = {}
        for col_num, config in column_configs.items():
            delegates[col_num] = ColumnFormatterDelegate(
                dialog,
                alignment=config['alignment'],
                margin=config.get('margin'),
                padding=config.get('padding'),
                formatter=config.get('formatter'),
                text_padding=config.get('text_padding')
            )
        
        # Apply delegates and settings to tree and list views
        for view in dialog.findChildren(QTreeView):
            if view.objectName() == 'treeView':
                view.setFont(view_font)
                view.setMinimumWidth(view_min_width)
                for col_num, delegate in delegates.items():
                    view.setItemDelegateForColumn(col_num, delegate)
                
                # Set column widths
                header = view.header()
                for col_num, config in column_configs.items():
                    if 'min_width' in config and config['min_width']:
                        header.resizeSection(col_num, config['min_width'])
        
        # Configure the sidebar (directory tree)
        for sidebar in dialog.findChildren(QTreeView):
            if sidebar.objectName() == 'sidebar':
                sidebar.setMinimumWidth(sidebar_config['min_width'])
                sidebar.setMaximumWidth(sidebar_config['max_width'])
                sidebar.setFont(view_font)
                    
        for view in dialog.findChildren(QListView):
            if view.objectName() == 'listView':
                view.setFont(view_font)
                view.setMinimumWidth(view_min_width)
                for col_num, delegate in delegates.items():
                    view.setItemDelegateForColumn(col_num, delegate)
        
        # Configure the splitter to show handle and set initial sizes
        from qtpy.QtWidgets import QSplitter
        for splitter in dialog.findChildren(QSplitter):
            splitter.setHandleWidth(8)
            splitter.setChildrenCollapsible(False)
            # Set initial sizes: sidebar 200px, file list takes remaining space
            splitter.setSizes([200, 600])

        # Calculate and set dialog width based on all components
        sidebar_width = 200        # Directory tree/sidebar on the left
        splitter_handle = 8        # QSplitter handle width
        columns_width = sum(config.get('min_width', 0) for config in column_configs.values())
        scrollbar_width = 20       # Vertical scrollbar
        dialog_margins = 40        # Left and right margins (20px each)
        
        dialog_width = sidebar_width + splitter_handle + columns_width + scrollbar_width + dialog_margins
        dialog.resize(dialog_width, 600)  # Width based on all components, height 600px

        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            file_path = dialog.selectedFiles()[0]
            return file_path

        return False

    @Slot()
    def saveFileAs(self):
        open_file = QFile(str(STATUS.file))
        if open_file == None:
            return

        current_file_name = open_file.fileName()

        # Check if current file is in config directory (new or unsaved file)
        config_dir = os.environ.get('CONFIG_DIR', '')
        if config_dir and current_file_name.startswith(config_dir):
            # Use PROGRAM_PREFIX as the default directory
            base_name = os.path.basename(current_file_name)
            if not base_name or base_name == 'None':
                base_name = 'new_file.ngc'
            default_path = os.path.join(PROGRAM_PREFIX, base_name)
        else:
            default_path = current_file_name

        save_file = self.save_as_dialog(default_path)
        if save_file:
            self.saveFile(save_file)
            # Load the newly saved file into LinuxCNC so STATUS.file is updated
            program_actions.load(save_file)

    def keyPressEvent(self, event):
        # Handle keyboard shortcuts
        if event.matches(QKeySequence.Find) or (event.key() == Qt.Key_F and event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            # Ctrl+F - Open find dialog
            self.findDialog()
            event.accept()
            return
        elif event.key() == Qt.Key_H and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+H - Open find dialog (focused on replace)
            self.findDialog()
            event.accept()
            return
        
        # keep the cursor centered
        if event.key() == Qt.Key_Up:
            self.moveCursor(QTextCursor.Up)
            self.centerCursor()

        elif event.key() == Qt.Key_Down:
            self.moveCursor(QTextCursor.Down)
            self.centerCursor()

        else:
            super(GcodeTextEdit, self).keyPressEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.FontChange:
            # Update syntax highlighter with new font
            self.gCodeHighlighter = GcodeSyntaxHighlighter(self.document(), self.font)

        super(GcodeTextEdit, self).changeEvent(event)

    @Slot(bool)
    def syntaxHighlightingOnOff(self, state):
        """Toggle syntax highlighting on/off"""
        pass

    @Property(bool)
    def syntaxHighlighting(self):
        return self.syntax_highlighting

    @syntaxHighlighting.setter
    def syntaxHighlighting(self, state):
        self.syntax_highlighting = state

    def setPlainText(self, p_str):
        # FixMe: Keep a reference to old QTextDocuments form previously loaded
        # files. This is needed to prevent garbage collection which results in a
        # seg fault if the document is discarded while still being highlighted.
        self.old_docs.append(self.document())

        LOG.debug('setPlanText')
        doc = QTextDocument()
        doc.setDocumentLayout(QPlainTextDocumentLayout(doc))
        doc.setPlainText(p_str)

        # start syntax highlighting
        if self.syntax_highlighting == True:
            self.gCodeHighlighter = GcodeSyntaxHighlighter(doc, self.font)
            LOG.debug('Syntax highlighting enabled.')

        self.setDocument(doc)
        self.margin.updateWidth()
        LOG.debug('Document set with text.')

        # start syntax highlighting
        # self.gCodeHighlighter = GcodeSyntaxHighlighter(self)

    @Slot(bool)
    def EditorReadOnly(self, state):
        """Set to Read Only to disable editing"""

        if state:
            self.setReadOnly(True)
        else:
            self.setReadOnly(False)

        self.readonly = state

    @Slot(bool)
    def EditorReadWrite(self, state):
        """Set to Read Only to disable editing"""

        if state:
            self.setReadOnly(False)
        else:
            self.setReadOnly(True)

        self.readonly != state

    @Property(bool)
    def readOnly(self):
        return self.readonly

    @readOnly.setter
    def readOnly(self, state):

        if state:
            self.setReadOnly(True)
        else:
            self.setReadOnly(False)

        self.readonly = state

    @Property(QColor)
    def currentLineBackground(self):
        return self.current_line_background

    @currentLineBackground.setter
    def currentLineBackground(self, color):
        self.current_line_background = color
        # Hack to get background to update
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
            enc = encodingDetector(file=fname)
            
            try:
                with open(fname,  'r', encoding=enc) as f:
                    gcode = f.read()

            except Exception as e:
                # LOG.debug(e)
                LOG.info(f"Error loading {f}")
            LOG.info(f"File encoding: {enc}")
            # set the syntax highlighter
            self.setPlainText(gcode)
            # self.gCodeHighlighter = GcodeSyntaxHighlighter(self.document(), self.font)

    @Slot(int)
    @Slot(object)
    def setCurrentLine(self, line):
        cursor = QTextCursor(self.document().findBlockByLineNumber(line - 1))
        self.setTextCursor(cursor)
        self.centerCursor()

    def getCurrentLine(self):
        return self.textCursor().blockNumber() + 1

    def onCursorChanged(self):
        # highlights current line, find a way not to use QTextEdit
        block_number = self.textCursor().blockNumber()
        if block_number != self.block_number:
            self.block_number = block_number
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(self.current_line_background)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections = [selection]
            if self.highlight_selections:
                selections.extend(self.highlight_selections)
            self.setExtraSelections(selections)

        # emit signals for backplot etc.
        self.focused_line = block_number + 1
        self.focusLine.emit(self.focused_line)

    def contextMenuEvent(self, event):
        self.run_action.setText("Run from line {}".format(self.focused_line))
        self.menu.popup(event.globalPos())
        event.accept()

    def runFromHere(self, *args, **kwargs):
        line = self.getCurrentLine()
        program_actions.run(line)

    def resizeEvent(self, *e):
        cr = self.contentsRect()
        rec = QRect(cr.left(), cr.top(), self.margin.getWidth(), cr.height())
        self.margin.setGeometry(rec)
        QPlainTextEdit.resizeEvent(self, *e)


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
        return self.parent.fontMetrics().horizontalAdvance(str(blocks)) + 5

    def updateWidth(self):  # check the number column width and adjust
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

            paint_rec = QRect(0, int(block_top), self.width(),
                              self.parent.fontMetrics().height())
            text_rec = QRect(0, int(block_top), self.width() -
                             4, self.parent.fontMetrics().height())
            painter.fillRect(paint_rec, background)
            painter.drawText(text_rec, Qt.AlignmentFlag.AlignRight, str(block_num + 1))
            block = block.next()

        painter.end()
        QWidget.paintEvent(self, event)

