
import os
from qtpy.QtWidgets import QMenu, QAction

from qtpyvcp import actions
from qtpyvcp.plugins import getPlugin
from qtpyvcp.widgets.dialogs import showDialog

class RecentFilesMenu(QMenu):
    """Recent Files Menu

    Recent files menu provider.

    Args:
        parent (QWidget, optional) : The menus parent. Default to None.
        files (list, optional) : List of initial files in the menu. Defaults to None.
        max_files (int, optional) : Max number of files to show. Defaults to 10.

    Example:

        YAML config::

            main_window:
                menu:
                  - title: File
                    items:
                      - title: &Recent Files
                        provider: qtpyvcp.widgets.recent_files_menu:RecentFilesMenu
                        kwargs:  # optional keyword arguments to pass to the constructor
                          max_files: 15
    """
    def __init__(self, parent=None, files=None, max_files=10):
        super(RecentFilesMenu, self).__init__(parent)

        self._actions = []

        self.status = getPlugin('status')

        for i in range(max_files):
            action = QAction(parent=self,
                             visible=False,
                             triggered=lambda: actions.program.load(self.sender().data()),
                             )

            self._actions.append(action)
            self.addAction(action)

        self.addSeparator()

        action = QAction(parent=self,
                         text='Browse for files ...',
                         triggered=lambda: showDialog('open_file'),
                         )

        self.addAction(action)

        self.update(files or self.status.recent_files)
        self.status.recent_files_changed.connect(self.update)

    def update(self, files):
        for i, fname in enumerate(files):
            fname = fname.encode('utf-8')
            text = "&{} {}".format(i + 1, os.path.basename(fname))
            action = self._actions[i]
            action.setText(text)
            action.setData(fname)
            action.setVisible(True)
