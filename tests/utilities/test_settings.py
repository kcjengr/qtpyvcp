import pytest
from qtpy.QtCore import QObject
from qtpyvcp import SETTINGS
from qtpyvcp.utilities.settings import (
    Setting, getSetting, setSetting, addSetting, connectSetting, setting
)


@pytest.fixture(autouse=True)
def clean_settings():
    original = dict(SETTINGS)
    SETTINGS.clear()
    yield
    SETTINGS.clear()
    SETTINGS.update(original)


class TestGetSetting:
    def test_returns_none_for_missing_key(self):
        assert getSetting('nonexistent') is None

    def test_returns_default_for_missing_key(self):
        result = getSetting('nonexistent', 'fallback')
        assert result == 'fallback'

    def test_returns_existing_setting(self):
        addSetting('my.setting', default_value=42)
        result = getSetting('my.setting')
        assert isinstance(result, Setting)
        assert result.value == 42

    def test_default_not_used_when_key_exists(self):
        addSetting('existing.setting', default_value=True)
        result = getSetting('existing.setting', 'fallback')
        assert result is not None
        assert result.value is True


class TestSetSetting:
    def test_raises_for_missing_key(self):
        with pytest.raises(ValueError, match="does not exist"):
            setSetting('nonexistent', 42)

    def test_sets_int_value(self):
        addSetting('my.setting', default_value=0)
        setSetting('my.setting', 10)
        assert getSetting('my.setting').value == 10

    def test_sets_string_value(self):
        addSetting('my.setting', default_value='hello')
        setSetting('my.setting', 'world')
        assert getSetting('my.setting').value == 'world'

    def test_sets_bool_value(self):
        addSetting('my.setting', default_value=False)
        setSetting('my.setting', True)
        assert getSetting('my.setting').value is True


class TestAddSetting:
    def test_creates_setting_in_settings_dict(self):
        addSetting('new.setting')
        assert 'new.setting' in SETTINGS

    def test_creates_setting_with_default_value(self):
        addSetting('new.setting', default_value=99)
        assert getSetting('new.setting').value == 99

    def test_creates_setting_with_persistent_false(self):
        addSetting('new.setting', persistent=False)
        assert SETTINGS['new.setting'].persistent is False

    def test_creates_setting_with_description(self):
        addSetting('new.setting', description='A test setting')
        assert SETTINGS['new.setting'].__doc__ == 'A test setting'


class TestSettingInit:
    def test_default_values(self):
        s = Setting()
        assert s.value is False
        assert s.default_value is False
        assert s.persistent is True

    def test_custom_default_value(self):
        s = Setting(default_value=42)
        assert s.value == 42
        assert s.default_value == 42

    def test_explicit_value_type(self):
        s = Setting(default_value=0, value_type='int')
        assert s.value_type is int

    def test_default_value_type_is_str_when_none_provided(self):
        s = Setting()
        assert s.value_type is bool

    def test_options_sets_enum_range(self):
        s = Setting(options=['red', 'green', 'blue'])
        assert s.min_value == 0
        assert s.max_value == 2
        assert s.enum_options == ['red', 'green', 'blue']

    def test_explicit_min_max_preserved_with_options(self):
        s = Setting(default_value=5, min_value=0, max_value=100)
        assert s.min_value == 0
        assert s.max_value == 100


class TestSettingGetValue:
    def test_get_returns_value_when_no_fget(self):
        s = Setting(default_value=42)
        assert s.getValue() == 42

    def test_get_uses_fget_when_provided(self):
        def fget(instance, setting_obj, *args, **kwargs):
            return 'computed'
        s = Setting(fget=fget)
        assert s.getValue() == 'computed'

    def test_get_passes_args_to_fget(self):
        def fget(instance, setting_obj, multiplier=1):
            return setting_obj.value * multiplier
        s = Setting(default_value=5, fget=fget)
        assert s.getValue(multiplier=3) == 15


class TestSettingSetValue:
    def test_sets_int_value(self):
        s = Setting(default_value=0)
        s.setValue(42)
        assert s.value == 42

    def test_coerces_string_to_int(self):
        s = Setting(default_value=0, value_type='int')
        s.setValue('10')
        assert s.value == 10

    def test_coerces_string_to_float(self):
        s = Setting(default_value=0.0, value_type='float')
        s.setValue('3.14')
        assert abs(s.value - 3.14) < 0.01

    def test_signal_emitted_on_set(self):
        s = Setting(default_value=0)
        received = []
        s.notify(lambda val: received.append(val), update=False)
        s.setValue(42)
        assert received == [42]

    def test_fset_used_when_provided(self):
        call_log = []
        def fset(instance, setting_obj, value):
            call_log.append(value)
        s = Setting(fset=fset)
        s.setValue(99)
        assert call_log == [99]


class TestSettingClampValue:
    def test_clamps_above_max(self):
        s = Setting(default_value=5, min_value=0, max_value=10)
        assert s.clampValue(15) == 10

    def test_clamps_below_min(self):
        s = Setting(default_value=5, min_value=0, max_value=10)
        assert s.clampValue(-3) == 0

    def test_no_clamp_within_range(self):
        s = Setting(default_value=5, min_value=0, max_value=10)
        assert s.clampValue(7) == 7

    def test_no_clamp_when_max_none(self):
        s = Setting(default_value=5, min_value=0)
        assert s.clampValue(999) == 999

    def test_no_clamp_when_min_none(self):
        s = Setting(default_value=5, max_value=100)
        assert s.clampValue(-999) == -999

    def test_clamp_at_exact_max(self):
        s = Setting(default_value=5, min_value=0, max_value=10)
        assert s.clampValue(10) == 10

    def test_clamp_at_exact_min(self):
        s = Setting(default_value=5, min_value=0, max_value=10)
        assert s.clampValue(0) == 0


class TestSettingNormalizeValue:
    def test_normalizes_type_conversion(self):
        s = Setting(default_value=0, value_type='int')
        result = s.normalizeValue('42')
        assert result == 42

    def test_normalizes_invalid_value_returns_current(self):
        s = Setting(default_value=5, value_type='int')
        result = s.normalizeValue('not_a_number')
        assert result == 5

    def test_normalizes_clamps_to_range(self):
        s = Setting(default_value=5, min_value=0, max_value=10, value_type='int')
        result = s.normalizeValue(99)
        assert result == 10

    def test_no_conversion_needed_same_type(self):
        s = Setting(default_value=42, value_type='int')
        result = s.normalizeValue(42)
        assert result == 42


class TestSettingResetValue:
    def test_resets_to_default(self):
        s = Setting(default_value=10)
        s.setValue(99)
        s.resetValue()
        assert s.value == 10

    def test_reset_when_never_changed(self):
        s = Setting(default_value=42)
        s.resetValue()
        assert s.value == 42

    def test_freset_used_when_provided(self):
        call_log = []
        def freset(instance, setting_obj, value):
            call_log.append(value)
        s = Setting(default_value=5, freset=freset)
        s.resetValue()
        assert call_log == [5]


class TestSettingNotify:
    def test_connects_slot_to_signal(self):
        s = Setting(default_value=0)
        received = []
        s.notify(lambda val: received.append(val), update=False)
        s.setValue(1)
        assert received == [1]

    def test_initial_call_when_update_true(self):
        s = Setting(default_value=42)
        received = []
        s.notify(lambda val: received.append(val), update=True)
        assert 42 in received

    def test_no_initial_call_when_update_false(self):
        s = Setting(default_value=42)
        received = []
        s.notify(lambda val: received.append(val), update=False)
        assert len(received) == 0

    def test_slot_exception_ignored(self):
        s = Setting(default_value=42)
        def bad_slot(val):
            raise RuntimeError('oops')
        s.notify(bad_slot, update=True)


class TestSettingDescriptorProtocol:
    def test_getter_returns_setting_instance(self):
        class MyClass(QObject):
            my_setting = Setting(default_value=10)

        obj = MyClass()
        result = obj.my_setting
        assert isinstance(result, Setting)

    def test_setter_delegates_to_setValue(self):
        class MyClass(QObject):
            my_setting = Setting(default_value=0)

        obj = MyClass()
        obj.my_setting = 99
        assert obj.my_setting.value == 99


class TestSettingCall:
    def test_call_delegates_to_getValue(self):
        s = Setting(default_value=42)
        assert s() == 42

    def test_call_with_args_delegates_to_getValue(self):
        def fget(instance, setting_obj, multiplier=1):
            return setting_obj.value * multiplier
        s = Setting(default_value=5, fget=fget)
        assert s(multiplier=3) == 15


class TestSettingStr:
    def test_str_returns_string_of_value(self):
        s = Setting(default_value=42)
        assert str(s) == '42'

    def test_str_with_string_value(self):
        s = Setting(default_value='hello')
        assert str(s) == 'hello'

    def test_str_with_bool_value(self):
        s = Setting(default_value=True)
        assert str(s) == 'True'


class TestSettingDecoratorMethods:
    def test_getter_sets_fget(self):
        def my_getter(instance, setting_obj, *args, **kwargs):
            return 'custom'
        s = Setting().getter(my_getter)
        assert s.fget is not None

    def test_setter_sets_fset(self):
        def my_setter(instance, setting_obj, value):
            pass
        s = Setting().setter(my_setter)
        assert s.fset is not None

    def test_resetter_sets_freset(self):
        def my_resetter(instance, setting_obj, value):
            pass
        s = Setting().resetter(my_resetter)
        assert s.freset is not None


class TestSettingDecorator:
    def test_decorator_registers_in_settings(self):
        @setting('my.decorated.setting', default_value=42)
        def my_func(setting_obj):
            return setting_obj.value

        assert 'my.decorated.setting' in SETTINGS

    def test_decorator_uses_function_docstring(self):
        @setting('doc.test')
        def my_setting(setting_obj):
            """This is the description."""
            return setting_obj.value

        assert SETTINGS['doc.test'].__doc__ == 'This is the description.'

    def test_decorator_creates_setting_with_default(self):
        @setting('value.test', default_value=99)
        def my_func(setting_obj):
            return setting_obj.value

        assert SETTINGS['value.test'].value == 99


class TestConnectSetting:
    def test_connects_slot_to_existing_setting(self):
        addSetting('existing.setting', default_value=0)
        received = []
        connectSetting('existing.setting', lambda val: received.append(val))
        setSetting('existing.setting', 42)
        assert 42 in received

    def test_raises_for_missing_key(self):
        with pytest.raises(ValueError, match="does not exists"):
            connectSetting('nonexistent', lambda x: x, silent_fail=False)

    def test_silent_fail_skips_error(self):
        result = connectSetting('nonexistent', lambda x: x, silent_fail=True)
        assert result is None

    def test_update_initial_value_on_connect(self):
        addSetting('existing.setting', default_value=77)
        received = []
        connectSetting('existing.setting', lambda val: received.append(val))
        assert 77 in received


class TestSettingTypeCoercion:
    def test_string_coerced_to_int(self):
        s = Setting(default_value=0, value_type='int')
        s.setValue('5')
        assert s.value == 5

    def test_float_coerced_to_int_clamped(self):
        s = Setting(default_value=0, min_value=0, max_value=10, value_type='int')
        s.setValue(15.7)
        assert s.value == 10

    def test_int_passed_through_as_is(self):
        s = Setting(default_value=0, value_type='int')
        s.setValue(42)
        assert s.value == 42

    def test_string_coerced_to_float(self):
        s = Setting(default_value=0.0, value_type='float')
        s.setValue('3.14')
        assert abs(s.value - 3.14) < 0.01
