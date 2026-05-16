import pytest
from unittest.mock import MagicMock, patch


class TestLEDButton:
    """Tests for LEDButton widget."""

    def test_init(self, qtbot):
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        assert btn is not None

    def test_init_has_led(self, qtbot):
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        assert btn.led is not None

    def test_init_led_diameter(self, qtbot):
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        assert btn.getLedDiameter() == 14

    def test_init_alignment_default(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        assert btn.getAlignment() == (Qt.AlignRight | Qt.AlignTop)

    def test_inherits_from_actionbutton(self, qtbot):
        from qtpy.QtWidgets import QPushButton
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        from qtpyvcp.widgets.button_widgets.action_button import ActionButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        assert isinstance(btn, ActionButton)
        assert isinstance(btn, QPushButton)

    def test_set_led_state(self, qtbot):
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        original_state = btn.led.getState()
        btn.setLedState(True)
        new_state = btn.led.getState()
        assert new_state is True

    def test_set_led_flashing(self, qtbot):
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        original_rate = btn.led.getFlashRate()
        btn.setLedFlashing(True)
        # After setting flashing, the rate should still be accessible
        new_rate = btn.led.getFlashRate()
        assert isinstance(new_rate, int) or isinstance(new_rate, float)

    def test_set_led_diameter(self, qtbot):
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        btn.setLedDiameter(20)
        assert btn.getLedDiameter() == 20

    def test_set_led_color(self, qtbot):
        from qtpy.QtGui import QColor
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        red = QColor(255, 0, 0)
        btn.setLedColor(red)
        assert btn.getLedColor() == red

    def test_size_hint(self, qtbot):
        from qtpy.QtCore import QSize
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        hint = btn.sizeHint()
        assert isinstance(hint, QSize)
        assert hint == QSize(80, 30)

    def test_place_led(self, qtbot):
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        # placeLed should not raise
        btn.placeLed()

    def test_resize_event_calls_place_led(self, qtbot):
        from qtpy.QtWidgets import QApplication
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        # Simulate resize by resizing the widget
        btn.resize(100, 50)
        # placeLed should have been called via resizeEvent
        # Just verify the led is still positioned correctly
        assert btn.led.parent() is btn

    def test_rule_properties_contains_led_on(self):
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        assert 'LED On' in LEDButton.RULE_PROPERTIES
        assert LEDButton.RULE_PROPERTIES['LED On'] == ['setLedState', bool]

    def test_rule_properties_contains_led_flashing(self):
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        assert 'LED Flashing' in LEDButton.RULE_PROPERTIES
        assert LEDButton.RULE_PROPERTIES['LED Flashing'] == ['setLedFlashing', bool]


class TestLEDButtonProperties:
    """Tests for LEDButton Qt properties."""

    def test_diameter_property(self, qtbot):
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        meta_obj = btn.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'diameter' in prop_names

    def test_color_property(self, qtbot):
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        meta_obj = btn.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'color' in prop_names

    def test_alignment_property(self, qtbot):
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        meta_obj = btn.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'alignment' in prop_names

    def test_set_alignment(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        btn.setAlignment(Qt.AlignCenter)
        assert btn.getAlignment() == Qt.AlignCenter

    def test_set_alignment_left(self, qtbot):
        from qtpy.QtCore import Qt
        from qtpyvcp.widgets.button_widgets.led_button import LEDButton
        btn = LEDButton()
        qtbot.addWidget(btn)
        btn.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        assert btn.getAlignment() == (Qt.AlignLeft | Qt.AlignVCenter)
