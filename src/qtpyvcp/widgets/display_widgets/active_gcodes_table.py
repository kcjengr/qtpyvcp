
from qtpy.QtCore import Qt, Slot, Property, QModelIndex, QSortFilterProxyModel
from qtpy.QtGui import QStandardItemModel, QColor, QBrush
from qtpy.QtWidgets import QTableView

from qtpyvcp.plugins import getPlugin


TABLE_DATA = """
G0: Rapid positioning
G1: Linear interpolation
G2: Clockwise circular interpolation
G3: Counter clockwise circular interpolation
G4: Dwell
G17: XY plane selection
G18: XZ plane selection
G19: YZ plane selection
G20: Inch units
G21: Millimeter units
G30: Go to pre-defined position
G30.1: Store predefined position
G40: Cancel radius compensation
G41: Radius compensation on left
G42: Radius compensation on right
G54: Active work coordinate system
G61: Exact path mode
G61.1: Exact stop mode
G64: Path blending
G73: Canned cycle - drilling with chip-break
G80: Cancel canned cycle
G81: Canned cycle - drilling
G82: Canned cycle - drilling with dwell
G83: Canned cycle - peck drilling 
G86: Canned cycle - boring, spindle stop, rapid out
G89: Canned cycle - borning, dwell, feed out
G90: Absolute distance mode
G91: Incremental distance mode
G90.1: I, J, K absolute distance mode
G91.1: I, J, K incremental distance mode
G93: Feed inverse time mode
G94: Feed per minute mode
G95: Feed per revolution mode
G97: RPM mode
G98: retract to initial Z height
G99: Retract to R height
"""

DATA = []

for num, line in enumerate(TABLE_DATA.strip().split('\n')):
    code, sep, description = line.partition(':')
    DATA.append({'code': code, 'description': description.strip()})


class ActiveGcodesModel(QStandardItemModel):
    def __init__(self, parent=None):
        super(ActiveGcodesModel, self).__init__(parent)

        self.status = getPlugin('status')
        self.gcodes = self.status.gcodes.getValue('list')

        self.active_code_color = QColor(Qt.darkGreen)
        self.active_code_bg = None

        self._column_labels = ["G-code", "Description"]

        self.setColumnCount(self.columnCount())
        self.setRowCount(self.rowCount())

        self.status.gcodes.notify(self.refreshModel)

    def refreshModel(self):
        # refresh model so current gcodes gets highlighted
        self.beginResetModel()
        self.gcodes = self.status.gcodes.getValue('list')
        self.endResetModel()

    def updateModel(self):
        # update model with new data
        self.beginResetModel()
        pass
        self.endResetModel()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._column_labels[section]

        return QStandardItemModel.headerData(self, section, orientation, role)

    def columnCount(self, parent=None):
        return len(self._column_labels)

    def rowCount(self, parent=None):
        return len(DATA) - 1

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.NoItemFlags

    def data(self, index, role=Qt.DisplayRole):
        row, col = index.row(), index.column()

        if role == Qt.DisplayRole or role == Qt.EditRole:
            data = DATA[row]
            code = data['code']
            if col == 0:
                return code
            elif col == 1:
                if code == 'G64':
                    return data['description'].format()
                return data['description']

        elif role == Qt.TextColorRole:
            if DATA[row]['code'] in self.gcodes:
                return QBrush(self.active_code_color)

        elif role == Qt.BackgroundRole and self.active_code_bg is not None:
            if DATA[row]['code'] in self.gcodes:
                return QBrush(self.active_code_bg)

        return QStandardItemModel.data(self, index, role)


class ActiveGcodesTable(QTableView):
    def __init__(self, parent=None):
        super(ActiveGcodesTable, self).__init__(parent)

        self.active_codes_model = ActiveGcodesModel(self)
        self.setModel(self.active_codes_model)

        # Appearance/Behaviour settings
        self.verticalHeader().hide()
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setEditTriggers(QTableView.NoEditTriggers)
        self.horizontalHeader().setDefaultSectionSize(60)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSortIndicator(0, Qt.AscendingOrder)

    @Property(QColor)
    def activeCodeColor(self):
        return self.model().active_code_color

    @activeCodeColor.setter
    def activeCodeColor(self, color):
        self.model().active_code_color = color
        self.model().refreshModel()

    @Property(QColor)
    def activeCodeBackground(self):
        return self.model().active_code_bg or QColor()

    @activeCodeBackground.setter
    def activeCodeBackground(self, color):
        self.model().active_code_bg = color
        self.model().refreshModel()
