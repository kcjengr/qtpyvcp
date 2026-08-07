"""
Tool Model Property fields
---------
"""

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QPushButton, QFileDialog, QDialog, QLabel


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
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            filename = dialog.selectedFiles()
        
        if filename:
            self.setFilename(filename[0])
        else:
            self.clearFilename()

    @Slot(int)
    def toolSelected(self, tool_no):
        self.tool_selected = tool_no
        
        with Session() as session:
            tool_data = session.query(ToolModel).filter(ToolModel.tool_no == tool_no).first()
            model = tool_data.model if tool_data else None

        if model:
            self.setFilename(model)
        else:
            self.clearFilename()
    
    @Slot()
    def saveField(self):
        if self.tool_selected is not None:
            
            with Session() as session:
                tool_data = session.query(ToolModel).filter(
                    ToolModel.tool_no == self.tool_selected).first()

                if tool_data:
                    tool_data.model = self.filename
                    session.commit()
        
    def setFilename(self, name):
        self.filename = name
        self.model_path.setText(self.filename)

    def clearFilename(self):
        self.filename = ""
        self.model_path.setText("")
