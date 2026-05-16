import pytest


class TestStatusLEDInit:
    def test_default_state(self, status_led):
        assert status_led.getState() is True

    def test_default_flashing(self, status_led):
        assert status_led.isFlashing() is False

    def test_default_diameter(self, status_led):
        assert status_led.getDiameter() == 30

    def test_inherits_from_led_widget(self, status_led):
        from qtpyvcp.widgets.base_widgets.led_widget import LEDWidget

        assert isinstance(status_led, LEDWidget)


class TestStatusLEDProperties:
    def test_set_state_true(self, status_led):
        status_led.setState(True)
        assert status_led.getState() is True

    def test_set_state_false(self, status_led):
        status_led.setState(False)
        assert status_led.getState() is False

    def test_set_flashing_true(self, status_led):
        status_led.setFlashing(True)
        assert status_led.isFlashing() is True

    def test_set_flashing_false(self, status_led):
        status_led.setFlashing(False)
        assert status_led.isFlashing() is False

    def test_toggle_state(self, status_led):
        status_led.setState(True)
        status_led.toggleState()
        assert status_led.getState() is False

    def test_toggle_state_from_false(self, status_led):
        status_led.setState(False)
        status_led.toggleState()
        assert status_led.getState() is True


class TestStatusLEDRuleProperties:
    def test_default_rule_property(self, status_led):
        assert status_led.DEFAULT_RULE_PROPERTY == "On"

    def test_rule_properties_contains_on(self, status_led):
        assert "On" in status_led.RULE_PROPERTIES
        assert status_led.RULE_PROPERTIES["On"] == ["setState", bool]

    def test_rule_properties_contains_flashing(self, status_led):
        assert "Flashing" in status_led.RULE_PROPERTIES
        assert status_led.RULE_PROPERTIES["Flashing"] == ["setFlashing", bool]


class TestStatusLEDQtProperties:
    def test_state_property(self, status_led):
        from qtpy.QtCore import Property

        prop = status_led.__class__.state
        assert isinstance(prop, Property)
        status_led.state = False
        assert status_led.state is False

    def test_flashing_property(self, status_led):
        from qtpy.QtCore import Property

        prop = status_led.__class__.flashing
        assert isinstance(prop, Property)
        status_led.flashing = True
        assert status_led.flashing is True

    def test_diameter_property(self, status_led):
        from qtpy.QtCore import Property

        prop = status_led.__class__.diameter
        assert isinstance(prop, Property)
        status_led.diameter = 40
        assert status_led.diameter == 40


class TestStatusLEDInheritance:
    def test_is_qwidget(self, status_led):
        from qtpy.QtWidgets import QWidget

        assert isinstance(status_led, QWidget)

    def test_focus_policy_no_focus(self, status_led):
        from qtpy.QtCore import Qt

        policy = status_led.focusPolicy()
        assert policy == Qt.NoFocus


class TestStatusLEDStartStopFlashing:
    def test_start_flashing(self, status_led):
        status_led.startFlashing()
        assert status_led.isFlashing() is True

    def test_stop_flashing(self, status_led):
        status_led.setFlashing(True)
        status_led.stopFlashing()
        assert status_led.isFlashing() is False

    def test_start_and_stop_chain(self, status_led):
        status_led.startFlashing()
        assert status_led.isFlashing() is True
        status_led.stopFlashing()
        assert status_led.isFlashing() is False


class TestStatusLEDFlashRate:
    def test_default_flash_rate(self, status_led):
        assert status_led.getFlashRate() == 200

    def test_set_flash_rate(self, status_led):
        status_led.setFlashRate(500)
        assert status_led.getFlashRate() == 500


class TestStatusLEDSizeHints:
    def test_size_hint(self, status_led):
        hint = status_led.sizeHint()
        assert hint.width() == 30
        assert hint.height() == 30

    def test_minimum_size_hint(self, status_led):
        hint = status_led.minimumSizeHint()
        assert hint.width() == 30
        assert hint.height() == 30
