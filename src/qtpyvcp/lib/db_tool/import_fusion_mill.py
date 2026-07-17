# coding=utf-8
"""Import a Fusion 360 tool library export into a fresh tool database, mill
flavor.

The mill counterpart of import_fusion_tools (which is lathe-flavored). It
reuses that module's generic, machine-agnostic parsing helpers
(load_fusion_library, _Numbers, _make_standalone_engine) and import_merged's
_fusion_tools_by_number, but differs in two deliberate ways:

* Diameter: a milling tool's cutting diameter is Fusion geometry DC, taken
  straight through. There is no nose-radius reinterpretation (the lathe
  importer doubles RE for the turning family, because a lathe tool's D is a
  nose radius) -- for a mill, D is simply the tool diameter LinuxCNC uses
  for cutter compensation and display.
* Extras: none. The mill extras table (tool_mill, schema v3) is just the
  ATC-storable boolean, which Fusion has no concept of. Tools import
  core-only, exactly like the plain .tbl importer; every tool reads as
  atc = storable (the schema default) until the user marks the oversize
  exceptions in the tool table editor. This is the only honest default --
  Fusion cannot know which of a shop's tools physically fit its carousel.

What a Fusion export does NOT carry, same as the lathe importer: LinuxCNC
tool offsets (X/Y/Z) and pocket. Those are machine-setup data -- they
import as their defaults and get set by touch-off / the tool table editor
(or merged in from a .tbl, see import_merged_mill).

Usage:
    fusion2db-mill library.tools output.db
    fusion2db-mill library.json output.db --units mm
"""

import argparse
import sys

from .import_common import guard_overwrite, new_tool_db_session, validate_units
from .import_fusion_tools import _Numbers, load_fusion_library
from .import_merged import _fusion_tools_by_number
from .tool_table import Tool


def fusion_mill_diameter(geo, num):
    """Cutting diameter for a mill tool from Fusion geometry: DC (diameter
    of cut), falling back to SFDM (shaft diameter) for the odd tool that
    declares no DC (e.g. a probe). 0.0 if neither is present."""
    return num.first_positive(geo.get('DC'), geo.get('SFDM')) or 0.0


def import_fusion_to_db_mill(src_path, db_path, units='inch', overwrite=False):
    """Create a fresh tool database at db_path from a Fusion 360 tool
    library export (.tools or .json), mill flavor (core columns only).

    Returns (imported_tool_numbers, skipped) with the same shape and
    file-safety guarantees as import_fusion_tools.import_fusion_to_db:
    refuses an existing db_path unless overwrite=True, runs on its own
    standalone engine, so it is safe to call from a running GUI process.
    """
    validate_units(units)
    guard_overwrite(db_path, overwrite)

    skipped = []
    by_number = _fusion_tools_by_number(load_fusion_library(src_path), skipped)
    if not by_number:
        raise ValueError("No usable tools found in %s -- nothing to import"
                          % src_path)

    with new_tool_db_session(db_path, units) as session:
        for tool_no in sorted(by_number):
            tool = by_number[tool_no]
            num = _Numbers(tool.get('unit'), units)
            geo = tool.get('geometry') or {}
            session.add(Tool(
                tool_no=tool_no,
                pocket=-1,
                diameter=fusion_mill_diameter(geo, num),
                remark=str(tool.get('description') or ''),
            ))

    return sorted(by_number), skipped


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Import a Fusion 360 tool library export (.tools or "
                     ".json) into a fresh tool database, mill flavor. Tool "
                     "numbers, cutting diameters, and descriptions come "
                     "across; X/Y/Z offsets and pocket are not part of a "
                     "Fusion export and start at their defaults -- set them "
                     "by touch-off / the tool table editor. Every tool "
                     "imports as ATC-storable; mark oversize exceptions in "
                     "the tool table editor.")
    parser.add_argument('fusion_file', help="Path to the .tools or .json export")
    parser.add_argument('db_file', help="Path to write the new .db file")
    parser.add_argument('--units', choices=('inch', 'mm'), default='inch',
                         help="Unit system for the new database (default: inch)")
    parser.add_argument('--overwrite', action='store_true',
                         help="Replace db_file if it already exists")
    args = parser.parse_args(argv)

    try:
        imported, skipped = import_fusion_to_db_mill(
            args.fusion_file, args.db_file, units=args.units,
            overwrite=args.overwrite)
    except (ValueError, FileExistsError) as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 1

    print("Imported %d tool(s) from %s -> %s (%s)" %
          (len(imported), args.fusion_file, args.db_file, args.units))
    print("Tool numbers: %s" % ', '.join(str(t) for t in imported))
    for label, reason in skipped:
        print("Skipped: %s -- %s" % (label, reason))
    print()
    print("Tool numbers, diameters, and descriptions were imported. X/Y/Z "
          "offsets and pocket are not part of a Fusion export -- set them by "
          "touch-off and the tool table editor. Every tool imported as "
          "ATC-storable; uncheck oversize tools in the ATC column.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
