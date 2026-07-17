# coding=utf-8
"""Lathe-flavored import dialogs, built on ImportToolDbDialogBase (see
import_tool_db_dialog for the shared skeleton). The mill counterpart is
import_tool_db_dialog_mill -- same skeleton, mill importers.

* ImportLegacyToolTableDialog -- classic LinuxCNC .tbl files. Deliberately
  minimal: every tool imports untyped (see
  qtpyvcp.lib.db_tool.import_legacy_tbl for why guessing a type risks a
  silent 2x diameter error).
* ImportFusionToolLibraryDialog -- Fusion 360 library exports (.tools /
  .json). Fusion declares each tool's type explicitly, so types and the
  full insert/holder/threading extras come across; machine-setup values
  (X/Z offsets, I/J angles, Q orientation) aren't part of a Fusion export
  and start at 0.
* ImportMergedToolDataDialog -- .tbl + Fusion merged by tool number:
  machine-setup data (offsets/angles/orientation) from the .tbl, tool
  types + insert/holder data from Fusion.
"""

from qtpyvcp.lib.db_tool.import_legacy_tbl import import_tbl_to_db
from qtpyvcp.lib.db_tool.import_fusion_tools import import_fusion_to_db
from qtpyvcp.lib.db_tool.import_merged import import_merged_to_db
from qtpyvcp.widgets.dialogs.import_tool_db_dialog import ImportToolDbDialogBase


class ImportLegacyToolTableDialog(ImportToolDbDialogBase):

    WINDOW_TITLE = "Import Legacy Tool Table"
    SOURCE_LABEL = "Legacy .tbl file:"
    SOURCE_DIALOG_TITLE = "Select Legacy Tool Table"
    SOURCE_FILTER = "Tool Table Files (*.tbl);;All Files (*)"
    NOTE = (
        "Every tool imports with just its core LinuxCNC fields "
        "(position, angle, diameter, orientation, remark) -- no type "
        "is guessed. Open the tool table editor afterward to set each "
        "tool's type and fill in insert/holder data."
    )

    def _run_import(self, src_path, db_path, units, overwrite):
        imported = import_tbl_to_db(src_path, db_path, units=units,
                                     overwrite=overwrite)
        return imported, []

    def _result_notes(self):
        return (
            "These are untyped starting points -- open the tool table "
            "editor and set each tool's Type plus its insert/holder data "
            "to unlock insert previews, groove-width checks, and min-bore "
            "safety validation."
        )


class ImportFusionToolLibraryDialog(ImportToolDbDialogBase):

    WINDOW_TITLE = "Import Fusion 360 Tool Library"
    SOURCE_LABEL = "Fusion export:"
    SOURCE_DIALOG_TITLE = "Select Fusion 360 Tool Library Export"
    SOURCE_FILTER = "Fusion Tool Libraries (*.tools *.json);;All Files (*)"
    NOTE = (
        "Tool types and insert/holder/threading data import directly from "
        "the library (tool numbers come from each tool's post-process "
        "number). X/Z offsets, front/back angles (I/J), and orientation "
        "(Q) are not part of a Fusion export -- set those by touch-off "
        "and the tool table editor before cutting."
    )

    def _run_import(self, src_path, db_path, units, overwrite):
        return import_fusion_to_db(src_path, db_path, units=units,
                                    overwrite=overwrite)

    def _result_notes(self):
        return (
            "Tool types and insert/holder data were imported from the "
            "library. Set each tool's X/Z offsets by touch-off, and its "
            "front/back angles and orientation (Q) in the tool table "
            "editor, before cutting."
        )


class ImportMergedToolDataDialog(ImportToolDbDialogBase):
    """Merge a legacy .tbl and a Fusion library into one COMPLETE database:
    machine-setup data (offsets/angles/orientation) from the .tbl, tool
    types + insert/holder data from Fusion, matched by tool number. The
    Fusion type is also what makes the .tbl's D column safe to interpret
    (nose radius vs drill diameter), so merged tools get correctly-typed
    diameters neither source could provide alone."""

    WINDOW_TITLE = "Import + Merge Tool Data"
    SOURCE_LABEL = "Legacy .tbl file:"
    SOURCE_DIALOG_TITLE = "Select Legacy Tool Table"
    SOURCE_FILTER = "Tool Table Files (*.tbl);;All Files (*)"
    SOURCE2_LABEL = "Fusion export:"
    SOURCE2_DIALOG_TITLE = "Select Fusion 360 Tool Library Export"
    SOURCE2_FILTER = "Fusion Tool Libraries (*.tools *.json);;All Files (*)"
    NOTE = (
        "Merges both sources into one complete table, matched by tool "
        "number: offsets, angles, and orientation come from the .tbl; "
        "tool types and insert/holder data come from the Fusion library. "
        "Tools present in only one source still import, with that "
        "source's limitations noted in the summary."
    )

    def _run_import(self, src_path, db_path, units, overwrite):
        fusion_path = self.src2_path_edit.text().strip()
        return import_merged_to_db(src_path, fusion_path, db_path,
                                    units=units, overwrite=overwrite)

    def _result_notes(self):
        return (
            "Merged: machine-setup data from the .tbl, tool types and "
            "insert/holder data from the Fusion library. Review the tool "
            "table editor before cutting -- especially any tools noted "
            "below as present in only one source."
        )
