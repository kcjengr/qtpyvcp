import os

from qtpy import uic
from qtpy.QtWidgets import QWidget

from qtpyvcp.widgets.utility_widgets.mdi_helper import mdi_text

WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))


class MdiHelperHandler(QWidget):

    def __init__(self, parent=None):
        super(MdiHelperHandler, self).__init__(parent)

        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None:
            return

        self.ui = uic.loadUi(os.path.join(WIDGET_PATH, "mdi_helper.ui"), self)

        self.ui.mdiKeypad.buttonClicked.connect(self.mdi_keypad)
        self.ui.mdiNavBtns.buttonClicked.connect(self.mdi_change_page)
        self.ui.mdiBackspace.clicked.connect(self.mdi_back_space)
        self.ui.mdiSetLabelsBtn.clicked.connect(self.mdi_set_labels)
        self.ui.mdiSendBtn.clicked.connect(self.mdi_clear)
        self.ui.gcodeListPageUpBtn.clicked.connect(self.gcode_list_page_up)
        self.ui.gcodeListPageDownBtn.clicked.connect(self.gcode_list_page_down)

        titles = mdi_text.gcode_titles()

        for key, value in sorted(titles.items()):
            self.ui.gcodeHelpListWidget.addItem("{} {}".format(key, value))

    def mdi_change_page(self, widget):
        self.ui.mdiStack.setCurrentIndex(widget.property('page'))

    def mdi_keypad(self, widget):
        char = str(widget.text())
        text = self.ui.mdiEntry.text() or None

        if text:
            text += char
        else:
            text = char
        self.ui.mdiEntry.setText(text)

    def mdi_set_labels(self, widget):
        # get smart and figure out what axes are used

        text = self.ui.mdiEntry.text() or None
        print(text)

        if text:
            words = mdi_text.gcode_words()
            if text in words:
                self.mdi_clear(None)
                for index, value in enumerate(words[text], start=1):
                    print(value)
                    getattr(self.ui, 'gcodeParameter_' + str(index)).setText(value)
            else:
                self.mdi_clear(None)
            titles = mdi_text.gcode_titles()
            if text in titles:
                self.ui.gcodeDescription.setText(titles[text])
            else:
                self.mdi_clear(None)
            self.ui.gcodeHelpLabel.setText(mdi_text.gcode_descriptions(text))
        else:
            self.mdi_clear(None)
            print('No Match')

    def mdi_clear(self, widget):
        for index in range(1, 8):
            getattr(self.ui, 'gcodeParameter_' + str(index)).setText('')
        self.ui.gcodeDescription.setText('')
        self.ui.gcodeHelpLabel.setText('')

    def mdi_back_space(self, widget):
        if self.ui.mdiEntry.text():
            text = self.ui.mdiEntry.text()[:-1]
            self.ui.mdiEntry.setText(text)

    def gcode_list_page_up(self, widget):
        rows = self.ui.gcodeHelpListWidget.count() - 1
        current_row = self.ui.gcodeHelpListWidget.currentRow()
        if current_row:
            if current_row > 25:
                self.ui.gcodeHelpListWidget.setCurrentRow(current_row - 25)
            else:
                self.ui.gcodeHelpListWidget.setCurrentRow(0)
        else:
            self.ui.gcodeHelpListWidget.setCurrentRow(rows)

    def gcode_list_page_down(self, widget):
        rows = self.ui.gcodeHelpListWidget.count() - 1
        current_row = self.ui.gcodeHelpListWidget.currentRow()
        if current_row < rows:
            if (current_row + 25) < rows:
                self.ui.gcodeHelpListWidget.setCurrentRow(current_row + 25)
            else:
                self.ui.gcodeHelpListWidget.setCurrentRow(rows)
        else:
            self.ui.gcodeHelpListWidget.setCurrentRow(0)
