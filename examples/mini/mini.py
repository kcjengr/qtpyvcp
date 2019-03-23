from qtpyvcp.widgets.form_widgets.main_window import VCPMainWindow

from qtpy.QtCore import Property, Signal, Slot

SETTINGS = {}

class Setting(Property):
    def __init__(self, id, *args, **kwargs):
        super(Setting, self).__init__(*args, **kwargs)
        SETTINGS[id] = self


class MiniVCP(VCPMainWindow):
    """Main window class for the Mini example VCP."""

    maximizedChanged = Signal(bool)

    def __init__(self, *args, **kwargs):
        super(MiniVCP, self).__init__(*args, **kwargs)

        for i in dir(self):
            if 'maximized' in i.lower():
                print "##################################", i

    # @Property(bool, user=True, notify=maximizedChanged)
    # def maximized(self):
    #     return self.isMaximized()
    #
    # @maximized.setter
    # def maximized(self, maximize):
    #     if maximize:
    #         self.showMaximized()
    #     else:
    #         self.showNormal()
    #     self.maximizedChanged.emit(maximize)
