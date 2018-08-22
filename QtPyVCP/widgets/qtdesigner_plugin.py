print "Loading Custom VCP QtDesigner Plug-ins"

from PyQt5.QtWidgets import QApplication
from QtPyVCP.core import Status, Action, Prefs, Info

app = QApplication.instance()
app.status = Status()
app.action = Action()
app.prefs = Prefs()
app.info = Info()

from QtPyVCP.widgets.form_widgets.designer_plugins import *
from QtPyVCP.widgets.button_widgets.designer_plugins import *
from QtPyVCP.widgets.display_widgets.designer_plugins import *
from QtPyVCP.widgets.input_widgets.designer_plugins import *
from QtPyVCP.widgets.hal_widgets.designer_plugins import *
