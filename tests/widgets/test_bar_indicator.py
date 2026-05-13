import pytest


class TestBarIndicatorInit:
    def test_default_value(self, bar_indicator):
        assert bar_indicator.value == 100

    def test_default_minimum(self, bar_indicator):
        assert bar_indicator.minimum == 0.0

    def test_default_maximum(self, bar_indicator):
        assert bar_indicator.maximum == 100.0

    def test_default_orientation_horizontal(self, bar_indicator):
        from qtpy.QtCore import Qt

        assert bar_indicator.orientation == Qt.Horizontal

    def test_default_format(self, bar_indicator):
        assert bar_indicator.format == ".2f"

    def test_default_prefix(self, bar_indicator):
        assert bar_indicator.prefix == ""

    def test_default_sufix(self, bar_indicator):
        assert bar_indicator.sufix == ""

    def test_border_radius_default(self, bar_indicator):
        assert bar_indicator.borderRadius == 2

    def test_border_width_default(self, bar_indicator):
        assert bar_indicator.borderWidth == 1


class TestBarIndicatorValue:
    def test_set_value_within_range(self, bar_indicator):
        bar_indicator.setValue(50)
        assert bar_indicator.value == 50

    def test_set_value_at_minimum(self, bar_indicator):
        bar_indicator.setValue(0)
        assert bar_indicator.value == 0

    def test_set_value_at_maximum(self, bar_indicator):
        bar_indicator.setValue(100)
        assert bar_indicator.value == 100

    def test_set_value_below_minimum_ignored(self, bar_indicator):
        bar_indicator.setValue(-50)
        assert bar_indicator.value == 100

    def test_set_value_above_maximum_ignored(self, bar_indicator):
        bar_indicator.setValue(200)
        assert bar_indicator.value == 100

    def test_set_value_float(self, bar_indicator):
        bar_indicator.setValue(75.5)
        assert bar_indicator.value == 75.5

    def test_set_value_int(self, bar_indicator):
        bar_indicator.setValue(25)
        assert bar_indicator.value == 25


class TestBarIndicatorMinMax:
    def test_set_minimum(self, bar_indicator):
        bar_indicator.setMinimum(10)
        assert bar_indicator.minimum == 10

    def test_set_maximum(self, bar_indicator):
        bar_indicator.setMaximum(200)
        assert bar_indicator.maximum == 200

    def test_set_minimum_changes_range(self, bar_indicator):
        bar_indicator.setMinimum(50)
        bar_indicator.setMaximum(150)
        bar_indicator.setValue(100)
        assert bar_indicator.value == 100

    def test_value_not_reclamped_when_max_decreases(self, bar_indicator):
        bar_indicator.setValue(50)
        bar_indicator.setMaximum(25)
        assert bar_indicator.value == 50


class TestBarIndicatorOrientation:
    def test_set_vertical_orientation(self, bar_indicator):
        from qtpy.QtCore import Qt

        bar_indicator.orientation = Qt.Vertical
        assert bar_indicator.orientation == Qt.Vertical

    def test_horizontal_orientation_stays_horizontal(self, bar_indicator):
        from qtpy.QtCore import Qt

        bar_indicator.orientation = Qt.Horizontal
        assert bar_indicator.orientation == Qt.Horizontal


class TestBarIndicatorText:
    def test_text_default_format(self, bar_indicator):
        text = bar_indicator.text()
        assert "100.00" in text

    def test_text_with_prefix(self, bar_indicator):
        bar_indicator.prefix = "Value: "
        text = bar_indicator.text()
        assert "Value:" in text

    def test_text_with_sufix(self, bar_indicator):
        bar_indicator.sufix = "%"
        text = bar_indicator.text()
        assert "%" in text

    def test_text_custom_format(self, bar_indicator):
        bar_indicator.format = ".0f"
        bar_indicator.setValue(75)
        text = bar_indicator.text()
        assert "75" in text
        assert "." not in text

    def test_text_with_prefix_and_sufix(self, bar_indicator):
        bar_indicator.prefix = "["
        bar_indicator.sufix = "]"
        bar_indicator.format = ".0f"
        bar_indicator.setValue(42)
        text = bar_indicator.text()
        assert "[ 42 ]" in text


class TestBarIndicatorGradient:
    def test_bar_gradient_default(self, bar_indicator):
        gradient = bar_indicator.barGradient
        assert isinstance(gradient, list)
        assert len(gradient) == 3

    def test_bar_gradient_sets_color_stops(self, bar_indicator):
        from qtpy.QtCore import Property

        prop = bar_indicator.__class__.barGradient
        assert isinstance(prop, Property)


class TestBarIndicatorColors:
    def test_text_color_default(self, bar_indicator):
        color = bar_indicator.textColor
        assert color.red() == 0
        assert color.green() == 0
        assert color.blue() == 0

    def test_set_text_color(self, bar_indicator):
        from qtpy.QtGui import QColor

        bar_indicator.textColor = QColor(255, 0, 0)
        color = bar_indicator.textColor
        assert color.red() == 255

    def test_border_color_default(self, bar_indicator):
        from qtpy.QtCore import Qt

        border = bar_indicator.borderColor
        assert border == Qt.gray

    def test_set_border_color(self, bar_indicator):
        from qtpy.QtGui import QColor

        bar_indicator.borderColor = QColor(0, 255, 0)
        color = bar_indicator.borderColor
        assert color.green() == 255


class TestBarIndicatorSizeHints:
    def test_minimum_size_hint(self, bar_indicator):
        hint = bar_indicator.minimumSizeHint()
        assert hint.width() >= 30
        assert hint.height() >= 30

    def test_resize_event(self, bar_indicator):
        bar_indicator.resize(400, 50)
        assert bar_indicator.width() == 400
        assert bar_indicator.height() == 50


class TestBarIndicatorProperties:
    def test_value_property(self, bar_indicator):
        from qtpy.QtCore import Property

        prop = bar_indicator.__class__.value
        assert isinstance(prop, Property)
        bar_indicator.value = 75
        assert bar_indicator.value == 75

    def test_minimum_property(self, bar_indicator):
        from qtpy.QtCore import Property

        prop = bar_indicator.__class__.minimum
        assert isinstance(prop, Property)
        bar_indicator.minimum = 10
        assert bar_indicator.minimum == 10

    def test_maximum_property(self, bar_indicator):
        from qtpy.QtCore import Property

        prop = bar_indicator.__class__.maximum
        assert isinstance(prop, Property)
        bar_indicator.maximum = 200
        assert bar_indicator.maximum == 200

    def test_format_property(self, bar_indicator):
        from qtpy.QtCore import Property

        prop = bar_indicator.__class__.format
        assert isinstance(prop, Property)
        bar_indicator.format = ".1f"
        assert bar_indicator.format == ".1f"

    def test_prefix_property(self, bar_indicator):
        from qtpy.QtCore import Property

        prop = bar_indicator.__class__.prefix
        assert isinstance(prop, Property)
        bar_indicator.prefix = "X: "
        assert bar_indicator.prefix == "X: "

    def test_sufix_property(self, bar_indicator):
        from qtpy.QtCore import Property

        prop = bar_indicator.__class__.sufix
        assert isinstance(prop, Property)
        bar_indicator.sufix = " mm"
        assert bar_indicator.sufix == " mm"


class TestBarIndicatorFocusPolicy:
    def test_no_focus_policy(self, bar_indicator):
        from qtpy.QtCore import Qt

        policy = bar_indicator.focusPolicy()
        assert policy == Qt.NoFocus
