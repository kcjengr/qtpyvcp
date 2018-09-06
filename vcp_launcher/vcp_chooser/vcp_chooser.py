import sys, os
from pkg_resources import load_entry_point
from PyQt5 import uic

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QApplication, QDialog, QTreeWidgetItem, QStyleFactory

from QtPyVCP import TOP_DIR

CHOOSER_DIR = os.path.abspath(os.path.dirname(__file__))

CUSTOM_VCP_DIR = os.path.expanduser('~/linuxcnc/vcps')
EXAMPLE_VCP_DIR = os.path.join(TOP_DIR, 'examples')

class VCPChooser(QDialog):
    def __init__(self, opts):
        super(VCPChooser, self).__init__()
        uic.loadUi(os.path.join(CHOOSER_DIR, 'vcp_chooser.ui'), self)

        self.opts = opts

        if os.path.exists(CUSTOM_VCP_DIR):
            category = QTreeWidgetItem(self.vcpTreeView)
            category.setText(0, 'Custom VCPs')
            category.setFlags(Qt.ItemIsEnabled)
            for dir_name in os.listdir(CUSTOM_VCP_DIR):
                if not os.path.isdir(os.path.join(CUSTOM_VCP_DIR, dir_name)):
                    continue
                child = QTreeWidgetItem(category)
                child.setText(0, dir_name)

        category = QTreeWidgetItem(self.vcpTreeView)
        category.setText(0, 'Standard VCPs')
        category.setFlags(Qt.ItemIsEnabled)
        self.vcpTreeView.setFirstItemColumnSpanned(category, True)

        for dir_name in os.listdir(EXAMPLE_VCP_DIR):
            if not os.path.isdir(os.path.join(EXAMPLE_VCP_DIR, dir_name)):
                continue
            child = QTreeWidgetItem(category)
            child.setText(0, dir_name)

        self.vcpTreeView.expandAll()
        self.vcpTreeView.activated.connect(self.on_launchVCPButton_clicked)

    @pyqtSlot()
    def on_launchVCPButton_clicked(self):
        selection = self.vcpTreeView.selectionModel().selectedRows()
        if selection == []:
            return
        vcp = selection[0].data()
        print vcp
        self.opts.vcp = vcp
        self.accept()

    @pyqtSlot()
    def on_cancelButton_clicked(self):
        print "rejected"
        self.reject()

    @pyqtSlot()
    def on_fileButton_pressed(self):
        vcp_file = QFileDialog.getOpenFileName(self,
                              caption="Select VCP File",
                              directory='examples',
                              filter='VCP Files (*.ui *py)',
                              options=QFileDialog.DontUseNativeDialog)

        if vcp_file:
            self.opts.vcp = vcp_file[0]
            self.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Windows'))
    launcher = VCPChooser()
    sys.exit(app.exec_())
