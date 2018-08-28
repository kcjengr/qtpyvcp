import sys
if (sys.version_info > (3, 0)):
    print("ERROR: It appears QtDesigner is trying to load the QtPyVCP widgets \n"
            "using a python version greater than 2.7, this is not supported. \n"
            "Make sure that you have the correct version of the libpyqt5.so \n"
            "file in /usr/lib/x86_64-linux-gnu/qt5/plugins/designer/, see the \n"
            "QtDesigner Plugins section of the QtPyVCP README for more info.")
    sys.exit()

from QtPyVCP.widgets.form_widgets.designer_plugins import *
from QtPyVCP.widgets.button_widgets.designer_plugins import *
from QtPyVCP.widgets.display_widgets.designer_plugins import *
from QtPyVCP.widgets.input_widgets.designer_plugins import *
from QtPyVCP.widgets.hal_widgets.designer_plugins import *
