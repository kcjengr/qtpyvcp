"""Homing Menu Provider"""

import linuxcnc
from qtpy.QtWidgets import QMenu, QAction

from qtpyvcp import actions
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.info import Info

INFO = Info()


class HomingMenu(QMenu):
    """Homing Menu Provider

    Args:
        parent (QWidget, optional) : The menus parent. Default to None.
        axes (list, optional) : List of axes for which to show a homing action.
            If not specified the axis letter list from the INI file will be used.

    ToDO:
        Add un-homing actions if the axis is already homed.
    """
    def __init__(self, parent=None, axes=None):
        super(HomingMenu, self).__init__(parent)

        self.status = getPlugin('status')

        home_all = QAction(parent=self, text="Home &All")
        actions.bindWidget(home_all, 'machine.home.all')
        self.addAction(home_all)

        # add homing actions for each axis
        for aletter in axes or INFO.AXIS_LETTER_LIST:
            home_axis = QAction(parent=self,
                                text="Home &{}".format(aletter.upper()))
            actions.bindWidget(home_axis, 'machine.home.axis:{}'.format(aletter.lower()))
            self.addAction(home_axis)
            home_axis.setVisible(True)

        self.setEnabled(self.status.stat.state == linuxcnc.STATE_ON)
        self.status.task_state.valueChanged.connect(lambda s:
                                      self.setEnabled(s == linuxcnc.STATE_ON))
