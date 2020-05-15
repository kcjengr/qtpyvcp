# -*- coding: utf-8 -*-
"""QtPyVCP MDI History Widget

This widget implements the following key elements:
[1] A history display of MDI commands issued with the latest
command at the top of the list and the oldest at the bottom
of the list.

[2] A queue system of commands that have been entered
but have not yet been executed. This allows the rapid entry
of MDI commands to be executed without having to wait for any
running commands to complete.

ToDo:
    * add/test for styling based on the class queue codes
    * be able to select and remove unwanted commands from the history
    * be able to select a row and run commands from that point upwards

"""

from qtpy.QtCore import Qt, Slot, Property, QTimer
from qtpy.QtWidgets import QListWidget
from qtpy.QtWidgets import QListWidgetItem

import qtpyvcp
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.info import Info
from qtpyvcp.actions.machine_actions import issue_mdi
from qtpyvcp.widgets.base_widgets.base_widget import CMDWidget

import linuxcnc


STATUS = getPlugin('status')
STAT = STATUS.stat
INFO = Info()



class MDIHistory(QListWidget, CMDWidget):
    """MDI History and Queuing Widget.

    This widget implements a visual view of the MDI command
    history.  It also implements a command queuing startegy
    so that commands can be entered and queued up for execution.
    Visual style is used to identify items that have been completed,
    are running and are yet to run.
    """

    # MDI Queue status constants
    MDIQ_DONE = 0
    MDIQ_RUNNING = 1
    MDIQ_TODO = 2
    MDQQ_ROLE = 256

    def __init__(self, parent=None):
        super(MDIHistory, self).__init__(parent)

        self.mdi_entryline_name = None
        self.mdi_entry_widget = None
        self.heart_beat_timer = None

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

        # now clear down the mdi entry text ready for new input
        self.mdi_entry_widget.clear()

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


    def heart_beat(self):
        """Supports heart beat on the MDI History execution queue."""
        # check if machine is idle and ready to run another command
        if STAT.interp_state != linuxcnc.INTERP_IDLE:
            # RS274NGC interpreter not in a state to execute
            print
            return

        # scan for the next command to execute from bottom up.
        list_length = self.count()-1
        while list_length >= 0:
            row_item = self.item(list_length)
            row_item_data = row_item.data(MDIHistory.MDQQ_ROLE)

            if row_item_data == MDIHistory.MDIQ_RUNNING:
                # machine is in idle state so the running command is done
                row_item.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_DONE)

            elif row_item_data == MDIHistory.MDIQ_TODO:
                cmd = str(row_item.text()).strip()
                row_item.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_RUNNING)
                print "Item found to execute on: {}".format(cmd)
                issue_mdi(cmd)
                break

            list_length -= 1

    def initialize(self):
        """Load up starting data and set signal connections."""
        history = STATUS.mdi_history.value
        self.set_history(history)
        self.clicked.connect(self.row_clicked)

        # get handle to windows list and seach through them
        # for the widget referenced in mdi_entryline_name
        for win_name, obj in qtpyvcp.WINDOWS.items():
            if hasattr(obj, self.mdi_entryline_name):
                self.mdi_entry_widget = getattr(obj, self.mdi_entryline_name)

        # setup the basic timer system as a heart beat on the queue
        self.heart_beat_timer = QTimer(self)
        self.heart_beat_timer.start(1000)
        self.heart_beat_timer.timeout.connect(self.heart_beat)


    def terminate(self):
        """Teardown processing."""
        self.heart_beat_timer.stop()
