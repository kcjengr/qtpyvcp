"""Lathe insert/drill/tap cutting-profile shape math.

Computes 2D XZ cutting-profile polygons in a canonical local frame:
cutting tip at the origin, +X away from the tip, and (for drill/tap/
thread families) the body extending toward -Z.

This qtpyvcp copy contains the SHAPE MATH ONLY -- the database-native
entry point that feeds it lives in
:mod:`qtpyvcp.lib.db_tool.insert_profile` (probe_basic's VTK tool
rendering reads insert geometry exclusively from the unified tool
database; there is no tool-library-file reader in qtpyvcp). The
conversational add-on maintains its own copy of this shape math for its
2D QML preview, and its golden suite pins the two pipelines'
polygons against each other so the renderers can never silently
disagree.

Pure stdlib, no qtpyvcp/Qt imports.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

NUMBER_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")

ISO_INSERT_STYLE_SPECS = {
    "a": {"description": "85 degree parallelogram", "family": "parallelogram", "nose_angle_deg": 85.0},
    "b": {"description": "82 degree parallelogram", "family": "parallelogram", "nose_angle_deg": 82.0},
    "c": {"description": "80 degree diamond", "family": "diamond", "nose_angle_deg": 80.0},
    "d": {"description": "55 degree diamond", "family": "diamond", "nose_angle_deg": 55.0},
    "e": {"description": "75 degree diamond", "family": "diamond", "nose_angle_deg": 75.0},
    "h": {"description": "hexagon", "family": "hexagon", "nose_angle_deg": 120.0},
    "k": {"description": "55 degree parallelogram", "family": "parallelogram", "nose_angle_deg": 55.0},
    "l": {"description": "rectangle", "family": "rectangle", "nose_angle_deg": 90.0},
    "m": {"description": "86 degree diamond", "family": "diamond", "nose_angle_deg": 86.0},
    "n": {"description": "55 degree parallelogram", "family": "parallelogram", "nose_angle_deg": 55.0},
    "o": {"description": "octagon", "family": "octagon", "nose_angle_deg": 135.0},
    "p": {"description": "pentagon", "family": "pentagon", "nose_angle_deg": 108.0},
    "r": {"description": "round", "family": "round", "nose_angle_deg": None},
    "s": {"description": "square", "family": "square", "nose_angle_deg": 90.0},
    "t": {"description": "triangle", "family": "triangle", "nose_angle_deg": 60.0},
    "v": {"description": "35 degree diamond", "family": "diamond", "nose_angle_deg": 35.0},
    "w": {"description": "trigon", "family": "trigon", "nose_angle_deg": 80.0},
    "x": {"description": "special parallelogram", "family": "parallelogram", "nose_angle_deg": 85.0},
}

# DXF-derived normalized template for threading inserts.
# Coordinate frame:
# - y=1.0 is active cutting tip, y decreases toward insert tail.
# - x<0 is one flank, x>0 is the opposite flank.
THREAD_DXF_TEMPLATE_POINTS = [
    (0.0000000000000000, 1.0000000000000000),
    (-0.0721590686053788, 0.8750158749950926),
    (-0.0721590686053788, 0.2499659409196191),
    (0.0000000000000000, 0.1249818159147117),
    (-0.0721590686053788, 0.0000000000000000),
    (0.0721590686053788, 0.0000000000000000),
    (0.6134675376554881, 0.3125238124926399),
    (0.6856266062608669, 0.4375079374975473),
    (0.8299447434716245, 0.4375079374975473),
    (0.7577856748662457, 0.5624920625024526),
    (0.2164772058161364, 0.8750158749950926),
    (0.0721590686053788, 0.8750158749950926),
]
THREAD_DXF_X_EXTENT_FROM_OAL = 0.5


def parse_number(raw_value, default=None):
    if isinstance(raw_value, bool):
        return float(int(raw_value))
    if isinstance(raw_value, (int, float)):
        return float(raw_value)

    text = str(raw_value or "").strip()
    if not text:
        return default

    match = NUMBER_RE.search(text)
    if match is None:
        return default

    return float(match.group(0))



def first_positive(*values):
    for value in values:
        parsed = parse_number(value, None)
        if parsed is not None and parsed > 0.0:
            return float(parsed)
    return 0.0


def normalize_style_key(style):
    text = str(style or "").strip().lower()
    if "groove" in text:
        return "groove"
    if "thread" in text:
        return "thread"

    for char in text:
        if "a" <= char <= "z":
            if char in ISO_INSERT_STYLE_SPECS:
                return char
            break

    return "generic"


def ensure_ccw(points):
    if len(points) < 3:
        return points

    area2 = 0.0
    for idx in range(len(points)):
        x1, y1 = points[idx]
        x2, y2 = points[(idx + 1) % len(points)]
        area2 += (x1 * y2) - (x2 * y1)

    if area2 < 0.0:
        return list(reversed(points))
    return points


def _normalize_angle(angle_rad):
    two_pi = 2.0 * math.pi
    value = angle_rad % two_pi
    return value if value >= 0.0 else (value + two_pi)


def _build_corner_fillet_points(prev_point, vertex_point, next_point, radius, min_segments=6):
    r = float(radius or 0.0)
    if r <= 0.0:
        return None

    vx, vz = vertex_point
    px, pz = prev_point
    nx, nz = next_point

    vec_prev = (px - vx, pz - vz)
    vec_next = (nx - vx, nz - vz)
    len_prev = math.hypot(vec_prev[0], vec_prev[1])
    len_next = math.hypot(vec_next[0], vec_next[1])
    if len_prev <= 1e-9 or len_next <= 1e-9:
        return None

    u_prev = (vec_prev[0] / len_prev, vec_prev[1] / len_prev)
    u_next = (vec_next[0] / len_next, vec_next[1] / len_next)

    dot_val = max(-1.0, min(1.0, (u_prev[0] * u_next[0]) + (u_prev[1] * u_next[1])))
    interior = math.acos(dot_val)
    if interior <= 1e-6 or interior >= (math.pi - 1e-6):
        return None

    max_radius = min(len_prev, len_next) * math.tan(0.5 * interior) * 0.95
    r_eff = min(r, max_radius)
    if r_eff <= 1e-9:
        return None

    tangent_dist = r_eff / max(1e-9, math.tan(0.5 * interior))
    tangent_prev = (vx + (u_prev[0] * tangent_dist), vz + (u_prev[1] * tangent_dist))
    tangent_next = (vx + (u_next[0] * tangent_dist), vz + (u_next[1] * tangent_dist))

    bisector = (u_prev[0] + u_next[0], u_prev[1] + u_next[1])
    bisector_len = math.hypot(bisector[0], bisector[1])
    if bisector_len <= 1e-9:
        return None
    bisector = (bisector[0] / bisector_len, bisector[1] / bisector_len)

    center_dist = r_eff / max(1e-9, math.sin(0.5 * interior))
    cx = vx + (bisector[0] * center_dist)
    cz = vz + (bisector[1] * center_dist)

    a_start = _normalize_angle(math.atan2(tangent_prev[1] - cz, tangent_prev[0] - cx))
    a_end = _normalize_angle(math.atan2(tangent_next[1] - cz, tangent_next[0] - cx))
    a_vertex = _normalize_angle(math.atan2(vz - cz, vx - cx))

    sweep_ccw = (a_end - a_start) % (2.0 * math.pi)
    sweep_cw = sweep_ccw - (2.0 * math.pi)

    mid_ccw = _normalize_angle(a_start + (0.5 * sweep_ccw))
    mid_cw = _normalize_angle(a_start + (0.5 * sweep_cw))

    mid_ccw_pt = (cx + (r_eff * math.cos(mid_ccw)), cz + (r_eff * math.sin(mid_ccw)))
    mid_cw_pt = (cx + (r_eff * math.cos(mid_cw)), cz + (r_eff * math.sin(mid_cw)))

    dist_ccw = math.hypot(mid_ccw_pt[0] - vx, mid_ccw_pt[1] - vz)
    dist_cw = math.hypot(mid_cw_pt[0] - vx, mid_cw_pt[1] - vz)
    sweep = sweep_ccw if dist_ccw <= dist_cw else sweep_cw

    if abs(sweep) <= 1e-9:
        return None

    start_to_vertex = (a_vertex - a_start) % (2.0 * math.pi)
    if sweep > 0.0 and start_to_vertex > sweep:
        sweep = sweep_cw
    elif sweep < 0.0 and ((a_start - a_vertex) % (2.0 * math.pi)) > abs(sweep):
        sweep = sweep_ccw

    segment_count = max(int(min_segments), int(abs(sweep) / (math.pi / 18.0)))
    arc_points = []
    for idx in range(segment_count + 1):
        tval = float(idx) / float(segment_count)
        ang = a_start + (sweep * tval)
        arc_points.append((cx + (r_eff * math.cos(ang)), cz + (r_eff * math.sin(ang))))

    return arc_points


def _fillet_all_polygon_corners(points, radius):
    if len(points) < 3:
        return points

    r = float(radius or 0.0)
    if r <= 0.0:
        return points

    base_points = list(points)
    count = len(base_points)
    out = []

    for idx in range(count):
        prev_point = base_points[(idx - 1) % count]
        vertex_point = base_points[idx]
        next_point = base_points[(idx + 1) % count]

        arc_points = _build_corner_fillet_points(prev_point, vertex_point, next_point, r)
        if not arc_points:
            out.append(vertex_point)
            continue

        out.extend(arc_points)

    return out


def _resolve_profile_anchor_xz(
    profile_points_xz,
    orientation,
    local_rotation_deg=0.0,
    nose_radius=0.0,
    center_on_tip_width=False,
    z_from_body_negative=False,
):
    if not isinstance(profile_points_xz, list) or not profile_points_xz:
        return (0.0, 0.0)

    parsed_points = []
    for point in profile_points_xz:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        point_x = parse_number(point[0], None)
        point_z = parse_number(point[1], None)
        if point_x is None or point_z is None:
            continue
        parsed_points.append((float(point_x), float(point_z)))

    if not parsed_points:
        return (0.0, 0.0)

    rotation_rad = math.radians(float(local_rotation_deg or 0.0))
    cos_rot = math.cos(rotation_rad)
    sin_rot = math.sin(rotation_rad)

    rotated_points = []
    for point_x, point_z in parsed_points:
        rotated_x = (point_x * cos_rot) - (point_z * sin_rot)
        rotated_z = (point_x * sin_rot) + (point_z * cos_rot)
        rotated_points.append((rotated_x, rotated_z))

    if bool(z_from_body_negative):
        tangent_x = min(point[0] for point in rotated_points)
    elif orientation in (1, 2):
        tangent_x = min(point[0] for point in rotated_points)
    else:
        tangent_x = max(point[0] for point in rotated_points)

    x_span = max(point[0] for point in rotated_points) - min(point[0] for point in rotated_points)
    x_tolerance = max(1e-6, x_span * 1e-3)
    front_cluster = [point for point in rotated_points if abs(point[0] - tangent_x) <= x_tolerance]
    if not front_cluster:
        front_cluster = rotated_points

    if bool(z_from_body_negative):
        tangent_z = min(point[1] for point in rotated_points)
    elif bool(center_on_tip_width):
        tangent_z = 0.5 * (
            max(point[1] for point in front_cluster) +
            min(point[1] for point in front_cluster)
        )
    elif orientation in (1, 4):
        tangent_z = max(point[1] for point in front_cluster)
    else:
        tangent_z = min(point[1] for point in front_cluster)

    radius = max(0.0, float(nose_radius or 0.0))
    if radius > 1e-9 and not bool(center_on_tip_width) and not bool(z_from_body_negative):
        x_offset = -radius if orientation in (1, 2) else radius
        z_offset = radius if orientation in (1, 4) else -radius
        center_rot_x = tangent_x - x_offset
        center_rot_z = tangent_z - z_offset
        tangent_x = center_rot_x + x_offset
        tangent_z = center_rot_z + z_offset

    anchor_local_x = (tangent_x * cos_rot) + (tangent_z * sin_rot)
    anchor_local_z = (-tangent_x * sin_rot) + (tangent_z * cos_rot)
    return (float(anchor_local_x), float(anchor_local_z))


THREAD_CORNER_ORIENTATIONS = (1, 2, 3, 4)


def resolve_thread_control_point(points_xz, leg_tangents_xz, orientation):
    """Datum a threading tool is set to, in the profile's own frame.

    Threading tooling is measured to an EDGE, not to the insert's centre:

        X   the nose tangent -- the crest of the nose arc, which sets thread
            depth. Always the profile's minimum X; the shape is built with its
            cutting tooth toward -X and mirrored downstream per orientation.
        Z   for a corner orientation (1-4), where the inscribed circle touches
            the LEADING leg -- +Z side for Q1/Q4, -Z for Q2/Q3, matching the
            handedness _transform_insert_polygon_xz applies.
            For a centred orientation, the nose centreline instead, which for a
            symmetric nose is the tip itself.

    Returns (x, z), or None when there is nothing to work from.
    """
    points = [p for p in (points_xz or []) if isinstance(p, (list, tuple)) and len(p) >= 2]
    if not points:
        return None

    nose_x = min(float(p[0]) for p in points)

    if int(orientation or 0) not in THREAD_CORNER_ORIENTATIONS:
        # Centred: Z on the tooth axis. Take it from the nose points rather than
        # the bounding box so a long insert body cannot drag the datum sideways.
        tolerance = max(1e-9, abs(nose_x) * 1e-6)
        nose_band = [float(p[1]) for p in points
                     if abs(float(p[0]) - nose_x) <= tolerance + 1e-9]
        if not nose_band:
            nose_band = [float(p[1]) for p in points]
        return (nose_x, 0.5 * (min(nose_band) + max(nose_band)))

    tangents = [t for t in (leg_tangents_xz or [])
                if isinstance(t, (list, tuple)) and len(t) >= 2]
    if not tangents:
        return None

    if int(orientation) in (1, 4):
        lead = max(tangents, key=lambda t: float(t[1]))
    else:
        lead = min(tangents, key=lambda t: float(t[1]))
    return (nose_x, float(lead[1]))


def _rotate_profile_points_xz(profile_points_xz, angle_deg, origin_x=0.0, origin_z=0.0):
    if not isinstance(profile_points_xz, list) or not profile_points_xz:
        return []

    rotation_rad = math.radians(float(angle_deg or 0.0))
    cos_rot = math.cos(rotation_rad)
    sin_rot = math.sin(rotation_rad)

    out = []
    for point in profile_points_xz:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        point_x = parse_number(point[0], None)
        point_z = parse_number(point[1], None)
        if point_x is None or point_z is None:
            continue

        local_x = float(point_x) - float(origin_x)
        local_z = float(point_z) - float(origin_z)
        rot_x = (local_x * cos_rot) - (local_z * sin_rot)
        rot_z = (local_x * sin_rot) + (local_z * cos_rot)
        out.append((float(origin_x) + rot_x, float(origin_z) + rot_z))

    return out


def _resolve_sidecut_zero_edge_offset_deg(shape, iso_nose_angle):
    if not isinstance(shape, InsertShape):
        return 0.0

    if str(shape.family or '').strip().lower() in ('thread', 'groove'):
        return 0.0

    dims = shape.dims if isinstance(shape.dims, dict) else {}
    included_angle = parse_number(dims.get('included_angle_deg'), None)
    if included_angle is None:
        included_angle = parse_number(iso_nose_angle, None)
    if included_angle is None:
        return 0.0

    # Canonical side-cut frame: active edge aligned to +X at zero offset.
    return 0.5 * float(included_angle)


@dataclass
class InsertShape:
    family: str
    points_xz: list
    dims: dict


def build_groove_shape(length_x, width_z, nose_radius):
    half_w = max(width_z * 0.5, 0.001)
    profile = [
        (0.0, -half_w),
        (length_x, -half_w),
        (length_x, half_w),
        (0.0, half_w),
    ]
    profile = _fillet_all_polygon_corners(profile, nose_radius)

    return InsertShape(
        family="groove",
        points_xz=ensure_ccw(profile),
        dims={
            "length_x": float(length_x),
            "width_z": float(width_z),
            "nose_radius": float(nose_radius),
            "nose_fillet_applied": bool(float(nose_radius or 0.0) > 0.0),
        },
    )


def build_drill_shape(body_length_x, diameter_z, tip_angle_deg):
    body_length = max(float(body_length_x), 0.001)
    diameter = max(float(diameter_z), 0.001)
    half_width = 0.5 * diameter
    tip_angle = max(30.0, min(170.0, float(tip_angle_deg)))

    half_angle_rad = math.radians(0.5 * tip_angle)
    tip_length = half_width / max(1e-6, math.tan(half_angle_rad))
    tip_length = max(0.0005, float(tip_length))

    # Drill profile frame: centered on Z axis with tip toward Z-.
    profile = [
        (0.0, 0.0),
        (-half_width, -tip_length),
        (-half_width, -(tip_length + body_length)),
        (half_width, -(tip_length + body_length)),
        (half_width, -tip_length),
    ]

    return InsertShape(
        family="drill",
        points_xz=ensure_ccw(profile),
        dims={
            "length_x": float(diameter),
            "length_z": float(tip_length + body_length),
            "body_length_x": float(body_length),
            "width_z": float(diameter),
            "diameter": float(diameter),
            "tip_angle_deg": float(tip_angle),
            "tip_length_z": float(tip_length),
        },
    )


def _build_tap_profile_points(major_diameter, pitch, flute_length, overall_length, shaft_diameter, chamfer_threads):
    """Same construction as the 2D simulation's tap polygon, but emitted in the
    canonical tap_at_origin / body-toward-Z-negative frame shared by drill/thread.
    """
    major_r = 0.5 * float(major_diameter)
    shaft_r = 0.5 * float(shaft_diameter)
    pitch = float(pitch)
    flute_length = float(flute_length)
    overall_length = float(overall_length)
    chamfer_threads = float(chamfer_threads)

    thread_depth = pitch * 0.6495  # UN/metric standard depth
    minor_r = max(pitch * 0.1, major_r - thread_depth)
    chamfer_z = chamfer_threads * pitch

    # Right-half profile: flat tip at minor_r -> thread V-notches (crest ramps
    # up to major_r over the chamfer, root stays at minor_r) -> shoulder -> tail.
    right = [(minor_r, 0.0)]
    n_half = int(2.0 * flute_length / max(1e-9, pitch)) + 4
    for half_i in range(1, n_half):
        z_pos = half_i * pitch * 0.5
        if z_pos > flute_length + pitch * 0.5:
            break
        z = min(z_pos, flute_length)
        cf = min(1.0, z_pos / chamfer_z) if chamfer_z > 0 else 1.0
        is_crest = (half_i % 2 == 0)
        x = minor_r + (major_r - minor_r) * cf if is_crest else minor_r
        right.append((x, -z))
        if z_pos >= flute_length:
            break

    right.append((shaft_r, -flute_length))
    right.append((shaft_r, -overall_length))

    # Mirror back to (-minor_r, 0.0) as the final vertex so the closing edge
    # of the polygon is the flat tip face itself (square to the X axis).
    left = [(-x, z) for (x, z) in reversed(right[1:])] + [(-minor_r, 0.0)]
    return [(float(x), float(z)) for (x, z) in right + left]


# Sharp-V height for a 60-degree form: H = P / (2 tan30) = 0.8660 P. That is the
# height that makes the tooth's BASE WIDTH come out at exactly one pitch, which
# is the check worth remembering -- adjacent thread teeth are one pitch apart,
# so an insert tooth has to span a pitch at its base to cut the form.
#
# Not to be confused with 0.6134 P, the truncated depth a finished thread is
# cut to. That is how far the tooth goes INTO the work, not how big the tooth
# is; sizing the insert from it drew every tooth 29% short with a base width of
# 0.708 P instead of P.
_THREAD_HEIGHT_PER_PITCH = 0.8660254   # sqrt(3)/2
_THREAD_ROOT_RADIUS_PER_PITCH = 0.144

# Threading insert form, taken from the parametric sketch Chris built in
# SketchBasic (scratch/insert_shapes/thread_insert.sketch). That sketch is the
# authority on the shape; these are its constraints reduced to numbers.
#
# It is an indexable TRIANGULAR insert -- three identical corners produced by a
# polar array, so symmetry is structural and cannot drift. Its construction:
#
#   * a construction circle whose radius is the insert size (inscribed circle)
#   * three edges tangent to it, mutually 120deg -- an equilateral triangle
#   * at each corner a cutting tooth: flanks at half the thread angle, tipped
#     with an arc tangent to both, its crest a driven height above the base
#
# Three dimensions drive it and nothing else does, which is the whole point:
# change the insert size and only the triangle scales; change the nose radius
# and only the tip changes; change the tooth height and only the tooth grows.
#
# Everything below is normalised to inradius = 1 and measured off the solved
# sketch, so a value here can be checked against it directly.
#
# Two things here are derived from the tooth width, not fixed, and freezing
# either of them is what malforms the insert:
#
#   flat length   equal_length to the tooth's base chord, so it tracks the tooth
#   base offset   where the tooth base line sits out from the centre. The flat
#                 has to END on the next triangle edge, and that edge is tangent
#                 to the inscribed circle at 120 degrees. Writing the tangent
#                 line as 0.5u + (sqrt(3)/2)v = 1 and putting the flat end
#                 u = -1 + 4w on it gives
#
#                     v = sqrt(3) - (4/sqrt(3)) * w
#
#                 Pinned to a constant instead, the flat stops landing on the
#                 edge as soon as pitch changes the tooth width, the legs come
#                 off tangent and the whole triangle rotates -- which is exactly
#                 what it did.
_THREAD_TOOTH_BASE_U = -1.0            # tooth's first base corner, on the edge


def _build_thread_flat_tooth_points(depth, half_angle_rad, flat_width):
    """A tooth whose crest is a flat, not an arc.

    The flanks are cut off where they are `flat_width` apart, so `depth` is the
    height of the FLAT above the base -- the same convention the radiused tooth
    uses for its arc crest, which is what keeps the two interchangeable.

    Fusion's own drawing is the check: a 72.00 base at 30 deg would reach a
    sharp apex at 62.36, and the drawn crest sits at 60.18 -- a truncation of
    2.18, which puts 2 x 2.18 x tan(30) = 2.52 across the flat, the width the
    drawing dimensions.
    """
    if depth <= 0.0:
        return []

    half_flat = max(0.0, 0.5 * float(flat_width))
    # Where the flanks would have met if they ran on to a point.
    apex = depth + (half_flat / math.tan(half_angle_rad))
    half_width = apex * math.tan(half_angle_rad)
    if half_flat <= 0.0 or half_flat >= half_width:
        return [(0.0, -half_width), (depth, 0.0), (0.0, half_width)]

    return [(0.0, -half_width), (depth, -half_flat),
            (depth, half_flat), (0.0, half_width)]


def _build_thread_tooth_points(depth, half_angle_rad, tip_radius, arc_segments=24):
    """The cutting tooth in its own frame: (height above base, lateral).

    Flanks at `half_angle_rad` either side of the tooth axis, tipped by an arc
    of `tip_radius` tangent to both. The arc centre sits r/sin(a) back from
    where the flanks would have met, which is what makes it tangent rather
    than merely close; `depth` is the crest height, so it is the arc's outer
    point that lands on the driven dimension -- matching how the sketch
    measures it.

    Returned first base corner -> nose -> second base corner.
    """
    if depth <= 0.0:
        return []

    radius = max(0.0, min(float(tip_radius), depth * 0.9))
    # Height the flanks would reach if they ran on to a sharp point.
    apex = depth - radius + (radius / math.sin(half_angle_rad)) if radius > 0.0 else depth
    half_width = apex * math.tan(half_angle_rad)

    if radius <= 0.0:
        return [(0.0, -half_width), (depth, 0.0), (0.0, half_width)]

    # Arc centre sits r/sin(a) back from the sharp apex, which puts its crest
    # exactly `depth` above the base -- the dimension the sketch drives.
    centre = apex - (radius / math.sin(half_angle_rad))
    # Sweep measured from the tooth axis, so the arc runs from the tangent
    # point on the first flank, over the crest, to the tangent point on the
    # second. Starting anywhere else leaves the outline crossing itself.
    limit = (math.pi / 2.0) - half_angle_rad

    points = [(0.0, -half_width)]
    for index in range(arc_segments + 1):
        angle = -limit + ((2.0 * limit) * (index / float(arc_segments)))
        points.append((centre + (radius * math.cos(angle)),
                       radius * math.sin(angle)))
    points.append((0.0, half_width))
    return points


def _thread_points_equal(first, second, tol=1e-9):
    return (abs(first[0] - second[0]) <= tol
            and abs(first[1] - second[1]) <= tol)


def _finish_thread_bar(tooth, length, width, tooth_height, half_angle,
                       theta, pitch_min, pitch_max, size, size_mode, tip_type,
                       nose_radius, flat_width, clamped):
    """THREAD ISO DOUBLE: a bar carrying a thread form at each end.

    The simple form of the shape: a rectangle, length by width, with the tooth
    centred on each end and spanning the full width. A full-profile insert is
    one pitch wide -- the cutting form IS the end of the bar -- so the tooth
    base and the bar width are the same number and there is no shoulder
    between them.

        length   insert size, read as an edge length
        width    max pitch, which the tooth base also equals

    Built from one end and mirrored, so the two forms are identical by
    construction rather than by arithmetic that could drift apart.

    u runs along the bar, v across it, emitted as (X, Z) = (-u, v): the bar
    lies along X, sticking out radially, with the cutting tooth at the -X end
    pointing at the work and the body behind it. Laid along Z instead it would
    be a blade lying flat down the axis, which is not how an on-edge insert
    sits in its holder.
    """
    half_tw = max(point[1] for point in tooth)
    half_w = max(0.5 * float(width), half_tw)
    half_l = max(0.5 * float(length), tooth_height * 1.5)
    base_u = half_l - tooth_height

    # One end, walked across the bar from +v to -v.
    end = [(base_u + height, lateral) for height, lateral in reversed(tooth)]

    profile = []
    for u, v in end:                       # cutting end, tooth pointing -X
        profile.append((-u, v))
    for u, v in end:                       # far end, the same tooth mirrored
        profile.append((u, -v))            # the loop has to come back the way
                                           # it went out, so v flips, not u

    # Datum: X at the crest -- the deepest the tool reaches, which is what
    # sets thread depth -- and Z on the bar's own side edge.
    control_x = -half_l
    control_z = half_w
    leg_tangents = ((0.0, -half_w), (0.0, half_w))

    return InsertShape(
        family="thread",
        points_xz=ensure_ccw(profile),
        dims={
            "length_x": float(2.0 * half_l),
            "width_z": float(2.0 * half_w),
            "thread_angle_deg": float(theta),
            "thread_pitch_min": float(pitch_min),
            "thread_pitch_max": float(pitch_max),
            "insert_inradius": float(half_w),
            "insert_size": float(size),
            "insert_size_mode": str(size_mode or "edge_length"),
            "tooth_height": float(tooth_height),
            "tooth_width_z": float(2.0 * half_tw),
            "template": "thread_bar_v1",
            "bar_length": float(2.0 * half_l),
            "bar_width": float(2.0 * half_w),
            "control_point_xz": (float(control_x), float(control_z)),
            "leg_tangents_xz": leg_tangents,
            "inscribed_centre_xz": (0.0, 0.0),
            "tip_type": str(tip_type or ""),
            "tip_radius": float(nose_radius),
            "tip_flat_width": float(flat_width),
            "nose_fillet_applied": bool(nose_radius > 0.0),
            "tooth_clamped": bool(clamped),
        },
    )


def build_thread_shape(length_x, width_z, thread_angle_deg, tip_type, tip_radius,
                       thread_pitch_max, thread_pitch_min=0.0, insert_ic=0.0,
                       size_mode='', insert_shape=''):
    """Threading insert built as a construction, not a point list.

    Three driven dimensions and nothing else -- the arrangement from the
    SketchBasic model, which is the authority on this shape:

      insert size    inscribed circle radius, so the triangle scales alone
      tooth height   crest above the base line, from the COARSEST rated pitch
                     (TPX): 0.6134*P is how deep a thread of that pitch is, so
                     an insert that cannot reach it cannot cut it
      nose radius    from the FINEST rated pitch (TPN): the nose has to fit the
                     root of the finest thread it is rated for. Applied only to
                     a radiused insert; a 'point' one keeps its sharp V.

    Everything else -- the 120 degree corner spacing, the tangency of the edges
    to the circle, the tooth flanks meeting the base line, the arc meeting the
    flanks -- is derived. That is what stops the shape malforming when a
    dimension moves: there is no vertex to drift, only a construction to
    re-evaluate.
    """
    theta = max(30.0, min(120.0, float(thread_angle_deg)))
    half_angle = math.radians(theta / 2.0)
    _ = width_z

    pitch_max = max(0.0, float(thread_pitch_max or 0.0))
    pitch_min = max(0.0, float(thread_pitch_min or 0.0))

    # LEVER 1 -- insert size.
    #
    # Read as the inscribed circle diameter on a TRIPLE and as the bar's
    # length on a DOUBLE. Size Mode is not consulted: insert_shape already
    # says which body is being built, and the body determines what its size
    # measures, so reading both would let two columns disagree about one
    # number. See is_bar above.
    #
    # Falls back to the insert length only when no size is recorded, so an
    # incomplete row still draws rather than collapsing to nothing.
    _ = size_mode
    size = float(insert_ic or 0.0)
    # On the bar the recorded size is the WIDTH across, not a circle, so half
    # of it is the half-width rather than an inradius. The name is kept because
    # every fallback and proportion below is expressed against it.
    inradius = size / 2.0
    if inradius <= 0.0:
        inradius = max(float(length_x) * THREAD_DXF_X_EXTENT_FROM_OAL, 0.001)

    # LEVER 3 -- nose radius from the finest rated pitch, radiused inserts only.
    # Resolved before the height, because the height depends on it.
    # A recorded radius always wins, whatever the tip type says. No real insert
    # comes to a mathematical point, so 'point' means "ground sharp, small tip
    # radius" rather than "zero" -- and discarding a measured 0.004" because a
    # text field said point threw away the better number for the worse one.
    #
    # Only the DERIVED radius is gated on tip type: inferring 0.144 x TPN for an
    # insert nobody described as radiused would be inventing geometry.
    # Fusion offers three tip types and D carries whichever one applies --
    # it is the dimension ACROSS the tip in every case, so nothing else has
    # to know which kind of tip this is:
    #
    #   point   no entry; D is 0 and stays 0, a documented valid value
    #   flat    D is the flat width, used as-is
    #   round   D is the tip diameter, so the radius is D/2 -- already halved
    #           by the time it reaches here, arriving as `tip_radius`
    # THREAD ISO DOUBLE is a bar with a form at each end, not a triangle.
    # `insert_shape` is a rough SIZE DESIGNATOR, not a feature catalogue: it
    # says how to read the recorded numbers, nothing more.
    #
    #   TRIPLE   insert size is the inscribed circle; 3 corners at 120 deg
    #   DOUBLE   insert size is the bar width; 2 corners at 180 deg, length
    #            from the insert's own OAL
    is_bar = 'double' in str(insert_shape or '').strip().lower()
    # Two numbers, both already recorded, so the DOUBLE needs no column of its
    # own:
    #
    #   length   the insert size, read as an edge length -- the bar's long
    #            edge. NOT an overall length: an insert has one and so does
    #            its holder, and reading the wrong one has caused real
    #            confusion more than once.
    #   width    the max pitch. A full-profile insert is exactly one pitch
    #            wide -- the cutting form IS the end of the bar -- so the
    #            tooth spans the full width and the two are the same number.
    bar_length = float(insert_ic or 0.0) if is_bar else 0.0
    bar_width = float(thread_pitch_max or 0.0)
    if is_bar and bar_length <= 0.0:
        bar_length = float(length_x or 0.0) or (bar_width * 4.0)

    tip_key = str(tip_type or '').strip().lower()
    is_radiused = tip_key in ('round', 'radius', 'radiused')
    is_flat = tip_key == 'flat'
    nose_radius = 0.0 if is_flat else float(tip_radius or 0.0)
    flat_width = float(tip_radius or 0.0) if is_flat else 0.0
    if nose_radius <= 0.0 and is_radiused and pitch_min > 0.0:
        nose_radius = pitch_min * _THREAD_ROOT_RADIUS_PER_PITCH

    # LEVER 2 -- tooth size from the coarsest rated pitch, via its BASE WIDTH.
    #
    # The base width is the dimension that has to be right: thread teeth sit one
    # pitch apart, so an insert tooth has to span a pitch at its base or it
    # cannot cut the form. Fix base = P and work back through the flanks:
    #
    #     sharp apex = (P/2) / tan(a)          gives base = 2 apex tan(a) = P
    #     crest      = apex + r - r/sin(a)     the nose shortens the tooth
    #
    # Driving the crest height straight off a pitch fraction instead is what put
    # the base at 1.23 P; doing it off 0.6134 P -- the depth a finished thread is
    # cut to, not the size of the tooth that cuts it -- put it at 0.71 P.
    # A flat crest truncates the apex instead of rounding it, so it SHORTENS
    # the tooth by half_flat/tan(a) where a radius shortens it by
    # r - r/sin(a). Same base either way, which is the dimension that matters.
    def _crest_drop():
        if is_flat:
            return (0.5 * flat_width) / math.tan(half_angle)
        return (nose_radius / math.sin(half_angle)) - nose_radius

    def _make_tooth(height):
        if is_flat:
            return _build_thread_flat_tooth_points(height, half_angle, flat_width)
        return _build_thread_tooth_points(height, half_angle, nose_radius)

    # Proportional fallbacks are measured against the dimension the tooth
    # actually stands on: half the bar's WIDTH, or the triangle's inradius.
    # Using the inradius for both would scale a bar's tooth off half its
    # LENGTH, which on a long insert is an order of magnitude out.
    body_scale = (0.5 * bar_width) if is_bar else inradius

    if pitch_max > 0.0:
        sharp_apex = (pitch_max / 2.0) / math.tan(half_angle)
        tooth_height = sharp_apex - _crest_drop()
    else:
        tooth_height = body_scale * 0.4        # the sketch's own proportion
    tooth_height = max(tooth_height, body_scale * 0.02)
    nose_radius = min(nose_radius, tooth_height * 0.9)
    flat_width = min(flat_width, tooth_height * 0.9)

    tooth = _make_tooth(tooth_height)
    if len(tooth) < 3:
        return InsertShape(family="thread", points_xz=[], dims={})

    # A tooth can only grow until its base line reaches the inscribed circle:
    # v = sqrt(3)R - (4/sqrt(3))w >= R gives w <= (3 - sqrt(3))/4 * R. Past that
    # the three corner blocks run into each other and the triangle stops being
    # a triangle. Clamping here rather than on the height keeps the limit on the
    # thing that actually collides.
    #
    # Hitting this means the insert is too small for the pitch it is rated to
    # cut, which is a tool-table problem wearing a geometry costume -- so the
    # clamped height is reported in dims rather than silently swallowed.
    # Measured, not assumed: sweeping the construction unclamped, the outline
    # first crosses itself at w = 0.5 R. The previous limit of (3-sqrt3)/4 R
    # (0.317 R) was a guess about the inscribed circle and cut teeth that were
    # perfectly valid.
    # On the DOUBLE bar the limit is simply the bar: a full-profile tooth may
    # span the whole width -- that is what "full profile" means -- and only a
    # tooth WIDER than its own body is impossible.
    if is_bar:
        width_limit = 0.5 * bar_width
    else:
        width_limit = 0.45 * inradius
    clamped = max(point[1] for point in tooth) > width_limit
    if clamped:
        tooth_height = (width_limit / math.tan(half_angle)) - _crest_drop()
        tooth_height = max(tooth_height, body_scale * 0.02)
        nose_radius = min(nose_radius, tooth_height * 0.9)
        flat_width = min(flat_width, tooth_height * 0.9)
        tooth = _make_tooth(tooth_height)
        if len(tooth) < 3:
            return InsertShape(family="thread", points_xz=[], dims={})

    # One corner in its own frame: u along the tooth base line, v outward from
    # the centre. The tooth's first base corner sits where the triangle edge
    # meets that line, so the tooth grows along the line rather than off it.
    if is_bar:
        return _finish_thread_bar(
            tooth, bar_length, bar_width, tooth_height, half_angle, theta,
            pitch_min, pitch_max, size, size_mode, tip_type,
            nose_radius, flat_width, clamped)

    base_u = _THREAD_TOOTH_BASE_U * inradius
    half_width = max(point[1] for point in tooth)
    # Derived, per the note above: keeps the flat ending on the tangent edge
    # whatever the tooth width, which is what holds the legs square to Z.
    base_v = (math.sqrt(3.0) * inradius) - ((4.0 / math.sqrt(3.0)) * half_width)
    axis_u = base_u + half_width

    corner = [(axis_u + lateral, base_v + height) for height, lateral in tooth]
    # equal_length: the flat matches the tooth's base chord (2 x half width).
    corner.append((base_u + (4.0 * half_width), base_v))

    # Three corners, 120 degrees apart -- a polar array, as the sketch has it.
    # Negative: the sketch tiles clockwise (its first corner sits at 130.34 deg
    # and the next at 10.34). Tiling the other way crosses the outline.
    #
    # u runs along the tooth base line and v out from the centre, emitted as
    # (X, Z) = (-v, u).
    #
    # The sign on v points the cutting tooth toward the work (-X, the axis)
    # with the insert body behind it, and a leg -- a line of constant u --
    # comes out perpendicular to the Z centreline, which is what lets the tooth
    # cut its form squarely. Emitted the other way round a leg lies along Z and
    # skews every thread it cuts.
    profile = []
    for index in range(3):
        angle = -(2.0 * math.pi / 3.0) * index
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        for u, v in corner:
            profile.append((-((u * sin_a) + (v * cos_a)),
                            (u * cos_a) - (v * sin_a)))

    # The profile is NOT translated to its tip here. Thread/groove/drill/tap
    # templates are handed back in final orientation and the control point is
    # resolved separately, per Q orientation, by _resolve_profile_anchor_xz --
    # see the 'thread' branch in lathe_conv. Pre-anchoring here would fight it.
    #
    # What the anchor cannot work out for itself is the threading datum:
    #
    #   X   the nose tangent -- the crest of the nose arc, the deepest the tool
    #       reaches, which is what sets thread depth
    #   Z   where the inscribed circle touches the leading leg. Threading
    #       tooling is measured to an edge, not to the insert's centre, so the
    #       Z reference belongs on the leg rather than under the tooth.
    #
    # Reported rather than applied: which leg leads depends on the Q
    # orientation, and only the caller knows that.
    control_x = -(base_v + tooth_height)
    control_z = base_u                      # leg u = -inradius, touched at v = 0
    # The other two legs, for an orientation whose leading edge is not the first.
    leg_tangents = []
    for index in range(3):
        angle = -(2.0 * math.pi / 3.0) * index
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        leg_tangents.append((-(base_u * sin_a), base_u * cos_a))

    min_x = min(point[0] for point in profile)
    max_x = max(point[0] for point in profile)
    min_z = min(point[1] for point in profile)
    max_z = max(point[1] for point in profile)

    return InsertShape(
        family="thread",
        points_xz=ensure_ccw(profile),
        dims={
            "length_x": float(max_x - min_x),
            "width_z": float(max_z - min_z),
            "thread_angle_deg": float(theta),
            "thread_pitch_min": float(pitch_min),
            "thread_pitch_max": float(pitch_max),
            "insert_inradius": float(inradius),
            "insert_size": float(size),
            "insert_size_mode": str(size_mode or "edge_length"),
            "tooth_height": float(tooth_height),
            "tooth_width_z": float(2.0 * half_width),
            "template": "thread_sketch_v1",
            # Threading datum: X at the nose tangent, Z at the inscribed-circle
            # tangency on the leading leg. See the note where these are built.
            "control_point_xz": (float(control_x), float(control_z)),
            "leg_tangents_xz": tuple(leg_tangents),
            "inscribed_centre_xz": (0.0, 0.0),
            "tip_type": str(tip_type or ""),
            "tip_radius": float(nose_radius),
            "nose_fillet_applied": bool(nose_radius > 0.0),
        },
    )

def build_rhombic_shape(length_x, width_z, included_angle_deg, nose_radius, style_key):
    ic = max(20.0, min(120.0, float(included_angle_deg)))
    alpha = math.radians(ic)

    # For ISO rhombic inserts, size is IC (inscribed circle diameter).
    # Use that to derive a true diamond from the nose angle.
    insert_ic = max(float(length_x), float(width_z), 0.001)
    side = insert_ic / max(1e-6, math.sin(alpha))
    x_back = 2.0 * side * math.cos(0.5 * alpha)
    half_w = side * math.sin(0.5 * alpha)
    x_mid = 0.5 * x_back

    profile = [
        (0.0, 0.0),
        (x_mid, -half_w),
        (x_back, 0.0),
        (x_mid, half_w),
    ]
    profile = _fillet_all_polygon_corners(profile, nose_radius)

    return InsertShape(
        family=str(style_key),
        points_xz=ensure_ccw(profile),
        dims={
            "length_x": float(x_back),
            "width_z": float(2.0 * half_w),
            "inscribed_circle_diameter": float(insert_ic),
            "included_angle_deg": float(ic),
            "nose_radius": float(nose_radius),
            "side_length": float(side),
            "nose_fillet_applied": bool(float(nose_radius or 0.0) > 0.0),
        },
    )


def build_iso_ic_diamond_shape(ic_diameter, included_angle_deg, style_key, nose_radius):
    ic = max(0.001, float(ic_diameter))
    nose_angle = max(20.0, min(120.0, float(included_angle_deg)))
    half_angle_rad = math.radians(nose_angle * 0.5)

    # For ISO size mode IC, derive true rhombic diagonals from inscribed-circle diameter.
    long_diag = ic / max(1e-6, math.sin(half_angle_rad))
    short_diag = ic / max(1e-6, math.cos(half_angle_rad))

    half_x = 0.5 * long_diag
    half_z = 0.5 * short_diag
    edge_length = math.hypot(half_x, half_z)
    corner_angles_deg = [nose_angle, 180.0 - nose_angle, nose_angle, 180.0 - nose_angle]
    requested_radius = max(0.0, float(nose_radius or 0.0))

    max_corner_radii = []
    effective_corner_radii = []
    for corner_angle in corner_angles_deg:
        max_radius = edge_length * math.tan(math.radians(corner_angle * 0.5)) * 0.95
        max_radius = max(0.0, float(max_radius))
        max_corner_radii.append(max_radius)
        effective_corner_radii.append(min(requested_radius, max_radius))

    profile = [
        (0.0, 0.0),
        (half_x, -half_z),
        (long_diag, 0.0),
        (half_x, half_z),
    ]
    profile = _fillet_all_polygon_corners(profile, nose_radius)

    return InsertShape(
        family=str(style_key),
        points_xz=ensure_ccw(profile),
        dims={
            "ic_diameter": float(ic),
            "length_x": float(long_diag),
            "width_z": float(short_diag),
            "included_angle_deg": float(nose_angle),
            "nose_radius": float(nose_radius),
            "edge_length": float(edge_length),
            "corner_angles_deg": [float(value) for value in corner_angles_deg],
            "corner_radius_requested": float(requested_radius),
            "corner_radius_max": [float(value) for value in max_corner_radii],
            "corner_radius_effective": [float(value) for value in effective_corner_radii],
            "nose_fillet_applied": bool(float(nose_radius or 0.0) > 0.0),
        },
    )


def build_trigon_shape(length_x, width_z, included_angle_deg, style_key, nose_radius):
    base_size = max(0.001, float(length_x))
    nose_angle = max(60.001, min(120.0, float(included_angle_deg)))
    obtuse_angle = 240.0 - nose_angle

    # Exact edge-turn construction for a 6-corner trigon profile.
    # This produces alternating interior angles: nose_angle, obtuse_angle, ...
    # for an equal-edge convex polygon.
    acute_turn = 180.0 - nose_angle
    obtuse_turn = 180.0 - obtuse_angle
    edge_directions_deg = [0.0]
    for idx in range(1, 6):
        turn = acute_turn if (idx % 2 == 1) else obtuse_turn
        edge_directions_deg.append(edge_directions_deg[-1] + turn)
    raw_points = [(0.0, 0.0)]
    for direction_deg in edge_directions_deg:
        last_x, last_z = raw_points[-1]
        step_x = math.cos(math.radians(direction_deg))
        step_z = math.sin(math.radians(direction_deg))
        raw_points.append((last_x + step_x, last_z + step_z))
    raw_points = raw_points[:-1]

    # Find acute corners and choose the front-most one as active tip.
    corner_angles = []
    for idx in range(6):
        prev_x, prev_z = raw_points[(idx - 1) % 6]
        curr_x, curr_z = raw_points[idx]
        next_x, next_z = raw_points[(idx + 1) % 6]
        vec_prev = (prev_x - curr_x, prev_z - curr_z)
        vec_next = (next_x - curr_x, next_z - curr_z)
        dot_val = (vec_prev[0] * vec_next[0]) + (vec_prev[1] * vec_next[1])
        len_prev = math.hypot(vec_prev[0], vec_prev[1])
        len_next = math.hypot(vec_next[0], vec_next[1])
        angle_deg = math.degrees(math.acos(max(-1.0, min(1.0, dot_val / max(1e-9, len_prev * len_next)))))
        corner_angles.append(angle_deg)

    acute_indices = [idx for idx, angle_deg in enumerate(corner_angles) if angle_deg < 120.0]
    tip_index = min(acute_indices, key=lambda idx: raw_points[idx][0]) if acute_indices else 0

    ordered = [raw_points[(tip_index + idx) % 6] for idx in range(6)]
    tip_x, tip_z = ordered[0]

    # Align tip bisector with +X so "away from tip" is positive X.
    prev_x, prev_z = ordered[-1]
    next_x, next_z = ordered[1]
    v_prev = (prev_x - tip_x, prev_z - tip_z)
    v_next = (next_x - tip_x, next_z - tip_z)
    len_prev = math.hypot(v_prev[0], v_prev[1])
    len_next = math.hypot(v_next[0], v_next[1])
    u_prev = (v_prev[0] / max(1e-9, len_prev), v_prev[1] / max(1e-9, len_prev))
    u_next = (v_next[0] / max(1e-9, len_next), v_next[1] / max(1e-9, len_next))
    bisector = (u_prev[0] + u_next[0], u_prev[1] + u_next[1])
    bisector_len = math.hypot(bisector[0], bisector[1])
    if bisector_len <= 1e-9:
        bisector = (1.0, 0.0)
    else:
        bisector = (bisector[0] / bisector_len, bisector[1] / bisector_len)

    align_angle = math.atan2(bisector[1], bisector[0])
    cos_a = math.cos(-align_angle)
    sin_a = math.sin(-align_angle)

    rotated = []
    for x_val, z_val in ordered:
        rel_x = x_val - tip_x
        rel_z = z_val - tip_z
        rot_x = (rel_x * cos_a) - (rel_z * sin_a)
        rot_z = (rel_x * sin_a) + (rel_z * cos_a)
        rotated.append((rot_x, rot_z))

    # Scale isotropically from canonical base to requested size.
    xs_raw = [pt[0] for pt in rotated]
    span_x_raw = max(0.001, max(xs_raw) - min(xs_raw))
    uniform_scale = base_size / span_x_raw
    profile = [(x_val * uniform_scale, z_val * uniform_scale) for x_val, z_val in rotated]
    profile = _fillet_all_polygon_corners(profile, nose_radius)

    xs = [pt[0] for pt in profile]
    zs = [pt[1] for pt in profile]
    corner_angles_deg = [nose_angle if (idx % 2 == 0) else obtuse_angle for idx in range(6)]

    return InsertShape(
        family=str(style_key),
        points_xz=ensure_ccw(profile),
        dims={
            "ic_diameter": float(base_size),
            "length_x": float(max(xs) - min(xs)),
            "width_z": float(max(zs) - min(zs)),
            "included_angle_deg": float(nose_angle),
            "nose_radius": float(nose_radius),
            "corner_angles_deg": [float(value) for value in corner_angles_deg],
            "corner_radius_requested": float(max(0.0, float(nose_radius or 0.0))),
            "nose_fillet_applied": bool(float(nose_radius or 0.0) > 0.0),
            "trigon_angle_pattern": "alternating",
        },
    )


def build_round_shape(length_x, width_z, nose_radius, style_key):
    radius = max(0.001, 0.5 * max(float(length_x), float(width_z), 2.0 * float(nose_radius or 0.0)))
    center_x = radius

    points = []
    segments = 40
    for idx in range(segments):
        angle = (2.0 * math.pi * float(idx)) / float(segments)
        x_val = center_x + (radius * math.cos(angle))
        z_val = radius * math.sin(angle)
        points.append((x_val, z_val))

    return InsertShape(
        family=str(style_key),
        points_xz=ensure_ccw(points),
        dims={
            "length_x": float(length_x),
            "width_z": float(width_z),
            "nose_radius": float(nose_radius),
            "radius": float(radius),
        },
    )


def build_regular_polygon_shape(length_x, width_z, sides, style_key, nose_radius):
    side_count = max(3, int(sides))
    raw_points = []
    for idx in range(side_count):
        angle = math.pi + ((2.0 * math.pi * float(idx)) / float(side_count))
        raw_points.append((1.0 + math.cos(angle), math.sin(angle)))

    max_x = max(pt[0] for pt in raw_points)
    max_abs_z = max(abs(pt[1]) for pt in raw_points)

    scale_x = float(length_x) / max(0.000001, max_x)
    scale_z = (0.5 * float(width_z)) / max(0.000001, max_abs_z)

    points = [(x_val * scale_x, z_val * scale_z) for x_val, z_val in raw_points]
    points = _fillet_all_polygon_corners(points, nose_radius)

    return InsertShape(
        family=str(style_key),
        points_xz=ensure_ccw(points),
        dims={
            "length_x": float(length_x),
            "width_z": float(width_z),
            "nose_radius": float(nose_radius),
            "sides": int(side_count),
        },
    )
