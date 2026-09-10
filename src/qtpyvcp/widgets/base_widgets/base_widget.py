"""
Base Widgets
------------

This file contains the definitions of the fundamental widgets upon which
all other QtPyVCP widgets are based.
"""

import os
import json

from PySide6.QtCore import Qt,Property, Slot, QTimer, QEnum
from enum import Enum
from PySide6.QtWidgets import QPushButton

from qtpyvcp import hal as qhal
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.utilities.machine_parameters import (
    read_parameter_values,
    get_parameter_value,
)

IN_DESIGNER = os.getenv('DESIGNER', False)

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


# Style classes in use across probe_basic and qtpyvcp. Declared as a QEnum so
# QtDesigner offers a drop-down rather than a free-text field. `none` disables
# flashing; the setter also accepts a plain string, so a class name outside
# this list can still be set from Python or a hand-edited .ui.
@QEnum
class FlashStyleClass(Enum):
    none = 0
    active = 1
    inactive = 2
    unhomed = 3
    homing = 4


FLASH_STYLE_NAMES = {0: '', 1: 'active', 2: 'inactive', 3: 'unhomed', 4: 'homing'}


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
        'Flashing': ['setFlashing', bool],
    }

    def __init__(self, parent=None):
        super(VCPBaseWidget, self).__init__()
        self._rules = '[]'
        self._style = ''
        self._data_channels = []
        self._security_level = 0
        # Flashing. The timer is created on first use, not here -- every
        # widget in a VCP inherits this class, and a QTimer each for the
        # ones that never flash is pure overhead.
        self._flash_timer = None
        self._flash_rate = 500
        self._flash_state = True
        self._flash_on_style = ''
        # self._hal_param_enable = False
        # self._hal_param_name = None
        # self._hal_param_type = "s32"
        # self._hal_param_access = "rw"
        
        
    # def postInitialize(self):
    #
    #     if self.enableHalParams:
    #         comp = qhal.getComponent("qtpyvcp")
    #         comp.addParam(self.halParamName, self.halParamType, self.halParamAccess)

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
    # Pparameter implementation ( Disabled for now )
    #

    # @Property(bool)
    # def enableHalParams(self):
    #     return self._hal_param_enable
    #
    # @enableHalParams.setter
    # def enableHalParams(self, enabled):
    #     self._hal_param_enable = enabled
    #
    # ###
    #
    # @Property(str)
    # def halParamName(self):
    #     if self._hal_param_name is None:
    #         return str(self.objectName()).replace('-', '_')
    #     return self._hal_param_name
    #
    # @halParamName.setter
    # def halParamName(self, name):
    #     self._hal_param_name = name
    #
    # ###
    #
    # @Property(str)
    # def halParamType(self):
    #     return self._hal_param_type
    #
    # @halParamType.setter
    # def halParamType(self, param_type):
    #     self._hal_param_type = param_type
    #
    # ###
    #
    # @Property(str)
    # def halParamAccess(self):
    #     return self._hal_param_access
    #
    # @halParamAccess.setter
    # def halParamAccess(self, param_access):
    #     self._hal_param_access = param_access
    
    def action_event(self, instance, value):
        print(instance)
        print(value)
        super().action_event(instance, value)
    
    #
    # Style Rules implementation
    #

    # ---------------------------------------------------------- flashing

    def _setFlashState(self, on):
        """Alternate the `flashState` dynamic property and repolish.

        The widget's own state is never touched -- toggling `checked` or
        `enabled` would fight whatever else drives them -- so the stylesheet
        selects on this instead::

            QPushButton[style="active"][flashState="false"] { ... }
        """
        self._flash_state = bool(on)
        self.setProperty('flashState', 'true' if on else 'false')
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)

    def _toggleFlashState(self):
        self._setFlashState(not self._flash_state)

    @Slot(bool)
    def setFlashing(self, flashing):
        """Start or stop flashing.

        Exposed as the `Flashing` rule property, so any channel expression
        can drive it. Re-asserting a flash that is already running is a
        no-op: rules re-evaluate on every channel update, and restarting the
        timer each time would leave the flash stuttering.
        """
        if flashing:
            if self._flash_timer is None:
                self._flash_timer = QTimer(self)
                self._flash_timer.timeout.connect(self._toggleFlashState)
            if not self._flash_timer.isActive():
                self._setFlashState(True)
                self._flash_timer.start(self._flash_rate)
        else:
            if self._flash_timer is not None:
                self._flash_timer.stop()
            # Always settle on the lit half, so a stopped flash never leaves
            # the widget stuck in its dim state.
            if not self._flash_state:
                self._setFlashState(True)

    def isFlashing(self):
        return self._flash_timer is not None and self._flash_timer.isActive()

    def _updateStyleFlash(self):
        """Start or stop flashing to match flashOnStyleClass."""
        if self._flash_on_style:
            self.setFlashing(self._style == self._flash_on_style)

    @Property(str)
    def flashOnStyleClass(self):
        """Flash whenever the widget's style class equals this value.

        Lets a widget flash on a condition something else already reports.
        The cycle start button, for example, is driven to style class
        `active` by a rule when the program is paused, so setting this to
        `active` makes it flash while paused with no second rule.

        Leave empty to disable. The flash itself is still available directly
        via the `Flashing` rule property.

        Returns:
            str
        """
        return self._flash_on_style

    @flashOnStyleClass.setter
    def flashOnStyleClass(self, style_class):
        if isinstance(style_class, FlashStyleClass):
            name = FLASH_STYLE_NAMES.get(style_class.value, '')
        elif isinstance(style_class, int):
            name = FLASH_STYLE_NAMES.get(style_class, '')
        else:
            name = str(style_class or '').strip()
        self._flash_on_style = name
        if self._flash_on_style:
            self._updateStyleFlash()
        else:
            self.setFlashing(False)

    @Property(int)
    def flashRate(self):
        """Flash half-period in milliseconds. Default 500.

        Returns:
            int
        """
        return self._flash_rate

    @flashRate.setter
    def flashRate(self, rate):
        self._flash_rate = max(50, int(rate))
        if self._flash_timer is not None and self._flash_timer.isActive():
            self._flash_timer.start(self._flash_rate)

    def setStyleClass(self, style_class):
        """Set the QSS style class for the widget.

        Sets the Qt dynamic property 'style' which can be used as a QSS
        selector:  WidgetClass[style="error"] { color: red; }
        """
        self._style = style_class
        self.setProperty('style', style_class)
        # Re-polish so QSS engine sees the property change
        self.style().unpolish(self)
        self.style().polish(self)
        self._updateStyleFlash()

    @Property(str, designable=False)
    def styleClass(self):
        """QSS style class selector property.

        This property can be changed dynamically to update the QSS style
        applied to the widget.  The underlying Qt dynamic property is named
        'style' so that QSS selectors like ``WidgetClass[style="error"]``
        continue to work unchanged.

        NOTE: This property is intentionally NOT named 'style' at the Python/
        Qt-meta level because that name shadows QWidget::style() (which returns
        the QStyle object), causing a segfault when Qt internally calls it.

        Example::

            /* Applied when styleClass / dynamic property 'style' == "error" */
            WidgetClass[style="error"] {
                color: red;
            }

            /* Applied when 'style' is not set */
            WidgetClass {
                color: black;
            }

        Returns:
            str
        """
        return self._style

    @styleClass.setter
    def styleClass(self, style):
        self.setStyleClass(style)

    @Property(str, designable=True, stored=True)
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
        params = read_parameter_values()
        # Read fresh parameter values each evaluation so rule expressions react
        # to runtime .var changes (ATC pocket updates, etc.).
        param = lambda number, default=0.0: get_parameter_value(read_parameter_values(), number, default)
        for rule in rules:
            # print(rule)
            ch = ChanList()
            triggers = []
            if IN_DESIGNER:
                return
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

            eval_env = {
                'ch': ch,
                'widget': self,
                'params': params,
                'param': param,
            }
            eval_exp = 'lambda: widget.{}({})'.format(
                            prop[0], rule['expression']).encode('utf-8')
            exp = eval(eval_exp, eval_env)

            widget_name = self.objectName()
            rule_name = rule.get('name', '<unnamed rule>')

            # Rules are compiled as zero-arg lambdas, but channel notifications
            # may pass payload args. Accept and ignore payload args so callbacks
            # stay stable across signal signatures.
            # NOTE: Keep per-rule callback binding here to avoid loop-scope
            # expression bleed regressions (see report around b1b5419f298e).
            def _make_rule_callback(exp_cb, cb_rule_name, cb_widget_name):
                def _rule_callback(*_args, **_kwargs):
                    try:
                        exp_cb()
                    except Exception:
                        LOG.exception(
                            "Error calling rules expression '%s' from %s:",
                            cb_rule_name,
                            cb_widget_name,
                        )
                return _rule_callback

            _rule_callback = _make_rule_callback(exp, rule_name, widget_name)

            # initial call to update
            _rule_callback()

            for trigger in triggers:
                trigger(_rule_callback)


class VCPWidget(VCPBaseWidget):
    """VCP Widget

    This is a general purpose widget for displaying data
    and other uses that do not involve user interaction.
    """
    def __init__(self, parent=None):
        super(VCPWidget, self).__init__()
        # Logically no focus policy here should be correct.
        # Risk is that VCPWidget maybe used as the base for
        # widgets that DO expect user interaction. So below would be a
        # breaking change until some cleaning is done. Test it?
        # Causes issue under pyside6 with runtime error
        #self.setFocusPolicy(Qt.NoFocus)


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
        self.status = getPlugin('status')
        # stop focus that will interfere with keyboard jog
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def mousePressEvent(self, event):
        # Test for UI LOCK and consume event but do nothing if LOCK in place
        if self.status.isLocked():
            LOG.debug('Accept mouse Press Event')
            event.accept()
            return 
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.status.isLocked():
            LOG.debug('Accept mouse Release Event')
            event.accept()
            return 
        super().mouseReleaseEvent(event)

