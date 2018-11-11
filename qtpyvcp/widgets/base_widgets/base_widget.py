"""QtPyVCP Base Widgets

This file contains the definitions of the fundamental widgets upon which all other QtPyVCP
widgets are based.
"""

import os
import json

from qtpy.QtCore import Property

from qtpyvcp.data_plugins import channelFromURL

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

class ChanList(list):
    def __getitem__(self, index):
        return super(ChanList, self).__getitem__(index)()

class QtPyVCPBaseWidget(object):
    """QtPyVCP Base Widget.

    Class on which all other QtPyVCP widgets are based.
    This class handles the rules and other things that should
    apply to all QtPyVCP widgets regardles of use.
    """
    IN_DESIGNER = os.getenv('DESIGNER') != None

    DEFAULT_RULE_PROPERTY = 'None'
    RULE_PROPERTIES = {
        'None': ['None', None],
        'Enable': ['setEnabled', bool],
        'Visible': ['setVisible', bool],
        'Style Class': ['setStyleClass', str],
        # 'Opacity': ['setOpacity', float]
    }

    def __init__(self, parent=None):
        super(QtPyVCPBaseWidget, self).__init__()
        self._rules = ''
        self._style = ''
        self._data_channels = []


    def setStyleClass(self, style_class):
        """Set the QSS style class for the widget"""
        self.setProperty('style', style_class)

    @Property(str, designable=True)
    def style(self):
        """QSS style class selector property.

        This property can be changed dynamically to update the QSS style
        applied to the widget.

        Example:

            The ``style`` property can be used as a selector in QSS to
            apply different styles depending on the value.

            ::

                /* This will be applied when the `style` is set to "error" */
                WidgetClass[style="error"] {
                    color: red;
                }

                /* This will be applied when the `style` is not set */
                WidgetClass {
                    color: black;
                }

        Returns:
            str
        """
        return self._style

    @style.setter
    def style(self, style):
        print style
        self._style = style
        self.style().unpolish(self)
        self.style().polish(self)

    @Property(str, designable=False)
    def rules(self):
        """JSON formatted list of dictionaries, defining the widget rules.

        Returns:
            str
        """
        return self._rules

    @rules.setter
    def rules(self, rules):
        self._rules = rules
        self.registerRules(rules)

    def registerRules(self, rules):
        rules = json.loads(rules)
        for rule in rules:
            # print rule
            ch = ChanList()
            triggers = []
            for chan in rule['channels']:
                # print chan['channel']
                try:
                    chan_obj = channelFromURL(chan['url'])
                    trigger = chan.get('trigger', False)
                    chan_type = chan.get('type', chan_obj.typ.__name__)

                    if chan_type == 'str':
                        ch.append(chan_obj.text)
                        if trigger:
                            triggers.append(chan_obj.onTextChanged)
                    else:
                        ch.append(chan_obj.value)
                        if trigger:
                            triggers.append(chan_obj.onValueChanged)

                except:
                    LOG.exception("Error evaluating rule: {}".format(chan['url']))
                    return

            prop = self.RULE_PROPERTIES[rule['property']]

            evil_env = {'ch': ch, 'widget': self}
            exp_str = 'lambda: widget.{}({})'.format(prop[0], rule['expression'])
            exp = eval(exp_str, evil_env)

            # initial call to update
            exp()

            for trigger in triggers:
                trigger(exp)

class VCPWidget(QtPyVCPBaseWidget):
    """VCP Widget

    This is a general purpose widget for displaying data
    and other uses that do not involve user interaction.
    """
    def __init__(self, parent=None):
        super(VCPWidget, self).__init__()

class CMDWidget(QtPyVCPBaseWidget):
    """Command Widget

    This widget should be used as the base class for all widgets
    that control the machine. Eventualy additional functionality
    will be added to this class.
    """
    def __init__(self, parent=None):
        super(CMDWidget, self).__init__()

class HALWidget(QtPyVCPBaseWidget):
    """HAL Widget

    This widget should be used as the base class for HAL widgets.
    ToDo: Implement HAL functionality.
    """
    def __init__(self, parent=None):
        super(HALWidget, self).__init__()
