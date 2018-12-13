#!/usr/bin/env python

from qtpy.QtWidgets import QPushButton
from qtpy.QtCore import Qt, Slot, Property, QSize
from qtpy.QtGui import QColor

from qtpyvcp.widgets.button_widgets.action_button import ActionButton

from qtpyvcp.widgets.base_widgets.led_widget import LEDWidget


class LEDButton(ActionButton):

    DEFAULT_RULE_PROPERTY = 'Enable'

    RULE_PROPERTIES = {
        'Enable': ['setEnabled', bool],
        'Visible': ['setVisible', bool],
        'Opacity': ['setOpacity', float],
        'Text': ['setText', str],
        'LED On': ['setLedState', bool],
        'LED Flashing': ['setLedFlashing', bool]
    }

    def __init__(self, parent=None):
        super(LEDButton, self).__init__(parent)

        self._alignment = Qt.AlignRight | Qt.AlignTop
        self.led = LEDWidget(self)
        self.led.setDiameter(14)
        self.placeLed()

    def placeLed(self):
        x = 0
        y = 0
        alignment = self._alignment
        ledDiameter = self.led.getDiameter()
        halfLed = ledDiameter / 2
        quarterLed = ledDiameter / 4 # cheap hueristic to avoid borders

        if alignment & Qt.AlignLeft:
            x = quarterLed
        elif alignment & Qt.AlignRight:
            x = self.width() - ledDiameter - quarterLed
        elif alignment & Qt.AlignHCenter:
            x = (self.width()/2) - halfLed
        elif alignment & Qt.AlignJustify:
            x = 0

        if alignment & Qt.AlignTop:
            y = quarterLed
        elif alignment & Qt.AlignBottom:
            y = self.height() - ledDiameter - quarterLed
        elif alignment & Qt.AlignVCenter:
            y = self.height()/2 - halfLed
        # print x, y
        self.led.move(x, y)
        self.updateGeometry()

    def resizeEvent(self, event):
        self.placeLed()

    def update(self):
        # self.placeLed()
        # super(LEDButton, self).update()
        pass

    def sizeHint( self ):
        return QSize(80, 30)

    @Slot(bool)
    def setLedState(self, state):
        self.led.setState(state)

    @Slot(bool)
    def setLedFlashing(self, flashing):
        self.led.setFlashing(flashing)

    def getLedDiameter(self):
        return self.led.getDiameter()

    @Slot(int)
    def setLedDiameter(self, value):
        self.led.setDiameter(value)
        self.placeLed()

    def getLedColor(self):
        return self.led.getColor()

    @Slot(QColor)
    def setLedColor(self, value):
        self.led.setColor(value)

    def getAlignment(self):
        return self._alignment

    @Slot(Qt.Alignment)
    def setAlignment(self, value):
        self._alignment = Qt.Alignment(value)
        self.update()

    diameter = Property(int, getLedDiameter, setLedDiameter)
    color = Property(QColor, getLedColor, setLedColor)
    alignment = Property(Qt.Alignment, getAlignment, setAlignment)
