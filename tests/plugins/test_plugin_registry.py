import pytest
from collections import OrderedDict
from qtpyvcp.plugins import (
    registerPlugin, registerPluginFromClass, getPlugin,
    iterPlugins, initialisePlugins, postGuiInitialisePlugins, terminatePlugins,
    _PLUGINS, Plugin
)


@pytest.fixture(autouse=True)
def clean_registry():
    _PLUGINS.clear()
    yield
    _PLUGINS.clear()


class MockPlugin(Plugin):
    def __init__(self, name='mock'):
        super(MockPlugin, self).__init__()
        self.name = name
        self.initialised = False
        self.post_gui_initialised = False
        self.terminated = False

    def initialise(self):
        self.initialised = True

    def postGuiInitialise(self, main_window):
        self.post_gui_initialised = True

    def terminate(self):
        self.terminated = True


class BrokenPlugin(Plugin):
    def __init__(self):
        super(BrokenPlugin, self).__init__()

    def initialise(self):
        raise RuntimeError("initialise failed")

    def terminate(self):
        raise RuntimeError("terminate failed")


class TestRegisterPlugin:
    def test_register_new_plugin(self):
        plugin = MockPlugin('test')
        registerPlugin('my_plugin', plugin)
        assert getPlugin('my_plugin') is plugin

    def test_register_multiple_plugins(self):
        p1 = MockPlugin('one')
        p2 = MockPlugin('two')
        registerPlugin('plugin_a', p1)
        registerPlugin('plugin_b', p2)
        assert getPlugin('plugin_a') is p1
        assert getPlugin('plugin_b') is p2

    def test_replace_existing_plugin(self, caplog):
        p1 = MockPlugin('first')
        p2 = MockPlugin('second')
        registerPlugin('my_plugin', p1)
        registerPlugin('my_plugin', p2)
        assert getPlugin('my_plugin') is p2

    def test_plugins_are_ordered_by_registration(self):
        p1 = MockPlugin('first')
        p2 = MockPlugin('second')
        p3 = MockPlugin('third')
        registerPlugin('c', p3)
        registerPlugin('a', p1)
        registerPlugin('b', p2)
        keys = [k for k, v in iterPlugins()]
        assert keys == ['c', 'a', 'b']


class TestRegisterPluginFromClass:
    def test_register_from_class_object(self):
        inst = registerPluginFromClass('my_plugin', MockPlugin, kwargs={'name': 'from_class'})
        assert isinstance(inst, MockPlugin)
        assert getPlugin('my_plugin') is inst

    def test_register_from_string_path(self):
        inst = registerPluginFromClass('my_plugin', 'qtpyvcp.plugins.base_plugins:Plugin')
        assert isinstance(inst, Plugin)
        assert getPlugin('my_plugin') is inst

    def test_invalid_plugin_class_raises_assertion(self):
        with pytest.raises(AssertionError):
            registerPluginFromClass('bad_plugin', object)

    def test_missing_module_raises_exception(self):
        with pytest.raises(Exception):
            registerPluginFromClass('bad_plugin', 'nonexistent.module:SomeClass')

    def test_args_passed_to_init(self):
        inst = registerPluginFromClass('my_plugin', MockPlugin, args=['custom_name'])
        assert inst.name == 'custom_name'


class TestGetPlugin:
    def test_get_existing_plugin(self):
        plugin = MockPlugin()
        registerPlugin('existing', plugin)
        assert getPlugin('existing') is plugin

    def test_get_missing_plugin_returns_none(self, caplog):
        result = getPlugin('nonexistent')
        assert result is None


class TestIterPlugins:
    def test_returns_items_iterator(self):
        p1 = MockPlugin('a')
        registerPlugin('key_a', p1)
        items = list(iterPlugins())
        assert len(items) == 1
        key, value = items[0]
        assert key == 'key_a'
        assert value is p1

    def test_empty_registry_yields_nothing(self):
        items = list(iterPlugins())
        assert items == []

    def test_multiple_plugins_iterated(self):
        registerPlugin('a', MockPlugin('a'))
        registerPlugin('b', MockPlugin('b'))
        registerPlugin('c', MockPlugin('c'))
        items = list(iterPlugins())
        assert len(items) == 3


class TestInitialisePlugins:
    def test_calls_initialise_on_each(self):
        p1 = MockPlugin('first')
        p2 = MockPlugin('second')
        registerPlugin('a', p1)
        registerPlugin('b', p2)
        initialisePlugins()
        assert p1.initialised is True
        assert p2.initialised is True

    def test_initialises_in_registration_order(self):
        order = []
        class TrackedPlugin(Plugin):
            def initialise(self):
                order.append(len(order) + 1)
        registerPlugin('first', TrackedPlugin())
        registerPlugin('second', TrackedPlugin())
        registerPlugin('third', TrackedPlugin())
        initialisePlugins()
        assert order == [1, 2, 3]


class TestPostGuiInitialisePlugins:
    def test_calls_post_gui_initialise_on_each(self):
        p1 = MockPlugin('first')
        p2 = MockPlugin('second')
        registerPlugin('a', p1)
        registerPlugin('b', p2)
        postGuiInitialisePlugins(main_window=None)
        assert p1.post_gui_initialised is True
        assert p2.post_gui_initialised is True

    def test_receives_main_window(self):
        class WindowTrackingPlugin(Plugin):
            def __init__(self):
                super(WindowTrackingPlugin, self).__init__()
                self.window = None
            def postGuiInitialise(self, main_window):
                self.window = main_window
        plugin = WindowTrackingPlugin()
        registerPlugin('window_plugin', plugin)
        mock_window = object()
        postGuiInitialisePlugins(mock_window)
        assert plugin.window is mock_window


class TestTerminatePlugins:
    def test_terminates_all_plugins(self):
        p1 = MockPlugin('first')
        p2 = MockPlugin('second')
        registerPlugin('a', p1)
        registerPlugin('b', p2)
        terminatePlugins()
        assert p1.terminated is True
        assert p2.terminated is True

    def test_terminates_in_reverse_order(self):
        order = []
        class TrackedPlugin(Plugin):
            def __init__(self, name):
                super(TrackedPlugin, self).__init__()
                self.name = name
            def terminate(self):
                order.append(self.name)
        registerPlugin('first', TrackedPlugin('first'))
        registerPlugin('second', TrackedPlugin('second'))
        registerPlugin('third', TrackedPlugin('third'))
        terminatePlugins()
        assert order == ['third', 'second', 'first']

    def test_skips_failed_plugin_and_continues(self, caplog):
        p1 = MockPlugin('good')
        p2 = BrokenPlugin()
        p3 = MockPlugin('also_good')
        registerPlugin('a', p1)
        registerPlugin('b', p2)
        registerPlugin('c', p3)
        terminatePlugins()
        assert p1.terminated is True
        assert p3.terminated is True
