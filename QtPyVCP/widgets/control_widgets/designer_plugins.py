#!/usr/bin/env python

from QtPyVCP.widgets.base_widgets.designer_plugin import _DesignerPlugin

from QtPyVCP.widgets.control_widgets.entry_widget import EntryWidget
class EntryPlugin(_DesignerPlugin):
    def pluginClass(self):
        return EntryWidget
    def toolTip(self):
        return "MDI command entry"
