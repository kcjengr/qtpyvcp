"""
HAL Interface
-------------

This module allows the creation of userspace HAL components in Python.
This includes pins and parameters of the various HAL types.

Example:

.. code-block:: python

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

    # connect the listener to the input pin
    comp.addListener('in', onInChanged)

"""

from hal_qlib import QComponent, QPin

COMPONENTS = {}


def component(name):
    comp = QComponent(name)
    COMPONENTS[name] = comp
    return comp
