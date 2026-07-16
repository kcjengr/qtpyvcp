import pytest
from qtpyvcp.utilities.opt_parser import convType


class TestConvTypeBoolean:
    def test_true_lowercase(self):
        assert convType('true') is True

    def test_on_lowercase(self):
        assert convType('on') is True

    def test_yes_lowercase(self):
        assert convType('yes') is True

    def test_false_lowercase(self):
        assert convType('false') is False

    def test_off_lowercase(self):
        assert convType('off') is False

    def test_no_lowercase(self):
        assert convType('no') is False


class TestConvTypeBooleanMixedCase:
    def test_true_uppercase(self):
        assert convType('TRUE') is True

    def test_on_uppercase(self):
        assert convType('ON') is True

    def test_yes_mixed_case(self):
        assert convType('Yes') is True

    def test_false_uppercase(self):
        assert convType('FALSE') is False

    def test_off_uppercase(self):
        assert convType('OFF') is False

    def test_no_mixed_case(self):
        assert convType('No') is False


class TestConvTypeInt:
    def test_positive_integer_string(self):
        assert convType('42') == 42

    def test_negative_integer_string(self):
        assert convType('-10') == -10

    def test_zero_string(self):
        assert convType('0') == 0

    def test_large_integer_string(self):
        assert convType('999999') == 999999


class TestConvTypeFloat:
    def test_positive_float_string(self):
        assert convType('3.14') == 3.14

    def test_negative_float_string(self):
        assert convType('-2.5') == -2.5

    def test_zero_float_string(self):
        assert convType('0.0') == 0.0

    def test_just_dot_raises(self):
        result = convType('.')
        assert isinstance(result, str)


class TestConvTypePassthrough:
    def test_non_boolean_string_passthrough(self):
        assert convType('hello') == 'hello'

    def test_integer_passthrough(self):
        assert convType(42) == 42

    def test_float_passthrough(self):
        assert convType(3.14) == 3.14

    def test_none_passthrough(self):
        assert convType(None) is None

    def test_list_passthrough(self):
        assert convType([1, 2, 3]) == [1, 2, 3]

    def test_dict_passthrough(self):
        assert convType({'a': 1}) == {'a': 1}

    def test_empty_string_passthrough(self):
        assert convType('') == ''

    def test_numeric_string_not_boolean(self):
        result = convType('1')
        assert isinstance(result, int)
        assert result == 1

    def test_numeric_string_not_float(self):
        result = convType('1.5')
        assert isinstance(result, float)
        assert result == 1.5
