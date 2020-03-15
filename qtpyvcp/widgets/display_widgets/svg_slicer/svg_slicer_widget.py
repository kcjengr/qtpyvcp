import sys
from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout
from qtpy.QtSvg import QSvgWidget, QSvgRenderer


import os


IN_DESIGNER = os.getenv('DESIGNER', False)


class SvgWidget(QSvgWidget):

    def __init__(self):
        super(SvgWidget, self).__init__()

        svg_str = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <svg width="300" height="300" viewBox="0 0 300 300" id="smile" version="1.1">
            <path
                style="fill:#ffaaaa"
                d="M 150,0 A 150,150 0 0 0 0,150 150,150 0 0 0 150,300 150,150 0 0 0 
                    300,150 150,150 0 0 0 150,0 Z M 72,65 A 21,29.5 0 0 1 93,94.33 
                    21,29.5 0 0 1 72,124 21,29.5 0 0 1 51,94.33 21,29.5 0 0 1 72,65 Z 
                    m 156,0 a 21,29.5 0 0 1 21,29.5 21,29.5 0 0 1 -21,29.5 21,29.5 0 0 1 
                    -21,-29.5 21,29.5 0 0 1 21,-29.5 z m -158.75,89.5 161.5,0 c 0,44.67 
                    -36.125,80.75 -80.75,80.75 -44.67,0 -80.75,-36.125 -80.75,-80.75 z"
            />
        </svg>
        """

        svg_bytes = bytearray(svg_str, encoding='utf-8')

        self.renderer().load(svg_bytes)
        self.setGeometry(100, 100, 300, 300)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SvgWidget()
    win.show()
    sys.exit(app.exec_())