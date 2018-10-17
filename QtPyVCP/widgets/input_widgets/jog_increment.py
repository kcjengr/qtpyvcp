#!/usr/bin/env python

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

from qtpy import uic
from qtpy.QtCore import Qt, QEvent, Slot, Property
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QWidget, QBoxLayout, QSizePolicy
from qtpyvcp.core import Status, Action, Info
from qtpyvcp.widgets.button_widgets.led_button import LEDButton

STATUS = Status()
ACTION = Action()
INFO = Info()

WIDGET_PATH = os.path.dirname(os.path.abspath(__file__))

class JogIncrementWidget(QWidget):

    def __init__(self, parent=None, standalone=False):
        super(JogIncrementWidget, self).__init__(parent)

        self._container = hBox = QBoxLayout(QBoxLayout.LeftToRight, self)

        hBox.setContentsMargins(0, 0, 0, 0)
        self._ledDiameter = 15
        self._ledColor = QColor('green')
        self._alignment = Qt.AlignTop | Qt.AlignRight
        # This prevents doing unneeded initialization
        # when QtDesginer loads the plugin.
        if parent is None and not standalone:
            return

        increments = INFO.getIncrements()
        for increment in increments:
            button = LEDButton()
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.setMinimumSize(50, 42)

            if increment != 0:
                raw_increment = increment.strip()
                # print '[', raw_increment, ']'
                button.setText(raw_increment)
                button.clicked.connect(self.setJogIncrement)
                hBox.addWidget(button)
        self.placeLed()

    def setJogIncrement(self):
        STATUS.setJogIncrement(self.sender().text())

    def layout_widgets(self, layout):
        return (layout.itemAt(i) for i in range(layout.count()))

    def placeLed(self):
        for w in self.layout_widgets(self._container):
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
    from qtpy.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = JogIncrementWidget(standalone=True)
    w.show()
    sys.exit(app.exec_())
