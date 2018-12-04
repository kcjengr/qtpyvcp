import os
import json

from qtpy.QtCore import QFileSystemWatcher, Signal

from qtpyvcp.plugins import QtPyVCPDataPlugin, QtPyVCPDataChannel, getDataPlugin

print getDataPlugin('status')

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

DEFAULT_TOOL = {
    'A': 0.0,
    'B': 0.0,
    'C': 0.0,
    'D': 0.0,
    'I': 0.0,
    'J': 0.0,
    'P': -1,
    'Q': 0.0,
    'T': -1,
    'U': 0.0,
    'V': 0.0,
    'W': 0.0,
    'X': 0.0,
    'Y': 0.0,
    'Z': 0.0,
    'comment': '',
}

#                          E X A M P L E   I N T E R F A C E
# tooltable:current_tool?            # will return the current tool data dictionary
# tooltable:current_tool?diameter    # will return the current tool diameter
# toollife:current_tool?hours


class CurrentTool(QtPyVCPDataChannel):

    def __init__(self):
        super(CurrentTool, self).__init__()

        self._value = DEFAULT_TOOL

    @property
    def value(self):
        return self._value

    @property
    def number(self):
        return self._value['T']

    @property
    def pocket(self):
        return self._value['P']

    @property
    def diameter(self):
        return self._value['D']

    @property
    def comment(self):
        return self._value['comment']

    def _update(self, value):
        self._value = value
        self.valueChanged.emit(value)

class ToolTable(QtPyVCPDataPlugin):

    protocol = 'tooltable'
    current_tool = CurrentTool()

    TOOL_TABLE = {}

    def __init__(self):
        super(ToolTable, self).__init__()

        file = '/home/kurt/dev/cnc/qtpyvcp/sim/tool.tbl'

        self.tool_table_file = file

        if self.TOOL_TABLE == {}:
            self.loadToolTable(file)

        self.current_tool._update(self.TOOL_TABLE[0])

    def loadToolTable(self, file=None):

        if file is None:
            file = self.tool_table_file

        if not os.path.exists(file):
            LOG.critical("Tool table file does not exist")
            return

        with open(file, 'r') as fh:
            lines = fh.readlines()

        table = {}

        for line in lines:

            line = line.strip()
            data, sep, comment = line.partition(';')

            tool = DEFAULT_TOOL.copy()
            for item in data.split():
                descriptor = item[0]
                if descriptor in 'TPXYZABCUVWDIJQ':
                    value = item.lstrip(descriptor)
                    if descriptor in ('T', 'P'):
                        try:
                            tool[descriptor] = int(value)
                        except:
                            print 'Error converting value to int'
                            break
                    else:
                        try:
                            tool[descriptor] = float(value)
                        except:
                            print 'Error converting value to float'
                            break

            tool['comment'] = comment.strip()

            tnum = tool['T']
            if tnum == -1:
                continue

            # add the tool to the table
            table[tnum] = tool

        self.__class__.TOOL_TABLE = table

        # print json.dumps(table, sort_keys=True, indent=4)



def main():

    tool_table_file = '/home/kurt/dev/cnc/QtPyVCP/sim/tool.tbl'

    import sys
    from qtpy.QtCore import QCoreApplication


    tool_table = ToolTable(tool_table_file)

    def file_changed(path):
        print('File Changed: %s' % path)
        tool_table.loadToolTable(tool_table_file)

    app = QCoreApplication(sys.argv)

    fs_watcher = QFileSystemWatcher([tool_table_file,])
    fs_watcher.fileChanged.connect(file_changed)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
