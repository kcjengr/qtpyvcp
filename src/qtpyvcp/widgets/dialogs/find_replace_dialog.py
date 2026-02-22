import os


from PySide6.QtCore import (Qt, QSize)
from PySide6.QtGui import (QFont, QIcon, QPalette, QTextCursor)

from PySide6.QtWidgets import (QLineEdit, QHBoxLayout,
                            QVBoxLayout, QLabel, QPushButton, QCheckBox, QLayout,
                            QSizePolicy)

from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog
IN_DESIGNER = os.getenv('DESIGNER', False)

# Simple find/replace dialog
class FindReplaceDialog(BaseDialog):
    """Simple find/replace dialog with match counting and navigation."""
    
    def __init__(self, parent):
        super(FindReplaceDialog, self).__init__(parent)

        self.parent = parent
        self.setWindowTitle("Find / Replace")
        self.setObjectName("findReplaceDialog")
        self.setMinimumWidth(520)
        self.setStyleSheet(
            "QDialog#findReplaceDialog QLineEdit {"
            "  font: 10pt \"sans\";"
            "  padding-left: 5px;"
            "}"
        )

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        main_layout.setSizeConstraint(QLayout.SetFixedSize)

        # === Top row: Find controls ===
        find_layout = QHBoxLayout()
        find_layout.setContentsMargins(6, 10, 6, 0)
        find_layout.setSpacing(12)
        find_label = QLabel("Find:")
        find_label.setFixedWidth(60)
        find_label.setFont(QFont("", 14))
        find_label.setStyleSheet("QLabel { font: 14pt; }")

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Enter search text...")
        self.find_input.setClearButtonEnabled(False)
        self.find_input.setMinimumHeight(40)
        self.find_input.setFont(QFont("sans", 10))
        self.find_input.setMinimumWidth(260)
        self.find_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Navigation arrows
        self.find_prev_arrow = QPushButton()
        self.find_prev_arrow.setText("")
        self.find_prev_arrow.setToolTip("Previous (Shift+Enter)")
        self.find_prev_arrow.setFixedSize(50, 42)
        self.find_prev_arrow.setIcon(QIcon(":/images/up_arrow.png"))
        self.find_prev_arrow.setIconSize(QSize(20, 20))
        
        self.find_next_arrow = QPushButton()
        self.find_next_arrow.setText("")
        self.find_next_arrow.setToolTip("Next (Enter)")
        self.find_next_arrow.setFixedSize(50, 42)
        self.find_next_arrow.setIcon(QIcon(":/images/down_arrow.png"))
        self.find_next_arrow.setIconSize(QSize(20, 20))
        
        # Status label for match count
        self.status_label = QLabel("")
        self.status_label.setFixedWidth(110)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            "QLabel {"
            "  border-style: solid;"
            "  border-color: rgb(95, 95, 95);"
            "  border-width: 1px;"
            "  border-radius: 5px;"
            "  color: white;"
            "  background: rgb(90, 90, 90);"
            "  font: 15pt;"
            "  font-weight: bold;"
            "}"
        )

        find_layout.addWidget(find_label)
        find_layout.addWidget(self.find_input, 1)
        find_layout.addWidget(self.find_prev_arrow)
        find_layout.addWidget(self.find_next_arrow)
        # === End top row ===

        # Replace layout
        replace_layout = QHBoxLayout()
        replace_layout.setContentsMargins(6, 0, 6, 0)
        replace_layout.setSpacing(12)
        replace_label = QLabel("Replace:")
        replace_label.setFixedWidth(60)
        replace_label.setFont(QFont("", 14))
        replace_label.setStyleSheet("QLabel { font: 14pt; }")

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with...")
        self.replace_input.setClearButtonEnabled(False)
        self.replace_input.setMinimumHeight(40)
        self.replace_input.setFont(QFont("sans", 10))

        replace_layout.addWidget(replace_label)
        replace_layout.addWidget(self.replace_input, 1)
        replace_layout.addWidget(self.status_label)

        # Action buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(6, 20, 6, 0)
        buttons_layout.setSpacing(15)

        self.replace_button = QPushButton("Replace")
        self.replace_button.setToolTip("Replace current match and find next")
        self.replace_button.setMinimumSize(120, 40)

        self.replace_all_button = QPushButton("Replace All")
        self.replace_all_button.setToolTip("Replace all matches")
        self.replace_all_button.setMinimumSize(120, 40)

        self.close_button = QPushButton("Close")
        self.close_button.setToolTip("Close dialog (Esc)")
        self.close_button.setMinimumSize(100, 40)

        self.undo_button = QPushButton("Undo")
        self.undo_button.setToolTip("Undo last replace")
        self.undo_button.setMinimumSize(100, 40)
        self.undo_button.setEnabled(False)

        buttons_layout.addWidget(self.replace_button)
        buttons_layout.addWidget(self.replace_all_button)
        buttons_layout.addWidget(self.undo_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_button)

        # Build main layout
        main_layout.addLayout(find_layout)
        main_layout.addLayout(replace_layout)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

        # Connect signals
        self.find_input.textChanged.connect(self.on_search_text_changed)
        self.find_input.returnPressed.connect(self.find_next)
        self.replace_input.returnPressed.connect(self.replace_current)
        
        self.find_prev_arrow.clicked.connect(self.find_previous)
        self.find_next_arrow.clicked.connect(self.find_next)
        self.replace_button.clicked.connect(self.replace_current)
        self.replace_all_button.clicked.connect(self.replace_all)
        self.undo_button.clicked.connect(self.undo_last_replace)
        self.close_button.clicked.connect(self.hide_dialog)

        # Store the original palette for status feedback
        self.default_palette = self.find_input.palette()
        self.error_palette = QPalette()
        self.error_palette.setColor(QPalette.ColorRole.Base, Qt.red)
        self.error_palette.setColor(QPalette.ColorRole.Text, Qt.white)

        self._replace_undo_stack = []

    def showEvent(self, event):
        """When dialog is shown, focus the find input and select any text."""
        super().showEvent(event)
        self.find_input.setFocus()
        self.find_input.selectAll()
        # Trigger initial search if there's text
        if self.find_input.text():
            self.on_search_text_changed(self.find_input.text())

    def hideEvent(self, event):
        """When dialog is hidden, clear search highlights."""
        self.parent.clearHighlights()
        super().hideEvent(event)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key_Escape:
            self.hide_dialog()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.find_previous()
            else:
                self.find_next()
        else:
            super().keyPressEvent(event)

    def _highlight_and_update(self, find_text):
        """Helper to highlight matches and update status label."""
        if find_text:
            self.find_input.setPalette(self.default_palette)
            self.parent.highlightAllMatches(
                find_text,
                case_sensitive=False,
                whole_words=False,
                use_regex=False,
                highlight_current=True
            )
            self.update_match_count()
        else:
            self.parent.clearHighlights()
            self.status_label.setText("")

    def on_search_text_changed(self, text):
        """Update search when text changes (incremental search)."""
        self._highlight_and_update(text)

    def update_match_count(self):
        """Update the status label with match count."""
        count = self.parent.getMatchCount(
            self.find_input.text(),
            case_sensitive=False,
            whole_words=False,
            use_regex=False
        )
        if count > 0:
            current = self.parent.getCurrentMatchIndex(
                self.find_input.text(),
                case_sensitive=False,
                whole_words=False,
                use_regex=False
            )
            self.status_label.setText(f"{current} of {count}")
        elif count == 0:
            self.status_label.setText("Not found")
        else:
            self.status_label.setText("")

    def find_next(self):
        """Find next occurrence."""
        find_text = self.find_input.text()
        if not find_text:
            return

        found = self.parent.findNext(
            find_text,
            case_sensitive=False,
            whole_words=False,
            use_regex=False,
            wrap=True
        )
        
        if found:
            self._highlight_and_update(find_text)
        else:
            # Visual feedback: briefly flash the input red
            self.find_input.setPalette(self.error_palette)

    def find_previous(self):
        """Find previous occurrence."""
        find_text = self.find_input.text()
        if not find_text:
            return

        found = self.parent.findPrevious(
            find_text,
            case_sensitive=False,
            whole_words=False,
            use_regex=False,
            wrap=True
        )
        
        if found:
            self._highlight_and_update(find_text)
        else:
            self.find_input.setPalette(self.error_palette)

    def replace_current(self):
        """Replace current selection and find next."""
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()

        if not find_text:
            return

        record = self.parent.replaceCurrentWithUndo(
            find_text,
            replace_text,
            case_sensitive=False,
            whole_words=False,
            use_regex=False
        )
        
        if record:
            self._replace_undo_stack.append([record])
            self.undo_button.setEnabled(True)
            # Find next after replacing
            self.find_next()

    def replace_all(self):
        """Replace all occurrences."""
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()

        if not find_text:
            return

        records = self.parent.replaceAllWithUndo(
            find_text,
            replace_text,
            case_sensitive=False,
            whole_words=False,
            use_regex=False
        )
        
        if records:
            self._replace_undo_stack.append(records)
            self.undo_button.setEnabled(True)
            self.status_label.setText(f"Replaced {len(records)}")
        else:
            self.status_label.setText("Not found")

    def hide_dialog(self):
        """Hide the dialog."""
        self.hide()

    def undo_last_replace(self):
        if not self._replace_undo_stack:
            return

        records = self._replace_undo_stack.pop()
        cursor = QTextCursor(self.parent.document())
        cursor.beginEditBlock()
        for record in reversed(records):
            start = record["pos"]
            new_text = record["new_text"]
            original = record["original"]
            cursor.setPosition(start)
            cursor.setPosition(start + len(new_text), QTextCursor.KeepAnchor)
            cursor.insertText(original)
        cursor.endEditBlock()

        self.undo_button.setEnabled(bool(self._replace_undo_stack))
        self._highlight_and_update(self.find_input.text())

