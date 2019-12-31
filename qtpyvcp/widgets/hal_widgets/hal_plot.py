
import os

from qtpy.QtGui import QColor
from qtpy.QtWidgets import *
from qtpy.QtCore import Property, Signal, Slot, QTime, QTimer, Qt
from collections import deque

import pyqtgraph as pg
import numpy as np

from qtpyvcp import hal
from qtpyvcp.widgets import HALWidget

IN_DESIGNER = os.getenv('DESIGNER', False)


class TimeAxisItem(pg.AxisItem):
    """Internal timestamp for x-axis"""
    def __init__(self, *args, **kwargs):
        super(TimeAxisItem, self).__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        """Function overloading the weak default version to provide timestamp"""
        return [QTime().currentTime().addMSecs(value).toString('mm:ss') for value in values]


class HalPlot(QWidget, HALWidget):
    """HAL Plot

    Plot for displaying HAL pin values.

    Input pin type is HAL type ( float).

    Up to four HAL pin values can be plotted

    .. table:: Generated HAL Pins

        ========================= =========== =========
        HAL Pin Name              Type        Direction
        ========================= =========== =========
        qtpyvcp.seriesXname.in     float          in
        ========================= =========== =========
    """

    def __init__(self, parent=None):
        super(HalPlot, self).__init__(parent)

        # HAL sampling frequency parameters
        self._frequency = 1       # Hz
        self._timeWindow = 600      # seconds

        # Internal timestamp for x-axis - data values are ms from when "timestamp" was started
        self.timestamp = QTime()
        self.timestamp.start()

        self._legend = False

        self._yAxisLabel = 'y label'
        self._yAxisUnits = 'y units'
        self._minY = 0
        self._maxY = 1

        self._s1enable = True
        self._s1name = "Series 1"
        self._s1colour = QColor('red')
        self._s1width = 1
        self._s1style = Qt.SolidLine
        self._s1_pin = None

        self._s2enable = False
        self._s2name = "Series 2"
        self._s2colour = QColor('blue')
        self._s2width = 1
        self._s2style = Qt.SolidLine
        self._s2_pin = None

        self._s3enable = False
        self._s3name = "Series 3"
        self._s3colour = QColor('green')
        self._s3width = 1
        self._s3style = Qt.SolidLine
        self._s3_pin = None

        self._s4enable = False
        self._s4name = "Series 4"
        self._s4colour = QColor('yellow')
        self._s4width = 1
        self._s4style = Qt.SolidLine
        self._s4_pin = None

        # PyQtGraph stuff
        self.graph = pg.GraphicsLayoutWidget()

        self.yAxis = pg.AxisItem(orientation='left')
        self.yAxis.setLabel(self._yAxisLabel, units=self._yAxisUnits)
        self.yAxis.setGrid(125)

        self.plot = self.graph.addPlot(axisItems={'bottom': TimeAxisItem(orientation='bottom'), 'left': self.yAxis})
        self.plot.setYRange(self._minY, self._maxY, padding=0.0)

        self.legend = self.plot.addLegend()

        self.p1 = pg.PlotCurveItem(name=self._s1name)
        self.p2 = pg.PlotCurveItem(name=self._s2name)
        self.p3 = pg.PlotCurveItem(name=self._s3name)
        self.p4 = pg.PlotCurveItem(name=self._s4name)

        self.setSeries()
        self.setData()

        self.Vlayout = QVBoxLayout(self)
        self.Vlayout.addWidget(self.graph)

        # HAL stuff
        self._typ = "float"
        self._fmt = "%s"

        if IN_DESIGNER:
            return

        # QTimer
        self.updatetimer = QTimer(self)
        self.updatetimer.timeout.connect(self.updateplot)
        self.updatetimer.start(self._refreshRate)

    def setSeries(self):
        # first remove the legend as it does not update correnctly
        try:
            self.legend.scene().removeItem(self.legend)
        except:
            pass

        # remove all plot items
        self.plot.clear()

        # add the legend and plot itmes
        if self._legend:
            self.legend = self.plot.addLegend()

        if self._s1enable:
            self.p1 = pg.PlotCurveItem(name=self._s1name)
            self.plot.addItem(self.p1)
            self.p1.setPen(QColor(self._s1colour), width=self._s1width, style=self._s1style)

        if self._s2enable:
            self.p2 = pg.PlotCurveItem(name=self._s2name)
            self.plot.addItem(self.p2)
            self.p2.setPen(QColor(self._s2colour), width=self._s2width, style=self._s2style)

        if self._s3enable:
            self.p3 = pg.PlotCurveItem(name=self._s3name)
            self.plot.addItem(self.p3)
            self.p3.setPen(QColor(self._s3colour), width=self._s3width, style=self._s3style)

        if self._s4enable:
            self.p4 = pg.PlotCurveItem(name=self._s4name)
            self.plot.addItem(self.p4)
            self.p4.setPen(QColor(self._s4colour), width=self._s4width, style=self._s4style)

    def setData(self):
        # Data stuff
        self._period = 1.0/self._frequency
        self._refreshRate = int(self._period * 1000)  # sample period in milliseconds
        self._timeWindowMS = self._timeWindow * 1000      # time window in milliseconds
        self._bufsize = int(self._timeWindowMS / self._refreshRate)

        # Data containers: collections.deque is list-like container with fast appends and pops on either end
        self.x = np.linspace(-self.timeWindow, 0.0, self._bufsize)
        self.now = self.timestamp.elapsed()
        self.x_data = deque(np.linspace(self.now-self._timeWindowMS, self.now, self._bufsize),self._bufsize)

        self.s1 = np.zeros(self._bufsize, dtype=np.float)
        self.s1_data = deque([0.0] * self._bufsize, self._bufsize)

        self.s2 = np.zeros(self._bufsize, dtype=np.float)
        self.s2_data = deque([0.0] * self._bufsize, self._bufsize)

        self.s3 = np.zeros(self._bufsize, dtype=np.float)
        self.s3_data = deque([0.0] * self._bufsize, self._bufsize)

        self.s4 = np.zeros(self._bufsize, dtype=np.float)
        self.s4_data = deque([0.0] * self._bufsize, self._bufsize)

    def updateplot(self):
        self.x_data.append(self.timestamp.elapsed())
        self.x[:] = self.x_data

        if self._s1enable:
            self.s1_data.append(self._s1_pin.value)
            self.s1[:] = self.s1_data
            self.p1.setData(self.x, self.s1)

        if self._s2enable:
            self.s2_data.append(self._s2_pin.value)
            self.s2[:] = self.s2_data
            self.p2.setData(self.x, self.s2)

        if self._s3enable:
            self.s3_data.append(self._s3_pin.value)
            self.s3[:] = self.s3_data
            self.p3.setData(self.x, self.s3)

        if self._s4enable:
            self.s4_data.append(self._s4_pin.value)
            self.s4[:] = self.s4_data
            self.p4.setData(self.x, self.s4)

    def setyAxis(self):
        self.yAxis.setLabel(self._yAxisLabel, units=self._yAxisUnits)

    def setYRange(self):
        self.plot.setYRange(self._minY, self._maxY, padding = 0.0)



    @Property(int)
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, frequency):
        self._frequency = frequency
        return self.setData()

    @Property(int)
    def timeWindow(self):
        return self._timeWindow

    @timeWindow.setter
    def timeWindow(self, timeWindow):
        self._timeWindow = timeWindow
        return self.setData()

    @Property(str)
    def yAxisLabel(self):
        return self._yAxisLabel

    @yAxisLabel.setter
    def yAxisLabel(self, yAxisLabel):
        self._yAxisLabel = yAxisLabel
        return self.setyAxis()

    @Property(str)
    def yAxisUnits(self):
        return self._yAxisUnits

    @yAxisUnits.setter
    def yAxisUnits(self, yAxisUnits):
        self._yAxisUnits = yAxisUnits
        return self.setyAxis()

    @Property(float)
    def minYRange(self):
        return self._minY

    @minYRange.setter
    def minYRange(self, minY):
        self._minY = minY
        return self.setYRange()

    @Property(float)
    def maxYRange(self):
        return self._maxY

    @maxYRange.setter
    def maxYRange(self, maxY):
        self._maxY = maxY
        return self.setYRange()


    # Legend propterties
    @Property(bool)
    def legendenable(self):
        return self._legend

    @legendenable.setter
    def legendenable(self, legendenable):
        self._legend = legendenable
        self.setSeries()


    # Series 1 properties
    @Property(bool)
    def series1enable(self):
        return self._s1enable

    @series1enable.setter
    def series1enable(self, series1enable):
        self._s1enable = series1enable
        self.setSeries()

    @Property(str)
    def series1name(self):
        return self._s1name

    @series1name.setter
    def series1name(self, series1name):
        self._s1name = series1name
        self.setSeries()

    @Property(QColor)
    def series1colour(self):
        return self._s1colour

    @series1colour.setter
    def series1colour(self, series1colour):
        self._s1colour = series1colour
        self.setSeries()

    @Property(int)
    def series1width(self):
        return self._s1width

    @series1width.setter
    def series1width(self, series1width):
        self._s1width = series1width
        self.setSeries()

    @Property(Qt.PenStyle)
    def series1style(self):
        return self._s1style

    @series1style.setter
    def series1style(self, series1style):
        self._s1style = series1style
        self.setSeries()


    # Series 2 properties
    @Property(bool)
    def series2enable(self):
        return self._s2enable

    @series2enable.setter
    def series2enable(self, series2enable):
        self._s2enable = series2enable
        self.setSeries()

    @Property(str)
    def series2name(self):
        return self._s2name

    @series2name.setter
    def series2name(self, series2name):
        self._s2name = series2name
        self.setSeries()

    @Property(QColor)
    def series2colour(self):
        return self._s2colour

    @series2colour.setter
    def series2colour(self, series2colour):
        self._s2colour = series2colour
        self.setSeries()

    @Property(int)
    def series2width(self):
        return self._s2width

    @series2width.setter
    def series2width(self, series2width):
        self._s2width = series2width
        self.setSeries()

    @Property(Qt.PenStyle)
    def series2style(self):
        return self._s2style

    @series2style.setter
    def series2style(self, series2style):
        self._s2style = series2style
        self.setSeries()


    # Series 3 properties
    @Property(bool)
    def series3enable(self):
        return self._s3enable

    @series3enable.setter
    def series3enable(self, series3enable):
        self._s3enable = series3enable
        self.setSeries()

    @Property(str)
    def series3name(self):
        return self._s3name

    @series3name.setter
    def series3name(self, series3name):
        self._s3name = series3name
        self.setSeries()

    @Property(QColor)
    def series3colour(self):
        return self._s3colour

    @series3colour.setter
    def series3colour(self, series3colour):
        self._s3colour = series3colour
        self.setSeries()

    @Property(int)
    def series3width(self):
        return self._s3width

    @series3width.setter
    def series3width(self, series3width):
        self._s3width = series3width
        self.setSeries()

    @Property(Qt.PenStyle)
    def series3style(self):
        return self._s3style

    @series3style.setter
    def series3style(self, series3style):
        self._s3style = series3style
        self.setSeries()


    # Series 4 properties
    @Property(bool)
    def series4enable(self):
        return self._s4enable

    @series4enable.setter
    def series4enable(self, series4enable):
        self._s4enable = series4enable
        self.setSeries()

    @Property(str)
    def series4name(self):
        return self._s4name

    @series4name.setter
    def series4name(self, series4name):
        self._s4name = series4name
        self.setSeries()

    @Property(QColor)
    def series4colour(self):
        return self._s4colour

    @series4colour.setter
    def series4colour(self, series4colour):
        self._s4colour = series4colour
        self.setSeries()

    @Property(int)
    def series4width(self):
        return self._s4width

    @series4width.setter
    def series4width(self, series4width):
        self._s4width = series4width
        self.setSeries()

    @Property(Qt.PenStyle)
    def series4style(self):
        return self._s4style

    @series4style.setter
    def series4style(self, series4style):
        self._s4style = series4style
        self.setSeries()


    def initialize(self):
        comp = hal.COMPONENTS['qtpyvcp']
        obj_name = str(self.objectName()).replace('_', '-')

        # add HAL pins
        if self._s1enable:
            self._s1_pin = comp.addPin(obj_name + "." + self._s1name.replace(' ', ''), self._typ, "in")

        if self._s2enable:
            self._s2_pin = comp.addPin(obj_name + "." + self._s2name.replace(' ', ''), self._typ, "in")

        if self._s3enable:
            self._s3_pin = comp.addPin(obj_name + "." + self._s3name.replace(' ', ''), self._typ, "in")

        if self._s4enable:
            self._s4_pin = comp.addPin(obj_name + "." + self._s4name.replace(' ', ''), self._typ, "in")
