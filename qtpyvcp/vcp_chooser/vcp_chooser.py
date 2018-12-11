import os
from pkg_resources import iter_entry_points
from qtpy import uic

from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import QMessageBox, QFileDialog, QApplication, QDialog, QTreeWidgetItem, QStyleFactory

from qtpyvcp import TOP_DIR

CHOOSER_DIR = os.path.abspath(os.path.dirname(__file__))

CUSTOM_VCP_DIR = os.path.expanduser('~/linuxcnc/vcps')
EXAMPLE_VCP_DIR = os.path.join(TOP_DIR, 'examples')

class VCPChooser(QDialog):
    def __init__(self, opts):
        super(VCPChooser, self).__init__()
        uic.loadUi(os.path.join(CHOOSER_DIR, 'vcp_chooser.ui'), self)

        self.setAttribute(Qt.WA_DeleteOnClose, True)

        self.opts = opts

        # example VCP section
        category = QTreeWidgetItem(self.vcpTreeView)
        category.setText(0, 'Example VCPs')
        category.setFlags(Qt.ItemIsEnabled)

        # add example VCPs to the treeview
        for entry_point in iter_entry_points(group='qtpyvcp.example_vcp'):
            child = QTreeWidgetItem(category)
            child.setText(0, entry_point.name)

        # installed VCP section
        category = QTreeWidgetItem(self.vcpTreeView)
        category.setText(0, 'Installed VCPs')
        category.setFlags(Qt.ItemIsEnabled)
        category.setHidden(True)

        # add installed VCPs to the treeview
        for entry_point in iter_entry_points(group='qtpyvcp.vcp'):
            child = QTreeWidgetItem(category)
            child.setText(0, entry_point.name)
            category.setHidden(False)

        if os.path.exists(CUSTOM_VCP_DIR):
            category = QTreeWidgetItem(self.vcpTreeView)
            category.setText(0, 'Custom VCPs')
            category.setFlags(Qt.ItemIsEnabled)
            for dir_name in os.listdir(CUSTOM_VCP_DIR):
                if not os.path.isdir(os.path.join(CUSTOM_VCP_DIR, dir_name)):
                    continue
                child = QTreeWidgetItem(category)
                child.setText(0, dir_name)

        self.vcpTreeView.expandAll()
        self.vcpTreeView.activated.connect(self.on_launchVCPButton_clicked)

    @Slot()
    def on_launchVCPButton_clicked(self):
        selection = self.vcpTreeView.selectionModel().selectedRows()
        if selection == []:
            return
        vcp = selection[0].data()
        print vcp
        self.opts.vcp = vcp
        self.accept()

    @Slot()
    def on_cancelButton_clicked(self):
        print "rejected"
        self.reject()

    @Slot()
    def on_fileButton_pressed(self):
        vcp_file = QFileDialog.getOpenFileName(self,
                              caption="Select VCP File",
                              directory=EXAMPLE_VCP_DIR,
                              filter='VCP Files (*.yaml)',
                              options=QFileDialog.DontUseNativeDialog)[0]

        if vcp_file != '':
            self.opts.vcp = vcp_file
            self.accept()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Windows'))
    launcher = VCPChooser()
    sys.exit(app.exec_())
