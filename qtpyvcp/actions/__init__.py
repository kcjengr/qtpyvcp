import sys
from qtpy.QtWidgets import QAction, QPushButton, QCheckBox, QSlider, QSpinBox, QComboBox

import machine_actions as machine
import program_actions as program
import spindle_actions as spindle
import coolant_actions as coolant
import tool_actions as tool

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

class InvalidAction(Exception):
    pass

def bindWidget(widget, action):
    """Binds a widget to an action.

    Args:
        widget (QWidget) : The widget to bind the action too. Typically `widget`
            is a QPushButton, QCheckBox, QComboBox, QSlider or QAction instance.

        action (str) : The string identifier of the action to bind the widget
            to, in the format ``action_class.action_name:arg1, arg2 ...``.

    Example:
        A QPushButton or QCheckBox would typically be bound to an action
        that does not take an argument, for example ``machine.power.toggle``::

            bindWidget(widget, 'machine.power.toggle')

        But it is possible to specify an argument by appending an ':' followed
        by the argument value. For example we can bind a QPushButton so that it
        homes the X axis when the button is pressed::

            bindWidget(widget, 'machine.home.axis:x')

        Widgets such as QSliders and QComboBoxs that have a value associated
        with them can also be bound to a action, and the value will
        automatically be passed to the action. For example we can bind
        a QSLider to the ``spindle.0.override`` action::

            bindWidget(widget, 'spindle.0.override')
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
        except(AttributeError, KeyError):
            raise InvalidAction("Could not get action method: %s" % item)

        prev_item = item

    if method is None or not callable(method):
        raise InvalidAction('Method is not callable: %s' % method)

    if args != '':
        # make a list out of comma separated args
        args = args.replace(' ', '').split(',')
        # convert numbers to int and unicode to str
        args = [int(arg) if arg.isdigit() else str(arg) for arg in args]

    if isinstance(widget, QAction):
        widget.triggered.connect(lambda: method(*args, **kwargs)) # should be able to do widget.triggered[()]

        # if it is a toggle action make the menu item checkable
        if action.endswith('toggle'):
            widget.setCheckable(True)

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
        raise InvalidAction('Can\'t bind action "{}" to unsupported widget type "{}"'
                            .format(action, widget.__class__.__name__))

    try:
        method.ok(*args, widget=widget, **kwargs)      # Set the initial widget OK state
        method.bindOk(*args, widget=widget, **kwargs)  # Update widget on OK status changes
    except:
        raise InvalidAction("Could not bind OK status to widget.")
