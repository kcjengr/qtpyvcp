"""QtPyVCP Base Widgets

This file contains the definitions of the fundamental widgets upon which all other QtPyVCP
widgets are based.
"""

import os
import json

from qtpy.QtCore import Property

import qtpyvcp
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)

class ChanList(list):
    """Channel value list.

    This list is intended to hold lambda functions for retrieving the current
    data channel values. When the list is indexed the function is called and
    the resulting value is returned.
    """
    def __getitem__(self, index):
        return super(ChanList, self).__getitem__(index)()

class QtPyVCPBaseWidget(object):
    """QtPyVCP Base Widget.

    Class on which all other QtPyVCP widgets are based.
    This class handles the rules and other things that should
    apply to all QtPyVCP widgets regardless of use.
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

                try:
                    protocol, sep, rest = chan['url'].partition(':')
                    item, sep, query = rest.partition('?')

                    plugin = qtpyvcp.PLUGINS[protocol]
                    eval_env = {'plugin': plugin}

                    # fast lambda function to get the current value of the channel
                    chan_val = eval("lambda: plugin.{}.handleQuery('{}')".format(item, query), eval_env)
                    ch.append(chan_val)

                    if chan.get('trigger', False):
                        chan_obj = eval("plugin.{}".format(item), eval_env)
                        triggers.append(chan_obj.valueChanged.connect)

                except:
                    LOG.exception("Error evaluating rule: {}".format(chan.get('url', '')))
                    return

            prop = self.RULE_PROPERTIES[rule['property']]

            if prop[1] is None:
                # donothing
                self._data_channels = ch
                continue

            evil_env = {'ch': ch, 'widget': self}
            evil_exp = 'lambda: widget.{}({})'.format(prop[0], rule['expression'])
            exp = eval(evil_exp, evil_env)

            # initial call to update
            try:
                exp()
            except:
                continue

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
