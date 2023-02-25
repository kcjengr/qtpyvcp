"""
Base Widgets
------------

This file contains the definitions of the fundamental widgets upon which
all other QtPyVCP widgets are based.
"""

import os
import json

from qtpy.QtCore import Property, Slot
from qtpy.QtWidgets import QPushButton

from qtpyvcp.plugins import getPlugin
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


class VCPPrimitiveWidget(object):
    """VCPPrimitiveWidget.

    Class on which all QtPyVCP widgets should be based.
    """
    def __init__(self, parent=None):
        super(VCPPrimitiveWidget, self).__init__()

    def initialize(self):
        """This method is called right before the main application starts."""
        pass

    def terminate(self):
        """This method is called right before the main application ends."""
        pass


class VCPBaseWidget(VCPPrimitiveWidget):
    """QtPyVCP Base Widget.

    This class handles the rules and other things that
    apply to QtPyVCP widgets regardless of use.
    """
    IN_DESIGNER = os.getenv('DESIGNER') != None

    DEFAULT_RULE_PROPERTY = 'None'
    RULE_PROPERTIES = {
        'None': ['None', None],
        'Enable': ['setEnabled', bool],
        'Visible': ['setVisible', bool],
        'Style Class': ['setStyleClass', str],
        'Style Sheet': ['setStyleSheet', str],
    }

    def __init__(self, parent=None):
        super(VCPBaseWidget, self).__init__()
        self._rules = '[]'
        self._style = ''
        self._data_channels = []
        self._security_level = 0

    #
    # Security implementation
    #
    
    @Property(int)
    def security(self):
        """ Security level
        
        An integer representing the security level for a widget.
        The higher the integer value the higher the operator access level
        needs to be to be able to interact with the widget.
        
        Example:
        
            security = 0 requires an operator to have an assigned security value
            of 0 or more.  This is essentially the lowest security rating.
            Negative numbers having no effect.
            
            security = 5 requires an operator to have an assigned security level
            of 5 or more to interact with the widget.  So an operator with a
            rating of 2 will not be able to interact with the widget. The widget
            will be represented as "disabled" to them.
        
        returns:
            int
        """
        return self._security_level

    @security.setter
    def security(self, security):
        self._security_level = security

    #
    # Style Rules implementation
    #
    def setStyleClass(self, style_class):
        """Set the QSS style class for the widget"""
        self.setProperty('style', style_class)

    @Property(str, designable=False)
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
        self._rules = rules or '[]'
        self.registerRules()

    def registerRules(self):
        rules = json.loads(self._rules)
        for rule in rules:
            # print(rule)
            ch = ChanList()
            triggers = []
            for chan in rule['channels']:

                try:
                    url = chan['url'].strip()
                    protocol, sep, item = url.partition(':')
                    chan_obj, chan_exp = getPlugin(protocol).getChannel(item)

                    ch.append(chan_exp)

                    if chan.get('trigger', False):
                        triggers.append(chan_obj.notify)

                except Exception:
                    LOG.exception("Error evaluating rule: {}"
                                  .format(chan.get('url', '')))
                    return

            prop = self.RULE_PROPERTIES[rule['property']]

            if prop[1] is None:
                # donothing
                self._data_channels = ch
                continue

            eval_env = {'ch': ch, 'widget': self}
            eval_exp = 'lambda: widget.{}({})'.format(
                            prop[0], rule['expression']).encode('utf-8')
            exp = eval(eval_exp, eval_env)

            # initial call to update
            try:
                exp()
            except:
                LOG.exception('Error calling rules expression:')
                continue

            for trigger in triggers:
                trigger(exp)


class VCPWidget(VCPBaseWidget):
    """VCP Widget

    This is a general purpose widget for displaying data
    and other uses that do not involve user interaction.
    """
    def __init__(self, parent=None):
        super(VCPWidget, self).__init__()

class CMDWidget(VCPBaseWidget):
    """Command Widget

    This widget should be used as the base class for all widgets
    that control the machine. Eventually additional functionality
    will be added to this class.
    """
    def __init__(self, parent=None):
        super(CMDWidget, self).__init__()

class HALWidget(VCPBaseWidget):
    """HAL Widget

    This widget should be used as the base class for HAL widgets.
    ToDo: Implement HAL functionality.
    """
    def __init__(self, parent=None):
        super(HALWidget, self).__init__()

        self._hal_object_name = None

    @Property(str)
    def pinBaseName(self):
        """The base name to use for the generated HAL pins.

        If not specified the widgets objectName will be used.

        Returns:
            str
        """
        if self._hal_object_name is None:
            return str(self.objectName()).replace('_', '-')
        return self._hal_object_name

    @pinBaseName.setter
    def pinBaseName(self, name):
        # ToDO: Validate HAL pin name
        self._hal_object_name = name

    @Slot()
    def getPinBaseName(self):
        return self.pinBaseName

class VCPButton(QPushButton, CMDWidget):
    """VCP Button Widget

    This is a general purpose button widget for displaying data
    and other uses that do not involve user interaction.
    """

    DEFAULT_RULE_PROPERTY = 'Enable'
    RULE_PROPERTIES = CMDWidget.RULE_PROPERTIES.copy()
    RULE_PROPERTIES.update({
        'Text': ['setText', str],
        'Checked': ['setChecked', bool]
    })

    def __init__(self, parent=None):
        super(VCPButton, self).__init__(parent)
