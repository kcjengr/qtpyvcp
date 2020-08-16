

from qtpy.QtWidgets import QApplication, QSpinBox, QDoubleSpinBox, QAbstractButton

from qtpyvcp.app.launcher import _initialize_object_from_dict
from qtpyvcp.utilities.settings import getSetting
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import Plugin


from qtpyvcp import CONFIG

LOG = getLogger(__name__)


class VirtualInputManager(Plugin):
    def __init__(self):
        super(VirtualInputManager, self).__init__()

        self.input_providers = dict()
        self.active_vkb = None
        self.enabled = False

    def activateVKB(self, widget, input_type=None):

        if input_type is None:
            # determine input type from widget type
            if isinstance(widget, QSpinBox):
                input_type = 'number:int'

            elif isinstance(widget, QDoubleSpinBox):
                input_type = 'number:float'

            elif not isinstance(widget, QAbstractButton) and hasattr(widget, 'text') and hasattr(widget, 'setText'):
                if hasattr(widget, 'isReadOnly') and widget.isReadOnly():
                    return
                try:
                    float(widget.text())
                    input_type = 'number:float'
                except Exception:
                    input_type = 'text:gcode'

            else:
                return

        try:
            vkb = self.input_providers[input_type]
        except KeyError:
            vkb = self.input_providers.get(input_type.split(':')[0])

        if input_type is None:
            return

        vkb.activate(widget)
        self.active_vkb = vkb

    def deactivateVKB(self):
        if self.active_vkb is not None:
            self.active_vkb.hide()
            self.active_vkb = None

    def onFocusChanged(self, old_widget, new_widget):

        # hide any active VKBs
        self.deactivateVKB()

        if new_widget is None or not self.enabled:
            return

        # show requested VKB type
        input_type = new_widget.property('inputType')
        self.activateVKB(new_widget, input_type)

    def onEnabledStateChanged(self, enabled):
        self.enabled = enabled

    def initialise(self):

        virtual_input_providers = CONFIG.get("virtual_input_providers", {})

        for input_type, provider in virtual_input_providers.items():
            obj = _initialize_object_from_dict(provider)
            input_type = input_type.replace('.', ':')
            self.input_providers[input_type] = obj

        app = QApplication.instance()
        app.focusChanged.connect(self.onFocusChanged)

        for vkb in self.input_providers.values():
            vkb.hide()

        vkb_setting = getSetting('virtual_input.enabled')
        self.enabled = vkb_setting.value
        vkb_setting.notify(self.onEnabledStateChanged)
