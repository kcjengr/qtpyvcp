import sys
from PyQt5.QtWidgets import QAction

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
            would be a QPushButton, QCheckBox or a QAction instance.

        action (string) : The string identifier of the action to bind the widget
            to, in the format `action_class.action_name:arg1, arg2 ...`.

    Example:
        bindWidget(widget, 'machine.home.axis:x')
        bindWidget(widget, 'spindle.forward:200')
        bindWidget(widget, 'spindle.off')
    """
    action, sep, args = action.partition(':')
    action = action.replace('-', '_')
    method = reduce(getattr, action.split('.'), sys.modules[__name__])
    if method is None:
        return

    # if it is a toggle action make the widget checkable
    if action.endswith('toggle'):
        widget.setCheckable(True)

    if isinstance(widget, QAction):
        sig = widget.triggered
    else:
        sig = widget.clicked

    if args == '':
        sig.connect(lambda: method())

    elif args == 'checked':
        sig.connect(method)

    else:
        # make a list out of comma separated args
        args = args.replace(' ', '').split(',')
        # convert numbers to int and unicode to str
        args = [int(arg) if arg.isdigit() else str(arg) for arg in args]

        if action.startswith('machine.jog'):
            widget.pressed.connect(lambda: method(*args))
            widget.released.connect(lambda: method(*args, speed=0))

        else:
            sig.connect(lambda: method(*args))

    try:
        method.ok(*args, widget=widget) # Set the initial widget state
        method.bindOk(*args, widget=widget)
    except:
        LOG.exception("Error in bindWidget")
        pass
