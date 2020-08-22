

from qtpy.QtWidgets import QApplication, QSpinBox, QDoubleSpinBox, QAbstractButton

from qtpyvcp.app.launcher import _initialize_object_from_dict
from qtpyvcp.utilities.settings import setting
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import Plugin


from qtpyvcp import CONFIG

LOG = getLogger(__name__)


class VirtualInputManager(Plugin):
    def __init__(self):
        super(VirtualInputManager, self).__init__()

        self.input_providers = dict()
        self.active_vkb = None

    def activateVirtualInput(self, widget, input_type=None):
        """Activate VKB

        Args:
            widget (QWidget) : The widget for which the VKB should provide input.
            input_type (str) : The type of input that the VKB should provide.
                Input types are specified as either `text` or `number` input,
                with an optional sub-type separated by a colon. For example a
                entry that accepts integer input could request a VKB matching
                an input type of `number:int`. If a VKB does not exist for the
                requested input type the VKB for the base input type will be used.
                If `input_type` is not specified a suitable input type will be
                chosen based on the widget type.
        """

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

    def deactivateVirtualInput(self):
        if self.active_vkb is not None:
            self.active_vkb.hide()
            self.active_vkb = None

    def onFocusChanged(self, old_widget, new_widget):

        # hide any active VKBs
        self.deactivateVirtualInput()

        if new_widget is None or not self.enabled():
            return

        # request VKB for input type
        input_type = new_widget.property('virtualInputType')
        self.activateVirtualInput(new_widget, input_type)

    @setting('virtual-input.enable', False)
    def enabled(obj):
        return obj.value

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
