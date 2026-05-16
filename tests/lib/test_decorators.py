import inspect
import logging
from unittest.mock import patch, MagicMock

import pytest


class TestDeprecatedFunction:
    def test_function_called_returns_result(self):
        from qtpyvcp.lib.decorators import deprecated

        @deprecated(reason='use new_func', replaced_by='new_func')
        def old_func():
            return 42

        result = old_func()
        assert result == 42

    def test_function_preserves_args_and_kwargs(self):
        from qtpyvcp.lib.decorators import deprecated

        @deprecated(reason='use new_add', replaced_by='new_add')
        def add(a, b):
            return a + b

        assert add(3, 4) == 7
        assert add(10, 20) == 30

    def test_function_warning_logged(self, caplog):
        from qtpyvcp.lib.decorators import deprecated

        @deprecated(reason='use new_func', replaced_by='new_func')
        def old_func():
            return 'ok'

        with caplog.at_level(logging.WARNING):
            old_func()

        assert len(caplog.records) > 0
        assert 'Deprecation Warning' in caplog.records[0].message
        assert 'old_func' in caplog.records[0].message
        assert 'use new_func' in caplog.records[0].message
        assert 'new_func' in caplog.records[0].message

    def test_function_warning_message_format(self, caplog):
        from qtpyvcp.lib.decorators import deprecated

        @deprecated(reason='no longer needed', replaced_by='replacement')
        def my_old_function():
            return True

        with caplog.at_level(logging.WARNING):
            my_old_function()

        assert 'my_old_function' in caplog.records[0].message

    def test_function_default_params(self, caplog):
        from qtpyvcp.lib.decorators import deprecated

        @deprecated()
        def legacy_func():
            return 1

        with caplog.at_level(logging.WARNING):
            legacy_func()

        assert 'Not Specified' in caplog.records[0].message

    def test_function_with_exception_still_raises(self):
        from qtpyvcp.lib.decorators import deprecated

        @deprecated(reason='use safe_func')
        def bad_func():
            raise ValueError('oops')

        with pytest.raises(ValueError, match='oops'):
            bad_func()


class TestDeprecatedClass:
    def test_non_widget_class_returns_unchanged(self):
        from qtpyvcp.lib.decorators import deprecated

        @deprecated(reason='old design', replaced_by='NewWidget')
        class OldClass:
            pass

        assert inspect.isclass(OldClass)
        assert OldClass.__name__ == 'OldClass'
        instance = OldClass()
        assert isinstance(instance, OldClass)

    def test_non_widget_class_no_warning_logged(self, caplog):
        from qtpyvcp.lib.decorators import deprecated

        with caplog.at_level(logging.WARNING):
            @deprecated(reason='use NewFoo', replaced_by='NewFoo')
            class OldFoo:
                pass

        assert len(caplog.records) == 0

    def test_non_widget_class_with_attributes(self):
        from qtpyvcp.lib.decorators import deprecated

        @deprecated(reason='old', replaced_by='new')
        class DataHolder:
            value = 100

            def get_value(self):
                return self.value

        assert DataHolder.value == 100
        obj = DataHolder()
        assert obj.get_value() == 100


class TestDeprecatedWidget:
    def test_widget_class_warning_logged(self, qtbot, caplog):
        from qtpyvcp.lib.decorators import deprecated
        from qtpy.QtWidgets import QWidget

        with caplog.at_level(logging.WARNING):
            @deprecated(reason='use ModernBtn', replaced_by='ModernBtn')
            class OldWidget(QWidget):
                pass

        assert len(caplog.records) > 0
        assert 'Deprecation Warning' in caplog.records[0].message
        assert 'OldWidget' in caplog.records[0].message
        assert 'use ModernBtn' in caplog.records[0].message
        assert 'ModernBtn' in caplog.records[0].message

    def test_widget_class_returns_unchanged(self, qtbot):
        from qtpyvcp.lib.decorators import deprecated
        from qtpy.QtWidgets import QWidget

        @deprecated(reason='use NewWidget', replaced_by='NewWidget')
        class OldQtWidget(QWidget):
            pass

        assert inspect.isclass(OldQtWidget)
        assert issubclass(OldQtWidget, QWidget)
        instance = OldQtWidget()
        assert isinstance(instance, QWidget)

    def test_widget_class_message_contains_module(self, qtbot, caplog):
        from qtpyvcp.lib.decorators import deprecated
        from qtpy.QtWidgets import QWidget

        with caplog.at_level(logging.WARNING):
            @deprecated(reason='migrate now', replaced_by='FutureWidget')
            class TestWidget(QWidget):
                pass

        assert 'test_decorators' in caplog.records[0].message


class TestDeprecatedPassthrough:
    def test_non_decorated_object_returns_unchanged(self):
        from qtpyvcp.lib.decorators import deprecated

        plain_value = 42
        result = deprecated()(plain_value)
        assert result == 42

    def test_integer_passthrough(self):
        from qtpyvcp.lib.decorators import deprecated

        result = deprecated()(100)
        assert result == 100

    def test_string_passthrough(self):
        from qtpyvcp.lib.decorators import deprecated

        result = deprecated()('hello')
        assert result == 'hello'

    def test_list_passthrough(self):
        from qtpyvcp.lib.decorators import deprecated

        my_list = [1, 2, 3]
        result = deprecated()(my_list)
        assert result == [1, 2, 3]

    def test_method_passthrough_returns_bound_method(self):
        from qtpyvcp.lib.decorators import deprecated

        class MyClass:
            def method(self):
                return 'method result'

        obj = MyClass()
        result = deprecated()(obj.method)
        assert callable(result)
        assert result() == 'method result'


class TestDeprecatedDecoratorIdentity:
    def test_decorator_can_be_called_without_parens_on_function(self):
        from qtpyvcp.lib.decorators import deprecated

        @deprecated(reason='old', replaced_by='new')
        def func():
            return True

        assert callable(func)
        assert func() is True

    def test_decorator_with_custom_reason_and_replacement(self, caplog):
        from qtpyvcp.lib.decorators import deprecated
        from qtpyvcp.utilities.logger import getLogger

        log = getLogger('qtpyvcp.lib.decorators')
        log.setLevel(logging.WARNING)

        @deprecated(reason='security vulnerability', replaced_by='secure_api')
        def insecure_func():
            return 'data'

        with caplog.at_level(logging.WARNING):
            insecure_func()

        assert len(caplog.records) > 0
        assert 'security vulnerability' in caplog.records[0].message
        assert 'secure_api' in caplog.records[0].message

    def test_function_wrapper_is_callable(self):
        from qtpyvcp.lib.decorators import deprecated

        @deprecated(reason='old', replaced_by='new')
        def wrapped_func(x, y=10):
            return x + y

        assert callable(wrapped_func)
        assert wrapped_func(5) == 15
        assert wrapped_func(5, y=20) == 25


class TestDeprecatedWithMockedLogger:
    def test_widget_deprecation_calls_log_warning(self):
        from qtpyvcp.lib.decorators import deprecated
        from qtpy.QtWidgets import QWidget

        mock_logger = MagicMock()

        with patch('qtpyvcp.lib.decorators.LOG', mock_logger):
            @deprecated(reason='use ModernBtn', replaced_by='ModernBtn')
            class OldButton(QWidget):
                pass

        assert mock_logger.warning.called
        warning_msg = mock_logger.warning.call_args[0][0]
        assert 'OldButton' in warning_msg
        assert 'use ModernBtn' in warning_msg

    def test_function_deprecation_calls_log_warn(self):
        from qtpyvcp.lib.decorators import deprecated
        from unittest.mock import MagicMock

        mock_logger = MagicMock()

        with patch('qtpyvcp.lib.decorators.LOG', mock_logger):
            @deprecated(reason='use new_adder', replaced_by='new_adder')
            def old_adder(a, b):
                return a + b

            result = old_adder(2, 3)

        assert result == 5
        assert mock_logger.warning.called
        warning_msg = mock_logger.warning.call_args[0][0]
        assert 'old_adder' in warning_msg
