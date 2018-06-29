#!/usr/bin/env python

from QtPyVCP.widgets.base_widgets.designer_plugin import DesignerPlugin
from QtPyVCP.widgets.display_widgets.dro_widget import DROWidget

class DROPlugin(DesignerPlugin):

    def pluginClass(self):
        return DROWidget
