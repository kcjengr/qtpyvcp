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

"""
import os

from PySide6.QtCore import Qt, Slot, Property, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget
from PySide6.QtWidgets import QListWidgetItem

import qtpyvcp
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.info import Info
from qtpyvcp.actions.machine_actions import issue_mdi
from qtpyvcp.actions.program_actions import load as loadProgram
from qtpyvcp.widgets.base_widgets.base_widget import CMDWidget

import linuxcnc

IN_DESIGNER = os.getenv('DESIGNER', False)
if not IN_DESIGNER:
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

        # name and widget handle for MDI cmd entry widget
        self.mdi_entryline_name = None
        self.mdi_entry_widget = None
        
        # List order direction where Natural is latest at bottom.
        # Default is Natural = False
        self.mdi_listorder_natural = False

        self.heart_beat_timer = None

        self.icon_run_name = 'media-playback-start'
        self.icon_run = QIcon.fromTheme(self.icon_run_name)
        self.icon_waiting_name = 'media-playback-pause'
        self.icon_waiting = QIcon.fromTheme(self.icon_waiting_name)

        #self.returnPressed.connect(self.submit)

    @Property(str)
    def mdiEntrylineName(self):
        """Return name of entry object to Designer"""
        return self.mdi_entryline_name

    @mdiEntrylineName.setter
    def mdiEntrylineName(self, object_name):
        """Set the name for Designer"""
        self.mdi_entryline_name = object_name

    @Property(bool)
    def mdiListOrderNatural(self):
        """Return if list order is Natural - True/False"""
        return self.mdi_listorder_natural
    
    @mdiListOrderNatural.setter
    def mdiListOrderNatural(self, order_flag):
        """Set Order flag for Designer"""
        self.mdi_listorder_natural = order_flag

    @Slot(bool)
    def toggleQueue(self, toggle):
        """Toggle queue pause.
        Starting point is the queue is active.
        """
        if toggle:
            self.heart_beat_timer.stop()
        else:
            self.heart_beat_timer.start()

    @Slot()
    def clearQueue(self):
        """Clear queue items pending run state for items yet to be run."""
        if self.mdi_listorder_natural:
            list_length = list(range(self.count()))
        else:
            list_length = list(range(self.count()-1, 0, -1))

        for list_item in list_length:
            row_item = self.item(list_item)
            row_item_data = row_item.data(MDIHistory.MDQQ_ROLE)

            if row_item_data == MDIHistory.MDIQ_TODO:
                row_item.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_DONE)
                row_item.setIcon(QIcon())

    @Slot()
    def removeSelectedItem(self):
        """Remove the selected lines"""
        selItems = self.selectedItems()
        if len(selItems) > 0:
            if self.mdi_listorder_natural:
                firstItemRow = self.row(selItems[0]) - 1
            else:
                firstItemRow = self.row(selItems[len(selItems)-1])
            for item in selItems:
                row = self.row(item)
                self.takeItem(row)
                if not self.mdi_listorder_natural:
                    STATUS.mdi_remove_entry(row)
                else:
                    # The order of MDI is latest LAST in the list.
                    # framework mdi history is latest FIRST in the list.
                    history_length = len(STATUS.mdi_history.value)
                    history_target_row = history_length-1-row 
                    STATUS.mdi_remove_entry(history_target_row)
            # select an item that makes sense for the case of a single
            # item having been selected and deleted.
            if firstItemRow < 0 and self.count() > 0:
                row = 0
            else:
                row = firstItemRow
            self.setCurrentRow(row)
            
    @Slot()
    def removeAll(self):
        """Remove all items from list and from history"""
        self.clear()
        STATUS.mdi_remove_all()

    @Slot()
    def runFromSelection(self):
        """Start running MDI from the selected row back to correct end."""
        if self.mdi_listorder_natural:
            row_list = list(range(self.currentRow(), self.count(), 1))
        else:
            row_list = list(range(self.currentRow(), -1, -1))

        # from selected row loop back to top/bottom and set ready for run
        for row in row_list:
            row_item = self.item(row)
            row_item.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_TODO)
            row_item.setIcon(self.icon_waiting)

    @Slot()
    def runSelection(self):
        """Run the selected row only."""
        row = self.currentRow()
        # from selected row loop back to top and set ready for run
        row_item = self.item(row)
        row_item.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_TODO)
        row_item.setIcon(self.icon_waiting)

    @Slot()
    def submit(self):
        """Put a new command on the queue for later execution.
        """
        # put the new command on the queue
        cmd = str(self.mdi_entry_widget.text()).strip()
        row_item = QListWidgetItem()
        row_item.setText(cmd)
        row_item.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_TODO)
        row_item.setIcon(self.icon_waiting)
        if self.mdi_listorder_natural:
            self.addItem(row_item)
        else:
            self.insertItem(0, row_item)
        
        # Set the recently added item as the "current" item
        # if the queue is not paused this will quickly get overridden
        # to the executing item highlight mode
        self.clearSelection()
        self.setCurrentItem(row_item)

        # put the command onto the status channel mdi history
        # This always adds this item at position Zero on the channel
        STATUS.mdi_history.setValue(cmd)

        # now clear down the mdi entry text ready for new input
        self.mdi_entry_widget.clear()

    def rowClicked(self):
        """Item row clicked."""
        pass

    @Slot()
    def copySelectionToGcodeEditor(self):
        fname = '/tmp/mdi_gcode.ngc'
        selection = self.selectedItems()
        with open(fname, 'w') as fh:
            for item in selection:
                cmd = str(item.text()).strip()
                fh.write(cmd + '\n')
            fh.write('M2\n')
        loadProgram(fname)

    @Slot()
    def moveRowItemUp(self):
        row = self.currentRow()
        if row == 0:
            return
        item = self.takeItem(row)
        self.insertItem(row-1, item)
        self.setCurrentRow(row-1)
        if not self.mdi_listorder_natural:
            STATUS.mdi_swap_entries(row, row-1)
        else:
            history_length = len(STATUS.mdi_history.value)
            history_target_row = history_length-1-row 
            STATUS.mdi_swap_entries(history_target_row, history_target_row+1)

    @Slot()
    def moveRowItemDown(self):
        row = self.currentRow()
        if row == self.count()-1:
            return
        item = self.takeItem(row)
        self.insertItem(row+1, item)
        self.setCurrentRow(row+1)
        if not self.mdi_listorder_natural:
            STATUS.mdi_swap_entries(row, row+1)
        else:
            history_length = len(STATUS.mdi_history.value)
            history_target_row = history_length-1-row 
            STATUS.mdi_swap_entries(history_target_row, history_target_row-1)
        
    def keyPressEvent(self, event):
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

    def setHistory(self, items_list):
        """Clear and reset the history in the list.
        item_list is a list of strings."""
        print('Clear and load history to list')
        self.clear()
        
        # check that there is anything do to
        if len(items_list) == 0:
            return 
        
        # load the history based on natural order or not
        if self.mdi_listorder_natural:
            items_list.reverse()
        
        for item in items_list:
            row_item = QListWidgetItem()
            row_item.setText(item)
            row_item.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_DONE)
            row_item.setIcon(QIcon())
            self.addItem(row_item)

    def heartBeat(self):
        """Supports heart beat on the MDI History execution queue.
        Issue the next command from the queue.
        Double check machine is in ok state to accept next command.
        Issue the command and if success mark command as being active.
        Mark last command as done.
        """
        # check if machine is idle and ready to run another command
        if STAT.interp_state != linuxcnc.INTERP_IDLE:
            # RS274NGC interpreter not in a state to execute, bail
            return

        # scan for the next command to execute from bottom up.
        if self.mdi_listorder_natural:
            list_length = list(range(self.count()))
        else:
            list_length = list(range(self.count()-1, 0, -1))
        
        for list_item in list_length:
            row_item = self.item(list_item)
            row_item_data = row_item.data(MDIHistory.MDQQ_ROLE)

            if row_item_data == MDIHistory.MDIQ_RUNNING:
                # machine is in idle state so the running command is done
                row_item.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_DONE)
                row_item.setIcon(QIcon())

            elif row_item_data == MDIHistory.MDIQ_TODO:
                self.clearSelection()
                self.setCurrentItem(row_item)
                cmd = str(row_item.text()).strip()
                row_item.setData(MDIHistory.MDQQ_ROLE, MDIHistory.MDIQ_RUNNING)
                row_item.setIcon(self.icon_run)
                issue_mdi(cmd)
                break

    def initialize(self):
        """Load up starting data and set signal connections."""
        # get a proper copy of the list so changes to it are contained.
        history = STATUS.mdi_history.value[:]
        self.setHistory(history)
        self.clicked.connect(self.rowClicked)

        # Get handle to windows list and search through them
        # for the widget referenced in mdi_entryline_name
        for win_name, obj in list(qtpyvcp.WINDOWS.items()):
            if hasattr(obj, str(self.mdi_entryline_name)):
                self.mdi_entry_widget = getattr(obj, self.mdi_entryline_name)
                # Use the handle to supress the widgets Rtn key behaviour
                self.mdi_entry_widget.supress_rtn_key_behaviour()
                break
        # Setup the basic timer system as a heart beat on the queue
        self.heart_beat_timer = QTimer(self)
        # use a sub-second second timer
        self.heart_beat_timer.start(250)
        self.heart_beat_timer.timeout.connect(self.heartBeat)

    def terminate(self):
        """Teardown processing."""
        self.heart_beat_timer.stop()
