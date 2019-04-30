import os

from qtpy import uic

from qtpy.QtWidgets import QWidget
from qtpy.QtCore import QSortFilterProxyModel
from qtpy.QtGui import QStandardItemModel, QStandardItem, QIcon

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

        titles = mdi_text.gcode_titles()

        self.gcode_list_model = QStandardItemModel(self.ui.gcodeHelpListView)
        self.gcode_list_model_proxy = QSortFilterProxyModel(self.ui.gcodeHelpListView)

        self.gcode_list_model_proxy.setSourceModel(self.gcode_list_model)

        self.ui.gcodeHelpListView.setModel(self.gcode_list_model_proxy)

        for key, value in sorted(titles.items()):
            self.help_line(key, value)

    def mdi_change_page(self, widget):

        print()
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

    def help_line(self, gcode, help_text):

        msg = '{}\t{}'.format(gcode, help_text)
        item = QStandardItem()
        item.setText(msg)
        item.setIcon(QIcon.fromTheme('help-browser'))
        item.setEditable(False)
        self.gcode_list_model.appendRow(item)
