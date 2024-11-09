"""
Tool Model Property fields
---------
"""

from qtpy.QtCore import Property, Slot

from qtpy.QtWidgets import (
    QWidget,
    QLineEdit,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QDialog,
    QLabel,
    QCheckBox,
    QSpinBox
)


from qtpyvcp.lib.db_tool.base import Session, Base, engine
from qtpyvcp.lib.db_tool.tool_table import ToolTable, Tool, ToolProperties

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog
from qtpyvcp.widgets.base_widgets.base_widget import VCPWidget
from blinker._utilities import text

LOG = getLogger(__name__)



class DBFileField(QWidget):
    """Tool Model property Widget"""

    def __init__(self, parent=None):
        super(DBFileField, self).__init__(parent)
        
        self.session = Session()
        
        self.tool_selected = None
        
        self.layout = QHBoxLayout(self)
        self.filename = None
        self._label_text = None
        self._query = None
        
        
        self.label = QLabel(self._label_text)
        self.model_path = QLineEdit()
        self.browse_button = QPushButton()
        self.browse_button.setText("Load")
        self.browse_button.clicked.connect(self.stl_dialog)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.model_path)
        self.layout.addWidget(self.browse_button)

    def initialise(self):
        selg.label.setText(self._label_text)
        
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
        
        table, column = self._query.split('.')            
        table_class = globals().get(table)
        
        self.tool_selected = tool_no
        
        tool_data = self.session.query(table_class).filter(table_class.tool_no == self.tool_selected).first()
        
        if tool_data:
            val = getattr(tool_data, column, None)
            self.setFilename(val)
        else:
            self.clearFilename()
    
    @Slot()
    def saveField(self):
        if self.tool_selected is not None:
        
            table, column = self._query.split('.')            
            table_class = globals().get(table)
            
            tool_data = self.session.query(table_class).filter(table_class.tool_no == self.tool_selected).first()
            
            if tool_data:
                setattr(tool_data, column, self.filename)
                self.session.commit()
        
    def setFilename(self, name):
        self.filename = name
        self.model_path.setText(self.filename)

    def clearFilename(self):
        self.filename = ""
        self.model_path.setText("")

    @Property(str)
    def labelText(self):
        return self._label_text

    @labelText.setter
    def labelText(self, text):
        self.label.setText(text)
        self._label_text = text

    @Property(str)
    def query(self):
        return self._query

    @query.setter
    def query(self, text):
        self._query = text


class DBTextField(QWidget):
    """Tool Model property Widget"""

    def __init__(self, parent=None):
        super(DBTextField, self).__init__(parent)
        
        self.session = Session()
        
        self.tool_selected = None
        
        self.layout = QHBoxLayout(self)
        self._label_text = None
        self._query = None
        
        
        self.label = QLabel()
        self.text = QLineEdit()
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.text)

    @Slot(int)
    def toolSelected(self, tool_no):
        
        table, column = self._query.split('.')            
        table_class = globals().get(table)
        
        self.tool_selected = tool_no
        tool_data = self.session.query(table_class).filter(table_class.tool_no == self.tool_selected).first()
        
        if tool_data:
            val = getattr(tool_data, column, None)
            self.text.setText(val)
        else:
            self.text.setText("")
            
    @Slot()
    def saveField(self):
        if self.tool_selected is not None:
            
            table, column = self._query.split('.')
            table_class = globals().get(table)
            
            tool_data = self.session.query(table_class).filter(table_class.tool_no == self.tool_selected).first()
        
            if tool_data:
                setattr(tool_data, column, self.text.text())
                self.session.commit()
    
    @Property(str)
    def labelText(self):
        return self._label_text

    @labelText.setter
    def labelText(self, text):
        self.label.setText(text)
        self._label_text = text

    @Property(str)
    def query(self):
        return self._query

    @query.setter
    def query(self, text):
        self._query = text
        
class DBCheckBoxField(QWidget):
    """Tool Model property Widget"""

    def __init__(self, parent=None):
        super(DBCheckBoxField, self).__init__(parent)
        
        self.session = Session()
        
        self.tool_selected = None
        
        self.layout = QHBoxLayout(self)
        self._label_text = None
        self._query = None
        
        
        self.label = QLabel()
        self.checkbox = QCheckBox()
        
                
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.checkbox)
        

    @Slot(int)
    def toolSelected(self, tool_no):
        
        table, column = self._query.split('.')            
        table_class = globals().get(table)
        
        self.tool_selected = tool_no
        
        
        tool_data = self.session.query(table_class).filter(table_class.tool_no == self.tool_selected).first()
        
        if tool_data:
            val = getattr(tool_data, column, None)
            self.checkbox.setCheckState(bool(int(val)))
        else:
            self.checkbox.setCheckState(False)
            
    @Slot()
    def saveField(self):
        if self.tool_selected is not None:
            
            table, column = self._query.split('.')
            table_class = globals().get(table)
            
            tool_data = self.session.query(table_class).filter(table_class.tool_no == self.tool_selected).first()
        
            
            if tool_data:
                setattr(tool_data, column, self.checkbox.isChecked())
                self.session.commit()
    
    @Property(str)
    def labelText(self):
        return self._label_text

    @labelText.setter
    def labelText(self, text):
        self.label.setText(text)
        self._label_text = text

    @Property(str)
    def query(self):
        return self._query

    @query.setter
    def query(self, text):
        self._query = text


class DBIntField(QWidget):
    """Tool Integer property Widget"""

    def __init__(self, parent=None):
        super(DBIntField, self).__init__(parent)
        
        self.session = Session()
        
        self.tool_selected = None
        
        self.layout = QHBoxLayout(self)
        self._label_text = None
        self._query = None
        
        
        self.label = QLabel()
        self.spinbox = QSpinBox()
        
                
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.spinbox)
        

    @Slot(int)
    def toolSelected(self, tool_no):
        
        table, column = self._query.split('.')            
        table_class = globals().get(table)
            
        self.tool_selected = tool_no
        
        tool_data = self.session.query(table_class).filter(table_class.tool_no == self.tool_selected).first()

        
        if tool_data:
            val = getattr(tool_data, column, None)
            self.spinbox.setValue(int(val))
        else:
            self.spinbox.setValue(0)
            self.spinbox.setDisabled(True)
            
    @Slot()
    def saveField(self):
        
        if self.tool_selected is not None:
            
            table, column = self._query.split('.')
            table_class = globals().get(table)
            
            tool_data = self.session.query(table_class).filter(table_class.tool_no == self.tool_selected).first()
        
            if tool_data:
                setattr(tool_data, column, self.spinbox.value())
                self.session.commit()
    
    @Property(str)
    def labelText(self):
        return self._label_text

    @labelText.setter
    def labelText(self, text):
        self.label.setText(text)
        self._label_text = text

    @Property(str)
    def query(self):
        return self._query

    @query.setter
    def query(self, text):
        self._query = text
