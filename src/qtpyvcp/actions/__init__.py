import os
import sys
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QPushButton, QCheckBox, QSlider, QSpinBox, QComboBox, QDial

from . import machine_actions as machine
from . import program_actions as program
from . import spindle_actions as spindle
from . import coolant_actions as coolant
from . import tool_actions as tool
from . import power_actions as power

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

IN_DESIGNER = os.getenv('DESIGNER', False)

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
    
    if IN_DESIGNER:
        return
    
    for item in action.split('.'):
        if item.isdigit():
            kwargs[prev_item] = int(item)
            continue
        try:
            method = getattr(method, item)
        except(AttributeError, KeyError):
            if IN_DESIGNER:
                return
            else:
                raise InvalidAction("Could not get action method: %s" % item)

        prev_item = item

    if method is None or not callable(method):
        if IN_DESIGNER:
            return
        else:
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

        if action.startswith('machine.jog.axis'):
            widget.pressed.connect(lambda: method(*args, **kwargs))
            widget.released.connect(lambda: method(*args, speed=0, **kwargs))

        else:
            widget.clicked.connect(lambda: method(*args, **kwargs))

    elif isinstance(widget, QSlider) or isinstance(widget, QSpinBox) or isinstance(widget, QDial):
        widget.valueChanged.connect(method)

    elif isinstance(widget, QComboBox):
        widget.activated[str].connect(method)

    else:
        raise InvalidAction('Can\'t bind action "{}" to unsupported widget type "{}"'
                            .format(action, widget.__class__.__name__))

    try:
        # Set the initial widget OK state and update on changes
        method.ok(*args, widget=widget, **kwargs)
        method.bindOk(*args, widget=widget, **kwargs)
    except Exception as e:
        msg = "%s raised while trying to bind '%s' action to '%s'" % \
              (e, action, widget)
        raise InvalidAction(msg, sys.exc_info()[2])
