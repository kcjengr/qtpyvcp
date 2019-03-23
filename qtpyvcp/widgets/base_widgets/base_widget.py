"""
Base Widgets
------------

This file contains the definitions of the fundamental widgets upon which
all other QtPyVCP widgets are based.
"""

import os
import json
import inspect

from qtpy.QtCore import Property
from qtpy.QtWidgets import QPushButton

from qtpyvcp import SETTINGS
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.utilities.settings import Setting

LOG = getLogger(__name__)


class WidgetSetting(object):
    def __init__(self, parent, name, signal):
        self.parent = parent
        self.signal = signal
        self.name = name


class VCPProperty(Property):
    def __init__(self, type=bool, persistent=True, *args, **kwargs):
        super(VCPProperty, self).__init__(type, *args, user=True, **kwargs)

    def setValue(self, value):
        self.parent.setProperty(self.name, value)

    def getValue(self):
        return self.parent.property(self.name)

    def notify(self, slot):
        self.signal.connect(slot)

    def __getattribute__(self, item):
        print "Gettater", item
        return super(VCPProperty, self).getter(item)


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
    This class handles the rules and other things that
    apply to all QtPyVCP widgets regardless of use.
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
        super(QtPyVCPBaseWidget, self).__init__()
        self._rules = '[]'
        self._style = ''
        self._data_channels = []

        # self.objectNameChanged.connect(self.registerSettings)

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
        self._rules = rules
        # self.registerRules(rules)

    def registerSettings(self):

        if self.objectName() is None:
            return

        meta = self.metaObject()
        for i in range(meta.propertyCount()):
            prop = meta.property(i)
            if prop.isUser():
                # print prop
                # print "sig", prop.hasNotifySignal(), prop.notifySignal().name()
                # print prop.name(), prop.read(self), prop.typeName()
                # print dir(prop)
                SETTINGS['{}.{}'.format(self.objectName(), prop.name())] = WidgetSetting(self, prop.name(), getattr(self, str(prop.notifySignal().name())))

    def registerRules(self):
        rules = json.loads(self._rules)
        for rule in rules:
            # print rule
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
                            prop[0], rule['expression'].encode('utf-8'))
            exp = eval(eval_exp, eval_env)

            # initial call to update
            try:
                exp()
            except:
                LOG.exception('Error calling rules expression:')
                continue

            for trigger in triggers:
                trigger(exp)

    def initialize(self):
        pass

    def terminate(self):
        pass


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
    that control the machine. Eventually additional functionality
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
