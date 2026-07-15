# coding=utf-8
"""Import a Fusion 360 tool library export into a fresh schema-v1 tool
database.

Accepts both export formats Fusion produces: a raw ``*.json`` library and
the native ``*.tools`` file (a ZIP wrapping ``tools.json``).

Unlike the legacy ``.tbl`` importer (import_legacy_tbl -- deliberately
untyped, because a .tbl carries no type information), a Fusion library
EXPLICITLY declares every tool's type, so this importer safely assigns
``tool_lathe.type`` and populates the full extras row: insert shape/size,
holder style/hand/dimensions, groove width, drill/tap geometry, threading
fields, and feeds/speeds presets. With the type set, the schema's D
semantics apply (diameter = 2 x nose radius for the turning family, plain
diameter for drill/tap) and the values are derived accordingly from the
Fusion geometry (RE / thread-tip-radius / DC / SFDM).

The field mapping is ported from the ratified schema-v1 seed generator
(pb_lathe_conv docs/schema_v1/generate_seed.py, frozen 2026-07-03) and its
audit (schema_v1_audit.md section 2) -- the reverse direction of
qtpyvcp.lib.db_tool.insert_profile's DB->Fusion translator.

What a Fusion export does NOT carry: LinuxCNC tool offsets (X/Z), the
front/back angles (I/J), and the lathe orientation code (Q). Those are
machine-setup data, not library data -- they import as 0 and get set by
touch-off / the tool table editor afterward.

Unit handling: each Fusion tool declares its own ``unit`` ("inches" /
"millimeters"); bare numbers are in that unit, while expression strings may
carry an explicit unit of their own ("0.04 mm" on an inch tool) which wins.
Everything is normalized to the new database's canonical unit system.
Lengths convert by 25.4, surface speed (SFM<->SMM) by 0.3048, and
angle/count fields are never converted.

Usage:
    fusion2db library.tools output.db
    fusion2db library.json output.db --units mm
"""

import argparse
import json
import os
import re
import sys
import zipfile

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from .migrate import run_migrations
from .tool_table import Meta, Tool, ToolLathe

NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
HOLDER_CODE_RE = re.compile(r"\b(S[A-Z]{2,5}[RLN])\b")

TURNING_FAMILY = ("turning", "boring", "grooving", "parting", "threading")

# Conversion classes for _Numbers: how a value scales between unit systems.
LENGTH = "length"            # 25.4 mm/inch
ANGLE = "angle"              # never converted (degrees, thread counts, ...)
SURFACE_SPEED = "surface"    # 0.3048 m/ft (SFM <-> SMM)


def _make_standalone_engine(db_path):
    """Fresh engine bound only to db_path -- same standalone pattern (and
    same rationale) as import_legacy_tbl: never touches the process-global
    db_tool engine a running GUI may have open."""
    eng = create_engine('sqlite:///%s' % db_path, echo=False)

    @event.listens_for(eng, 'connect')
    def _sqlite_pragmas(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.execute('PRAGMA busy_timeout=5000')
        cursor.close()

    return eng


def load_fusion_library(path):
    """Tool dict list from a Fusion export -- either a raw .json library or
    the native .tools ZIP (tools.json member)."""
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            member = 'tools.json'
            if member not in zf.namelist():
                json_members = [n for n in zf.namelist() if n.lower().endswith('.json')]
                if not json_members:
                    raise ValueError(
                        "%s is a ZIP archive but contains no tools.json -- "
                        "not a Fusion tool library export" % path)
                member = json_members[0]
            payload = json.loads(zf.read(member))
    else:
        with open(path) as fh:
            payload = json.load(fh)

    tools = payload.get('data')
    if not isinstance(tools, list):
        raise ValueError(
            "%s has no 'data' tool list -- not a Fusion tool library export" % path)
    return tools


def map_type(fusion_type):
    """Fusion type string -> schema-v1 tool_lathe.type (ratified mapping)."""
    t = str(fusion_type or "").lower()
    if "tap" in t:
        return "tap"
    if "drill" in t:
        return "drill"
    if "thread" in t:
        return "threading"
    if "part" in t:
        return "parting"
    if "groov" in t:
        return "grooving"
    if "boring" in t:
        return "boring"
    if "turning" in t or "profil" in t:
        return "turning"
    return "custom"


class _Numbers:
    """Unit-aware numeric parsing for one tool.

    Bare numbers are in the tool's own declared unit; an explicit unit
    inside a string value ("0.04 mm", ".65 in") wins over that. Values
    normalize to the target unit system by conversion class -- length
    (25.4), surface speed (0.3048), or angle/count (no conversion).
    """

    def __init__(self, tool_unit, target_units):
        self.tool_is_mm = 'mm' in str(tool_unit or '').lower() or \
                          'milli' in str(tool_unit or '').lower()
        self.target_is_mm = (target_units == 'mm')

    def _convert(self, value, value_is_mm, kind):
        if kind == ANGLE or value_is_mm == self.target_is_mm:
            return value
        if kind == SURFACE_SPEED:
            # SMM -> SFM or SFM -> SMM (meters <-> feet)
            return value / 0.3048 if value_is_mm else value * 0.3048
        return value / 25.4 if value_is_mm else value * 25.4

    def parse(self, raw, kind=LENGTH):
        """First numeric token of raw, normalized to the target units."""
        if raw is None:
            return None
        if isinstance(raw, bool):
            return None
        if isinstance(raw, (int, float)):
            return self._convert(float(raw), self.tool_is_mm, kind)
        text = str(raw).strip()
        m = NUM_RE.search(text)
        if not m:
            return None
        value = float(m.group(0))
        lowered = text.lower()
        if 'mm' in lowered:
            value_is_mm = True
        elif 'in' in lowered:
            value_is_mm = False
        else:
            value_is_mm = self.tool_is_mm
        return self._convert(value, value_is_mm, kind)

    def first_positive(self, *vals, **kwargs):
        kind = kwargs.get('kind', LENGTH)
        for v in vals:
            n = self.parse(v, kind=kind)
            if n is not None and n > 0.0:
                return n
        return None


def extras_from_fusion(tool, ttype, num):
    """tool_lathe extras dict from one Fusion tool (ratified seed-generator
    mapping, made unit-aware via _Numbers)."""
    geo = tool.get("geometry") or {}
    holder = tool.get("holder") or {}
    expr = tool.get("expressions") or {}
    presets = ((tool.get("start-values") or {}).get("presets") or [{}])
    preset = presets[0] if presets else {}

    holder_style = None
    m = HOLDER_CODE_RE.search(str(tool.get("description") or ""))
    if m:
        holder_style = m.group(1)
    elif str(holder.get("THSC") or "").strip():
        holder_style = str(holder.get("THSC")).strip().upper()

    hand = str(holder.get("HAND") or "").strip().upper() or None
    if hand not in ("R", "L"):
        setup_hand = (tool.get("setup") or {}).get("HAND")
        hand = "R" if setup_hand is True else ("L" if setup_hand is False else None)

    size_mode_raw = str(geo.get("SIZE_SPECIFICATION_MODE") or "").strip().upper()
    insert_size = num.first_positive(
        geo.get("INSD"), geo.get("tool_insertSize"), expr.get("tool_insertSize"),
        expr.get("tool_cuttingWidth"), holder.get("CW"), geo.get("S"),
    )
    size_mode = None
    if insert_size is not None:
        size_mode = "IC" if size_mode_raw == "IC" else "edge_length"

    is_groove = ttype in ("grooving", "parting")
    is_round_tool = ttype in ("drill", "tap")
    is_thread = ttype == "threading"

    return {
        "type": ttype,
        "insert_shape": (str(geo.get("SC") or "").strip().upper() or None)
                        if not is_round_tool else None,
        "insert_size_mode": size_mode if not is_round_tool else None,
        "insert_size": insert_size if not is_round_tool else None,
        "insert_thickness": num.first_positive(geo.get("S"), expr.get("tool_thickness"))
                            if not is_round_tool else None,
        "holder_style": holder_style if not is_round_tool else None,
        "holder_hand": hand if not is_round_tool else None,
        "holder_shank_width": num.first_positive(holder.get("W")) if not is_round_tool else None,
        "holder_cut_width": num.first_positive(holder.get("CW")) if not is_round_tool else None,
        "holder_oal": num.first_positive(holder.get("OAL")) if not is_round_tool else None,
        "groove_width": num.first_positive(
            geo.get("tool_grooveWidth"), expr.get("tool_grooveWidth"),
            geo.get("tool_insertWidth"), expr.get("tool_insertWidth"),
        ) if is_groove else None,
        "max_depth_of_cut": num.first_positive(
            geo.get("H"), holder.get("H"),
            expr.get("tool_maxDOC"), expr.get("tool_maxDepthOfCut"),
        ) if is_groove else None,
        "drill_point_angle": num.first_positive(
            geo.get("SIG"), expr.get("tool_tipAngle"), kind=ANGLE,
        ) if ttype == "drill" else None,
        "flute_length": num.first_positive(
            geo.get("LCF"), geo.get("LB"), expr.get("tool_fluteLength"),
        ) if is_round_tool else None,
        "overall_length": num.first_positive(
            geo.get("OAL"), expr.get("tool_overallLength"),
        ) if (is_round_tool or is_thread) else None,
        "shaft_diameter": num.first_positive(
            geo.get("SFDM"), expr.get("tool_shaftDiameter"),
        ) if is_round_tool else None,
        "chamfer_threads": num.first_positive(
            geo.get("tap_chamfer_threads"), kind=ANGLE,
        ) if ttype == "tap" else None,
        "thread_pitch_max": num.first_positive(
            geo.get("TPX"), geo.get("TP"), geo.get("TPN"),
            expr.get("tool_maxThreadPitch"), expr.get("tool_threadPitch"),
        ) if (is_thread or ttype == "tap") else None,
        "thread_angle": (num.first_positive(geo.get("thread-profile-angle"), kind=ANGLE) or 60.0)
                        if (is_thread or ttype == "tap") else None,
        "thread_tip_type": (str(geo.get("thread-tip-type") or "").strip().lower() or "point")
                           if is_thread else None,
        "surface_speed": num.first_positive(preset.get("v_c"), kind=SURFACE_SPEED),
        "feed_per_rev": num.first_positive(preset.get("f_n")),
        "depth_of_cut": num.first_positive(preset.get("depth-of-cut")),
        "notes": "",
    }


def import_fusion_to_db(src_path, db_path, units='inch', overwrite=False):
    """Create a fresh schema-v1 tool database at db_path from a Fusion 360
    tool library export (.tools or .json).

    Returns (imported_tool_numbers, skipped) where skipped is a list of
    (label, reason) strings for entries that could not become tools --
    bare holder entries, tools with no post-process number (nothing to use
    as T#), and duplicate tool numbers (first occurrence wins, matching
    the seed generator's behavior).

    Refuses to touch an existing file unless overwrite=True, and uses its
    own standalone engine -- safe to call from inside a running GUI process
    (same guarantees as import_legacy_tbl.import_tbl_to_db).
    """
    if units not in ('inch', 'mm'):
        raise ValueError("units must be 'inch' or 'mm', got %r" % units)

    if os.path.exists(db_path):
        if not overwrite:
            raise FileExistsError(
                "%s already exists -- pass overwrite=True (or --overwrite) "
                "to replace it. This creates a new starting-point database, "
                "it does not merge into an existing one." % db_path)
        os.remove(db_path)

    entries = load_fusion_library(src_path)

    tools = {}
    skipped = []
    for tool in entries:
        description = str(tool.get('description') or '').strip()
        fusion_type = str(tool.get('type') or '').strip()
        label = description or fusion_type or 'unnamed entry'

        if fusion_type.lower() == 'holder':
            skipped.append((label, 'bare holder entry, not a tool'))
            continue

        raw_num = (tool.get('post-process') or {}).get('number')
        try:
            tool_no = int(raw_num)
        except (TypeError, ValueError):
            tool_no = 0
        if tool_no <= 0:
            skipped.append((label, 'no post-process tool number'))
            continue
        if tool_no in tools:
            skipped.append((label, 'duplicate tool number T%d (first kept)' % tool_no))
            continue

        ttype = map_type(fusion_type)
        num = _Numbers(tool.get('unit'), units)
        geo = tool.get('geometry') or {}

        # D per schema section 5.1: type IS set here, so diameter really
        # means diameter -- drill/tap take it directly, the turning family
        # doubles the nose radius.
        if ttype in ('drill', 'tap'):
            d_val = num.first_positive(geo.get('DC'), geo.get('SFDM')) or 0.0
        else:
            d_val = 2.0 * (num.first_positive(
                geo.get('RE'), geo.get('thread-tip-radius')) or 0.0)

        tools[tool_no] = {
            'core': {
                'tool_no': tool_no,
                'pocket': -1,
                'diameter': d_val,
                'remark': description,
            },
            'extras': extras_from_fusion(tool, ttype, num),
        }

    if not tools:
        raise ValueError("No usable tools found in %s -- nothing to import"
                          % src_path)

    engine = _make_standalone_engine(db_path)
    run_migrations(engine)

    session = sessionmaker(bind=engine)()
    try:
        meta = session.query(Meta).first()
        meta.units = units

        for tool_no in sorted(tools):
            record = tools[tool_no]
            tool_row = Tool(**record['core'])
            tool_row.lathe = ToolLathe(**record['extras'])
            session.add(tool_row)

        session.commit()
    finally:
        session.close()
        engine.dispose()

    return sorted(tools.keys()), skipped


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Import a Fusion 360 tool library export (.tools or "
                     ".json) into a fresh schema-v1 tool database. Tool "
                     "types and insert/holder data come across from the "
                     "library; machine-setup values (X/Z offsets, I/J "
                     "angles, Q orientation) are not part of a Fusion "
                     "export and start at 0 -- set them by touch-off / the "
                     "tool table editor.")
    parser.add_argument('fusion_file', help="Path to the .tools or .json export")
    parser.add_argument('db_file', help="Path to write the new .db file")
    parser.add_argument('--units', choices=('inch', 'mm'), default='inch',
                         help="Unit system for the new database (default: inch)")
    parser.add_argument('--overwrite', action='store_true',
                         help="Replace db_file if it already exists")
    args = parser.parse_args(argv)

    try:
        imported, skipped = import_fusion_to_db(
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
    print("Tool types and insert/holder data were imported from the "
          "library. X/Z offsets, front/back angles (I/J), and orientation "
          "(Q) are not part of a Fusion export -- set them by touch-off "
          "and the tool table editor before cutting.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
