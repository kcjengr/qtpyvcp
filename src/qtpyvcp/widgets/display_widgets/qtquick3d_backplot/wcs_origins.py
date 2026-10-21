"""Work-offset origin labels for the Qt Quick 3D backplot.

One row per work coordinate system that the loaded program actually uses.
Configured-but-unused offsets and the no-program state produce no rows, so an
empty file draws no part origins. The row carries the label text
(``G54`` .. ``G59.3``) and the scene position of the origin. The 2D QML overlay
projects those positions to screen coordinates, so the labels stay readable at
any zoom and always face the operator.
"""

from PySide6.QtCore import QAbstractListModel, QByteArray, Qt

# LinuxCNC WCS index 0 is G54; index 8 is G59.3 (G53 is machine coordinates and
# is not a work offset).
WCS_LABELS = (
    "G54", "G55", "G56", "G57", "G58",
    "G59", "G59.1", "G59.2", "G59.3",
)


class WcsOriginModel(QAbstractListModel):
    """QML list model of visible work-offset origins."""

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
        """Replace the rows with ``(label, QVector3D scene_position, wcs)``."""
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
