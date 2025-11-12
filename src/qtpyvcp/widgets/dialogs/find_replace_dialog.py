
from qtpy.QtWidgets import (QLineEdit, QHBoxLayout,
                            QVBoxLayout, QLabel, QPushButton, QCheckBox, QMessageBox)
from qtpy.QtGui import QTextCursor, QTextDocument

from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog


# more complex dialog required by find replace
class FindReplaceDialog(BaseDialog):
    def __init__(self, parent):
        super(FindReplaceDialog, self).__init__(parent)

        self.parent = parent
        self.setWindowTitle("Find Replace")
        self.setFixedSize(400, 200)
        
        # Track if we've wrapped around to avoid infinite loops
        self.has_wrapped = False

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
        
        # Reset wrap flag when search text changes
        self.find_input.textChanged.connect(self.reset_wrap_flag)

    def find_text(self):
        find_text = self.find_input.text()
        
        if not find_text:
            return

        # Get the search flags from parent if available (like GcodeTextEdit)
        flags = QTextDocument.FindFlag()
        if hasattr(self.parent, 'find_case') and self.parent.find_case:
            flags |= QTextDocument.FindCaseSensitively
        if hasattr(self.parent, 'find_words') and self.parent.find_words:
            flags |= QTextDocument.FindWholeWords
        
        # Try to find the text from current position
        found = self.parent.find(find_text, flags)
        
        # If not found, try wrapping to beginning silently
        if not found:
            # Move cursor to beginning of document
            cursor = self.parent.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.parent.setTextCursor(cursor)
            
            # Try finding again from the beginning
            found_after_wrap = self.parent.find(find_text, flags)
            
            if not found_after_wrap:
                # Only show dialog if truly not found anywhere
                QMessageBox.information(self, "Find", f"'{find_text}' not found.")

    def reset_wrap_flag(self):
        """Reset the wrap flag when search text changes"""
        self.has_wrapped = False

    def replace_text(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()

        self.parent.replaceText(find_text, replace_text)

    def replace_all_text(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()

        if find_text == "":
            return

        self.parent.replaceAllText(find_text, replace_text)

    def hide_dialog(self):
        self.hide()
