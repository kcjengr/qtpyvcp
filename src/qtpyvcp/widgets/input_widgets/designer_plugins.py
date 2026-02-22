from PySide6.QtUiTools import QUiLoader

from qtpyvcp.widgets.qtdesigner import _DesignerPlugin
from qtpyvcp.widgets.qtdesigner.designer_plugin import RulesEditorExtension

from qtpyvcp.widgets.input_widgets.line_edit import VCPLineEdit
class VCPLineEditPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPLineEdit

from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry
class MDIEntryPlugin(_DesignerPlugin):
    def pluginClass(self):
        return MDIEntry

    def toolTip(self):
        return "MDI command entry"

from qtpyvcp.widgets.input_widgets.mdihistory_widget import MDIHistory
class MDIHistoryPlugin(_DesignerPlugin):
    def pluginClass(self):
        return MDIHistory

# from gcode_editor import GcodeEditor
# class GcodeEditorPlugin(_DesignerPlugin):
#     def pluginClass(self):
#         return GcodeEditor

from qtpyvcp.widgets.input_widgets.gcode_text_edit import GcodeTextEdit
class GCodeEditPlugin(_DesignerPlugin):
    def pluginClass(self):
        return GcodeTextEdit

from qtpyvcp.widgets.input_widgets.recent_file_combobox import RecentFileComboBox
class RecentFileComboBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return RecentFileComboBox

from qtpyvcp.widgets.input_widgets.tool_table import ToolTable
class ToolTablePlugin(_DesignerPlugin):
    def pluginClass(self):
        return ToolTable

from qtpyvcp.widgets.input_widgets.jog_increment import JogIncrementWidget
class JogIncrementPlugin(_DesignerPlugin):
    def pluginClass(self):
        return JogIncrementWidget

from qtpyvcp.widgets.input_widgets.file_system import FileSystemTable
class FileSystemPlugin(_DesignerPlugin):
    def pluginClass(self):
        return FileSystemTable

from qtpyvcp.widgets.input_widgets.file_system import RemovableDeviceComboBox
class RemovableDeviceComboBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return RemovableDeviceComboBox

from qtpyvcp.widgets.input_widgets.action_slider import ActionSlider
class ActionSliderPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionSlider

from qtpyvcp.widgets.input_widgets.action_dial import ActionDial
class ActionDialPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionDial

from qtpyvcp.widgets.input_widgets.action_combobox import ActionComboBox
class ActionComboBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ActionComboBox

from qtpyvcp.widgets.input_widgets.probesim_widget import ProbeSim
class ProbeSimPlugin(_DesignerPlugin):
    def pluginClass(self):
        return ProbeSim

from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
from qtpyvcp.widgets.qtdesigner.settings_selector import SettingSelectorExtension
class VCPSettingsLineEditPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPSettingsLineEdit
    def objectName(self):
        return 'settings_lineedit'
    def designerExtensions(self):
        return [SettingSelectorExtension, RulesEditorExtension]

from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSlider
class VCPSettingsSliderPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPSettingsSlider
    def objectName(self):
        return 'settings_slider'
    def designerExtensions(self):
        return [SettingSelectorExtension, RulesEditorExtension]

from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSpinBox
class VCPSettingsSpinBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPSettingsSpinBox
    def objectName(self):
        return 'settings_spinbox'
    def designerExtensions(self):
        return [SettingSelectorExtension, RulesEditorExtension]

from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsDoubleSpinBox
class VCPSettingsDoubleSpinBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPSettingsDoubleSpinBox
    def objectName(self):
        return 'settings_double_spinbox'
    def designerExtensions(self):
        return [SettingSelectorExtension, RulesEditorExtension]

from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsCheckBox
class VCPSettingsCheckBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPSettingsCheckBox
    def designerExtensions(self):
        return [SettingSelectorExtension, RulesEditorExtension]
    def domXml(self):
        return """
        <widget class="VCPSettingsCheckBox" name="settings_checkbox">
          <property name="text">
            <string>CheckBox</string>
          </property>
        </widget>"""

from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
class VCPSettingsPushButtonPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPSettingsPushButton
    def designerExtensions(self):
        return [SettingSelectorExtension, RulesEditorExtension]
    def domXml(self):
        return """
        <widget class="VCPSettingsPushButton" name="settings_pushbutton">
          <property name="text">
            <string>Settings Button</string>
          </property>
        </widget>"""

from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsComboBox
class VCPSettingsComboBoxPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPSettingsComboBox
    def designerExtensions(self):
        return [SettingSelectorExtension, RulesEditorExtension]

from qtpyvcp.widgets.input_widgets.offset_table import OffsetTable
class OffsetTablePlugin(_DesignerPlugin):
    def pluginClass(self):
        return OffsetTable
    def objectName(self):
        return 'offset_table'

from qtpyvcp.widgets.input_widgets.dro_line_edit import DROLineEdit
from qtpyvcp.widgets.qtdesigner.dro_editor import DroEditorExtension
class DROLineEditPlugin(_DesignerPlugin):
    def pluginClass(self):
        return DROLineEdit
    def objectName(self):
        return 'dro_entry'
    def designerExtensions(self):
        return [DroEditorExtension, RulesEditorExtension]
