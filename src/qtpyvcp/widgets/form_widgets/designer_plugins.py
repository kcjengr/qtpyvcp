from qtpyvcp.widgets.qtdesigner import _DesignerPlugin

from .main_window import VCPMainWindow
import os

class MainWindowPlugin(_DesignerPlugin):
    def pluginClass(self):
        return VCPMainWindow

    def isContainer(self):
        return True

    def group(self):
        return "Use ONLY as a Toplevel!!!"

    def domXml(self):
        return '''<widget class="VCPMainWindow" name="VCP Main Window">
                   <property name="geometry">
                    <rect>
                     <x>0</x>
                     <y>0</y>
                     <width>500</width>
                     <height>300</height>
                    </rect>
                   </property>
                   <widget class="QWidget" name="centralwidget"/>
                  </widget>'''

    def createWidget(self, parent):
        # Create the widget using the base class method
        widget = super().createWidget(parent)
        
        # In designer mode, load stylesheet from environment if available
        if hasattr(widget, 'loadStylesheet'):
            qss_env = os.getenv('QSS_STYLESHEET')
            if qss_env is not None:
                widget.loadStylesheet(qss_env)
        
        return widget


from qtpyvcp.widgets.form_widgets.probe_widget.probe import SubCaller


class ProbePlugin(_DesignerPlugin):
    def pluginClass(self):
        return SubCaller()

    def toolTip(self):
        return "Probe widget"

    def isContainer(self):
        return True

    def createWidget(self, parent):
        t = SubCaller(parent)
        return t
