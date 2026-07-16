import pytest


class TestLEDWidgetInit:
    def test_default_diameter(self, led_widget):
        assert led_widget.getDiameter() == 30

    def test_default_color(self, led_widget):
        from qtpy.QtGui import QColor

        color = led_widget.getColor()
        assert color.name() == QColor("red").name()

    def test_default_alignment(self, led_widget):
        from qtpy.QtCore import Qt

        assert led_widget.getAlignment() & Qt.AlignCenter

    def test_default_state_true(self, led_widget):
        assert led_widget.getState() is True

    def test_default_flashing_false(self, led_widget):
        assert led_widget.isFlashing() is False

    def test_default_flash_rate(self, led_widget):
        assert led_widget.getFlashRate() == 200

    def test_timer_initialized(self, led_widget):
        from qtpy.QtCore import QTimer

        timer = led_widget._timer
        assert isinstance(timer, QTimer)


class TestLEDWidgetProperties:
    def test_set_diameter(self, led_widget):
        led_widget.setDiameter(50)
        assert led_widget.getDiameter() == 50

    def test_set_color(self, led_widget):
        from qtpy.QtGui import QColor

        led_widget.setColor(QColor("green"))
        color = led_widget.getColor()
        assert color.name() == QColor("green").name()

    def test_set_alignment(self, led_widget):
        from qtpy.QtCore import Qt

        led_widget.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        alignment = led_widget.getAlignment()
        assert alignment & Qt.AlignLeft
        assert alignment & Qt.AlignTop

    def test_set_state_true(self, led_widget):
        led_widget.setState(True)
        assert led_widget.getState() is True

    def test_set_state_false(self, led_widget):
        led_widget.setState(False)
        assert led_widget.getState() is False

    def test_set_flashing(self, led_widget):
        led_widget.setFlashing(True)
        assert led_widget.isFlashing() is True

    def test_set_flash_rate(self, led_widget):
        led_widget.setFlashRate(500)
        assert led_widget.getFlashRate() == 500


class TestLEDWidgetMethods:
    def test_toggle_state_from_true(self, led_widget):
        led_widget.setState(True)
        led_widget.toggleState()
        assert led_widget.getState() is False

    def test_toggle_state_from_false(self, led_widget):
        led_widget.setState(False)
        led_widget.toggleState()
        assert led_widget.getState() is True

    def test_start_flashing_starts_timer(self, led_widget):
        led_widget.startFlashing()
        assert led_widget.isFlashing() is True

    def test_stop_flashing_stops_timer(self, led_widget):
        led_widget.setFlashing(True)
        led_widget.stopFlashing()
        assert led_widget.isFlashing() is False

    def test_start_and_stop_flashing_chain(self, led_widget):
        led_widget.startFlashing()
        assert led_widget.isFlashing() is True
        led_widget.stopFlashing()
        assert led_widget.isFlashing() is False


class TestLEDWidgetSizeHints:
    def test_size_hint_equals_diameter(self, led_widget):
        hint = led_widget.sizeHint()
        assert hint.width() == 30
        assert hint.height() == 30

    def test_minimum_size_hint_equals_diameter(self, led_widget):
        hint = led_widget.minimumSizeHint()
        assert hint.width() == 30
        assert hint.height() == 30

    def test_size_hint_changes_with_diameter(self, led_widget):
        led_widget.setDiameter(64)
        hint = led_widget.sizeHint()
        assert hint.width() == 64
        assert hint.height() == 64


class TestLEDWidgetDisabledState:
    def test_enabled_by_default(self, led_widget):
        assert led_widget.isEnabled() is True

    def test_set_enabled_false(self, led_widget):
        led_widget.setEnabled(False)
        assert led_widget.isEnabled() is False

    def test_set_enabled_true(self, led_widget):
        led_widget.setEnabled(False)
        led_widget.setEnabled(True)
        assert led_widget.isEnabled() is True


class TestLEDWidgetQtProperties:
    def test_diameter_property_get_set(self, led_widget):
        from qtpy.QtCore import Property

        prop = led_widget.__class__.diameter
        assert isinstance(prop, Property)
        led_widget.diameter = 40
        assert led_widget.diameter == 40

    def test_color_property_get_set(self, led_widget):
        from qtpy.QtGui import QColor
        from qtpy.QtCore import Property

        prop = led_widget.__class__.color
        assert isinstance(prop, Property)
        led_widget.color = QColor("blue")
        assert led_widget.color.name() == QColor("blue").name()

    def test_state_property_get_set(self, led_widget):
        from qtpy.QtCore import Property

        prop = led_widget.__class__.state
        assert isinstance(prop, Property)
        led_widget.state = False
        assert led_widget.state is False

    def test_flashing_property_get_set(self, led_widget):
        from qtpy.QtCore import Property

        prop = led_widget.__class__.flashing
        assert isinstance(prop, Property)
        led_widget.flashing = True
        assert led_widget.flashing is True

    def test_flash_rate_property_get_set(self, led_widget):
        from qtpy.QtCore import Property

        prop = led_widget.__class__.flashRate
        assert isinstance(prop, Property)
        led_widget.flashRate = 100
        assert led_widget.flashRate == 100


class TestLEDWidgetFocusPolicy:
    def test_no_focus_policy(self, led_widget):
        from qtpy.QtCore import Qt

        policy = led_widget.focusPolicy()
        assert policy == Qt.NoFocus
