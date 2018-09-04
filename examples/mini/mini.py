import os
from QtPyVCP.widgets.form_widgets.main_window import VCPMainWindow

VCP_DIR = os.path.abspath(os.path.dirname(__file__))

class MiniVCP(VCPMainWindow):
    """Main window class for the Mini VCP."""
    def __init__(self, *args, **kwargs):
        super(MiniVCP, self).__init__(*args, **kwargs)

        ui_file = os.path.join(VCP_DIR, 'mini.ui')
        self.loadUi(ui_file) # load the UI file
        self.initUi()        # initialize menu actions etc.

def main():
    import sys
    from QtPyVCP.application import VCPApplication
    app = VCPApplication(ini=sys.argv[1])
    app.window = MiniVCP()
    app.window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
