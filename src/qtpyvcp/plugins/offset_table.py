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
        0: [],
        1: [],
        2: [],
        3: [],
        4: [],
        5: [],
        6: [],
        7: [],
        8: []
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

        self.x_column = None
        self.y_column = None
        self.z_column = None
        self.a_column = None
        self.b_column = None
        self.c_column = None
        self.u_column = None
        self.v_column = None
        self.w_column = None
        self.r_column = None

        self.column_labels = dict()

        if 'X' in self.columns:
            self.x_column = self.columns.index('X')
            self.column_labels['X'] = self.x_column
        if 'Y' in self.columns:
            self.y_column = self.columns.index('Y')
            self.column_labels['Y'] = self.y_column
        if 'Z' in self.columns:
            self.z_column = self.columns.index('Z')
            self.column_labels['Z'] = self.z_column
        if 'A' in self.columns:
            self.a_column = self.columns.index('A')
            self.column_labels['A'] = self.a_column
        if 'B' in self.columns:
            self.b_column = self.columns.index('B')
            self.column_labels['B'] = self.b_column
        if 'C' in self.columns:
            self.c_column = self.columns.index('C')
            self.column_labels['C'] = self.c_column
        if 'U' in self.columns:
            self.u_column = self.columns.index('U')
            self.column_labels['U'] = self.u_column
        if 'V' in self.columns:
            self.v_column = self.columns.index('V')
            self.column_labels['V'] = self.v_column
        if 'W' in self.columns:
            self.w_column = self.columns.index('W')
            self.column_labels['W'] = self.w_column
        if 'R' in self.columns:
            self.r_column = self.columns.index('R')
            self.column_labels['R'] = self.r_column

        # print(f"X: {self.x_column}\nY: {self.y_column}\nZ: {self.z_column}\nA: {self.a_column}\nB: {self.b_column}\nC: {self.c_column}\nU: {self.u_column}\nV: {self.v_column}\nW: {self.w_column}\nZ: {self.r_column}")

        for i in range(9):
            for j in range(len(self.columns)):
                self.DEFAULT_OFFSET.get(i).insert(j, 0.0)

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
        if not isinstance(columns, (str, list, tuple)):
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

    def iterTools(self, offset_table=None, columns=None):
        offset_table = offset_table or self.OFFSET_TABLE
        columns = self.validateColumns(columns) or self.columns
        for offset in sorted(offset_table.keys()):
            offset_data = offset_table[offset]
            yield [offset_data[key] for key in columns]

    def loadOffsetTable(self):

        if self.parameter_file:
            with open(self.parameter_file, 'r') as fh:
                for line in fh:
                    param, data = int(line.split()[0]), float(line.split()[1])

                    # G54
                    if (param == 5221) and (self.x_column is not None):
                        # X
                        self.g5x_offset_table.get(0)[self.x_column] = data
                    if (param == 5222) and (self.y_column is not None):
                        # Y
                        self.g5x_offset_table.get(0)[self.y_column] = data
                    if (param == 5223) and (self.z_column is not None):
                        # Z
                        self.g5x_offset_table.get(0)[self.z_column] = data
                    if (param == 5224) and (self.a_column is not None):
                        # A
                        self.g5x_offset_table.get(0)[self.a_column] = data
                    if (param == 5225) and (self.b_column is not None):
                        # B
                        self.g5x_offset_table.get(0)[self.b_column] = data
                    if (param == 5226) and (self.c_column is not None):
                        # C
                        self.g5x_offset_table.get(0)[self.c_column] = data
                    if (param == 5227) and (self.u_column is not None):
                        # U
                        self.g5x_offset_table.get(0)[self.u_column] = data
                    if (param == 5228) and (self.v_column is not None):
                        # V
                        self.g5x_offset_table.get(0)[self.v_column] = data
                    if (param == 5229) and (self.w_column is not None):
                        # W
                        self.g5x_offset_table.get(0)[self.w_column] = data
                    if (param == 5230) and (self.r_column is not None):
                        # R
                        self.g5x_offset_table.get(0)[self.r_column] = data

                    # G55

                    if (param == 5241) and (self.x_column is not None):
                        # X
                        self.g5x_offset_table.get(1)[self.x_column] = data
                    if (param == 5242) and (self.y_column is not None):
                        # Y
                        self.g5x_offset_table.get(1)[self.y_column] = data
                    if (param == 5243) and (self.z_column is not None):
                        # Z
                        self.g5x_offset_table.get(1)[self.z_column] = data
                    if (param == 5244) and (self.a_column is not None):
                        # A
                        self.g5x_offset_table.get(1)[self.a_column] = data
                    if (param == 5245) and (self.b_column is not None):
                        # B
                        self.g5x_offset_table.get(1)[self.b_column] = data
                    if (param == 5246) and (self.c_column is not None):
                        # C
                        self.g5x_offset_table.get(1)[self.c_column] = data
                    if (param == 5247) and (self.u_column is not None):
                        # U
                        self.g5x_offset_table.get(1)[self.u_column] = data
                    if (param == 5248) and (self.v_column is not None):
                        # V
                        self.g5x_offset_table.get(1)[self.v_column] = data
                    if (param == 5249) and (self.w_column is not None):
                        # W
                        self.g5x_offset_table.get(1)[self.w_column] = data
                    if (param == 5250) and (self.r_column is not None):
                        # R
                        self.g5x_offset_table.get(1)[self.r_column] = data

                    # G56

                    if (param == 5261) and (self.x_column is not None):
                        # X
                        self.g5x_offset_table.get(2)[self.x_column] = data
                    if (param == 5262) and (self.y_column is not None):
                        # Y
                        self.g5x_offset_table.get(2)[self.y_column] = data
                    if (param == 5263) and (self.z_column is not None):
                        # Z
                        self.g5x_offset_table.get(2)[self.z_column] = data
                    if (param == 5264) and (self.a_column is not None):
                        # A
                        self.g5x_offset_table.get(2)[self.a_column] = data
                    if (param == 5265) and (self.b_column is not None):
                        # B
                        self.g5x_offset_table.get(2)[self.b_column] = data
                    if (param == 5266) and (self.c_column is not None):
                        # C
                        self.g5x_offset_table.get(2)[self.c_column] = data
                    if (param == 5267) and (self.u_column is not None):
                        # U
                        self.g5x_offset_table.get(2)[self.u_column] = data
                    if (param == 5268) and (self.v_column is not None):
                        # V
                        self.g5x_offset_table.get(2)[self.v_column] = data
                    if (param == 5269) and (self.w_column is not None):
                        # W
                        self.g5x_offset_table.get(2)[self.w_column] = data
                    if (param == 5270) and (self.r_column is not None):
                        # R
                        self.g5x_offset_table.get(2)[self.r_column] = data

                    # G57

                    if (param == 5281) and (self.x_column is not None):
                        # X
                        self.g5x_offset_table.get(3)[self.x_column] = data
                    if (param == 5282) and (self.y_column is not None):
                        # Y
                        self.g5x_offset_table.get(3)[self.y_column] = data
                    if (param == 5283) and (self.x_column is not None):
                        # Z
                        self.g5x_offset_table.get(3)[self.z_column] = data
                    if (param == 5284) and (self.a_column is not None):
                        # A
                        self.g5x_offset_table.get(3)[self.a_column] = data
                    if (param == 5285) and (self.b_column is not None):
                        # B
                        self.g5x_offset_table.get(3)[self.b_column] = data
                    if (param == 5286) and (self.c_column is not None):
                        # C
                        self.g5x_offset_table.get(3)[self.c_column] = data
                    if (param == 5287) and (self.u_column is not None):
                        # U
                        self.g5x_offset_table.get(3)[self.u_column] = data
                    if (param == 5288) and (self.v_column is not None):
                        # V
                        self.g5x_offset_table.get(3)[self.v_column] = data
                    if (param == 5289) and (self.w_column is not None):
                        # W
                        self.g5x_offset_table.get(3)[self.w_column] = data
                    if (param == 5290) and (self.r_column is not None):
                        # R
                        self.g5x_offset_table.get(3)[self.r_column] = data

                    # G58

                    if (param == 5301) and (self.x_column is not None):
                        # X
                        self.g5x_offset_table.get(4)[self.x_column] = data
                    if (param == 5302) and (self.y_column is not None):
                        # Y
                        self.g5x_offset_table.get(4)[self.y_column] = data
                    if (param == 5303) and (self.z_column is not None):
                        # Z
                        self.g5x_offset_table.get(4)[self.z_column] = data
                    if (param == 5304) and (self.a_column is not None):
                        # A
                        self.g5x_offset_table.get(4)[self.a_column] = data
                    if (param == 5305) and (self.b_column is not None):
                        # B
                        self.g5x_offset_table.get(4)[self.b_column] = data
                    if (param == 5306) and (self.c_column is not None):
                        # C
                        self.g5x_offset_table.get(4)[self.c_column] = data
                    if (param == 5307) and (self.u_column is not None):
                        # U
                        self.g5x_offset_table.get(4)[self.u_column] = data
                    if (param == 5308) and (self.v_column is not None):
                        # V
                        self.g5x_offset_table.get(4)[self.v_column] = data
                    if (param == 5309) and (self.w_column is not None):
                        # W
                        self.g5x_offset_table.get(4)[self.w_column] = data
                    if (param == 5310) and (self.r_column is not None):
                        # R
                        self.g5x_offset_table.get(4)[self.r_column] = data

                    # G59

                    if (param == 5321) and (self.x_column is not None):
                        # X
                        self.g5x_offset_table.get(5)[self.x_column] = data
                    if (param == 5322) and (self.y_column is not None):
                        # Y
                        self.g5x_offset_table.get(5)[self.y_column] = data
                    if (param == 5323) and (self.z_column is not None):
                        # Z
                        self.g5x_offset_table.get(5)[self.z_column] = data
                    if (param == 5324) and (self.a_column is not None):
                        # A
                        self.g5x_offset_table.get(5)[self.a_column] = data
                    if (param == 5325) and (self.b_column is not None):
                        # B
                        self.g5x_offset_table.get(5)[self.b_column] = data
                    if (param == 5326) and (self.c_column is not None):
                        # C
                        self.g5x_offset_table.get(5)[self.c_column] = data
                    if (param == 5327) and (self.u_column is not None):
                        # U
                        self.g5x_offset_table.get(5)[self.u_column] = data
                    if (param == 5328) and (self.v_column is not None):
                        # V
                        self.g5x_offset_table.get(5)[self.v_column] = data
                    if (param == 5329) and (self.w_column is not None):
                        # W
                        self.g5x_offset_table.get(5)[self.w_column] = data
                    if (param == 5330) and (self.r_column is not None):
                        # R
                        self.g5x_offset_table.get(5)[self.r_column] = data

                    # G59.1

                    if (param == 5341) and (self.x_column is not None):
                        # X
                        self.g5x_offset_table.get(6)[self.x_column] = data
                    if (param == 5342) and (self.y_column is not None):
                        # Y
                        self.g5x_offset_table.get(6)[self.y_column] = data
                    if (param == 5343) and (self.z_column is not None):
                        # Z
                        self.g5x_offset_table.get(6)[self.z_column] = data
                    if (param == 5344) and (self.a_column is not None):
                        # A
                        self.g5x_offset_table.get(6)[self.a_column] = data
                    if (param == 5345) and (self.b_column is not None):
                        # B
                        self.g5x_offset_table.get(6)[self.b_column] = data
                    if (param == 5346) and (self.c_column is not None):
                        # C
                        self.g5x_offset_table.get(6)[self.c_column] = data
                    if (param == 5347) and (self.u_column is not None):
                        # U
                        self.g5x_offset_table.get(6)[self.u_column] = data
                    if (param == 5348) and (self.v_column is not None):
                        # V
                        self.g5x_offset_table.get(6)[self.v_column] = data
                    if (param == 5349) and (self.w_column is not None):
                        # W
                        self.g5x_offset_table.get(6)[self.w_column] = data
                    if (param == 5350) and (self.r_column is not None):
                        # R
                        self.g5x_offset_table.get(6)[self.r_column] = data

                    # G59.2

                    if (param == 5361) and self.x_column:
                        # X
                        self.g5x_offset_table.get(7)[self.x_column] = data
                    if (param == 5362) and self.y_column:
                        # Y
                        self.g5x_offset_table.get(7)[self.y_column] = data
                    if (param == 5363) and self.z_column:
                        # Z
                        self.g5x_offset_table.get(7)[self.z_column] = data
                    if (param == 5364) and self.a_column:
                        # A
                        self.g5x_offset_table.get(7)[self.a_column] = data
                    if (param == 5365) and self.b_column:
                        # B
                        self.g5x_offset_table.get(7)[self.b_column] = data
                    if (param == 5366) and self.c_column:
                        # C
                        self.g5x_offset_table.get(7)[self.c_column] = data
                    if (param == 5367) and self.u_column:
                        # U
                        self.g5x_offset_table.get(7)[self.u_column] = data
                    if (param == 5368) and self.v_column:
                        # V
                        self.g5x_offset_table.get(7)[self.v_column] = data
                    if (param == 5369) and self.w_column:
                        # W
                        self.g5x_offset_table.get(7)[self.w_column] = data
                    if (param == 5370) and self.r_column:
                        # R
                        self.g5x_offset_table.get(7)[self.r_column] = data

                    # G59.3

                    if (param == 5381) and (self.x_column is not None):
                        # X
                        self.g5x_offset_table.get(8)[self.x_column] = data
                    if (param == 5382) and (self.y_column is not None):
                        # Y
                        self.g5x_offset_table.get(8)[self.y_column] = data
                    if (param == 5383) and (self.z_column is not None):
                        # Z
                        self.g5x_offset_table.get(8)[self.z_column] = data
                    if (param == 5384) and (self.a_column is not None):
                        # A
                        self.g5x_offset_table.get(8)[self.a_column] = data
                    if (param == 5385) and (self.b_column is not None):
                        # B
                        self.g5x_offset_table.get(8)[self.b_column] = data
                    if (param == 5386) and (self.c_column is not None):
                        # C
                        self.g5x_offset_table.get(8)[self.c_column] = data
                    if (param == 5387) and (self.u_column is not None):
                        # U
                        self.g5x_offset_table.get(8)[self.u_column] = data
                    if (param == 5388) and (self.v_column is not None):
                        # V
                        self.g5x_offset_table.get(8)[self.v_column] = data
                    if (param == 5389) and (self.w_column is not None):
                        # W
                        self.g5x_offset_table.get(8)[self.w_column] = data
                    if (param == 5390) and (self.r_column is not None):
                        # R
                        self.g5x_offset_table.get(8)[self.r_column] = data

        self.offset_table_changed.emit(self.g5x_offset_table)

        return self.g5x_offset_table

    def getTableColumnsIndex(self):
        return self.column_labels
        
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
        
        mdi_commands = ""
        
        for index in range(len(self.rows)):
            mdi_list = list()
            mdi_list.append("G10 L2")
            mdi_list.append("P{}".format(index + 1))

            for char in columns:

                column_index = self.columns.index(char)

                mdi_list.append("{}{}".format(char, self.g5x_offset_table[index][column_index]))

            mdi_command = " ".join(mdi_list)
            
            mdi_commands = f"{mdi_commands};{mdi_command}"
            
        issue_mdi(mdi_commands)

