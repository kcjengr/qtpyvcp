#   Copyright (c) 2018 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of QtPyVCP.
#
#   QtPyVCP is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   QtPyVCP is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with QtPyVCP.  If not, see <http://www.gnu.org/licenses/>.

import os
import math

from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Slot, Property
from PySide6.QtWidgets import QWidget, QBoxLayout, QSizePolicy

from qtpyvcp.utilities.info import Info
from qtpyvcp.actions.machine_actions import parseJogIncrement
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.settings import getSetting, setSetting
from qtpyvcp.widgets.button_widgets.led_button import LEDButton

IN_DESIGNER = os.getenv('DESIGNER', False)
if not IN_DESIGNER:
    STATUS = getPlugin('status')
INFO = Info()


class JogIncrementWidget(QWidget):

    def __init__(self, parent=None, standalone=False):
        super(JogIncrementWidget, self).__init__(parent)

        self._container = hBox = QBoxLayout(QBoxLayout.LeftToRight, self)

        hBox.setContentsMargins(0, 0, 0, 0)
        self._ledDiameter = 15
        self._ledColor = QColor('green')
        self._alignment = Qt.AlignTop | Qt.AlignRight
        self._buttons_by_value = []
        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None and not standalone:
            return

        increments = INFO.getIncrements()
        for increment in increments:
            button = LEDButton()

            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setFocusPolicy(Qt.NoFocus)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.setMinimumSize(50, 42)

            if increment != 0:
                raw_increment = increment.strip()
                button.setText(raw_increment)
                button.clicked.connect(self.setJogIncrement)

                parsed_increment = parseJogIncrement(raw_increment)
                self._buttons_by_value.append((button, parsed_increment))

                hBox.addWidget(button)

            self._sync_checked_button_with_setting()
        self.placeLed()

    def setJogIncrement(self):
        setSetting('machine.jog.increment', self.sender().text())

    def _sync_checked_button_with_setting(self):
        if len(self._buttons_by_value) == 0:
            return

        setting = getSetting('machine.jog.increment')
        if setting is None:
            self._buttons_by_value[0][0].setDefault(True)
            self._buttons_by_value[0][0].setChecked(True)
            return

        active_increment = parseJogIncrement(setting.getValue())

        selected_button = None
        for button, button_increment in self._buttons_by_value:
            if math.isclose(button_increment, active_increment, rel_tol=1e-9, abs_tol=1e-9):
                selected_button = button
                break

        if selected_button is None:
            selected_button = self._buttons_by_value[0][0]

        selected_button.setDefault(True)
        selected_button.setChecked(True)

    def layoutWidgets(self, layout):
        return (layout.itemAt(i) for i in range(layout.count()))

    def placeLed(self):
        for w in self.layoutWidgets(self._container):
            w.widget().setLedDiameter(self._ledDiameter)
            w.widget().setLedColor(self._ledColor)
            w.widget().setAlignment(self._alignment)

    def getLedDiameter(self):
        return self._ledDiameter

    @Slot(int)
    def setLedDiameter(self, value):
        self._ledDiameter = value
        self.placeLed()

    def getLedColor(self):
        return self._ledColor

    @Slot(QColor)
    def setLedColor(self, value):
        self._ledColor = value
        self.placeLed()

    def getAlignment(self):
        return self._alignment

    @Slot(Qt.Alignment)
    def setAlignment(self, value):
        self._alignment = Qt.Alignment(value)
        self.placeLed()

    def getOrientation(self):
        if self._container.direction() == QBoxLayout.LeftToRight:
            return Qt.Horizontal
        else:
            return Qt.Vertical

    @Slot(Qt.Orientation)
    def setOrientation(self, value):
        if value == Qt.Horizontal:
            self._container.setDirection(QBoxLayout.LeftToRight)
        else:
            self._container.setDirection(QBoxLayout.TopToBottom)
        self.adjustSize()

    def getLayoutSpacing(self):
        return self._container.spacing()

    @Slot(int)
    def setLayoutSpacing(self, value):
        self._container.setSpacing(value)

    diameter = Property(int, getLedDiameter, setLedDiameter)
    color = Property(QColor, getLedColor, setLedColor)
    alignment = Property(Qt.Alignment, getAlignment, setAlignment)
    orientation = Property(Qt.Orientation, getOrientation, setOrientation)
    layoutSpacing = Property(int, getLayoutSpacing, setLayoutSpacing)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = JogIncrementWidget(standalone=True)
    w.show()
    sys.exit(app.exec_())
