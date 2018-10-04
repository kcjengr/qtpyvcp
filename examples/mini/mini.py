import os
from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

VCP_DIR = os.path.abspath(os.path.dirname(__file__))
UI_FILE = os.path.join(VCP_DIR, 'mini.ui')

class MiniVCP(VCPMainWindow):
    """Main window class for the Mini example VCP."""
    def __init__(self, *args, **kwargs):
        super(MiniVCP, self).__init__(*args, **kwargs)

        self.loadUi(UI_FILE)
        self.initUi()

        self.setWindowTitle("Mini VCP")
