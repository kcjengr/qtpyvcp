"""
Tool Model Property fields
---------
"""

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QPushButton, QFileDialog, QDialog, QLabel


from qtpyvcp.lib.db_tool.base import Session, Base, engine
from qtpyvcp.lib.db_tool.tool_table import ToolTable, Tool, ToolModel

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog
from qtpyvcp.widgets.base_widgets.base_widget import VCPWidget

LOG = getLogger(__name__)


class ToolSTLField(QWidget):
    """Tool Model property Widget"""

    def __init__(self, parent=None):
        super(ToolSTLField, self).__init__(parent)
        
        self.session = Session()
        
        self.tool_selected = None
        
        self.layout = QHBoxLayout(self)
        self.filename = None
        
        self.label = QLabel("Tool STL Path")
        self.model_path = QLineEdit()
        self.browse_button = QPushButton()
        self.browse_button.setText("Load STL")
        self.browse_button.clicked.connect(self.stl_dialog)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.model_path)
        self.layout.addWidget(self.browse_button)

    def stl_dialog(self):
        dialog = QFileDialog(self)
        dialog.setWindowTitle('Open STL Tool file')
        dialog.setNameFilter('(*.stl)')
        
        filename = None
        
        if dialog.exec_() == QDialog.Accepted:
            filename = dialog.selectedFiles()
        
        if filename:
            self.setFilename(filename[0])
        else:
            self.clearFilename()

    @Slot(int)
    def toolSelected(self, tool_no):
        self.tool_selected = tool_no
        
        tool_data = self.session.query(ToolModel).filter(ToolModel.tool_no == tool_no).first()
        
        if tool_data:
            self.setFilename(tool_data.model)
        else:
            self.clearFilename()
    
    @Slot()
    def saveField(self):
        if self.tool_selected is not None:
            
            tool_data = self.session.query(ToolModel).filter(ToolModel.tool_no == self.tool_selected).first()
        
            if tool_data:
                tool_data.model = self.filename
                self.session.commit()
        
    def setFilename(self, name):
        self.filename = name
        self.model_path.setText(self.filename)

    def clearFilename(self):
        self.filename = ""
        self.model_path.setText("")
