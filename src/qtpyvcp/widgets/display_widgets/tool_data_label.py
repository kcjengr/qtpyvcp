from qtpy.QtCore import Property, QTimer, Signal, Slot
from qtpy.QtWidgets import QLabel

from qtpyvcp.widgets import VCPWidget
from qtpyvcp.utilities import logger

LOG = logger.getLogger(__name__)

class ToolDataLabel(QLabel, VCPWidget):
    """Label widget that displays tool table data for a specific column."""
    
    # Signal for runtime use
    toolDataChanged = Signal(object)
    
    DEFAULT_RULE_PROPERTY = "Text"
    RULE_PROPERTIES = VCPWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'Text': ['setText', str],
    })
    
    def __init__(self, parent=None):
        super(ToolDataLabel, self).__init__(parent)
        
        # Properties - store as string directly
        self._tool_column = 'T'  # Store as string
        self._tool_number = 0
        self._prefix = ''
        self._suffix = ''
        self._empty_text = 'N/A'
        self._sync_settings_key = ''  # New property for settings key
        
        # Tool table plugin (will be initialized at runtime)
        self.tool_table = None
        self._runtime_initialized = False
        
        # Show sample data initially
        self.update_display()
    
    def initialize_runtime(self):
        """Initialize runtime connections - called when actually used in Probe Basic"""
        if self._runtime_initialized:
            return
            
        try:
            from qtpyvcp.plugins import getPlugin
            self.tool_table = getPlugin('tooltable')
            if self.tool_table and hasattr(self.tool_table, 'tool_table_changed'):
                self.tool_table.tool_table_changed.connect(self.on_tool_table_changed)
            self._runtime_initialized = True
        except Exception as e:
            LOG.warning(f"Could not connect to tooltable plugin: {e}")
    
    @Slot(str)
    def setToolNumberFromString(self, tool_number_str):
        """Slot to set tool number from string - can be connected in Qt Designer"""
        # Try to initialize runtime on first use
        if not self._runtime_initialized:
            self.initialize_runtime()
            
        try:
            tool_number = int(tool_number_str) if tool_number_str.strip() else 0
            self.setToolNumber(tool_number)
        except ValueError:
            self.setToolNumber(0)
    
    @Slot(int)
    def setToolNumber(self, tool_number):
        """Set the tool number to display data for"""
        if self._tool_number != tool_number:
            self._tool_number = tool_number
            self.update_display()
    
    def update_display(self):
        """Update the label display"""
        # Use the column string directly
        column_letter = self._tool_column
        
        # If no runtime connection, show sample data
        if not self._runtime_initialized or not self.tool_table:
            sample_values = {
                'T': 1, 'P': 1, 'D': 0.125, 'X': 1.0000, 'Y': 0.0000, 'Z': 2.5000,
                'A': 0.0000, 'B': 0.0000, 'C': 0.0000, 'U': 0.0000, 'V': 0.0000, 'W': 0.0000,
                'I': 90.0, 'J': 15.0, 'Q': 1, 'R': 'Sample Tool'
            }
            value = sample_values.get(column_letter, 'N/A')
            text = f"{self._prefix}{value}{self._suffix}"
            self.setText(text)
            return
            
        # Runtime mode - get real tool data
        if self._tool_number <= 0:
            self.setText(self._empty_text)
            self.toolDataChanged.emit(None)
            return
        
        try:
            tool_table = self.tool_table.getToolTable()
            tool_data = tool_table.get(self._tool_number)
            
            if tool_data and column_letter in tool_data:
                value = tool_data[column_letter]
                text = f"{self._prefix}{value}{self._suffix}"
                self.setText(text)
                self.toolDataChanged.emit(value)
            else:
                self.setText(self._empty_text)
                self.toolDataChanged.emit(None)
                
        except Exception as e:
            LOG.warning(f"Error updating tool data display: {e}")
            self.setText(self._empty_text)
            self.toolDataChanged.emit(None)
    
    @Slot(dict)
    def on_tool_table_changed(self, tool_table):
        """Handle tool table changes"""
        if self._runtime_initialized:
            self.update_display()
    
    def showEvent(self, event):
        """Called when widget becomes visible - sync with settings if specified"""
        super(ToolDataLabel, self).showEvent(event)
        
        # Initialize runtime if not already done
        if not self._runtime_initialized:
            self.initialize_runtime()
        
        # Try to sync with specified settings key
        if self._sync_settings_key:
            QTimer.singleShot(100, self.sync_with_settings)
    
    def sync_with_settings(self):
        """Sync with a specific settings key"""
        if not self._sync_settings_key:
            return
            
        try:
            from qtpyvcp.utilities.settings import getSetting
            value = getSetting(self._sync_settings_key)
            if value is not None:
                self.setToolNumberFromString(str(value))
                LOG.debug(f"Synced with settings key '{self._sync_settings_key}': {value}")
        except Exception as e:
            LOG.debug(f"Could not sync with settings key '{self._sync_settings_key}': {e}")
    
    # Properties for Qt Designer
    @Property(str)
    def toolColumn(self):
        """Tool table column to display (T,P,D,X,Y,Z,A,B,C,U,V,W,I,J,Q,R)"""
        return self._tool_column
    
    @toolColumn.setter
    def toolColumn(self, value):
        # Validate that it's a valid column
        valid_columns = ['T', 'P', 'D', 'X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W', 'I', 'J', 'Q', 'R']
        if value.upper() in valid_columns:
            if self._tool_column != value.upper():
                self._tool_column = value.upper()
                self.update_display()
        else:
            # If invalid, keep current value
            LOG.warning(f"Invalid tool column '{value}'. Valid columns are: {', '.join(valid_columns)}")
    
    @Property(int)
    def toolNumber(self):
        """Tool number to display data for"""
        return self._tool_number
    
    @toolNumber.setter
    def toolNumber(self, value):
        self.setToolNumber(value)
    
    @Property(str)
    def syncSettingsKey(self):
        """Settings key to sync with on startup (e.g. 'conversational.tool_number')"""
        return self._sync_settings_key
    
    @syncSettingsKey.setter
    def syncSettingsKey(self, value):
        self._sync_settings_key = value
    
    @Property(str)
    def prefix(self):
        """Text to prepend to the formatted value"""
        return self._prefix
    
    @prefix.setter
    def prefix(self, value):
        self._prefix = value
        self.update_display()
    
    @Property(str)
    def suffix(self):
        """Text to append to the formatted value"""
        return self._suffix
    
    @suffix.setter
    def suffix(self, value):
        self._suffix = value
        self.update_display()
    
    @Property(str)
    def emptyText(self):
        """Text to display when no tool data is available"""
        return self._empty_text
    
    @emptyText.setter
    def emptyText(self, value):
        self._empty_text = value
        self.update_display()