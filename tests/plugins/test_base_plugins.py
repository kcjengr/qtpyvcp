import pytest
from qtpyvcp.plugins.base_plugins import Plugin, DataPlugin, DataChannel, isDataChan


class TestPlugin:
    def test_initial_state(self):
        plugin = Plugin()
        assert plugin._initialized is False
        assert plugin._postGuiInitialized is False

    def test_initialise_sets_flag(self):
        plugin = Plugin()
        plugin.initialise()
        assert plugin._initialized is True

    def test_post_gui_initialise_sets_flag(self):
        plugin = Plugin()
        plugin.postGuiInitialise(main_window=None)
        assert plugin._postGuiInitialized is True

    def test_log_property_creates_logger(self):
        plugin = Plugin()
        logger = plugin.log
        assert logger is not None
        # Second access returns same instance (cached)
        assert plugin.log is logger

    def test_terminate_is_noop_by_default(self):
        plugin = Plugin()
        # Should not raise
        plugin.terminate()


class TestIsDataChan:
    def test_returns_true_for_datachannel(self):
        dc = DataChannel(data=42)
        assert isDataChan(dc) is True

    def test_returns_false_for_regular_object(self):
        assert isDataChan("not a channel") is False
        assert isDataChan(123) is False


class TestPluginSubclass:
    def test_subclass_can_override_initialise(self):
        class MyPlugin(Plugin):
            def initialise(self):
                self.custom_flag = True
                super(MyPlugin, self).initialise()

        plugin = MyPlugin()
        plugin.initialise()
        assert plugin._initialized is True
        assert plugin.custom_flag is True

    def test_subclass_can_override_terminate(self):
        class MyPlugin(Plugin):
            def terminate(self):
                self.terminated = True

        plugin = MyPlugin()
        plugin.terminate()
        assert plugin.terminated is True


class _DataPluginHolder(DataPlugin):
    """Helper DataPlugin subclass with channels for testing."""
    counter = DataChannel(data=0)
    message = DataChannel(data='hello', settable=True)
    value = DataChannel(data=3.14)


class TestDataPlugin:
    def test_channels_discovered_via_inspection(self):
        holder = _DataPluginHolder()
        assert 'counter' in holder.channels
        assert 'message' in holder.channels
        assert 'value' in holder.channels

    def test_getChannel_returns_channel_and_lambda(self, qapp):
        holder = _DataPluginHolder()
        chan_obj, chan_exp = holder.getChannel('counter')
        assert chan_obj is not None
        assert chan_exp is not None
        assert callable(chan_exp)
        assert chan_exp() == 0

    def test_getChannel_returns_value(self, qapp):
        holder = _DataPluginHolder()
        holder.counter.value = 5
        _, chan_exp = holder.getChannel('counter')
        assert chan_exp() == 5

    def test_getChannel_with_string_arg(self, qapp):
        holder = _DataPluginHolder()
        holder.message.value = 'test_message'
        _, chan_exp = holder.getChannel('message?string')
        assert chan_exp() == 'test_message'

    def test_getChannel_returns_none_for_missing_channel(self, qapp):
        holder = _DataPluginHolder()
        chan_obj, chan_exp = holder.getChannel('nonexistent')
        assert chan_obj is None
        assert chan_exp is None

    def test_setLogLevel_accepts_string(self, capsys):
        class LogPlugin(DataPlugin):
            pass
        plugin = LogPlugin()
        # Should not raise
        plugin.setLogLevel('DEBUG')

    def test_setLogLevel_accepts_int(self):
        class LogPlugin(DataPlugin):
            pass
        plugin = LogPlugin()
        # Should not raise
        plugin.setLogLevel(20)

    def test_setLogLevel_none_is_noop(self):
        class LogPlugin(DataPlugin):
            pass
        plugin = LogPlugin()
        plugin.setLogLevel(None)


class TestDataChannelBasic:
    def setup_method(self):
        self.channel = DataChannel(data=42)

    def test_get_value_with_no_fget_returns_data(self):
        assert self.channel.getValue() == 42

    def test_set_value_sets_data_and_emits_signal(self, qapp):
        received = []
        self.channel.signal.connect(received.append)
        self.channel.setValue(99)
        assert self.channel.value == 99
        assert received == [99]

    def test_get_string_returns_str_of_value(self):
        assert self.channel.getString() == '42'

    def test_settable_flag(self):
        assert self.channel.settable is False

    def test_default_value_is_none(self):
        ch = DataChannel()
        assert ch.value is None


class TestDataChannelWithFget:
    def setup_method(self):
        class Holder:
            _val = 100
        holder = Holder()
        self.channel = DataChannel(data=0)
        self.channel.instance = holder

    def test_get_value_calls_fget(self):
        def fget(instance, channel, *args):
            return instance._val + args[0] if args else instance._val
        self.channel.fget = fget
        assert self.channel.getValue() == 100

    def test_get_value_passes_args_to_fget(self):
        def fget(instance, channel, *args):
            return instance._val + args[0]
        self.channel.fget = fget
        assert self.channel.getValue(5) == 105


class TestDataChannelWithFset:
    def setup_method(self):
        self.channel = DataChannel(data=0)

    def test_set_value_with_fset_calls_fset(self, qapp):
        called_with = []
        def fset(instance, channel, value):
            called_with.append((instance, channel, value))
            channel.value = value * 2
        self.channel.fset = fset
        self.channel.setValue(10)
        assert len(called_with) == 1
        assert called_with[0][2] == 10
        assert self.channel.value == 20


class TestDataChannelDecorators:
    def test_getter_decorator_sets_fget(self):
        channel = DataChannel(data=0)

        def fget(instance, ch, *args):
            return 42

        result = channel.getter(fget)
        assert result is channel
        assert channel.fget is not None
        assert channel.getValue() == 42

    def test_setter_decorator_sets_fset(self):
        channel = DataChannel(data=0)

        def fset(instance, ch, value):
            ch.value = value * 10

        result = channel.setter(fset)
        assert result is channel
        assert channel.fset is not None
        channel.setValue(5)
        assert channel.value == 50

    def test_tostring_decorator_sets_fstr(self):
        channel = DataChannel(data=42)

        def fstr(instance, ch, *args):
            return 'custom_{}'.format(ch.value)

        result = channel.tostring(fstr)
        assert result is channel
        assert channel.fstr is not None
        assert channel.getString() == 'custom_42'


class TestDataChannelNotify:
    def test_notify_connects_signal(self, qapp):
        channel = DataChannel(data=0)
        received = []
        channel.notify(received.append)
        channel.setValue(77)
        assert received == [77]

    def test_notify_with_string_type(self, qapp):
        channel = DataChannel(data=42)
        received = []
        channel.notify(received.append, 'string')
        channel.setValue(99)
        # signal connects via getString lambda
        assert received == ['99']


class TestDataChannelDescriptor:
    def setup_method(self):
        class Holder:
            counter = DataChannel(data=0)

        self.holder = Holder()
        self.instance = Holder()

    def test_get_descriptor_sets_instance(self):
        ch = self.instance.counter
        assert isinstance(ch, DataChannel)
        assert ch.instance is self.instance

    def test_set_descriptor_calls_set_value(self):
        self.instance.counter = 10
        assert self.instance.counter.value == 10

    def test_call_returns_get_value(self):
        self.instance.counter = 5
        assert self.instance.counter() == 5


class TestDataChannelGetItem:
    def test_getitem_returns_indexed_value(self):
        channel = DataChannel(data=[1, 2, 3])
        assert channel[0] == 1
        assert channel[1] == 2
        assert channel[2] == 3

    def test_getitem_raises_for_non_indexable(self):
        channel = DataChannel(data=42)
        with pytest.raises(TypeError):
            _ = channel[0]


class TestDataChannelStr:
    def test_str_returns_string_of_value(self):
        channel = DataChannel(data=123)
        assert str(channel) == '123'

    def test_str_with_custom_fstr(self):
        channel = DataChannel(data=42)

        def fstr(instance, ch, *args):
            return 'x{}'.format(ch.value)

        channel.fstr = fstr
        assert str(channel) == 'x42'


class TestDataChannelDocString:
    def test_doc_from_fget(self):
        def getter(inst, ch):
            """This is my docstring."""
            return 0
        channel = DataChannel(fget=getter)
        assert channel.__doc__ == "This is my docstring."

    def test_explicit_doc_overrides_fget(self):
        def getter(inst, ch):
            """Wrong doc."""
            return 0
        channel = DataChannel(fget=getter, doc="Correct doc")
        assert channel.__doc__ == "Correct doc"


class TestDataChannelEquality:
    def test_channel_with_same_data_is_not_equal_by_identity(self):
        ch1 = DataChannel(data=42)
        ch2 = DataChannel(data=42)
        # They are different objects
        assert ch1 is not ch2
