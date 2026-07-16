import pytest
from unittest.mock import MagicMock, patch


class TestDesignerPlugin:
    """Tests for _DesignerPlugin base class."""

    def test_init_sets_initialized_false(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        plugin = _DesignerPlugin()

        assert plugin.initialized is False

    def test_init_sets_manager_none(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        plugin = _DesignerPlugin()

        assert plugin.manager is None

    def test_name_returns_widget_class_name(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class TestWidget:
            pass

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return TestWidget

        plugin = TestPlugin()
        assert plugin.name() == 'TestWidget'

    def test_objectName_lowercase_without_vcp_prefix(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class TestWidget:
            pass

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return TestWidget

        plugin = TestPlugin()
        assert plugin.objectName() == 'testwidget'

    def test_objectName_strips_vcp_prefix(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class VCPMyWidget:
            pass

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return VCPMyWidget

        plugin = TestPlugin()
        assert plugin.objectName() == 'mywidget'

    def test_toolTip_returns_empty(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class TestWidget:
            pass

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return TestWidget

        plugin = TestPlugin()
        assert plugin.toolTip() == ""

    def test_whatsThis_returns_empty(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class TestWidget:
            pass

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return TestWidget

        plugin = TestPlugin()
        assert plugin.whatsThis() == ""

    def test_isContainer_returns_false(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class TestWidget:
            pass

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return TestWidget

        plugin = TestPlugin()
        assert plugin.isContainer() is False

    def test_icon_returns_empty_qicon(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin
        from qtpy.QtGui import QIcon

        class TestWidget:
            pass

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return TestWidget

        plugin = TestPlugin()
        icon = plugin.icon()
        assert isinstance(icon, QIcon)
        assert icon.isNull() is True

    def test_domXml_format(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class MyWidget:
            pass

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return MyWidget

        plugin = TestPlugin()
        dom = plugin.domXml()

        assert 'class="MyWidget"' in dom
        assert 'name="mywidget"' in dom

    def test_domXml_uses_objectName(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class VCPFrameWidget:
            pass

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return VCPFrameWidget

        plugin = TestPlugin()
        dom = plugin.domXml()

        assert 'name="framewidget"' in dom


class TestDesignerPluginGroup:
    """Tests for group method."""

    def test_group_from_module_name(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class MyWidget:
            __module__ = 'qtpyvcp.widgets.base_widgets.my_widget'

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return MyWidget

        plugin = TestPlugin()
        group = plugin.group()

        assert 'QtPyVCP - Base' in group

    def test_group_with_custom_name(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class MyWidget:
            pass

        class TestPlugin(_DesignerPlugin):
            group_name = "Custom Group"

            def pluginClass(self):
                return MyWidget

        plugin = TestPlugin()
        assert plugin.group() == "Custom Group"

    def test_group_from_short_module_name(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class MyWidget:
            __module__ = 'qtpyvcp.widgets.containers.my_frame'

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return MyWidget

        plugin = TestPlugin()
        group = plugin.group()

        assert 'QtPyVCP - Containers' in group


class TestDesignerPluginInitialize:
    """Tests for initialize and isInitialized methods."""

    def test_is_initialized_after_init(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class TestWidget:
            pass

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return TestWidget

        plugin = TestPlugin()
        assert plugin.isInitialized() is False

    def test_initialize_sets_flag(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class TestWidget:
            pass

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return TestWidget

        plugin = TestPlugin()
        mock_editor = MagicMock()
        mock_editor.extensionManager.return_value = MagicMock()

        with patch('qtpyvcp.widgets.qtdesigner.designer_plugin.DesignerHooks') as MockHooks:
            MockHooks.return_value.form_editor = None
            MockHooks.return_value.setup_hooks = MagicMock()
            plugin.initialize(mock_editor)

        assert plugin.initialized is True

    def test_initialize_idempotent(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class TestWidget:
            pass

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return TestWidget

        plugin = TestPlugin()
        mock_editor = MagicMock()
        mock_editor.extensionManager.return_value = MagicMock()

        with patch('qtpyvcp.widgets.qtdesigner.designer_plugin.DesignerHooks') as MockHooks:
            MockHooks.return_value.form_editor = None
            plugin.initialize(mock_editor)
            first_initialized = plugin.initialized
            plugin.initialize(mock_editor)

        assert plugin.initialized is first_initialized


class TestDesignerPluginExtensions:
    """Tests for designerExtensions method."""

    def test_extensions_with_rule_properties(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin
        from qtpyvcp.widgets.qtdesigner.rules_editor import RulesEditorExtension

        class WidgetWithRules:
            RULE_PROPERTIES = {'Visible': ['setVisible', bool]}

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return WidgetWithRules

        plugin = TestPlugin()
        extensions = plugin.designerExtensions()

        assert len(extensions) == 1
        assert extensions[0] is RulesEditorExtension

    def test_extensions_without_rule_properties(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class WidgetWithoutRules:
            pass

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return WidgetWithoutRules

        plugin = TestPlugin()
        extensions = plugin.designerExtensions()

        assert len(extensions) == 0


class TestDesignerPluginCreateWidget:
    """Tests for createWidget method."""

    def test_create_widget_returns_instance(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class TestWidget:
            def __init__(self, parent=None):
                self.parent = parent

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return TestWidget

        plugin = TestPlugin()
        widget = plugin.createWidget(parent=None)

        assert isinstance(widget, TestWidget)
        assert widget.parent is None

    def test_create_widget_sets_extensions(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class WidgetWithRules:
            RULE_PROPERTIES = {'Visible': ['setVisible', bool]}

            def __init__(self, parent=None):
                self.parent = parent

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return WidgetWithRules

        plugin = TestPlugin()
        widget = plugin.createWidget(parent=None)

        assert hasattr(widget, 'extensions')
        assert len(widget.extensions) == 1


class TestDesignerPluginIncludeFile:
    """Tests for includeFile method."""

    def test_include_file_returns_module(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class TestWidget:
            __module__ = 'qtpyvcp.widgets.base_widgets.test'

        class TestPlugin(_DesignerPlugin):
            def pluginClass(self):
                return TestWidget

        plugin = TestPlugin()
        include_file = plugin.includeFile()

        assert include_file == 'qtpyvcp.widgets.base_widgets.test'


class TestDesignerPluginAbstract:
    """Tests for abstract method enforcement."""

    def test_plugin_class_not_implemented(self):
        from qtpyvcp.widgets.qtdesigner.designer_plugin import _DesignerPlugin

        class IncompletePlugin(_DesignerPlugin):
            pass

        plugin = IncompletePlugin()

        with pytest.raises(NotImplementedError):
            plugin.pluginClass()
