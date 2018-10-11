import sys
from PyQt5.QtWidgets import QAction, QPushButton, QCheckBox, QSlider, QSpinBox, QComboBox

import machine_actions as machine
import program_actions as program
import spindle_actions as spindle
import coolant_actions as coolant
import tool_actions as tool

# Set up logging
from QtPyVCP.utilities import logger
LOG = logger.getLogger(__name__)

def bindWidget(widget, action):
    """Binds a widget to an action.

    Args:
        widget (QtWidget) : The widget to bind the action too. Typically `widget`
            is a QPushButton, QCheckBox, QComboBox, QSlider or QAction instance.

        action (string) : The string identifier of the action to bind the widget
            to, in the format `action_class.action_name:arg1, arg2 ...`.

    Example:
        bindWidget(widget, 'machine.power.toggle')
        bindWidget(widget, 'machine.home.axis:x')
        bindWidget(widget, 'spindle.forward:200')
    """
    action, sep, args = str(action).partition(':')
    action = action.replace('-', '_')

    kwargs = {}

    prev_item = ''
    method = sys.modules[__name__]
    for item in action.split('.'):
        if item.isdigit():
            kwargs[prev_item] = int(item)
            continue
        try:
            method = getattr(method, item)
        except:
            LOG.exception("Invalid action: {}".format(action))
            return
        prev_item = item

    if method is None or not callable(method):
        return

    if args != '':
        # make a list out of comma separated args
        args = args.replace(' ', '').split(',')
        # convert numbers to int and unicode to str
        args = [int(arg) if arg.isdigit() else str(arg) for arg in args]

    # print method
    # print args, kwargs

    # if it is a toggle action make the widget checkable
    if action.endswith('toggle'):
        widget.setCheckable(True)

    if isinstance(widget, QAction):
        widget.triggered.connect(lambda: method(*args, **kwargs)) # should be able to do widget.triggered[()]

    elif isinstance(widget, QPushButton) or isinstance(widget, QCheckBox):

        if action.startswith('machine.jog'):
            widget.pressed.connect(lambda: method(*args, **kwargs))
            widget.released.connect(lambda: method(*args, speed=0, **kwargs))

        else:
            widget.clicked.connect(lambda: method(*args, **kwargs))

    elif isinstance(widget, QSlider) or isinstance(widget, QSpinBox):
        widget.valueChanged.connect(method)

    elif isinstance(widget, QComboBox):
        widget.activated[str].connect(method)

    else:
        LOG.error('Can\'t bind action "{}" to unsupported widget type "{}"'\
            .format(action, widget.__class__.__name__))
        return

    try:
        method.ok(*args, widget=widget, **kwargs) # Set the initial widget state
        method.bindOk(*args, widget=widget, **kwargs)

    except:
        LOG.exception("Error in bindWidget")
