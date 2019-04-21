#!/usr/bin/env python

import os

from qtpyvcp.utilities import logger
from qtpyvcp.widgets.form_widgets.main_window import VCPMainWindow

import probe_basic_rc
#import nav_handler
#import probe_basic.nav_handler as nav_handler

LOG = logger.getLogger('QtPyVCP.' + __name__)

VCP_DIR = os.path.abspath(os.path.dirname(__file__))


class ProbeBasic(VCPMainWindow):
    """Main window class for the ProbeBasic VCP."""
    def __init__(self, *args, **kwargs):
        super(ProbeBasic, self).__init__(*args, **kwargs)
        #nav_handler.setupNav(self)


#nav_handler.py

from functools import partial

def setupNav(parent):
    parent.probetabGroup.buttonClicked.connect(partial(probetabChangePage, parent))

def probeChangePage(parent, button):
    parent.probe_tab_widget.setCurrentIndex(button.property('page'))
    if button.property('buttonName'):
        getattr(parent, button.property('buttonName')).setChecked(True)