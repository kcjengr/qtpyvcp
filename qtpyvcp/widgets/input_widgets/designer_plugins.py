from qtpyvcp.widgets.qtdesigner import _DesignerPlugin

from line_edit import VCPLineEdit
class VCPLineEditPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPLineEdit

from mdientry_widget import MDIEntry
class MDIEntryPlugin(_DesignerPlugin):
    def pluginClass(self):
        return MDIEntry

    def toolTip(self):
        return "MDI command entry"

from gcode_editor import GcodeEditor
class GcodeEditorPlugin(_DesignerPlugin):
    def pluginClass(self):
        return GcodeEditor

from recent_file_combobox import RecentFileComboBox
class RecentFileComboBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return RecentFileComboBox

from tool_table import ToolTable
class ToolTablePlugin(_DesignerPlugin):
    def pluginClass(self):
        return ToolTable

from jog_increment import JogIncrementWidget
class JogIncrementPlugin(_DesignerPlugin):
    def pluginClass(self):
        return JogIncrementWidget

from file_system import FileSystemTable
class FileSystemPlugin(_DesignerPlugin):
    def pluginClass(self):
        return FileSystemTable

from file_system import RemovableDeviceComboBox
class RemovableDeviceComboBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return RemovableDeviceComboBox

from action_slider import ActionSlider
class ActionSliderPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionSlider

from action_dial import ActionDial
class ActionDialPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionDial

from action_combobox import ActionComboBox
class ActionComboBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionComboBox

from probesim_widget import ProbeSim
class ProbeSimPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ProbeSim

from setting_slider import VCPSettingsLineEdit
class VCPSettingsLineEditPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPSettingsLineEdit
    def objectName(self):
        return 'settings_lineedit'

from setting_slider import VCPSettingsSlider
class VCPSettingsSliderPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPSettingsSlider
    def objectName(self):
        return 'settings_slider'

from setting_slider import VCPSettingsSpinBox
class VCPSettingsSpinBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPSettingsSpinBox
    def objectName(self):
        return 'settings_spinbox'

from setting_slider import VCPSettingsDoubleSpinBox
class VCPSettingsDoubleSpinBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPSettingsDoubleSpinBox
    def objectName(self):
        return 'settings_double_spinbox'

from setting_slider import VCPSettingsCheckBox
class VCPSettingsCheckBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPSettingsCheckBox
    def objectName(self):
        return 'settings_checkbox'

from offset_table import OffsetTable
class OffsetTablePlugin(_DesignerPlugin):
    def pluginClass(self):
        return OffsetTable

    def objectName(self):
        return 'offset_table'
