from PySide6.QtGui import QIcon
from PySide6.QtDesigner import QDesignerCustomWidgetInterface

from .plugin_extension import ExtensionFactory, Q_TYPEID
from .designer_hooks import DesignerHooks

from .rules_editor import RulesEditorExtension


class _DesignerPlugin(QDesignerCustomWidgetInterface):

    group_name = None

    def __init__(self):
        super().__init__()
        self.initialized = False
        self.manager = None
        self._form_editor = None

    # This MUST be overridden to return the widget class

    def pluginClass(self):
        raise NotImplementedError()

    def designerExtensions(self):
        if hasattr(self.pluginClass(), 'RULE_PROPERTIES'):
            return [RulesEditorExtension,]
        else:
            return []

    # Override to set the default widget name used in QtDesinger
    def objectName(self):
        name = self.name().lower()
        if name.startswith('vcp'):
            name = name[3:]
        return name

    # Override to set the tooltip displayed in the QtDesinger widget box
    def toolTip(self):
        return ""

    # Override to set the 'whats this' in QtDesinger
    def whatsThis(self):
        return ""

    # Override to specify that widgets can be added as children in QtDesigner
    def isContainer(self):
        return False

    # Override to set the icon used for the widget in QtDesigner
    def icon(self):
        return  QIcon()

    # Override to set the QtDesigner widget box group heading
    def group(self):
        if self.group_name is None:
            try:
                tmp = self.pluginClass().__module__.split('.')[2].split('_')[0].capitalize()
                return "QtPyVCP - {}".format(tmp)
            except:
                return "QtPyVCP - Undefined"
        else:
            return self.group_name

    # Override to set initial QtDesigner property values
    def domXml(self):
        return f"<ui language='c++'>\n<widget class='{self.name()}' name='{self.objectName()}'>\n</widget>\n</ui>"

#==============================================================================
#  These methods should not need to be overridden
#==============================================================================

    def initialize(self, form_editor):
        if self.initialized:
            return

        designer_hooks = DesignerHooks()
        designer_hooks.form_editor = form_editor
        self._form_editor = form_editor

        self.manager = form_editor.extensionManager()

        if len(self.designerExtensions()) > 0 and self.manager:
            factory = ExtensionFactory(self.manager)
            self.manager.registerExtensions(factory, Q_TYPEID['QDesignerTaskMenuExtension'])

        self.initialized = True

    def isInitialized(self):
        return self._form_editor is not None

    def createWidget(self, parent):

        w = self.pluginClass()(parent)
        w.extensions = self.designerExtensions()
        return w

    def name(self):
        return self.pluginClass().__name__

    def includeFile(self):
        return self.pluginClass().__module__
