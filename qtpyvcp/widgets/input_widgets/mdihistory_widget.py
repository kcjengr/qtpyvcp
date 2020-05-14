"""MDI History Widget
Maintains MDI history and implements a queue system to support
entering in new MDI commands while others are being executed.
"""
from qtpy.QtCore import Qt, Slot, Property
#from qtpy.QtGui import QValidator
from qtpy.QtWidgets import QListWidget
from qtpy.QtWidgets import QListWidgetItem

from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.info import Info
from qtpyvcp.actions.machine_actions import issue_mdi
from qtpyvcp.widgets.base_widgets.base_widget import CMDWidget
from qtpyvcp.widgets.input_widgets.mdientry_widget import MDIEntry


STATUS = getPlugin('status')
INFO = Info()



class MDIHistory(QListWidget, CMDWidget):
    """MDI History and Queuing Widget.

    This widget implements a visual view of the MDI command
    history.  It also implements a command queuing startegy
    so that commands can be entered and queued up for execution.
    Visual style is used to identify items that have been completed,
    are running and are yet to run.
    """
    MDIQ_DONE = 0
    MDIQ_RUNNING = 1
    MDIQ_TODO = 2
    MDQQ_ROLE = 256

    def __init__(self, parent=None):
        super(MDIHistory, self).__init__(parent)

        print 'init parent = {}'.format(parent)

        self.mdi_entryline_name = None
        self.mdi_entry_widget = None

        #self.returnPressed.connect(self.submit)

    @Property(str)
    def mdi_entryline_name(self):
        """Return name of entry object to Designer"""
        return self._mdi_entryline_name

    @mdi_entryline_name.setter
    def mdi_entryline_name(self, object_name):
        """Set the name for Designer"""
        self._mdi_entryline_name = object_name

    @Slot()
    def submit(self):
        """Issue the next command from the queue.
        Double check machine is in ok state to accept next command.
        Issue the command and if success mark command as being active.
        Mark last command as done.
        """
        # put the new command on the queue
        cmd = str(self.mdi_entry_widget.text()).strip()
        row_item = QListWidgetItem()
        row_item.setText(cmd)
        row_item.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_TODO)
        self.insertItem(0, row_item)

        # scan for the next command to execute from bottom up.
        list_length = self.count()-1
        while list_length >= 0:
            row_item = self.item(list_length)
            row_item_data = row_item.data(MDIHistory.MDQQ_ROLE)
            if row_item_data == MDIHistory.MDIQ_TODO:
                print "Item found to execute on: {}".format(row_item.text())
                break
            list_length -= 1


        #issue_mdi(cmd)
        #STATUS.mdi_history.setValue(cmd)

    def row_clicked(self):
        """Item row clicked."""
        print 'item clicked in list: {}'.format(self.currentItem().text())

    def key_press_event(self, event):
        """Key movement processing.
        Arrow keys move the selected list item up/down
        Return key generates a submit situation by making the item as
        the next available command to processes.
        """
        row = self.currentRow()
        if event.key() == Qt.Key_Up:
            if row > 0:
                row -= 1
        elif event.key() == Qt.Key_Down:
            if row < self.count()-1:
                row += 1
        else:
            super(MDIHistory, self).keyPressEvent(event)

        self.setCurrentRow(row)

    #def focusInEvent(self, event):
    #    super(MDIHistory, self).focusInEvent(event)
    #    pass

    def set_history(self, items_list):
        """Clear and reset the history in the list.
        item_list is a list of strings."""
        print 'Clear and load history to list'
        self.clear()
        for item in items_list:
            row_item = QListWidgetItem()
            row_item.setText(item)
            row_item.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_DONE)
            self.addItem(row_item)


        #self.addItems(history_list)

    def initialize(self):
        """Load up starting data and set signal connections."""
        history = STATUS.mdi_history.value
        self.set_history(history)
        self.clicked.connect(self.row_clicked)
        #STATUS.mdi_history.notify(self.set_history)
        self.mdi_entry_widget = self.parent().findChild(MDIEntry, self.mdi_entryline_name)
        #print 'find child: {}'.format(self.parent().findChild(MDIEntry, 'mdiEntry'))


    def terminate(self):
        """Teardown processing."""
        pass
