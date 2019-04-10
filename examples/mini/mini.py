from qtpyvcp.widgets.form_widgets.main_window import VCPMainWindow

from qtpyvcp import hal

class MiniVCP(VCPMainWindow):
    """Main window class for the Mini example VCP."""
    def __init__(self, *args, **kwargs):
        super(MiniVCP, self).__init__(*args, **kwargs)

        comp = hal.component('hello')
        comp.addPin('testing', 'float', 'in')
        comp.addListener('testing', self.onHalTestingChanged)
        comp.ready()

    def onHalTestingChanged(self, val):
        print "hello.testing value changed: ", val
