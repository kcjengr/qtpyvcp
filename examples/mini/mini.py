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

    from qtpyvcp import hal

    # create a new component and add some pins
    comp = hal.component("loop-back")
    comp.addPin("in", "float", "in")
    comp.addPin("out", "float", "out")

    # mark the component as 'ready'
    comp.ready()

    # define a function to call when the input pin changes
    def onInChanged(new_value):
        # loop the out pin to the in pin value
        comp.getPin('out').value = new_value

    # connect the
    comp.addListener('in', onInChanged)
