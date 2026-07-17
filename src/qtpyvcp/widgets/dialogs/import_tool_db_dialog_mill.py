# coding=utf-8
"""Mill-flavored import dialogs, built on ImportToolDbDialogBase (see
import_tool_db_dialog for the shared skeleton). The lathe counterpart is
import_tool_db_dialog_lathe -- same skeleton, lathe importers.

* ImportLegacyToolTableDialog -- classic LinuxCNC .tbl files. Uses the
  shared, machine-agnostic import_legacy_tbl (core columns only), same as
  the lathe.
* ImportFusionToolLibraryDialog -- Fusion 360 library exports (.tools /
  .json). Uses the mill Fusion importer (import_fusion_mill): tool numbers,
  cutting diameters (Fusion DC), and descriptions come across; the rich
  lathe insert/holder extras do not apply to a mill.
* ImportMergedToolDataDialog -- .tbl + Fusion merged by tool number
  (import_merged_mill): machine-setup data (offsets, pocket) from the .tbl,
  tool identity (diameter, description) from Fusion.

Every imported tool starts ATC-storable (the tool_mill.atc schema
default); mark oversize tools that do not fit the carousel in the tool
table editor's ATC column afterward.
"""

from qtpyvcp.lib.db_tool.import_legacy_tbl import import_tbl_to_db
from qtpyvcp.lib.db_tool.import_fusion_mill import import_fusion_to_db_mill
from qtpyvcp.lib.db_tool.import_merged_mill import import_merged_to_db_mill
from qtpyvcp.widgets.dialogs.import_tool_db_dialog import ImportToolDbDialogBase


class ImportLegacyToolTableDialog(ImportToolDbDialogBase):

    WINDOW_TITLE = "Import Legacy Tool Table"
    SOURCE_LABEL = "Legacy .tbl file:"
    SOURCE_DIALOG_TITLE = "Select Legacy Tool Table"
    SOURCE_FILTER = "Tool Table Files (*.tbl);;All Files (*)"
    NOTE = (
        "Every tool imports with its core LinuxCNC fields (position, "
        "diameter, remark). Every tool starts ATC-storable -- open the "
        "tool table editor afterward to mark any oversize tools that do "
        "not fit the carousel."
    )

    def _run_import(self, src_path, db_path, units, overwrite):
        imported = import_tbl_to_db(src_path, db_path, units=units,
                                     overwrite=overwrite)
        return imported, []

    def _result_notes(self):
        return (
            "Tools imported with their core LinuxCNC fields. Every tool is "
            "ATC-storable by default -- uncheck the ATC column in the tool "
            "table editor for any oversize tool that must be loaded by hand."
        )


class ImportFusionToolLibraryDialog(ImportToolDbDialogBase):

    WINDOW_TITLE = "Import Fusion 360 Tool Library"
    SOURCE_LABEL = "Fusion export:"
    SOURCE_DIALOG_TITLE = "Select Fusion 360 Tool Library Export"
    SOURCE_FILTER = "Fusion Tool Libraries (*.tools *.json);;All Files (*)"
    NOTE = (
        "Tool numbers (from each tool's post-process number), cutting "
        "diameters, and descriptions import from the library. X/Y/Z "
        "offsets and pocket are not part of a Fusion export -- set those "
        "by touch-off and the tool table editor before cutting."
    )

    def _run_import(self, src_path, db_path, units, overwrite):
        return import_fusion_to_db_mill(src_path, db_path, units=units,
                                        overwrite=overwrite)

    def _result_notes(self):
        return (
            "Tool numbers, diameters, and descriptions were imported from "
            "the library. Set each tool's X/Y/Z offsets by touch-off and "
            "its pocket in the tool table editor. Every tool is ATC-"
            "storable by default -- uncheck the ATC column for oversize "
            "tools."
        )


class ImportMergedToolDataDialog(ImportToolDbDialogBase):
    """Merge a legacy .tbl and a Fusion library into one database: machine-
    setup data (offsets, pocket) from the .tbl, tool identity (diameter,
    description) from Fusion, matched by tool number. A mill tool's D is a
    plain diameter in both sources, so the .tbl's measured value wins and
    Fusion's DC only fills gaps -- no nose-radius reinterpretation."""

    WINDOW_TITLE = "Import + Merge Tool Data"
    SOURCE_LABEL = "Legacy .tbl file:"
    SOURCE_DIALOG_TITLE = "Select Legacy Tool Table"
    SOURCE_FILTER = "Tool Table Files (*.tbl);;All Files (*)"
    SOURCE2_LABEL = "Fusion export:"
    SOURCE2_DIALOG_TITLE = "Select Fusion 360 Tool Library Export"
    SOURCE2_FILTER = "Fusion Tool Libraries (*.tools *.json);;All Files (*)"
    NOTE = (
        "Merges both sources into one table, matched by tool number: "
        "offsets and pocket come from the .tbl; cutting diameter and "
        "description come from Fusion (the .tbl's diameter wins when it "
        "carried one). Tools present in only one source still import."
    )

    def _run_import(self, src_path, db_path, units, overwrite):
        fusion_path = self.src2_path_edit.text().strip()
        return import_merged_to_db_mill(src_path, fusion_path, db_path,
                                        units=units, overwrite=overwrite)

    def _result_notes(self):
        return (
            "Merged: machine-setup data from the .tbl, tool identity from "
            "the Fusion library. Review the tool table editor before "
            "cutting -- especially any tools noted below as present in only "
            "one source. Every tool is ATC-storable by default; uncheck the "
            "ATC column for oversize tools."
        )
