"""Live lathe insert/drill/tap cutting-profile geometry.

Given a raw Fusion tool dict (the same dict structure stored in a Fusion
lathe tool-library JSON), computes a 2D XZ cutting-profile polygon in a
canonical local frame: cutting tip at the origin, +X away from the tip,
and (for drill/tap/thread families) the body extending toward -Z.

This is the single source of truth for insert/drill/tap shape math, used
live by both the 3D VTK tool viewer (tool_actor.py) and the pb_lathe_conv
2D conversational simulation, so geometry always reflects whichever tool
library is currently active with no on-disk cache to go stale.

Pure stdlib, no qtpyvcp/Qt imports, so it is also importable by the
standalone offline preview-generation script.
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


def dict_get(mapping, *keys):
    current = mapping
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


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


def build_tap_shape(tool):
    geometry = dict_get(tool, "geometry") or {}
    expressions = dict_get(tool, "expressions") or {}

    major_diameter = first_positive(
        geometry.get("DC"),
        geometry.get("tool_diameter"),
        expressions.get("tool_diameter"),
        0.5,
    )
    pitch = first_positive(
        geometry.get("TP"),
        geometry.get("TPX"),
        geometry.get("TPN"),
        expressions.get("tool_threadPitch"),
        0.05,
    )
    flute_length = first_positive(
        geometry.get("LCF"),
        geometry.get("LB"),
        expressions.get("tool_fluteLength"),
        1.2,
    )
    overall_length = first_positive(
        geometry.get("OAL"),
        expressions.get("tool_overallLength"),
        3.0,
    )
    shaft_diameter = first_positive(
        geometry.get("SFDM"),
        expressions.get("tool_shaftDiameter"),
        major_diameter * 0.75,
    )
    thread_angle = first_positive(
        geometry.get("thread-profile-angle"),
        60.0,
    )
    chamfer_threads = first_positive(
        geometry.get("tap_chamfer_threads"),
        2.5,
    )

    points = _build_tap_profile_points(
        major_diameter, pitch, flute_length, overall_length, shaft_diameter, chamfer_threads,
    )

    return InsertShape(
        family="tap",
        points_xz=ensure_ccw(points),
        dims={
            "diameter": float(major_diameter),
            "pitch": float(pitch),
            "flute_length_z": float(flute_length),
            "overall_length_z": float(overall_length),
            "shaft_diameter": float(shaft_diameter),
            "thread_angle_deg": float(thread_angle),
            "chamfer_threads": float(chamfer_threads),
            "tip_angle_deg": 180.0,
        },
    )


def build_thread_shape(length_x, width_z, thread_angle_deg, tip_type, tip_radius, thread_pitch_max):
    theta = max(30.0, min(120.0, float(thread_angle_deg)))
    body_length = max(float(length_x) * THREAD_DXF_X_EXTENT_FROM_OAL, 0.001)
    _ = width_z
    _ = thread_pitch_max

    # Use the DXF template's native proportions: one uniform body-length scale
    # for both depth and lateral coordinates.
    pitch_scale = 1.0
    lateral_scale = body_length

    profile = []
    for lateral_norm, depth_norm in THREAD_DXF_TEMPLATE_POINTS:
        x_val = (1.0 - float(depth_norm)) * body_length
        z_val = float(lateral_norm) * lateral_scale
        profile.append((x_val, z_val))

    profile = _fillet_all_polygon_corners(profile, tip_radius)

    min_x = min(point[0] for point in profile)
    max_x = max(point[0] for point in profile)
    min_z = min(point[1] for point in profile)
    max_z = max(point[1] for point in profile)
    derived_length = float(max_x - min_x)
    derived_width = float(max_z - min_z)

    return InsertShape(
        family="thread",
        points_xz=ensure_ccw(profile),
        dims={
            "length_x": float(derived_length),
            "width_z": float(derived_width),
            "thread_angle_deg": float(theta),
            "thread_pitch_max": float(thread_pitch_max),
            "thread_pitch_scale": float(pitch_scale),
            "template": "thread_dxf_v1",
            "tip_type": str(tip_type or ""),
            "tip_radius": float(tip_radius),
            "nose_fillet_applied": bool(float(tip_radius or 0.0) > 0.0),
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


def build_insert_shape(tool):
    geometry = dict_get(tool, "geometry") or {}
    holder = dict_get(tool, "holder") or {}
    expressions = dict_get(tool, "expressions") or {}

    style_raw = geometry.get("SC")
    scty = str(geometry.get("SCTY") or "").strip().lower()
    style_key = normalize_style_key(style_raw)

    tool_type = str(tool.get("type") or "").strip().lower()

    if "tap" in tool_type:
        return build_tap_shape(tool)

    if "drill" in tool_type:
        drill_diameter = first_positive(
            geometry.get("DC"),
            geometry.get("tool_diameter"),
            expressions.get("tool_diameter"),
            geometry.get("SFDM"),
            0.125,
        )
        drill_tip_angle = first_positive(
            geometry.get("SIG"),
            expressions.get("tool_tipAngle"),
            118.0,
        )
        drill_body_length = first_positive(
            geometry.get("LCF"),
            geometry.get("LB"),
            expressions.get("tool_fluteLength"),
            expressions.get("tool_bodyLength"),
            geometry.get("OAL"),
            expressions.get("tool_overallLength"),
            1.0,
        )

        return build_drill_shape(drill_body_length, drill_diameter, drill_tip_angle)

    if "thread" in tool_type:
        style_key = "thread"
    elif style_key == "generic" and scty == "g":
        style_key = "groove"

    holder_style = str(holder.get("THSC") or "").strip().lower()
    description = str(tool.get("description") or "").strip().lower()
    is_internal_groove = (
        style_key == "groove"
        and (
            ("internal" in holder_style)
            or ("internal" in description and "external" not in description)
        )
    )

    internal_groove_max_depth = None
    if is_internal_groove:
        holder_cw = parse_number(holder.get("CW"), None)
        holder_w = parse_number(holder.get("W"), None)
        if holder_cw is not None and holder_w is not None:
            internal_groove_max_depth = float(holder_cw) - (0.5 * float(holder_w))

    nose_radius = first_positive(
        geometry.get("RE"),
        geometry.get("thread-tip-radius"),
        expressions.get("tool_cornerRadius"),
        0.0,
    )

    insert_size = first_positive(
        geometry.get("INSD"),
        geometry.get("tool_insertSize"),
        expressions.get("tool_insertSize"),
        expressions.get("tool_cuttingWidth"),
        holder.get("CW"),
        geometry.get("S"),
        0.24,
    )

    if style_key == "thread":
        insert_length = first_positive(
            geometry.get("OAL"),
            expressions.get("tool_overallLength"),
            geometry.get("INSD"),
            geometry.get("tool_insertSize"),
            expressions.get("tool_insertSize"),
            geometry.get("S"),
            expressions.get("tool_thickness"),
            0.24,
        )
        # Width parameter is accepted for compatibility, but DXF template
        # scaling is driven by thread angle + length + pitch parameters.
        insert_width = first_positive(
            geometry.get("thread-body-width"),
            expressions.get("thread-body-width"),
            geometry.get("S"),
            expressions.get("tool_thickness"),
            geometry.get("tool_insertWidth"),
            expressions.get("tool_insertWidth"),
            geometry.get("INSD"),
            geometry.get("tool_insertSize"),
            expressions.get("tool_insertSize"),
            insert_length,
            0.06,
        )
    elif style_key == "groove":
        insert_length = first_positive(
            internal_groove_max_depth,
            geometry.get("H"),
            holder.get("H"),
            expressions.get("tool_maxDOC"),
            expressions.get("tool_maxDepthOfCut"),
            geometry.get("S"),
            geometry.get("INSD"),
            geometry.get("tool_insertSize"),
            expressions.get("tool_insertSize"),
            expressions.get("tool_cuttingWidth"),
            holder.get("CW"),
            0.24,
        )
        insert_width = first_positive(
            geometry.get("tool_grooveWidth"),
            expressions.get("tool_grooveWidth"),
            geometry.get("tool_insertWidth"),
            expressions.get("tool_insertWidth"),
            geometry.get("INSD"),
            expressions.get("tool_insertSize"),
            holder.get("CW"),
            0.06,
        )
    else:
        insert_length = float(insert_size)
        insert_width = first_positive(
            geometry.get("tool_insertWidth"),
            expressions.get("tool_insertWidth"),
            geometry.get("tool_insertSize"),
            expressions.get("tool_insertSize"),
            geometry.get("INSD"),
            expressions.get("tool_cuttingWidth"),
            insert_length,
            0.06,
        )

    if style_key == "groove":
        return build_groove_shape(insert_length, insert_width, nose_radius)

    if style_key == "thread":
        thread_angle = first_positive(geometry.get("thread-profile-angle"), 60.0)
        tip_type = str(geometry.get("thread-tip-type") or "").strip().lower() or "point"
        thread_tip_radius = first_positive(geometry.get("thread-tip-radius"), nose_radius, 0.0)
        thread_pitch_max = first_positive(
            geometry.get("TPX"),
            geometry.get("TP"),
            geometry.get("TPN"),
            expressions.get("tool_maxThreadPitch"),
            expressions.get("tool_threadPitch"),
            0.0,
        )
        return build_thread_shape(
            insert_length,
            insert_width,
            thread_angle,
            tip_type,
            thread_tip_radius,
            thread_pitch_max,
        )

    style_spec = ISO_INSERT_STYLE_SPECS.get(style_key)
    if style_spec is None:
        style_spec = ISO_INSERT_STYLE_SPECS["c"]

    style_family = str(style_spec.get("family") or "diamond")
    nose_angle_deg = style_spec.get("nose_angle_deg")
    if nose_angle_deg is None:
        nose_angle_deg = 80.0
    nose_angle_deg = float(nose_angle_deg)

    if style_family == "trigon":
        return build_trigon_shape(insert_length, insert_width, nose_angle_deg, style_key, nose_radius)

    if style_family == "triangle":
        return build_regular_polygon_shape(insert_length, insert_width, 3, style_key, nose_radius)

    if style_family == "round":
        return build_round_shape(insert_length, insert_width, nose_radius, style_key)

    if style_family == "hexagon":
        return build_regular_polygon_shape(insert_length, insert_width, 6, style_key, nose_radius)

    if style_family == "octagon":
        return build_regular_polygon_shape(insert_length, insert_width, 8, style_key, nose_radius)

    if style_family == "pentagon":
        return build_regular_polygon_shape(insert_length, insert_width, 5, style_key, nose_radius)

    size_mode = str(geometry.get("SIZE_SPECIFICATION_MODE") or "").strip().upper()
    if style_family in ("diamond", "parallelogram") and size_mode == "IC":
        return build_iso_ic_diamond_shape(insert_size, nose_angle_deg, style_key, nose_radius)

    return build_rhombic_shape(insert_length, insert_width, nose_angle_deg, nose_radius, style_key)


def compute_live_insert_profile(tool):
    """Compute the live profile_doc-shaped dict for `tool` (a raw Fusion tool dict).

    Returns {profile_format, family, insert_polygon_xz, dimensions}. Anchor
    (control_point_xz) is intentionally omitted -- callers resolve that live
    from their own currently-active orientation via _resolve_profile_anchor_xz.
    """
    if not isinstance(tool, dict):
        return None

    geometry = dict_get(tool, "geometry") or {}
    style_key = normalize_style_key(geometry.get("SC"))
    style_spec = ISO_INSERT_STYLE_SPECS.get(style_key)
    iso_nose_angle = style_spec.get("nose_angle_deg") if isinstance(style_spec, dict) else None

    shape = build_insert_shape(tool)

    insert_polygon_xz = [[float(x), float(z)] for x, z in shape.points_xz]

    sidecut_zero_offset_deg = _resolve_sidecut_zero_edge_offset_deg(shape, iso_nose_angle)
    if abs(float(sidecut_zero_offset_deg)) > 1e-12:
        rotated_points = _rotate_profile_points_xz(
            insert_polygon_xz, sidecut_zero_offset_deg, origin_x=0.0, origin_z=0.0,
        )
        if rotated_points:
            insert_polygon_xz = [
                [float(x_val), float(z_val)]
                for x_val, z_val in ensure_ccw(rotated_points)
            ]

    return {
        "profile_format": 1,
        "family": shape.family,
        "insert_polygon_xz": insert_polygon_xz,
        "dimensions": shape.dims,
    }
