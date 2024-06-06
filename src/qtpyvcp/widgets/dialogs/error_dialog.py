import os
from traceback import format_exception

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Slot, QFile
from PySide6.QtWidgets import QDialog, QApplication

from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog

LOG = getLogger(__name__)

IGNORE_LIST = []


class ErrorDialog(BaseDialog):
    def __init__(self, exc_info):
        super(ErrorDialog, self).__init__(stay_on_top=True)
        
        file_path = os.path.join(os.path.dirname(__file__), 'error_dialog.ui')
        ui_file = QFile(file_path)
        ui_file.open(QFile.ReadOnly)
        
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        self.ui.show()

        self.exc_info = exc_info
        exc_type, exc_msg, exc_tb = exc_info

        self.exc_typ = exc_type.__name__
        self.exc_msg = exc_msg
        self.exc_tb = "".join(format_exception(*exc_info))
        color = 'orange' if 'warning'in self.exc_typ.lower() else 'red'
        self.ui.errorType.setText("<font color='{}'>{}:</font>"
                               .format(color, self.exc_typ))
        self.ui.errorValue.setText(str(exc_msg))
        self.ui.setWindowTitle('Unhandled Exception - {}'.format(self.exc_typ))
        self.ui.tracebackText.setText(self.exc_tb)
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
            print(IGNORE_LIST)
        self.accept()

    @Slot()
    def on_reportIssue_clicked(self):
        import PySide6
        import urllib.request, urllib.parse, urllib.error
        import webbrowser
        import subprocess
        import linuxcnc
        # import hiyapyco
        import json
        import qtpyvcp
        issue_title = "{}: {}".format(self.exc_typ, self.exc_msg)
        issue_body = ISSUE_TEMPLATE.format(
            tracback=self.exc_tb.strip(),
            qt_version=PySide6.QT_VERSION,
            qt_api=PySide6.API_NAME,
            api_version= PySide6.PYSIDE_VERSION,
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
                        .format(title=urllib.parse.quote(issue_title),
                                body=urllib.parse.quote(issue_body))

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
