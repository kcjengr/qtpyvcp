"""Renderer-independent G-code canon.

This is the renderer-independent canon.  It performs unit normalisation, WCS
handling, rotary-table sampling and float anchoring, and instead of allocating
renderer objects it accumulates plain NumPy buffers exposed via
:class:`~.geometry.BackplotGeometry`.
"""

import math
import re
from array import array
from collections import OrderedDict

import numpy as np

from qtpyvcp.utilities import logger

from .base_canon import StatCanon
from .geometry import BackplotGeometry, OffsetTransition, PathGeometry

LOG = logger.getLogger(__name__)

# Role -> (r, g, b, a) default colours.
DEFAULT_ROLE_COLORS = {
    'traverse': (200, 35, 35, 255),
    'arcfeed': (110, 110, 255, 255),
    'feed': (210, 210, 255, 255),
    'dwell': (0, 0, 255, 255),
    'user': (0, 100, 255, 255),
}

# Line-type token order used by the native builder (see backplot_bridge_pybind.cpp).
LINE_TYPE_TOKENS = {
    'traverse': 0,
    'feed': 1,
    'arcfeed': 2,
    'dwell': 3,
    'user': 4,
}

_KINS_BY_MCODE = {428: 0, 429: 1, 430: 2}


def _coerce_rgba(value):
    """Normalise a colour into an ``(r, g, b, a)`` uint8 tuple."""
    if value is None:
        return (255, 255, 255, 255)
    if hasattr(value, 'getRgb'):  # QColor
        return tuple(int(c) for c in value.getRgb())
    if isinstance(value, (tuple, list)):
        rgba = [int(c) for c in value]
        if len(rgba) == 3:
            rgba.append(255)
        return tuple(rgba[:4])
    return (255, 255, 255, 255)


class BackplotCanon(StatCanon):
    """Canon producing renderer-independent :class:`BackplotGeometry`."""

    def __init__(self, datasource, colors=None, geometry='XYZ', random=False, stat=None):
        super().__init__(geometry=geometry, random=random, stat=stat)
        self._datasource = datasource

        if datasource is not None:
            self.arcdivision = datasource.getArcDivision()
        else:
            self.arcdivision = 64

        source_colors = colors or DEFAULT_ROLE_COLORS
        self.role_colors = {role: _coerce_rgba(source_colors.get(role))
                            for role in LINE_TYPE_TOKENS}

        self._cpp_line_type_codes = dict(LINE_TYPE_TOKENS)

        self.path_records = OrderedDict()   # wcs_index -> list of record tuples
        self.path_segments = []             # [{wcs_index, lines:[(token, line)]}]
        self.initial_wcs_offsets = OrderedDict()
        self.offset_transitions = []
        self.added_segments = 0

        self._preview_switchkins_type = 0
        self._preview_program_units = None
        self._last_units_factor_log = None
        self._pending_tool_event_motion = False
        self._pending_tool_event_traverse_suppressed = 0
        self._anchored_wcs = set()

        self._active_wcs_index = 0
        self._tool_offsets = (0.0,) * 9
        self._rotary_axis_wrapped = {'A': False, 'B': False, 'C': False}

        if datasource is not None:
            self._active_wcs_index = datasource.getActiveWcsIndex()
            self._tool_offsets = tuple(datasource.getToolOffset())
            self._rotary_axis_wrapped = dict(datasource.getRotaryAxisWrapped())
            g5x = datasource.getActiveWcsOffsets()
            # Canonical index has G53 at 0 while active index is zero-based
            # from G54.
            super().set_g5x_offset(
                self._active_wcs_index + 1,
                g5x[0], g5x[1], g5x[2], g5x[3], g5x[4],
                g5x[5], g5x[6], g5x[7], g5x[8],
            )

        self.foam_z = 0.0
        self.foam_w = 0.0
        LOG.debug("BackplotCanon --- Init Done ---")

    # -- tool state ---------------------------------------------------------

    def change_tool(self, pocket):
        super().change_tool(pocket)
        self.first_move = True
        self.path_initialized = False
        self._pending_tool_event_motion = True
        self._pending_tool_event_traverse_suppressed = 0

    def tool_offset(self, xo, yo, zo, ao, bo, co, uo, vo, wo):
        # Keep preview geometry independent from runtime tool table offsets.
        self.first_move = True
        self.path_initialized = False

        self.tlo_x, self.tlo_y, self.tlo_z = xo, yo, zo
        self.tlo_a, self.tlo_b, self.tlo_c = ao, bo, co
        self.tlo_u, self.tlo_v, self.tlo_w = uo, vo, wo
        self._tool_offsets = (xo, yo, zo, ao, bo, co, uo, vo, wo)
        self.tool_offsets = self._tool_offsets
        self._pending_tool_event_motion = True
        self._pending_tool_event_traverse_suppressed = 0

    def next_line(self, st):
        super().next_line(st)

        seq = self._coerce_int(getattr(st, 'sequence_number', None))
        for mcode in getattr(st, 'mcodes', ()) or ():
            code = self._coerce_int(mcode)
            if code in _KINS_BY_MCODE:
                kins_type = _KINS_BY_MCODE[code]
                if self._preview_switchkins_type != kins_type:
                    LOG.info("Preview switchkins: M%s -> type=%s (seq=%s)",
                             code, kins_type, seq)
                self._preview_switchkins_type = kins_type

        units = self._coerce_int(getattr(st, 'units', 0) or 0)
        if units in (1, 2, 3):
            self._preview_program_units = units

    # -- small coercers -----------------------------------------------------

    @staticmethod
    def _coerce_int(value):
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value) if value.is_integer() else None
        text = str(value or '').strip()
        if not text:
            return None
        try:
            numeric = float(text)
        except (TypeError, ValueError):
            return None
        return int(numeric) if numeric.is_integer() else None

    @staticmethod
    def _coerce_float_or_default(value, default=1.0):
        if isinstance(value, bool):
            return float(int(value))
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value or '').strip()
        if not text:
            return float(default)
        pattern = r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$'
        if re.fullmatch(pattern, text):
            return float(text)
        return float(default)

    # -- units --------------------------------------------------------------

    def _program_to_machine_length_factor(self):
        # gcode.parse() hands the canon inches regardless of G20/G21, so the
        # conversion depends only on machine units (see the comment above).
        machine_is_metric = bool(self._datasource.isMachineMetric()) if self._datasource else False
        factor = 25.4 if machine_is_metric else 1.0

        fallback_units = ''
        if self._datasource is not None:
            fallback_units = str(self._datasource.getProgramUnits() or '').strip().lower()
        log_key = (machine_is_metric, self._preview_program_units,
                   fallback_units, round(float(factor), 9))
        if self._last_units_factor_log != log_key:
            LOG.debug("units factor: metric=%s preview=%s fallback=%s factor=%.9f",
                      machine_is_metric, self._preview_program_units,
                      fallback_units, factor)
            self._last_units_factor_log = log_key
        return factor

    @staticmethod
    def _scale_linear_axes(point_values, factor):
        scaled = list(point_values)
        f = BackplotCanon._coerce_float_or_default(factor, 1.0)
        for idx in (0, 1, 2, 6, 7, 8):
            if idx < len(scaled):
                scaled[idx] = float(scaled[idx]) * f
        return scaled

    # -- rotary helpers -----------------------------------------------------

    @staticmethod
    def _rotate_point_about_axis(point_xyz, pivot_xyz, axis_name, angle_deg):
        px, py, pz = float(point_xyz[0]), float(point_xyz[1]), float(point_xyz[2])
        ox, oy, oz = float(pivot_xyz[0]), float(pivot_xyz[1]), float(pivot_xyz[2])
        x, y, z = px - ox, py - oy, pz - oz

        theta = math.radians(float(angle_deg))
        ct, st = math.cos(theta), math.sin(theta)

        axis = str(axis_name or '').upper()
        if axis == 'A':
            rx, ry, rz = x, y * ct - z * st, y * st + z * ct
        elif axis == 'B':
            rx, ry, rz = x * ct + z * st, y, -x * st + z * ct
        else:
            rx, ry, rz = x * ct - y * st, x * st + y * ct, z
        return (rx + ox, ry + oy, rz + oz)

    @classmethod
    def _transform_point_to_part_frame(cls, point_xyz, pivots_local, angles_by_axis, active_axes):
        p = (float(point_xyz[0]), float(point_xyz[1]), float(point_xyz[2]))
        for axis in ('A', 'B', 'C'):
            if axis not in active_axes:
                continue
            p = cls._rotate_point_about_axis(p, pivots_local[axis], axis,
                                             float(angles_by_axis.get(axis, 0.0)))
        return p

    @staticmethod
    def _rotary_delta_deg(start_angle, end_angle, wrapped=False):
        delta = float(end_angle) - float(start_angle)
        if not wrapped:
            return delta
        return ((delta + 180.0) % 360.0) - 180.0

    def _sample_table_rotary_motion_points(self, start_point, end_point, wcs_index,
                                           switchkins_type=0, program_to_machine_factor=1.0):
        sx, sy, sz = float(start_point[0]), float(start_point[1]), float(start_point[2])
        ex, ey, ez = float(end_point[0]), float(end_point[1]), float(end_point[2])

        axis_owner = self._datasource.getAxisMotionOwners() if self._datasource else {}
        origins = self._datasource.getRotaryAxisOrigins() if self._datasource else {}
        wrapped_axes = self._rotary_axis_wrapped

        deltas = {
            'A': self._rotary_delta_deg(start_point[3], end_point[3], wrapped_axes.get('A', False)),
            'B': self._rotary_delta_deg(start_point[4], end_point[4], wrapped_axes.get('B', False)),
            'C': self._rotary_delta_deg(start_point[5], end_point[5], wrapped_axes.get('C', False)),
        }
        start_angles = {'A': float(start_point[3]), 'B': float(start_point[4]), 'C': float(start_point[5])}
        end_angles = {'A': float(end_point[3]), 'B': float(end_point[4]), 'C': float(end_point[5])}

        active_axes = []
        for axis in ('A', 'B', 'C'):
            if axis_owner.get(axis, 'head') != 'table':
                continue
            if (abs(deltas[axis]) <= 1e-8 and abs(start_angles[axis]) <= 1e-8
                    and abs(end_angles[axis]) <= 1e-8):
                continue
            if origins.get(axis) is None:
                continue
            active_axes.append(axis)

        if int(switchkins_type) == 1 and not active_axes:
            return None
        if not active_axes:
            return None

        wcs_offsets = self._scale_linear_axes(
            self.initial_wcs_offsets.get(wcs_index, (0.0,) * 9),
            program_to_machine_factor,
        )
        pivots_local = {}
        for axis in active_axes:
            origin = origins[axis]
            pivots_local[axis] = (
                float(origin[0] - wcs_offsets[0]),
                float(origin[1] - wcs_offsets[1]),
                float(origin[2] - wcs_offsets[2]),
            )

        max_delta = max(abs(deltas[axis]) for axis in active_axes)
        step_deg = 2.0
        steps = 1 if max_delta <= 1e-8 else max(2, math.ceil(max_delta / step_deg))

        sampled = []
        for i in range(steps + 1):
            frac = float(i) / float(steps)
            machine_xyz = (sx + (ex - sx) * frac, sy + (ey - sy) * frac, sz + (ez - sz) * frac)
            angles_now = {axis: start_angles[axis] + deltas[axis] * frac for axis in ('A', 'B', 'C')}
            sampled.append(self._transform_point_to_part_frame(machine_xyz, pivots_local, angles_now, active_axes))
        return sampled

    # -- comment handling ---------------------------------------------------

    def comment(self, comment):
        items = comment.lower().split(',', 1)
        if items and items[0] in ('axis', 'backplot'):
            cmd = items[1].strip() if len(items) > 1 else ''
            if cmd == "hide":
                self.suppress += 1
            elif cmd == "show":
                self.suppress -= 1
            elif cmd == 'stop':
                LOG.info("Backplot generation aborted.")
                raise KeyboardInterrupt
            elif cmd.startswith("xy_z_pos"):
                self.foam_z = float(cmd.split(',')[1])
            elif cmd.startswith("uv_z_pos"):
                self.foam_w = float(cmd.split(',')[1])

    def message(self, msg):
        pass

    # -- WCS / path accumulation -------------------------------------------

    def set_g5x_offset(self, index, x, y, z, a, b, c, u, v, w):
        super().set_g5x_offset(index, x, y, z, a, b, c, u, v, w)
        if index <= 0:
            return

        new_wcs = index - 1
        if new_wcs not in self.path_records:
            self.path_records[new_wcs] = []
            self.initial_wcs_offsets[new_wcs] = (x, y, z, a, b, c, u, v, w)

        if not self.path_segments or self.path_segments[-1]['wcs_index'] != new_wcs:
            self.path_segments.append({'wcs_index': new_wcs, 'lines': []})

        self._active_wcs_index = new_wcs

    def set_xy_rotation(self, rotation):
        # Rotation is applied once by the widget's WCS transform; baking it here
        # too would rotate geometry twice.
        self.rotation_xy = 0.0
        self.rotation_cos = 1.0
        self.rotation_sin = 0.0

    def get_floating_wcs(self):
        return {wcs for wcs in self.path_records if wcs not in self._anchored_wcs}

    def add_path_point(self, line_type, start_point, end_point):
        if self._active_wcs_index not in self.path_records:
            self.path_records[self._active_wcs_index] = []

        if not self.path_segments or self.path_segments[-1]['wcs_index'] != self._active_wcs_index:
            self.path_segments.append({'wcs_index': self._active_wcs_index, 'lines': []})
        segment_index = len(self.path_segments) - 1

        program_to_machine = self._program_to_machine_length_factor()
        start_scaled = self._scale_linear_axes(start_point, program_to_machine)
        end_scaled = self._scale_linear_axes(end_point, program_to_machine)

        if self.position_anchored:
            self._anchored_wcs.add(self._active_wcs_index)

        # Loaded geometry ignores runtime TLO.
        tool_offsets_scaled = [0.0] * 9
        wcs_offsets_scaled = self._scale_linear_axes(
            self.initial_wcs_offsets[self._active_wcs_index], program_to_machine)

        adj_start = list(start_scaled)
        adj_end = list(end_scaled)
        for i in range(9):
            if i == 2:
                adj_start[i] -= tool_offsets_scaled[i]
                adj_end[i] -= tool_offsets_scaled[i]
            else:
                adj_start[i] += tool_offsets_scaled[i]
                adj_end[i] += tool_offsets_scaled[i]
        for count, value in enumerate(wcs_offsets_scaled):
            adj_start[count] -= value
            adj_end[count] -= value

        line_number = int(getattr(self, 'seq_num', -1))

        skip_render = False
        if self._pending_tool_event_motion and line_type in ('traverse', 'feed', 'arcfeed'):
            if line_type == 'traverse':
                if self._pending_tool_event_traverse_suppressed == 0:
                    skip_render = True
                    self._pending_tool_event_traverse_suppressed = 1
                else:
                    x_eps = 1e-7
                    if abs(start_scaled[0]) <= x_eps and abs(end_scaled[0]) <= x_eps:
                        skip_render = True
                    else:
                        self._pending_tool_event_motion = False
                        self._pending_tool_event_traverse_suppressed = 0
            else:
                self._pending_tool_event_motion = False
                self._pending_tool_event_traverse_suppressed = 0

        self.path_records[self._active_wcs_index].append((
            line_type,
            (tuple(adj_start), tuple(adj_end)),
            int(self._preview_switchkins_type),
            float(program_to_machine),
            line_number,
            segment_index,
            bool(skip_render),
        ))
        self.path_segments[-1]['lines'].append((line_type,
                                                (tuple(adj_start), tuple(adj_end))))

    # -- geometry build -----------------------------------------------------

    def build_geometry(self) -> BackplotGeometry:
        """Turn the accumulated points into :class:`BackplotGeometry`."""
        result = BackplotGeometry(
            added_segments=0,
            floating_wcs=self.get_floating_wcs(),
            foam=(float(self.foam_z), float(self.foam_w)),
        )

        is_foam = bool(self._datasource.isMachineFoam()) if self._datasource else False

        for wcs_index, records in self.path_records.items():
            points = array('f')
            colors = []
            line_numbers = []
            has_motion = False
            current_segment = None
            foam_z = float(self.foam_z) / 25.4
            foam_w = float(self.foam_w) / 25.4

            for row in records:
                (line_type, line_data, switchkins_type, program_to_machine,
                 line_number, segment_index, skip_render) = row

                if segment_index != current_segment:
                    current_segment = segment_index
                    has_motion = False

                if skip_render:
                    continue

                start_point, end_point = line_data
                rgba = self.role_colors.get(line_type, (255, 255, 255, 255))

                if is_foam:
                    self._emit_segment(points, colors, line_numbers,
                                       (start_point[0], start_point[1], start_point[8] + foam_z),
                                       (end_point[0], end_point[1], start_point[8] + foam_z),
                                       rgba, line_number)
                    self._emit_segment(points, colors, line_numbers,
                                       (start_point[6], start_point[7], start_point[8] + foam_w),
                                       (end_point[6], end_point[7], start_point[8] + foam_w),
                                       rgba, line_number)
                else:
                    if (not has_motion) and line_type == 'traverse':
                        continue

                    sampled = self._sample_table_rotary_motion_points(
                        start_point, end_point, wcs_index, switchkins_type, program_to_machine)
                    if sampled and len(sampled) > 1:
                        prev = sampled[0]
                        for curr in sampled[1:]:
                            self._emit_segment(points, colors, line_numbers, prev, curr,
                                               rgba, line_number)
                            prev = curr
                    else:
                        self._emit_segment(points, colors, line_numbers, start_point,
                                           end_point, rgba, line_number)

                    if line_type in ('traverse', 'feed', 'arcfeed'):
                        has_motion = True

            path = PathGeometry(
                wcs_index=wcs_index,
                points=np.frombuffer(points, dtype=np.float32).reshape(-1, 3).copy(),
                colors=np.asarray(colors, dtype=np.uint8).reshape(-1, 4) if colors
                else np.zeros((0, 4), dtype=np.uint8),
                line_numbers=np.asarray(line_numbers, dtype=np.int32) if line_numbers
                else np.zeros((0,), dtype=np.int32),
            )
            result.paths[wcs_index] = path

        added = sum(p.segment_count for p in result.paths.values())
        self.added_segments = added
        result.added_segments = added
        result.offset_transitions = self._build_offset_transitions()
        self.offset_transitions = result.offset_transitions
        return result

    @staticmethod
    def _emit_segment(points, colors, line_numbers, start_point, end_point,
                      rgba, line_number):
        """Append one 2-point line segment and its per-segment metadata."""
        points.extend((end_point[0], end_point[1], end_point[2],
                       start_point[0], start_point[1], start_point[2]))
        colors.append(rgba)
        line_numbers.append(int(line_number))

    def _build_offset_transitions(self):
        transitions = []
        if (self._datasource is not None and self._datasource.isMachineFoam()) or len(self.path_segments) <= 1:
            return transitions

        summaries = []
        for segment in self.path_segments:
            wcs_index = segment['wcs_index']
            seg_start = seg_end = None
            has_cut = False
            first_cut_start = last_cut_end = None

            for line_type, line_data in segment['lines']:
                start_point, end_point = line_data
                if line_type in ('feed', 'arcfeed'):
                    has_cut = True
                    if first_cut_start is None:
                        first_cut_start = list(start_point[:3])
                    last_cut_end = list(end_point[:3])
                if seg_start is None:
                    seg_start = list(start_point[:3])
                seg_end = list(end_point[:3])

            summaries.append((wcs_index, seg_start, seg_end, has_cut, first_cut_start, last_cut_end))

        for i in range(1, len(summaries)):
            prev_wcs, _, prev_end, prev_cut, _, _ = summaries[i - 1]
            next_wcs, next_start, _, next_cut, next_first_cut, _ = summaries[i]
            if not prev_cut or not next_cut or prev_wcs == next_wcs:
                continue
            if prev_wcs < 0 or next_wcs < 0:
                continue
            transition_to = next_first_cut if next_first_cut is not None else next_start
            if prev_end is None or transition_to is None:
                continue
            transitions.append(OffsetTransition(prev_wcs, next_wcs, prev_end, transition_to))
        return transitions
