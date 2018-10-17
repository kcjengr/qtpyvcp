import os
import sys
if (sys.version_info > (3, 0)):
    print("ERROR: It appears QtDesigner is trying to load the QtPyVCP widgets \n"
            "using a python version greater than 2.7, this is not supported. \n"
            "Make sure that you have the correct version of the libpyqt5.so \n"
            "file in /usr/lib/x86_64-linux-gnu/qt5/plugins/designer/, see the \n"
            "QtDesigner Plugins section of the QtPyVCP README for more info.")
    sys.exit()

import qtpy
if qtpy.API != 'pyqt5':
    print("ERROR: You must use the PyQt5 bindings in order to use the custom \n"
            "widgets in QtDesigner.")
    sys.exit()

os.environ['DESIGNER'] = 'true'

from qtpyvcp.widgets.form_widgets.designer_plugins import *
from qtpyvcp.widgets.button_widgets.designer_plugins import *
from qtpyvcp.widgets.display_widgets.designer_plugins import *
from qtpyvcp.widgets.input_widgets.designer_plugins import *
from qtpyvcp.widgets.hal_widgets.designer_plugins import *
