"""Scene label rows for the Qt Quick 3D backplot.

The same model backs work-offset origin labels, machine axis tick labels and
program-bound tick labels. Each row carries text and a scene position; the QML
overlay projects the position to screen coordinates so labels stay readable at
any zoom and always face the operator.
"""

from PySide6.QtCore import QAbstractListModel, QByteArray, Qt

# LinuxCNC WCS index 0 is G54; index 8 is G59.3 (G53 is machine coordinates and
# is not a work offset).
WCS_LABELS = (
    "G54", "G55", "G56", "G57", "G58",
    "G59", "G59.1", "G59.2", "G59.3",
)


class SceneLabelModel(QAbstractListModel):
    """QML list model of scene-space text labels."""

    LabelRole = Qt.ItemDataRole.UserRole + 1
    PosRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []

    def rowCount(self, parent=None):
        if parent is not None and parent.isValid():
            return 0
        return len(self._rows)

    def roleNames(self):
        return {
            self.LabelRole: QByteArray(b"label"),
            self.PosRole: QByteArray(b"pos"),
        }

    def data(self, index, role):
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        label, position, _wcs_index = self._rows[index.row()]
        if role == self.LabelRole:
            return label
        if role == self.PosRole:
            return position
        return None

    def set_rows(self, rows):
        """Replace the rows with ``(label, QVector3D scene_position, tag)``."""
        rows = list(rows)
        if rows == self._rows:
            return
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rows(self):
        return tuple(self._rows)

    def wcs_indices(self):
        return tuple(row[2] for row in self._rows)


# Backwards-compatible name for callers that only use work-offset origins.
WcsOriginModel = SceneLabelModel
