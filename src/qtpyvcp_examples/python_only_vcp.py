from qtpyvcp.widgets.form_widgets.main_window import VCPMainWindow

class PythonOnlyVCP(VCPMainWindow):
    """Main window class for the python only VCP."""
    def __init__(self, *args, **kwargs):
        super(PythonOnlyVCP, self).__init__(*args, **kwargs)

        self.setWindowTitle("Python-only VCP")
