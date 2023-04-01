
from qtpy.QtWidgets import (QLineEdit, QHBoxLayout,
                            QVBoxLayout, QLabel, QPushButton, QCheckBox)

from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog


# more complex dialog required by find replace
class FindReplaceDialog(BaseDialog):
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

        self.parent.findForwardText(find_text)

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
