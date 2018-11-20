import os

from qtpy.QtCore import Property

from qtpyvcp.widgets.rules import registerRules
from qtpyvcp.utilities.status import Status, StatusItem


class QtPyVCPBaseWidget(object):
    """QtPyVCP Base Widget.

    Base class on which all QtPyVCP widgets are based.
    """

    STATUS = Status()

    IN_DESIGNER = os.getenv('DESIGNER') != None

    DEFAULT_RULE_PROPERTY = 'None'
    RULE_PROPERTIES = {
        'None': ['None', None],
        'Enable': ['setEnabled', bool],
        'Visible': ['setVisible', bool],
        # 'Opacity': ['setOpacity', float]
    }

    def __init__(self, parent=None):
        super(QtPyVCPBaseWidget, self).__init__()
        self._rules = ''
        self._data_channels = []

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
        registerRules(self, rules)

class VCPWidget(QtPyVCPBaseWidget):
    def __init__(self, parent=None):
        super(VCPWidget, self).__init__()

class CMDWidget(QtPyVCPBaseWidget):
    def __init__(self, parent=None):
        super(CMDWidget, self).__init__()

class HALWidget(QtPyVCPBaseWidget):
    def __init__(self, parent=None):
        super(HALWidget, self).__init__()
