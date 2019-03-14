from qtpy.QtGui import QIcon
from qtpy.QtDesigner import QPyDesignerCustomWidgetPlugin

from plugin_extension import ExtensionFactory, Q_TYPEID
from designer_hooks import DesignerHooks

from rules_editor import RulesEditorExtension

class _DesignerPlugin(QPyDesignerCustomWidgetPlugin):

    def __init__(self, parent=None):
        super(_DesignerPlugin, self).__init__(parent=parent)
        self.initialized = False
        self.manager = None

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
        return QIcon()

    # Override to set the QtDesigner widget box group heading
    def group(self):
        group = self.pluginClass().__module__.split('.')[2].split('_')[0].capitalize()
        return "QtPyVCP - {}".format(group)

    # Override to set initial QtDesigner property values
    def domXml(self):
        return '<widget class="{}" name="{}">\n</widget>\n'.format(
            self.name(), self.objectName())

#==============================================================================
#  These methods should not need to be overridden
#==============================================================================

    def initialize(self, form_editor):
        if self.initialized:
            return

        designer_hooks = DesignerHooks()
        designer_hooks.form_editor = form_editor

        self.manager = form_editor.extensionManager()

        if len(self.designerExtensions()) > 0 and self.manager:
            factory = ExtensionFactory(parent=self.manager)
            self.manager.registerExtensions(factory,
                                            Q_TYPEID['QDesignerTaskMenuExtension'])

        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def createWidget(self, parent):
        w = self.pluginClass()(parent)
        w.extensions = self.designerExtensions()
        return w

    def name(self):
        return self.pluginClass().__name__

    def includeFile(self):
        return self.pluginClass().__module__
