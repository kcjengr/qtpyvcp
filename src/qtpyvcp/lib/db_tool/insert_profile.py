# coding=utf-8
"""Lathe insert display data, straight from the tool database.

The single insert-geometry source for probe_basic's VTK lathe tool
rendering (plan §6 Phase 5, ratified 2026-07-08): users describe a tool
in the probe_basic tool table (type, insert shape/size, holder
dimensions, nose radius via D) and VTK renders exactly that -- no
library files, no import step, one source of truth.

Two-stage, all schema-native:

* ``insert_record(core, extras, remark)`` -- flattens a DB core row +
  tool_lathe extras into one typed record keyed by schema column names.
* ``compute_insert_profile(record)`` -- dispatches directly into the
  shape builders of :mod:`qtpyvcp.lib.lathe_insert_geometry` with
  explicit arguments and returns a profile document
  ``{profile_format, family, insert_polygon_xz, dimensions}``.

D semantics (plan §5.1): the DB stores D as a *diameter*. Turning-family
tools (turning/boring/grooving/parting/threading) get
``nose_radius = D / 2``; drills and taps get ``drill_diameter = D``
unchanged. Tools with no extras row, or type ``custom``/unset, are
rendered as ISO turning inserts from whatever insert fields they carry
(the shape falls back to a C-style diamond exactly as the geometry
builder always has).

The conversational add-on's QML preview computes its polygons through a
byte-equal copy of the same shape builders (fed from its own inputs);
the add-on's golden suite pins this module's output polygon-for-polygon
against that path, so the two renderers can never silently disagree
about the same database row.
"""

from qtpyvcp.lib.lathe_insert_geometry import (
    ISO_INSERT_STYLE_SPECS,
    InsertShape,
    _build_tap_profile_points,
    _resolve_sidecut_zero_edge_offset_deg,
    _rotate_profile_points_xz,
    build_drill_shape,
    build_groove_shape,
    build_iso_ic_diamond_shape,
    build_regular_polygon_shape,
    build_rhombic_shape,
    build_round_shape,
    build_thread_shape,
    build_trigon_shape,
    ensure_ccw,
    first_positive,
    normalize_style_key,
)

TURNING_FAMILY = frozenset({'turning', 'boring', 'grooving', 'parting',
                            'threading'})
ROUND_TOOLS = frozenset({'drill', 'tap'})

_POLYGON_SIDES = {'triangle': 3, 'pentagon': 5, 'hexagon': 6, 'octagon': 8}


def _num(value):
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _text(value):
    return str(value or '').strip()


def insert_record(core, extras, remark=''):
    """One flat, typed record of everything insert rendering needs,
    keyed by the schema's own column names."""
    extras = extras or {}
    tool_type = _text(extras.get('type')).lower()
    d_diameter = _num(core.get('D'))
    is_round = tool_type in ROUND_TOOLS

    return {
        'tool_no': int(core.get('T', 0) or 0),
        'type': tool_type,
        'remark': _text(remark or core.get('R')),
        'nose_radius': 0.0 if is_round else d_diameter / 2.0,
        'drill_diameter': d_diameter if is_round else 0.0,
        'is_round_tool': is_round,
        'insert_shape': _text(extras.get('insert_shape')),
        'insert_size_mode': _text(extras.get('insert_size_mode')).upper(),
        'insert_size': _num(extras.get('insert_size')),
        'insert_thickness': _num(extras.get('insert_thickness')),
        'groove_width': _num(extras.get('groove_width')),
        'max_depth_of_cut': _num(extras.get('max_depth_of_cut')),
        'drill_point_angle': _num(extras.get('drill_point_angle')),
        'flute_length': _num(extras.get('flute_length')),
        'overall_length': _num(extras.get('overall_length')),
        'shaft_diameter': _num(extras.get('shaft_diameter')),
        'chamfer_threads': _num(extras.get('chamfer_threads')),
        'thread_pitch_max': _num(extras.get('thread_pitch_max')),
        # Kept distinct from the max: the two ends size different things --
        # TPX the tooth, TPN the nose radius.
        'thread_pitch_min': _num(extras.get('thread_pitch_min')),
        'thread_angle': _num(extras.get('thread_angle')),
        'thread_tip_type': _text(extras.get('thread_tip_type')).lower(),
        'holder_style': _text(extras.get('holder_style')),
        'holder_hand': _text(extras.get('holder_hand')).upper(),
        'holder_shank_width': _num(extras.get('holder_shank_width')),
        'holder_cut_width': _num(extras.get('holder_cut_width')),
        'holder_oal': _num(extras.get('holder_oal')),
    }


def holder_style_code(record):
    """The holder style in the form the geometry/rotation logic keys on:
    full ISO turning codes (SCLCR, SDJCL, ...) reduce to their style
    letter (index 2, lowercased); descriptive values ('GROOVE EXTERNAL',
    'BORING BAR L') pass through lowercased."""
    text = record['holder_style']
    upper = text.upper()
    if (len(upper) >= 4 and upper.isalpha() and upper[0] == 'S'
            and upper[-1] in ('R', 'L', 'N') and ' ' not in upper):
        return upper[2].lower()
    return text.lower()


def is_internal_groove(record):
    """Internal grooving/parting detection: the holder style names it, or
    the remark says internal (and not external)."""
    style = holder_style_code(record)
    remark = record['remark'].lower()
    return ('internal' in style
            or ('internal' in remark and 'external' not in remark))


def internal_groove_max_depth(record):
    """Internal-groove usable depth = holder cut width - shank/2 (plan
    §4), or None when the holder dimensions aren't recorded."""
    cut_width = record['holder_cut_width']
    shank = record['holder_shank_width']
    if cut_width > 0.0 and shank > 0.0:
        return cut_width - 0.5 * shank
    return None


def _compute_shape(record):
    tool_type = record['type']

    if tool_type == 'tap':
        major = first_positive(record['drill_diameter'], 0.5)
        pitch = first_positive(record['thread_pitch_max'], 0.05)
        flute = first_positive(record['flute_length'], 1.2)
        overall = first_positive(record['overall_length'], 3.0)
        shaft = first_positive(record['shaft_diameter'], major * 0.75)
        angle = first_positive(record['thread_angle'], 60.0)
        chamfer = first_positive(record['chamfer_threads'], 2.5)
        points = _build_tap_profile_points(major, pitch, flute, overall,
                                           shaft, chamfer)
        return InsertShape(
            family='tap',
            points_xz=ensure_ccw(points),
            dims={
                'diameter': float(major),
                'pitch': float(pitch),
                'flute_length_z': float(flute),
                'overall_length_z': float(overall),
                'shaft_diameter': float(shaft),
                'thread_angle_deg': float(angle),
                'chamfer_threads': float(chamfer),
                'tip_angle_deg': 180.0,
            },
        )

    if tool_type == 'drill':
        diameter = first_positive(record['drill_diameter'], 0.125)
        tip_angle = first_positive(record['drill_point_angle'], 118.0)
        body = first_positive(record['flute_length'],
                              record['overall_length'], 1.0)
        return build_drill_shape(body, diameter, tip_angle)

    nose_radius = max(0.0, record['nose_radius'])
    insert_size = first_positive(record['insert_size'],
                                 record['holder_cut_width'],
                                 record['insert_thickness'], 0.24)

    if tool_type == 'threading':
        # Built as a construction from driven dimensions, so length/width only
        # survive as fallbacks for a row with no insert size. See
        # build_thread_shape.
        #
        # Length is the INSERT's overall length, never the holder's -- the two
        # are different blocks in the Fusion export and mean different things.
        # On a DOUBLE it is the bar tip to tip.
        # A threading insert is dimensioned from insert_size and insert_width,
        # never from an overall length -- an insert has one and so does its
        # holder, and the two mean different things. These two only survive as
        # fallbacks for a row that records neither.
        length = first_positive(record['insert_size'],
                                record['insert_thickness'], 0.24)
        width = first_positive(record['insert_thickness'], length, 0.06)
        return build_thread_shape(
            length, width,
            first_positive(record['thread_angle'], 60.0),
            record['thread_tip_type'] or 'point',
            nose_radius,
            first_positive(record['thread_pitch_max'], 0.0),
            first_positive(record['thread_pitch_min'], 0.0),
            first_positive(record['insert_size'], 0.0),
            record['insert_size_mode'],
            # Which body to build: TRIPLE is a triangle, DOUBLE a 2-ended bar.
            record['insert_shape'])

    if tool_type in ('grooving', 'parting'):
        internal_depth = (internal_groove_max_depth(record)
                          if is_internal_groove(record) else None)
        # insert_size is deliberately NOT in either chain. On a blade the
        # tool table shows groove_width in the Insert Size cell, so a stored
        # insert_size is a shadowed value the operator cannot see -- reading
        # it as a fallback would draw the tool from a number that is not on
        # screen anywhere.
        length = first_positive(internal_depth,
                                record['max_depth_of_cut'],
                                record['insert_thickness'],
                                record['holder_cut_width'], 0.24)
        width = first_positive(record['groove_width'],
                               record['holder_cut_width'], 0.06)
        return build_groove_shape(length, width, nose_radius)

    # ISO turning/boring inserts (and untyped/custom tools, which render
    # from whatever insert fields they carry).
    style_key = normalize_style_key(record['insert_shape'])
    style_spec = ISO_INSERT_STYLE_SPECS.get(style_key)
    if style_spec is None:
        style_spec = ISO_INSERT_STYLE_SPECS['c']
    family = str(style_spec.get('family') or 'diamond')
    nose_angle = style_spec.get('nose_angle_deg')
    nose_angle = 80.0 if nose_angle is None else float(nose_angle)

    length = float(insert_size)
    width = first_positive(record['insert_size'], length, 0.06)

    if family == 'trigon':
        return build_trigon_shape(length, width, nose_angle, style_key,
                                  nose_radius)
    if family == 'round':
        return build_round_shape(length, width, nose_radius, style_key)
    if family in _POLYGON_SIDES:
        return build_regular_polygon_shape(length, width,
                                           _POLYGON_SIDES[family],
                                           style_key, nose_radius)
    if (family in ('diamond', 'parallelogram')
            and record['insert_size_mode'] == 'IC'):
        return build_iso_ic_diamond_shape(insert_size, nose_angle,
                                          style_key, nose_radius)
    return build_rhombic_shape(length, width, nose_angle, nose_radius,
                               style_key)


def compute_insert_profile(record):
    """Profile document for one tool record -- same output shape the
    geometry builders have always produced: ``{profile_format, family,
    insert_polygon_xz, dimensions}``."""
    if not isinstance(record, dict):
        return None

    style_key = normalize_style_key(record['insert_shape'])
    style_spec = ISO_INSERT_STYLE_SPECS.get(style_key)
    iso_nose_angle = (style_spec.get('nose_angle_deg')
                      if isinstance(style_spec, dict) else None)

    shape = _compute_shape(record)
    polygon = [[float(x), float(z)] for x, z in shape.points_xz]

    sidecut_offset = _resolve_sidecut_zero_edge_offset_deg(shape,
                                                           iso_nose_angle)
    if abs(float(sidecut_offset)) > 1e-12:
        rotated = _rotate_profile_points_xz(polygon, sidecut_offset,
                                            origin_x=0.0, origin_z=0.0)
        if rotated:
            polygon = [[float(x), float(z)] for x, z in ensure_ccw(rotated)]

    return {
        'profile_format': 1,
        'family': shape.family,
        'insert_polygon_xz': polygon,
        'dimensions': shape.dims,
    }
