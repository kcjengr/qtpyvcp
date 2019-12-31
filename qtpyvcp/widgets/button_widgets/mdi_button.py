
import re

from qtpy.QtCore import Property
from qtpy.QtWidgets import QApplication

from qtpyvcp.widgets import VCPButton
from qtpyvcp.actions.machine_actions import issue_mdi

from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

# input format: T#<object_name> M6 G43
# result: [("T", "object_name")]
# if a group is not present it will be an empty string
PARSE_VARS = re.compile(r'(\w)#<([^>]+)>', re.I)

class MDIButton(VCPButton):
    """
    MDI Button

    This widget is intended for calling individual MDI commands. Useful for
    `Go To Home`, `Tool Change` and similar actions.

    The MDI command can include variables to be expanded from widgets present
    in the active window. For example, to make a `Change Tool` button you could
    add an MDIButton and a QLineEdit named ``tool_number_entry``. Then set the
    the MDICommand property of the button to::

      T#<tool_number_entry> M6 G43

    When the button is pressed ``#<tool_number_entry>`` will be substituted with
    the current text in the QLineEdit.

    Button for issuing MDI commands.

    Args:
        parent (QWidget, optional) : The parent widget of the button, or None.
        command (str, optional) : A gcode command string for the button to trigger.
    """

    def __init__(self, parent=None, command=''):
        super(MDIButton, self).__init__(parent)

        self._mdi_cmd = command

        issue_mdi.bindOk(widget=self)
        self.clicked.connect(self.issueMDI)

    def issueMDI(self):
        window = QApplication.instance().activeWindow()

        try:
            cmd = self._mdi_cmd.format(ch=self._data_channels)
        except IndexError:
            LOG.exception("Failed to format MDI command.")
            return

        vars = PARSE_VARS.findall(self._mdi_cmd)
        for cmd_word, object_name in vars:

            try:

                # get the value from the GUI input widget
                wid = getattr(window, object_name)

                try:
                    # QSpinBox, QSlider, QDial
                    val = wid.value()
                except AttributeError:
                    # QLabel, QLineEdit
                    val = wid.text()

                cmd = cmd.replace("{}#<{}>".format(cmd_word, object_name),
                                  "{}{}".format(cmd_word, val))
            except:
                LOG.exception("Couldn't expand '{}' variable.".format(object_name))
                return

        issue_mdi(cmd)

    @Property(str)
    def MDICommand(self):
        """Sets the MDI command property (str).

            A valid RS274 gcode command string. It can include variables to be
            expanded from UI widgets present in the active window.

        Example:
            Assuming there is a QLineEdit in the active window with the
            objectName ``tool_number_entry``, the ``#<tool_number_entry>``
            variable would be substituted with the current text in the QLineEdit::

                T#<tool_number_entry> M6 G43
        """
        return self._mdi_cmd

    @MDICommand.setter
    def MDICommand(self, mdi_cmd):
        self._mdi_cmd = mdi_cmd
