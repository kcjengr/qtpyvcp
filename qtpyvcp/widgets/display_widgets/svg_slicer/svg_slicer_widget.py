import sys
from xml.dom import minidom

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout
from qtpy.QtSvg import QSvgWidget, QSvgRenderer


import os

from qtpyvcp.plugins import getPlugin

STATUS = getPlugin('status')


IN_DESIGNER = os.getenv('DESIGNER', False)


class SvgWidget(QSvgWidget):

    def __init__(self, parent=None):
        super(SvgWidget, self).__init__(parent)

        self.status = STATUS

        self._svg_header = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN" "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd">
<svg width="23.838" height="23.838" xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:slic3r="http://slic3r.org/namespaces/slic3r">
"""
        self._svg_end = "</svg>"
        self._current_layer = 0

        self._file_name = ""
        self._layers = None

        self.status.file.notify(self.load_file)
        
        self.setGeometry(100, 100, 300, 300)

    def get_layers(self):
        xmldoc = minidom.parse(self._file_name)

        assert isinstance(xmldoc, minidom.Document)

        _layers = []
        for node in xmldoc.getElementsByTagName('g'):
            _layers.append(node)

        return _layers

    def select_layers(self):
        xmldoc = minidom.parse(self._file_name)

        assert isinstance(xmldoc, minidom.Document)

        svg_data = None

        # for all group nodes...
        for node in xmldoc.getElementsByTagName('g'):
            if int(node.attributes['id'].value.lstrip('layer')) == self._current_layer:
                svg_data = node.toxml()
                break

        return svg_data

    def load_file(self, file_name):
        self._file_name = file_name
        self._layers = self.get_layers()

        layer = self.select_layers()

        svg_file = "{}{}\n{}".format(self._svg_header, layer, self._svg_end)

        svg_bytes = bytearray(svg_file, encoding='utf-8')
        # self.renderer().load(svg_bytes)

    @Slot(int)
    def selectLayer(self, layer):
        self._current_layer = layer
        layer = self.select_layers()

        svg_file = "{}{}\n{}".format(self._svg_header, layer, self._svg_end)

        svg_bytes = bytearray(svg_file, encoding='utf-8')
        self.renderer().load(svg_bytes)
