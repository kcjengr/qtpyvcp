import os
import yaml
from pkg_resources import iter_entry_points
from qtpy import uic

from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import QFileDialog, QApplication, QDialog, QTreeWidgetItem, \
    QStyleFactory

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
        self._vcp_data = {}

        self.selection = self.vcpTreeView.selectionModel()

        # example VCP section
        category = QTreeWidgetItem(self.vcpTreeView)
        category.setText(0, 'Example VCPs')
        category.setFlags(Qt.ItemIsEnabled)

        # add example VCPs to the treeview
        for entry_point in iter_entry_points(group='qtpyvcp.example_vcp'):
            child = QTreeWidgetItem(category)
            child.setText(0, self.get_vcp_data(entry_point))

        # installed VCP section
        category = QTreeWidgetItem(self.vcpTreeView)
        category.setText(0, 'Installed VCPs')
        category.setFlags(Qt.ItemIsEnabled)
        category.setHidden(True)

        # add installed VCPs to the treeview
        for entry_point in iter_entry_points(group='qtpyvcp.vcp'):
            child = QTreeWidgetItem(category)
            child.setText(0, self.get_vcp_data(entry_point))
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
        self.selection.selectionChanged.connect(self.on_selection_changed)

    def get_vcp_data(self, entry_point):
        vcp_data = {'entry_point_name': entry_point.name}
        try:
            vcp = entry_point.load()
            vcp_config_file = vcp.VCP_CONFIG_FILE

            with open(vcp_config_file, 'r') as fh:
                lines = fh.readlines()

            clean = []
            for line in lines:
                # clean jinja templating commands
                if line.strip().startswith('{%') or '{{' in line:
                    continue
                clean.append(line)

            vcp_data.update(yaml.load(''.join(clean)).get('vcp', {}))
            vcp_name = vcp_data.get('name', entry_point.name)

        except:
            vcp_name = entry_point.name

        self._vcp_data[vcp_name] = vcp_data

        return vcp_name

    def on_selection_changed(self):
        selection = self.selection.selectedRows()
        if selection == []:
            return

        vcp_data = self._vcp_data[selection[0].data()]

        desc = vcp_data.get('description', '')
        self.vcpDescription.setText(desc)


    @Slot()
    def on_launchVCPButton_clicked(self):
        selection = self.selection.selectedRows()
        if selection == []:
            return
        vcp_name = selection[0].data()
        vcp = self._vcp_data[vcp_name].get('entry_point_name', '')

        self.opts.vcp = vcp
        self.accept()

    @Slot()
    def on_cancelButton_clicked(self):
        self.reject()

    @Slot()
    def on_fileButton_pressed(self):
        vcp_file = QFileDialog.getOpenFileName(self,
                              caption="Select VCP File",
                              directory=EXAMPLE_VCP_DIR,
                              filter='VCP Files (*.yml *.yaml)',
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
