import pytest


class TestEvalLineEditInit:
    def test_default_orig_value(self, eval_line_edit):
        assert eval_line_edit.orig_value == ""

    def test_inherits_from_qlineedit(self, eval_line_edit):
        from qtpy.QtWidgets import QLineEdit

        assert isinstance(eval_line_edit, QLineEdit)


class TestEvalLineEditFocusIn:
    def test_focus_in_stores_text(self, eval_line_edit):
        eval_line_edit.setText("42.5")
        eval_line_edit.focusInEvent(None)
        assert eval_line_edit.orig_value == "42.5"

    def test_focus_in_stores_empty_text(self, eval_line_edit):
        eval_line_edit.setText("")
        eval_line_edit.focusInEvent(None)
        assert eval_line_edit.orig_value == ""

    def test_focus_in_stores_negative_text(self, eval_line_edit):
        eval_line_edit.setText("-10")
        eval_line_edit.focusInEvent(None)
        assert eval_line_edit.orig_value == "-10"


class TestEvalLineEditExpressionToggle:
    def test_single_dash_toggles_sign_positive(self, eval_line_edit):
        eval_line_edit.setText("42")
        eval_line_edit.focusInEvent(None)
        eval_line_edit.setText("-")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "-42"

    def test_single_dash_toggles_sign_negative(self, eval_line_edit):
        eval_line_edit.setText("-10")
        eval_line_edit.focusInEvent(None)
        eval_line_edit.setText("-")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "10"

    def test_single_dash_zero(self, eval_line_edit):
        eval_line_edit.setText("0")
        eval_line_edit.focusInEvent(None)
        eval_line_edit.setText("-")
        eval_line_edit.evaluate_()
        text = eval_line_edit.text()
        assert text == "-0" or text == "0"


class TestEvalLineEditOperatorPrefix:
    def test_plus_prefix_evaluates(self, eval_line_edit):
        eval_line_edit.setText("10")
        eval_line_edit.focusInEvent(None)
        eval_line_edit.setText("+5")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "15"

    def test_multiply_prefix_evaluates(self, eval_line_edit):
        eval_line_edit.setText("10")
        eval_line_edit.focusInEvent(None)
        eval_line_edit.setText("*2")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "20"

    def test_divide_prefix_evaluates(self, eval_line_edit):
        eval_line_edit.setText("100")
        eval_line_edit.focusInEvent(None)
        eval_line_edit.setText("/2")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "50.0"

    def test_minus_equals_prefix_evaluates(self, eval_line_edit):
        eval_line_edit.setText("50")
        eval_line_edit.focusInEvent(None)
        eval_line_edit.setText("-=10")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "40"

    def test_plus_equals_prefix_evaluates(self, eval_line_edit):
        eval_line_edit.setText("25")
        eval_line_edit.focusInEvent(None)
        eval_line_edit.setText("+=15")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "40"


class TestEvalLineEditExpressionEvaluation:
    def test_simple_addition(self, eval_line_edit):
        eval_line_edit.setText("10 + 5")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "15"

    def test_simple_subtraction(self, eval_line_edit):
        eval_line_edit.setText("20 - 8")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "12"

    def test_simple_multiplication(self, eval_line_edit):
        eval_line_edit.setText("6 * 7")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "42"

    def test_simple_division(self, eval_line_edit):
        eval_line_edit.setText("10 / 4")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "2.5"

    def test_float_division(self, eval_line_edit):
        eval_line_edit.setText("1 / 2")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "0.5"

    def test_parenthesized_expression(self, eval_line_edit):
        eval_line_edit.setText("(10 + 5) * 2")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "30"

    def test_negative_number(self, eval_line_edit):
        eval_line_edit.setText("-5")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "-5"

    def test_complex_expression(self, eval_line_edit):
        eval_line_edit.setText("-(10+5)*(1.0/2.0)")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "-7.5"

    def test_power_operator(self, eval_line_edit):
        eval_line_edit.setText("2 ** 8")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "256"

    def test_modulo_operator(self, eval_line_edit):
        eval_line_edit.setText("17 % 5")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "2"


class TestEvalLineEditErrorHandling:
    def test_invalid_expression_logs_error(self, eval_line_edit, caplog):
        import logging

        with caplog.at_level(logging.ERROR):
            eval_line_edit.setText("not valid python @@@")
            eval_line_edit.evaluate_()

        assert any("Error evaluating numeric expression" in record.message for record in caplog.records)

    def test_invalid_expression_preserves_text(self, eval_line_edit):
        eval_line_edit.setText("invalid!!!")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "invalid!!!"


class TestEvalLineEditEdgeCases:
    def test_just_number(self, eval_line_edit):
        eval_line_edit.setText("42")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "42"

    def test_decimal_number(self, eval_line_edit):
        eval_line_edit.setText("3.14159")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "3.14159"

    def test_scientific_notation(self, eval_line_edit):
        eval_line_edit.setText("1e3")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "1000.0"

    def test_whitespace_around_expression(self, eval_line_edit):
        eval_line_edit.setText("  10 + 5  ")
        eval_line_edit.evaluate_()
        assert eval_line_edit.text() == "15"

    def test_single_operator_plus(self, eval_line_edit):
        eval_line_edit.setText("+")
        eval_line_edit.evaluate_()
        assert "+" in eval_line_edit.text()

    def test_empty_text(self, eval_line_edit):
        eval_line_edit.setText("")
        eval_line_edit.evaluate_()


class TestEvalLineEditReturnPressed:
    def test_return_pressed_triggers_evaluation(self, eval_line_edit, qtbot):
        from qtpy.QtCore import Qt

        eval_line_edit.setText("10")
        qtbot.addWidget(eval_line_edit)
        qtbot.keyClick(eval_line_edit, Qt.Key_Return)
        assert eval_line_edit.text() == "10"

    def test_enter_key_triggers_evaluation(self, eval_line_edit, qtbot):
        from qtpy.QtCore import Qt

        eval_line_edit.setText("2 + 3")
        qtbot.addWidget(eval_line_edit)
        qtbot.keyClick(eval_line_edit, Qt.Key_Return)
        assert eval_line_edit.text() == "5"
