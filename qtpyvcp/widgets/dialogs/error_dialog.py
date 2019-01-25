import os
from traceback import format_exception

from qtpy import uic
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QDialog, QApplication

from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)

IGNORE_LIST = []

class ErrorDialog(QDialog):
    def __init__(self, exc_info):
        super(ErrorDialog, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'error_dialog.ui'), self)

        self.exc_info = exc_info
        exc_type, exc_msg, exc_tb = exc_info

        self.exc_typ = exc_type.__name__
        self.exc_msg = exc_msg
        self.exc_tb = "".join(format_exception(*exc_info))
        color = 'orange' if 'warning'in self.exc_typ.lower() else 'red'
        self.errorType.setText("<font color='{}'>{}:</font>"
                               .format(color, self.exc_typ))
        self.errorValue.setText(str(exc_msg))
        self.setWindowTitle('Unhandled Exception - {}'.format(self.exc_typ))
        self.tracebackText.setText(self.exc_tb)
        self.show()

    @Slot()
    def on_quitApp_clicked(self):
        if os.getenv('DESIGNER', False):
            self.accept()
        else:
            QApplication.exit()

    @Slot()
    def on_ignoreException_clicked(self):
        if self.ignoreCheckBox.isChecked():
            LOG.warn("User selected to ignore future occurrences of exception.",
                     exc_info=self.exc_info)
            IGNORE_LIST.append((str(self.exc_info[0]),
                                str(self.exc_info[1]),
                                self.exc_info[2].tb_lineno))
            print IGNORE_LIST
        self.accept()

    @Slot()
    def on_reportIssue_clicked(self):
        import qtpy
        import urllib
        import webbrowser
        import subprocess
        import linuxcnc
        # import hiyapyco
        import json
        import qtpyvcp
        issue_title = "{}: {}".format(self.exc_typ, self.exc_msg)
        issue_body = ISSUE_TEMPLATE.format(
            tracback=self.exc_tb.strip(),
            qt_version=qtpy.QT_VERSION,
            qt_api=qtpy.API_NAME,
            api_version=qtpy.PYQT_VERSION or qtpy.PYSIDE_VERSION,
            dist=subprocess.check_output(['lsb_release', '-d']).strip(),
            kernel=subprocess.check_output(['uname', '-r']).strip(),
            lcnc_version=linuxcnc.version,
            qtpyvcp_version=qtpyvcp.__version__,
            # config=hiyapyco.dump(qtpyvcp.CONFIG, default_flow_style=False),
            options=json.dumps(qtpyvcp.OPTIONS, indent=4, sort_keys=True),
            log_file=qtpyvcp.OPTIONS.get('log_file'),
            config_file=qtpyvcp.OPTIONS.get('config_file'),
            )


        new_issue_url = "https://github.com/kcjengr/qtpyvcp/issues/new?" \
                        "title={title}&body={body}&&labels=bug,auto+generated"\
                        .format(title=urllib.quote(issue_title),
                                body=urllib.quote(issue_body))

        webbrowser.open(new_issue_url, new=2, autoraise=True)


ISSUE_TEMPLATE = \
"""(Please fill in this issue template with as much information as you can about the 
circumstances under which the issue occurred, and the steps needed to reproduce it.)

## Steps to reproduce the problem

(provide as detailed a step by step as you can) 

 1.
 2.
 3.

## This is what I expected to happen

(explain what you thought should have happened)

## This is what happened instead

(explain what happened instead)

## It worked properly before this

(did it work before? what changed?)

## Traceback

```python
{tracback}
```

## Options

```json
{options}
```

## System Info
```
 * {dist}
 * Kernel: {kernel}
 * Qt version: v{qt_version}
 * Qt bindings: {qt_api} v{api_version}
 * LinuxCNC version: v{lcnc_version}
 * QtPyVCP version: {qtpyvcp_version}
```

## Attachments

Please also find and attach the following files, along with any others that may be helpful:
* {log_file}
* {config_file}
"""
