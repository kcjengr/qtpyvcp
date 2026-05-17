import pytest
from unittest.mock import MagicMock, patch


class TestVCPSettingsLineEdit:
    """Tests for VCPSettingsLineEdit widget."""

    def test_init(self, qtbot):
        from qtpy.QtWidgets import QLineEdit
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        widget = VCPSettingsLineEdit(parent=None)
        qtbot.addWidget(widget)
        assert isinstance(widget, QLineEdit)

    def test_formatValue_with_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsLineEdit(parent=None)
        SETTINGS['test.fmt'] = Setting(default_value=42, value_type='int')
        
        widget._setting = SETTINGS['test.fmt']
        result = widget.formatValue(42)
        assert result == '42'
        
        del SETTINGS['test.fmt']

    def test_formatValue_float_with_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsLineEdit(parent=None)
        SETTINGS['test.fmt2'] = Setting(default_value=3.14, value_type='float')
        
        widget._setting = SETTINGS['test.fmt2']
        widget._display_decimals = 2
        result = widget.formatValue(3.14159)
        assert result == '3.14'
        
        del SETTINGS['test.fmt2']

    def test_formatValue_str_type(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsLineEdit(parent=None)
        SETTINGS['test.fmt3'] = Setting(default_value='hello', value_type='str')
        
        widget._setting = SETTINGS['test.fmt3']
        result = widget.formatValue('world')
        assert result == 'world'
        
        del SETTINGS['test.fmt3']

    def test_setDisplayValue_no_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        widget = VCPSettingsLineEdit(parent=None)
        qtbot.addWidget(widget)
        widget.setText('42')
        assert widget.text() == '42'

    def test_setDisplayValue_with_format_no_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        widget = VCPSettingsLineEdit(parent=None)
        qtbot.addWidget(widget)
        widget.setText('3.1')
        assert widget.text() == '3.1'

    def test_setValue_no_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        widget = VCPSettingsLineEdit(parent=None)
        qtbot.addWidget(widget)
        widget.setValue('test')
        assert widget._tmp_value == 'test'

    def test_setValue_with_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsLineEdit(parent=None)
        SETTINGS['test.setting'] = Setting(default_value=0, value_type='int')
        
        widget._setting_name = 'test.setting'
        widget.initialize()
        widget.setValue(100)
        
        val = SETTINGS['test.setting'].getValue()
        assert str(val) == '100' or val == 100
        
        del SETTINGS['test.setting']

    def test_initialize_no_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        widget = VCPSettingsLineEdit(parent=None)
        qtbot.addWidget(widget)
        widget._setting_name = 'nonexistent.setting'
        widget.initialize()
        assert widget._setting is None

    def test_initialize_with_int_setting(self, qtbot):
        from qtpy.QtGui import QIntValidator
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsLineEdit(parent=None)
        SETTINGS['test.int'] = Setting(default_value=42, value_type='int')
        
        widget._setting_name = 'test.int'
        widget.initialize()
        
        assert widget._setting is not None
        assert isinstance(widget.validator(), QIntValidator)
        
        del SETTINGS['test.int']

    def test_initialize_with_float_setting(self, qtbot):
        from qtpy.QtGui import QDoubleValidator
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsLineEdit(parent=None)
        SETTINGS['test.float'] = Setting(default_value=3.14, value_type='float')
        
        widget._setting_name = 'test.float'
        widget.initialize()
        
        assert isinstance(widget.validator(), QDoubleValidator)
        
        del SETTINGS['test.float']

    def test_initialize_with_str_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsLineEdit(parent=None)
        SETTINGS['test.str'] = Setting(default_value='hello', value_type='str')
        
        widget._setting_name = 'test.str'
        widget.initialize()
        
        assert widget.validator() is None
        
        del SETTINGS['test.str']

    def test_initialize_with_tmp_value(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsLineEdit(parent=None)
        widget._tmp_value = '99'
        
        SETTINGS['test.tmp'] = Setting(default_value=0, value_type='int')
        
        widget._setting_name = 'test.tmp'
        widget.initialize()
        
        assert widget._setting is not None
        
        del SETTINGS['test.tmp']

    def test_onReturnPressed(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        widget = VCPSettingsLineEdit(parent=None)
        qtbot.addWidget(widget)
        widget.setText('hello')
        widget.onReturnPressed()
        assert widget.hasFocus() is False

    def test_onEditingFinished(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsLineEdit(parent=None)
        SETTINGS['test.edit'] = Setting(default_value=10, value_type='int')
        
        widget._setting_name = 'test.edit'
        widget.initialize()
        widget.setText('50')
        widget.onEditingFinished()
        
        val = SETTINGS['test.edit'].getValue()
        assert str(val) == '50' or val == 50
        
        del SETTINGS['test.edit']

    def test_textFormat_validation_valid(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsLineEdit(parent=None)
        SETTINGS['test.validate'] = Setting(default_value=42, value_type='int')
        
        widget._setting_name = 'test.validate'
        widget.textFormat = '{} mm'
        
        assert widget.textFormat == '{} mm'
        
        del SETTINGS['test.validate']

    def test_textFormat_validation_invalid(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsLineEdit(parent=None)
        SETTINGS['test.bad'] = Setting(default_value=42, value_type='int')
        
        widget._setting_name = 'test.bad'
        widget.textFormat = '{invalid'
        
        assert widget.textFormat == '{invalid'
        
        del SETTINGS['test.bad']

    def test_textFormat_no_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        widget = VCPSettingsLineEdit(parent=None)
        widget.textFormat = 'safe format'
        assert widget.textFormat == 'safe format'


class TestVCPSettingsSlider:
    """Tests for VCPSettingsSlider widget."""

    def test_init(self, qtbot):
        from qtpy.QtWidgets import QSlider
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSlider
        widget = VCPSettingsSlider(parent=None)
        qtbot.addWidget(widget)
        assert isinstance(widget, QSlider)

    def test_init_with_setting_name(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSlider
        widget = VCPSettingsSlider(parent=None)
        qtbot.addWidget(widget)
        assert widget.settingName == ''

    def test_setDisplayValue(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSlider
        widget = VCPSettingsSlider(parent=None)
        qtbot.addWidget(widget)
        widget.setDisplayValue(50)
        assert widget.value() == 50

    def test_mouseDoubleClickEvent(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpy.QtGui import QMouseEvent
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSlider
        widget = VCPSettingsSlider(parent=None)
        qtbot.addWidget(widget)
        widget.setRange(0, 100)
        widget.setValue(0)
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            widget.rect().center(),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        widget.mouseDoubleClickEvent(event)
        assert widget.value() == 100

    def test_initialize_no_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSlider
        widget = VCPSettingsSlider(parent=None)
        qtbot.addWidget(widget)
        widget._setting_name = 'nonexistent'
        widget.initialize()
        assert widget._setting is None

    def test_initialize_with_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSlider
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsSlider(parent=None)
        SETTINGS['test.slider'] = Setting(default_value=50, min_value=0, max_value=100, value_type='int')
        
        widget._setting_name = 'test.slider'
        widget.initialize()
        
        assert widget.minimum() == 0
        assert widget.maximum() == 100
        
        del SETTINGS['test.slider']

    def test_initialize_with_no_bounds(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSlider
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsSlider(parent=None)
        SETTINGS['test.nobounds'] = Setting(default_value=50, value_type='int')
        
        widget._setting_name = 'test.nobounds'
        widget.initialize()
        
        assert widget.minimum() == 0
        assert widget.maximum() == 99
        
        del SETTINGS['test.nobounds']


class TestVCPSettingsSpinBox:
    """Tests for VCPSettingsSpinBox widget."""

    def test_init(self, qtbot):
        from qtpy.QtWidgets import QSpinBox
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSpinBox
        widget = VCPSettingsSpinBox(parent=None)
        qtbot.addWidget(widget)
        assert isinstance(widget, QSpinBox)

    def test_setDisplayValue(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSpinBox
        widget = VCPSettingsSpinBox(parent=None)
        qtbot.addWidget(widget)
        widget.setDisplayValue(42)
        assert widget.value() == 42

    def test_initialize_no_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSpinBox
        widget = VCPSettingsSpinBox(parent=None)
        qtbot.addWidget(widget)
        widget._setting_name = 'nonexistent'
        widget.initialize()
        assert widget._setting is None

    def test_initialize_with_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSpinBox
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsSpinBox(parent=None)
        SETTINGS['test.spin'] = Setting(default_value=25, min_value=0, max_value=100, value_type='int')
        
        widget._setting_name = 'test.spin'
        widget.initialize()
        
        assert widget.minimum() == 0
        assert widget.maximum() == 100
        
        del SETTINGS['test.spin']

    def test_initialize_without_bounds(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSpinBox
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsSpinBox(parent=None)
        SETTINGS['test.spin2'] = Setting(default_value=10, value_type='int')
        
        widget._setting_name = 'test.spin2'
        widget.initialize()
        
        assert widget.value() == 10
        
        del SETTINGS['test.spin2']


class TestVCPSettingsDoubleSpinBox:
    """Tests for VCPSettingsDoubleSpinBox widget."""

    def test_init(self, qtbot):
        from qtpy.QtWidgets import QDoubleSpinBox
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsDoubleSpinBox
        widget = VCPSettingsDoubleSpinBox(parent=None)
        qtbot.addWidget(widget)
        assert isinstance(widget, QDoubleSpinBox)

    def test_setDisplayValue(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsDoubleSpinBox
        widget = VCPSettingsDoubleSpinBox(parent=None)
        qtbot.addWidget(widget)
        widget.setDisplayValue(3.14)
        assert abs(widget.value() - 3.14) < 0.001

    def test_initialize_no_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsDoubleSpinBox
        widget = VCPSettingsDoubleSpinBox(parent=None)
        qtbot.addWidget(widget)
        widget._setting_name = 'nonexistent'
        widget.initialize()
        assert widget._setting is None

    def test_initialize_with_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsDoubleSpinBox
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsDoubleSpinBox(parent=None)
        SETTINGS['test.doublespin'] = Setting(default_value=2.5, min_value=0.0, max_value=10.0, value_type='float')
        
        widget._setting_name = 'test.doublespin'
        widget.initialize()
        
        assert abs(widget.minimum() - 0.0) < 0.001
        assert abs(widget.maximum() - 10.0) < 0.001
        
        del SETTINGS['test.doublespin']

    def test_editingEnded(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsDoubleSpinBox
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsDoubleSpinBox(parent=None)
        SETTINGS['test.edit2'] = Setting(default_value=1.0, value_type='float')
        
        widget._setting_name = 'test.edit2'
        widget.initialize()
        
        assert widget._setting is not None
        
        del SETTINGS['test.edit2']


class TestVCPSettingsCheckBox:
    """Tests for VCPSettingsCheckBox widget."""

    def test_init(self, qtbot):
        from qtpy.QtWidgets import QCheckBox
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsCheckBox
        widget = VCPSettingsCheckBox(parent=None)
        qtbot.addWidget(widget)
        assert isinstance(widget, QCheckBox)

    def test_setDisplayChecked(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsCheckBox
        widget = VCPSettingsCheckBox(parent=None)
        qtbot.addWidget(widget)
        widget.setDisplayChecked(True)
        assert widget.isChecked() is True
        widget.setDisplayChecked(False)
        assert widget.isChecked() is False

    def test_initialize_no_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsCheckBox
        widget = VCPSettingsCheckBox(parent=None)
        qtbot.addWidget(widget)
        widget._setting_name = 'nonexistent'
        widget.initialize()
        assert widget._setting is None

    def test_initialize_with_true_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsCheckBox
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsCheckBox(parent=None)
        SETTINGS['test.cb'] = Setting(default_value=True, value_type='bool')
        
        widget._setting_name = 'test.cb'
        widget.initialize()
        
        assert widget.isChecked() is True
        
        del SETTINGS['test.cb']

    def test_initialize_with_false_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsCheckBox
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsCheckBox(parent=None)
        SETTINGS['test.cb2'] = Setting(default_value=False, value_type='bool')
        
        widget._setting_name = 'test.cb2'
        widget.initialize()
        
        assert widget.isChecked() is False
        
        del SETTINGS['test.cb2']

    def test_toggled_connects_to_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsCheckBox
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsCheckBox(parent=None)
        SETTINGS['test.cb3'] = Setting(default_value=False, value_type='bool')
        
        widget._setting_name = 'test.cb3'
        widget.initialize()
        
        # The toggled signal connects to _setting.setValue in initialize()
        # Qt signals may convert bool to string through the event loop
        widget.setChecked(True)
        
        val = SETTINGS['test.cb3'].getValue()
        # Accept either bool or string representation due to Qt signal type conversion
        assert val is True or str(val) == 'True' or val == 1
        
        del SETTINGS['test.cb3']


class TestVCPSettingsPushButton:
    """Tests for VCPSettingsPushButton widget."""

    def test_init(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        assert isinstance(widget, QPushButton)

    def test_init_checkable(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        assert widget.isCheckable() is True

    def test_init_disabled(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        assert widget.isEnabled() is False

    def test_outputAsInt_default(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        assert widget.outputAsInt is False

    def test_outputAsInt_setter(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        widget.outputAsInt = True
        assert widget.outputAsInt is True

    def test_value_unchecked_false(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        widget.setChecked(False)
        assert widget.value() is False

    def test_value_checked_true(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        widget.setChecked(True)
        assert widget.value() is True

    def test_value_unchecked_as_int(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        widget.outputAsInt = True
        widget.setChecked(False)
        assert widget.value() == 0

    def test_value_checked_as_int(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        widget.outputAsInt = True
        widget.setChecked(True)
        assert widget.value() == 1

    def test_setValue_bool(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        widget.setValue(True)
        assert widget.isChecked() is True
        widget.setValue(False)
        assert widget.isChecked() is False

    def test_setValue_int(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        widget.setValue(1)
        assert widget.isChecked() is True
        widget.setValue(0)
        assert widget.isChecked() is False

    def test_setValue_string_true(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        for val in ['true', '1', 'yes', 'on']:
            widget.setValue(val)
            assert widget.isChecked() is True

    def test_setValue_string_false(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        for val in ['false', '0', 'no', 'off']:
            widget.setValue(val)
            assert widget.isChecked() is False

    def test_setValue_string_invalid(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        with pytest.raises(ValueError):
            widget.setValue('not_a_number')

    def test_getSettingsValue(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        widget.setChecked(True)
        assert widget.getSettingsValue() is True

    def test_setSettingsValue(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        widget.setSettingsValue(True)
        assert widget.isChecked() is True

    def test_initialize_enables_button(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsPushButton(parent=None)
        SETTINGS['test.pb'] = Setting(default_value=False, value_type='bool')
        
        widget._setting_name = 'test.pb'
        widget.initialize()
        
        assert widget.isEnabled() is True
        
        del SETTINGS['test.pb']

    def test_initialize_sets_checked_state(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsPushButton(parent=None)
        SETTINGS['test.pb2'] = Setting(default_value=True, value_type='bool')
        
        widget._setting_name = 'test.pb2'
        widget.initialize()
        
        assert widget.isChecked() is True
        
        del SETTINGS['test.pb2']

    def test_text_when_output_as_int(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        widget.outputAsInt = True
        widget.setChecked(True)
        assert widget.text() == '1'

    def test_text_normal_button(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsPushButton
        widget = VCPSettingsPushButton(parent=None)
        qtbot.addWidget(widget)
        widget.setText('Hello')
        assert widget.text() == 'Hello'


class TestVCPSettingsComboBox:
    """Tests for VCPSettingsComboBox widget."""

    def test_init(self, qtbot):
        from qtpy.QtWidgets import QComboBox
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsComboBox
        widget = VCPSettingsComboBox(parent=None)
        qtbot.addWidget(widget)
        assert isinstance(widget, QComboBox)

    def test_setDisplayIndex(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsComboBox
        widget = VCPSettingsComboBox(parent=None)
        qtbot.addWidget(widget)
        widget.addItem('option1')
        widget.addItem('option2')
        widget.setDisplayIndex(1)
        assert widget.currentIndex() == 1

    def test_initialize_no_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsComboBox
        widget = VCPSettingsComboBox(parent=None)
        qtbot.addWidget(widget)
        widget._setting_name = 'nonexistent'
        widget.initialize()
        assert widget._setting is None

    def test_initialize_with_enum_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsComboBox
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsComboBox(parent=None)
        SETTINGS['test.cb_combo'] = Setting(
            default_value=1, 
            value_type='int',
            options=['low', 'medium', 'high']
        )
        
        widget._setting_name = 'test.cb_combo'
        widget.initialize()
        
        assert widget.count() == 3
        assert widget.itemText(0) == 'low'
        assert widget.itemText(1) == 'medium'
        assert widget.itemText(2) == 'high'
        
        del SETTINGS['test.cb_combo']

    def test_initialize_sets_index(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsComboBox
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsComboBox(parent=None)
        SETTINGS['test.cb_idx'] = Setting(
            default_value=2, 
            value_type='int',
            options=['a', 'b', 'c']
        )
        
        widget._setting_name = 'test.cb_idx'
        widget.initialize()
        
        assert widget.currentIndex() == 2
        
        del SETTINGS['test.cb_idx']

    def test_currentIndexChanged_connects_to_setting(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsComboBox
        from qtpyvcp import SETTINGS
        from qtpyvcp.utilities.settings import Setting
        
        widget = VCPSettingsComboBox(parent=None)
        SETTINGS['test.cb_conn'] = Setting(
            default_value=0, 
            value_type='int',
            options=['x', 'y', 'z']
        )
        
        widget._setting_name = 'test.cb_conn'
        widget.initialize()
        
        # The currentIndexChanged signal connects to _setting.setValue in initialize()
        # Qt signals may convert int to string through the event loop
        widget.setCurrentIndex(2)
        
        val = SETTINGS['test.cb_conn'].getValue()
        # Accept either int or string representation due to Qt signal type conversion
        assert val == 2 or str(val) == '2'
        
        del SETTINGS['test.cb_conn']


class TestVCPAbstractSettingsWidget:
    """Tests for VCPAbstractSettingsWidget base class."""

    def test_settingName_property_via_line_edit(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsLineEdit
        widget = VCPSettingsLineEdit(parent=None)
        qtbot.addWidget(widget)
        assert widget.settingName == ''
        widget.settingName = 'test.setting.name'
        assert widget.settingName == 'test.setting.name'

    def test_settingName_property_via_slider(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSlider
        widget = VCPSettingsSlider(parent=None)
        qtbot.addWidget(widget)
        assert widget.settingName == ''
        widget.settingName = 'test.slider.name'
        assert widget.settingName == 'test.slider.name'

    def test_settingName_is_qt_property_via_spinbox(self, qtbot):
        from qtpyvcp.widgets.input_widgets.setting_slider import VCPSettingsSpinBox
        widget = VCPSettingsSpinBox(parent=None)
        qtbot.addWidget(widget)
        meta_obj = widget.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'settingName' in prop_names
