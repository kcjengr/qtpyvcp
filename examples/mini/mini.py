
from qtpy.QtCore import Slot

from qtpyvcp.widgets.form_widgets.main_window import VCPMainWindow

from qtpyvcp.actions import decorators

class MiniVCP(VCPMainWindow):
    """Main window class for the Mini example VCP."""
    def __init__(self, *args, **kwargs):
        super(MiniVCP, self).__init__(*args, **kwargs)

        self.setWindowTitle("Mini VCP")

    @Slot()
    def on_test_clicked(self):
        print decorators.issue_mdi.__dict__
        decorators.issue_mdi('testing')
