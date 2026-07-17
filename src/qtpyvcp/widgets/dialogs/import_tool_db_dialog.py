# coding=utf-8
"""ImportToolDbDialogBase -- shared skeleton for dialogs that import
external tool data into a fresh tool database, as a starting point for
transitioning to the DB-backed tool table (not a live merge into the
database a running session already has open).

Source picker (and an optional second source, for merge-style importers),
destination picker (defaulting to this config's own tool database path via
``qtpyvcp.plugins.db_tool_table._default_db_path``), a units combo
(defaulting to the machine's configured units), an overwrite confirmation,
an offer to point this session's ``[EMCIO] TOOL_DB_FILE`` at the new file
(``qtpyvcp.plugins.db_tool_table.set_tool_db_file``, INI backed up first),
and a result summary.

A subclass supplies which importer to run and its guidance text -- see
probe_basic's ``LatheToolTable``/``MillToolTable``-flavored import dialogs
(``probe_basic_lathe.import_tbl_dialog`` / ``probe_basic.import_tool_dialog``)
for real examples wiring this up against the machine-specific importers in
``qtpyvcp.lib.db_tool`` (``import_legacy_tbl`` is machine-agnostic;
``import_fusion_tools``/``import_merged`` vs. their ``_mill`` counterparts
differ in diameter semantics -- a lathe nose radius vs. a mill cutting
diameter).

Conversions run against standalone SQLAlchemy engines scoped only to the
chosen destination file -- never the app's live tool table connection --
so these are safe to run from a menu action while the VCP already has a
different tool database open. Either way the new database only takes
effect once the VCP is restarted, and the dialog says so explicitly.
"""

import os

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
)

from qtpyvcp.plugins.db_tool_table import _default_db_path, set_tool_db_file
from qtpyvcp.utilities.info import Info
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)


class ImportToolDbDialogBase(QDialog):
    """Shared skeleton: source picker, destination picker (defaulting to
    this config's own tool database path), units combo (defaulting to the
    machine's configured units), overwrite confirmation, the
    set-as-active-INI-edit offer, and the result summary."""

    WINDOW_TITLE = "Import Tool Data"
    SOURCE_LABEL = "Source file:"
    SOURCE_DIALOG_TITLE = "Select Source File"
    SOURCE_FILTER = "All Files (*)"
    # Second source row, built only when SOURCE2_LABEL is set (a merge
    # dialog); single-source importers leave these None.
    SOURCE2_LABEL = None
    SOURCE2_DIALOG_TITLE = "Select Source File"
    SOURCE2_FILTER = "All Files (*)"
    NOTE = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumWidth(520)

        self.src_path_edit = QLineEdit()
        src_browse_btn = QPushButton("Browse...")
        src_browse_btn.clicked.connect(self._browse_src)
        src_row = QHBoxLayout()
        src_row.addWidget(self.src_path_edit)
        src_row.addWidget(src_browse_btn)

        self.src2_path_edit = None
        src2_row = None
        if self.SOURCE2_LABEL is not None:
            self.src2_path_edit = QLineEdit()
            src2_browse_btn = QPushButton("Browse...")
            src2_browse_btn.clicked.connect(self._browse_src2)
            src2_row = QHBoxLayout()
            src2_row.addWidget(self.src2_path_edit)
            src2_row.addWidget(src2_browse_btn)

        self.db_path_edit = QLineEdit()
        # Default to this config's own tool database path -- the natural
        # destination, so importing "just works" after a restart for the
        # common case. The user can Browse to any other name to build up
        # backup/per-job variants instead.
        try:
            self.db_path_edit.setText(_default_db_path())
        except Exception as exc:
            LOG.warning("Could not resolve default tool database path: %s", exc)
        db_browse_btn = QPushButton("Browse...")
        db_browse_btn.clicked.connect(self._browse_db)
        db_row = QHBoxLayout()
        db_row.addWidget(self.db_path_edit)
        db_row.addWidget(db_browse_btn)

        self.units_combo = QComboBox()
        self.units_combo.addItems(["inch", "mm"])
        try:
            if Info().getIsMachineMetric():
                self.units_combo.setCurrentText("mm")
        except Exception as exc:
            LOG.warning("Could not resolve machine units, defaulting to inch: %s", exc)

        form = QFormLayout()
        # Widget spacing rule: double the 6px platform default.
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(12)
        form.addRow(self.SOURCE_LABEL, src_row)
        if src2_row is not None:
            form.addRow(self.SOURCE2_LABEL, src2_row)
        form.addRow("New tool database:", db_row)
        form.addRow("Units:", self.units_combo)

        note = QLabel(
            self.NOTE
            + "\n\nThis creates a new database file. It does not change the "
            "database this session already has open -- restart the "
            "application to use the new file."
        )
        note.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._do_import)
        buttons.rejected.connect(self.reject)
        self._ok_button = buttons.button(QDialogButtonBox.Ok)
        self._ok_button.setText("Import")

        layout = QVBoxLayout(self)
        # Dialog content padding: 12px ADDED on every side over the ~11px
        # platform default (which is what "content right on the edge"
        # looked like), so ~23px total. This HAS to be layout
        # contentsMargins, not stylesheet padding -- QSS padding on a
        # container QDialog is silently ignored by QLayout child placement
        # (verified by offscreen measurement).
        layout.setContentsMargins(23, 23, 23, 23)
        layout.setSpacing(12)  # double the 6px default between sections too
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addWidget(buttons)

    # ------------------------------------------------------------ hooks

    def _run_import(self, src_path, db_path, units, overwrite):
        """Run the actual conversion. Returns (imported_numbers, skipped)
        where skipped is a list of (label, reason) pairs (may be empty)."""
        raise NotImplementedError

    def _result_notes(self):
        """Importer-specific 'what to do next' text for the summary."""
        return ""

    # ------------------------------------------------------------ browse

    def _browse_src(self):
        path, _filter = QFileDialog.getOpenFileName(
            self, self.SOURCE_DIALOG_TITLE, self.src_path_edit.text(),
            self.SOURCE_FILTER,
        )
        if path:
            self.src_path_edit.setText(path)

    def _browse_src2(self):
        path, _filter = QFileDialog.getOpenFileName(
            self, self.SOURCE2_DIALOG_TITLE, self.src2_path_edit.text(),
            self.SOURCE2_FILTER,
        )
        if path:
            self.src2_path_edit.setText(path)

    def _browse_db(self):
        path, _filter = QFileDialog.getSaveFileName(
            self, "Save New Tool Database", self.db_path_edit.text(),
            "Tool Database (*.db);;All Files (*)",
        )
        if path:
            self.db_path_edit.setText(path)

    # ------------------------------------------------------------ import

    def _do_import(self):
        src_path = self.src_path_edit.text().strip()
        db_path = self.db_path_edit.text().strip()

        if not src_path or not os.path.isfile(src_path):
            QMessageBox.warning(self, self.WINDOW_TITLE,
                                 f"Select a valid file for '{self.SOURCE_LABEL.rstrip(':')}'.")
            return
        if self.src2_path_edit is not None:
            src2_path = self.src2_path_edit.text().strip()
            if not src2_path or not os.path.isfile(src2_path):
                QMessageBox.warning(self, self.WINDOW_TITLE,
                                     f"Select a valid file for '{self.SOURCE2_LABEL.rstrip(':')}'.")
                return
        if not db_path:
            QMessageBox.warning(self, self.WINDOW_TITLE,
                                 "Choose a destination for the new tool database.")
            return

        overwrite = False
        if os.path.exists(db_path):
            confirm = QMessageBox(self)
            confirm.setIcon(QMessageBox.Question)
            confirm.setWindowTitle("Replace Existing File")
            confirm.setText(f"{db_path} already exists.")
            confirm.setInformativeText(
                "Replacing it creates a brand new starting-point database "
                "from the source file -- it does not merge with what's "
                "already there. If this is your active tool database, the "
                "replacement only takes effect after restarting the "
                "application."
            )
            confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            confirm.setDefaultButton(QMessageBox.Cancel)
            yes_btn = confirm.button(QMessageBox.Yes)
            yes_btn.setText("Replace It")
            if confirm.exec() != QMessageBox.Yes:
                return
            overwrite = True

        try:
            imported, skipped = self._run_import(
                src_path, db_path, self.units_combo.currentText(), overwrite)
        except Exception as exc:
            LOG.error("Tool data import failed: %s", exc)
            QMessageBox.critical(self, "Import Failed", str(exc))
            return

        ini_note = ""
        set_active = QMessageBox(self)
        set_active.setIcon(QMessageBox.Question)
        set_active.setWindowTitle("Set as Active Tool Database")
        set_active.setText(f"Set {os.path.basename(db_path)} as the active tool database?")
        set_active.setInformativeText(
            "This updates the TOOL_DB_FILE line in this session's INI file "
            "so the new database loads on next startup -- it does not "
            "change anything in this running session. The INI is backed "
            "up first."
        )
        set_active.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        set_active.setDefaultButton(QMessageBox.Yes)
        yes_btn = set_active.button(QMessageBox.Yes)
        yes_btn.setText("Set as Active")
        no_btn = set_active.button(QMessageBox.No)
        no_btn.setText("Not Now")

        if set_active.exec() == QMessageBox.Yes:
            ini_path = Info().INI_FILE
            if not ini_path or not os.path.isfile(ini_path):
                QMessageBox.warning(
                    self, "Could Not Update INI",
                    "Could not determine this session's INI file -- set "
                    "TOOL_DB_FILE manually instead.")
            else:
                try:
                    action, backup_path = set_tool_db_file(ini_path, db_path)
                except Exception as exc:
                    LOG.error("Failed to update TOOL_DB_FILE in %s: %s", ini_path, exc)
                    QMessageBox.critical(
                        self, "INI Update Failed",
                        f"Could not update {ini_path}:\n{exc}\n\n"
                        "Set TOOL_DB_FILE manually instead.")
                else:
                    verb = "Updated" if action == "replaced" else "Added"
                    ini_note = (
                        f"\n\n{verb} TOOL_DB_FILE in {os.path.basename(ini_path)} "
                        f"(backup saved: {os.path.basename(backup_path)})."
                    )

        skipped_note = ""
        if skipped:
            skipped_note = "\n\nSkipped:\n" + "\n".join(
                f"  - {label}: {reason}" for label, reason in skipped)

        result = QMessageBox(self)
        result.setIcon(QMessageBox.Information)
        result.setWindowTitle("Import Complete")
        result.setText(f"Imported {len(imported)} tool(s) into {os.path.basename(db_path)}")
        result.setInformativeText(
            self._result_notes()
            + skipped_note
            + ini_note +
            "\n\nRestart the application to load this tool database."
        )
        result.setStandardButtons(QMessageBox.Ok)
        result.exec()
        self.accept()
