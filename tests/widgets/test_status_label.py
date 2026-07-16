import pytest


class TestStatusLabelInit:
    def test_default_text(self, status_label):
        assert status_label.text() == "Not Set"

    def test_format_default(self, status_label):
        assert status_label.format == "{}"

    def test_expression_default(self, status_label):
        assert status_label.expression == "val"


class TestStatusLabelSetValue:
    def test_set_string_value(self, status_label):
        status_label.setValue("hello")
        assert status_label.text() == "hello"

    def test_set_int_value(self, status_label):
        status_label.setValue(42)
        assert status_label.text() == "42"

    def test_set_float_value(self, status_label):
        status_label.setValue(3.14)
        assert status_label.text() == "3.14"

    def test_set_bool_true(self, status_label):
        status_label.setValue(True)
        assert status_label.text() == "True"

    def test_set_bool_false(self, status_label):
        status_label.setValue(False)
        assert status_label.text() == "False"


class TestStatusLabelFormat:
    def test_format_empty_braces(self, status_label):
        status_label.format = "{}"
        status_label.setValue(100)
        assert status_label.text() == "100"

    def test_format_with_padding(self, status_label):
        status_label.format = "{:>6}"
        status_label.setValue(42)
        assert status_label.text() == "    42"

    def test_format_decimal_places(self, status_label):
        status_label.format = "{:.1f}"
        status_label.setValue(3.14159)
        assert status_label.text() == "3.1"

    def test_format_string_with_prefix(self, status_label):
        status_label.format = "Value: {}"
        status_label.setValue(75)
        assert status_label.text() == "Value: 75"

    def test_format_hexadecimal(self, status_label):
        status_label.format = "{:#x}"
        status_label.setValue(255)
        assert status_label.text() == "0xff"


class TestStatusLabelExpression:
    def test_expression_default_val(self, status_label):
        status_label.setValue(42)
        assert status_label.text() == "42"

    def test_expression_double_value(self, status_label):
        status_label.expression = "val * 2"
        status_label.setValue(21)
        assert status_label.text() == "42"

    def test_expression_add_constant(self, status_label):
        status_label.expression = "val + 10"
        status_label.setValue(5)
        assert status_label.text() == "15"

    def test_expression_multiply(self, status_label):
        status_label.expression = "val * 1.5"
        status_label.setValue(10)
        assert status_label.text() == "15.0"

    def test_expression_with_format(self, status_label):
        status_label.expression = "val * 2"
        status_label.format = "{:.1f}"
        status_label.setValue(7.5)
        assert status_label.text() == "15.0"

    def test_invalid_expression_logs_error(self, caplog, status_label):
        with caplog.at_level("ERROR"):
            status_label.expression = "invalid_python_syntax_here!!!"

        assert any("Python expression is not valid" in record.message for record in caplog.records)

    def test_invalid_expression_preserves_default_lambda(self, status_label):
        status_label.expression = "val * 10"
        status_label.setValue(5)
        assert status_label.text() == "50"
        status_label.expression = "syntax_error!!!"
        status_label.setValue(7)
        text = status_label.text()
        assert text == "70"


class TestStatusLabelQtProperties:
    def test_format_property(self, status_label):
        from qtpy.QtCore import Property

        prop = status_label.__class__.format
        assert isinstance(prop, Property)
        status_label.format = "{}"
        assert status_label.format == "{}"

    def test_expression_property(self, status_label):
        from qtpy.QtCore import Property

        prop = status_label.__class__.expression
        assert isinstance(prop, Property)
        status_label.expression = "val"
        assert status_label.expression == "val"


class TestStatusLabelRuleProperties:
    def test_default_rule_property(self, status_label):
        assert status_label.DEFAULT_RULE_PROPERTY == "Text"

    def test_rule_properties_contains_text(self, status_label):
        assert "Text" in status_label.RULE_PROPERTIES
        assert status_label.RULE_PROPERTIES["Text"] == ["setText", str]


class TestStatusLabelInheritance:
    def test_is_qlabel(self, status_label):
        from qtpy.QtWidgets import QLabel

        assert isinstance(status_label, QLabel)

    def test_focus_policy_no_focus(self, status_label):
        from qtpy.QtCore import Qt

        policy = status_label.focusPolicy()
        assert policy == Qt.NoFocus


class TestStatusLabelEdgeCases:
    def test_set_none_value(self, status_label):
        status_label.setValue(None)
        text = status_label.text()
        assert "None" in text

    def test_set_empty_string(self, status_label):
        status_label.setValue("")
        assert status_label.text() == ""

    def test_set_negative_int(self, status_label):
        status_label.setValue(-10)
        assert status_label.text() == "-10"

    def test_set_negative_float(self, status_label):
        status_label.setValue(-3.14)
        assert status_label.text() == "-3.14"

    def test_set_large_number(self, status_label):
        status_label.setValue(999999999)
        assert status_label.text() == "999999999"

    def test_expression_abs_value(self, status_label):
        status_label.expression = "abs(val)"
        status_label.setValue(-50)
        assert status_label.text() == "50"

    def test_expression_round_value(self, status_label):
        status_label.expression = "round(val, 1)"
        status_label.setValue(3.14159)
        assert status_label.text() == "3.1"
