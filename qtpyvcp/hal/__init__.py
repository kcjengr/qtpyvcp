"""
HAL Interface
-------------

This module allows the creation of userspace HAL components in Python.
This includes pins and parameters of the various HAL types.

Example:

.. code-block:: python

    from qtpyvcp import hal

    # create a new component and add some pins
    comp = hal.getComponent("loop-back")
    comp.addPin("in", "float", "in")
    comp.addPin("out", "float", "out")

    # mark the component as 'ready'
    comp.ready()

    # define a function to call when the input pin changes
    def onInChanged(new_value):
        # loop the out pin to the in pin value
        comp.getPin('out').value = new_value

    # connect the listener to the input pin
    comp.addListener('in', onInChanged)

"""

from qtpyvcp.utilities.logger import getLogger

from hal_qlib import QComponent, QPin

COMPONENTS = {}
LOG = getLogger(__name__)


def component(name):
    """Initializes a new HAL component and registers it."""
    comp = QComponent(name)
    COMPONENTS[name] = comp
    return comp


def getComponent(name='qtpyvcp'):
    """Get HAL component.

    Args:
        name (str) : The name of the component to get. Defaults to `qtpyvcp`.

    Returns:
        QComponent : An existing or new HAL component.
    """

    try:
        comp = COMPONENTS[name]
        LOG.debug("Using existing HAL component: %s", name)
    except KeyError:
        LOG.info("Creating new HAL component: %s", name)
        comp = component(name)

    return comp


if __name__ == "__main__":

    from qtpy.QtWidgets import QApplication
    from qtpyvcp import hal

    app = QApplication([])

    # create a new component and add some pins
    comp = hal.getComponent("loop-back")
    comp.addPin("in", "float", "in")
    comp.addPin("out", "float", "out")

    # mark the component as 'ready'
    comp.ready()

    # define a function to call when the input pin changes
    def onInChanged(new_value):
        print("loop-back.in pin changed:", new_value)
        # loop the out pin to the in pin value
        comp.getPin('out').value = new_value

    # connect the listener to the input pin
    comp.addListener('in', onInChanged)

    app.exec_()
