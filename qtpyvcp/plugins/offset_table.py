#   Copyright (c) 2018 Kurt Jacobson
#      <kurtcjacobson@gmail.com>
#
#   This file is part of QtPyVCP.
#
#   QtPyVCP is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   QtPyVCP is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with QtPyVCP.  If not, see <http://www.gnu.org/licenses/>.

"""
Offset Table data plugin.

Exposes all the info available in the Offset table. Watches the
offset table for changes and re-loads as needed.

Offset Table YAML configuration:

.. code-block:: yaml

    data_plugins:
      offsettable:
        kwargs:
          # specify the columns that should be read and writen to the
          # tooltable file. To use all columns set to: ABCUVWXYZ
          columns: XYZAB
"""

import os

import linuxcnc

from qtpy.QtCore import QFileSystemWatcher, QTimer, Signal

from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import DataPlugin, DataChannel, getPlugin

from qtpyvcp.actions.machine_actions import issue_mdi


CMD = linuxcnc.command()
LOG = getLogger(__name__)
STATUS = getPlugin('status')
STAT = STATUS.stat
INFO = Info()


def merge(a, b):
    """Shallow merge two dictionaries"""
    r = a.copy()
    r.update(b)
    return r


class OffsetTable(DataPlugin):
    DEFAULT_OFFSET = {
        0: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        1: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        2: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        3: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        4: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        5: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        6: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        7: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        8: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    }

    NO_TOOL = merge(DEFAULT_OFFSET, {'T': 0, 'R': 'No Tool Loaded'})  # FIXME Requires safe removal

    COLUMN_LABELS = [
        'X',
        'Y',
        'Z',
        'A',
        'B',
        'C',
        'U',
        'V',
        'W',
        'R'
    ]

    ROW_LABELS = [
        'G54',
        'G55',
        'G56',
        'G57',
        'G58',
        'G59',
        'G59.1',
        'G59.2',
        'G59.3'
    ]

    offset_table_changed = Signal(dict)
    active_offset_changed = Signal(int)

    def __init__(self, columns='XYZABCUVWR', file_header_template=None):
        super(OffsetTable, self).__init__()

        file_name = INFO.getParameterFile()

        self.parameter_file = None
        if file_name:
            self.parameter_file = os.path.join(os.path.dirname(os.path.realpath(file_name)), file_name)

        self.fs_watcher = None

        self.command = linuxcnc.command()
        self.status = STATUS

        self.columns = self.validateColumns(columns) or [c for c in 'XYZABCUVWR']
        self.rows = self.ROW_LABELS

        self.setCurrentOffsetNumber(1)

        self.g5x_offset_table = self.DEFAULT_OFFSET.copy()
        self.current_index = STATUS.stat.g5x_index

        self.loadOffsetTable()

        self.status.g5x_index.notify(self.setCurrentOffsetNumber)

    @DataChannel
    def current_offset(self, chan, item=None):
        """Current Offset Info

        Available items:

        * X -- x offset
        * Y -- y offset
        * Z -- z offset
        * A -- a offset
        * B -- b offset
        * C -- c offset
        * U -- u offset
        * V -- v offset
        * W -- w offset
        * R -- r offset

        Rules channel syntax::

            offsettable:current_offset
            offsettable:current_offset?X
            offsettable:current_offset?x_offset

        :param item: the name of the tool data item to get
        :return: dict, int, float, str
        """
        return self.current_offset

    def initialise(self):
        self.fs_watcher = QFileSystemWatcher([self.parameter_file])
        self.fs_watcher.fileChanged.connect(self.onParamsFileChanged)

    @staticmethod
    def validateColumns(columns):
        """Validate display column specification.

        The user can specify columns in multiple ways, method is used to make
        sure that that data is validated and converted to a consistent format.

        Args:
            columns (str | list) : A string or list of the column IDs
                that should be shown in the tooltable.

        Returns:
            None if not valid, else a list of uppercase column IDs.
        """
        if not isinstance(columns, (basestring, list, tuple)):
            return

        return [col for col in [col.strip().upper() for col in columns]
                if col in 'XYZABCUVWR' and not col == '']

    # def newOffset(self, tnum=None):
    #     """Get a dict of default tool values for a new tool."""
    #     if tnum is None:
    #         tnum = len(self.OFFSET_TABLE)
    #     new_tool = self.DEFAULT_OFFSET.copy()
    #     new_tool.update({'T': tnum, 'P': tnum, 'R': 'New Tool'})
    #     return new_tool

    def onParamsFileChanged(self, path):
        LOG.debug('Params file changed: {}'.format(path))
        # ToolEdit deletes the file and then rewrites it, so wait
        # a bit to ensure the new data has been writen out.
        QTimer.singleShot(50, self.reloadOffsetTable)

    def setCurrentOffsetNumber(self, offset_num):
        self.current_offset.setValue(offset_num)
        self.current_index = offset_num
        self.active_offset_changed.emit(offset_num)

    def reloadOffsetTable(self):
        # rewatch the file if it stop being watched because it was deleted
        if self.parameter_file not in self.fs_watcher.files():
            self.fs_watcher.addPath(self.parameter_file)

        # reload with the new data
        offset_table = self.loadOffsetTable()
        self.offset_table_changed.emit(offset_table)

    def iterTools(self, offset_table=None, columns=None):
        offset_table = offset_table or self.OFFSET_TABLE
        columns = self.validateColumns(columns) or self.columns
        for offset in sorted(offset_table.iterkeys()):
            offset_data = offset_table[offset]
            yield [offset_data[key] for key in columns]

    def loadOffsetTable(self):

        if self.parameter_file:
            with open(self.parameter_file, 'r') as fh:
                for line in fh:
                    param, data = int(line.split()[0]), float(line.split()[1])

                    if 5230 >= param >= 5221:
                        self.g5x_offset_table.get(0)[param - 5221] = data
                    elif 5250 >= param >= 5241:
                        self.g5x_offset_table.get(1)[param - 5241] = data
                    elif 5270 >= param >= 5261:
                        self.g5x_offset_table.get(2)[param - 5261] = data
                    elif 5290 >= param >= 5281:
                        self.g5x_offset_table.get(3)[param - 5281] = data
                    elif 5310 >= param >= 5301:
                        self.g5x_offset_table.get(4)[param - 5301] = data
                    elif 5330 >= param >= 5321:
                        self.g5x_offset_table.get(5)[param - 5321] = data
                    elif 5350 >= param >= 5341:
                        self.g5x_offset_table.get(6)[param - 5341] = data
                    elif 5370 >= param >= 5361:
                        self.g5x_offset_table.get(7)[param - 5361] = data
                    elif 5390 >= param >= 5381:
                        self.g5x_offset_table.get(8)[param - 5381] = data

        self.offset_table_changed.emit(self.g5x_offset_table)

        return self.g5x_offset_table

    def getOffsetTable(self):
        return self.g5x_offset_table

    def saveOffsetTable(self, offset_table, columns):
        """ Stores the offset table in memory.

        Args:
            offset_table (dict) : Dictionary of dictionaries containing
                the tool data to write to the file.
            columns (str | list) : A list of data columns to write.
                If `None` will use the value of ``self.columns``.
        """
        self.g5x_offset_table = offset_table

        for index in range(len(self.rows)):
            mdi_list = list()
            mdi_list.append("G10 L2")
            mdi_list.append("P{}".format(index+1))

            for char in columns:

                column_index = self.columns.index(char)

                mdi_list.append("{}{}".format(char, self.g5x_offset_table[index][column_index]))

            mdi_command = " ".join(mdi_list)

            issue_mdi(mdi_command)
