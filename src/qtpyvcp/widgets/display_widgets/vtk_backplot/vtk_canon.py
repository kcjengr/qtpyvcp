from collections import OrderedDict

import math
import re

import vtk
import vtk.qt
from .linuxcnc_datasource import LinuxCncDataSource
from .path_actor import PathActor

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from qtpyvcp.utilities import logger
from qtpyvcp.widgets.display_widgets.vtk_backplot.base_canon import StatCanon


LOG = logger.getLogger(__name__)

COLOR_MAP = {
    'traverse': QColor(200, 35, 35, 255),
    'arcfeed': QColor(110, 110, 255, 255),
    'feed': QColor(210, 210, 255, 255),
    'dwell': QColor(0, 0, 255, 255),
    'user': QColor(0, 100, 255, 255)
}

class VTKCanon(StatCanon):
    def __init__(self, colors=COLOR_MAP, *args, **kwargs):
        cpp_mode = bool(kwargs.pop('cpp_mode', False))
        super(VTKCanon, self).__init__(*args, **kwargs)
        self._datasource = LinuxCncDataSource()
        self.arcdivision = self._datasource.getArcDivision()
        self._cpp_mode = cpp_mode and (not self._datasource.isMachineFoam())
        self._cpp_line_type_codes = {
            'traverse': 0,
            'feed': 1,
            'arcfeed': 2,
            'dwell': 3,
            'user': 4,
        }

        self.path_colors = colors
        self.path_actors = OrderedDict()
        self.path_points = OrderedDict()
        self.initial_wcs_offsets = OrderedDict()

        self.paths_start_point = OrderedDict()
        self.paths_angle_point = OrderedDict()
        self.paths_end_point = OrderedDict()
        self.path_segments = list()
        self.offset_transitions = list()

        self.active_wcs_index = self._datasource.getActiveWcsIndex()
        self.active_rotation = self._datasource.getRotationOfActiveWcs()
        self.tool_offset = self._datasource.getToolOffset()
        self.added_segments = 0
        self._preview_switchkins_type = 0
        self._preview_program_units = None
        self._last_units_factor_log = None

        g5x = self._datasource.getActiveWcsOffsets()

        # ensure Canon has correct starting offsets per var file
        # set_g5x_offset() receives LinuxCNC's canonical index where G53 is 0,
        # while active_wcs_index is already zero-based from G54.
        super().set_g5x_offset(self.active_wcs_index + 1, g5x[0],g5x[1],g5x[2],g5x[3],g5x[4],g5x[5],g5x[6],g5x[7],g5x[8])
        
        self.foam_z = 0.0
        self.foam_w = 0.0
        LOG.debug("VTKCanon --- Init Done ---")

    def next_line(self, st):
        super().next_line(st)

        # Capture switchkins transitions seen by the preview interpreter so
        # load-time shaping follows M428/M429 state the same way runtime does.
        seq = self._coerce_int(getattr(st, 'sequence_number', None))
        for mcode in getattr(st, 'mcodes', ()):
            code = self._coerce_int(mcode)
            if code is None:
                continue
            if code == 428:
                LOG.warning(
                    "VTK preview switchkins command: M428 encountered (seq=%s)",
                    seq,
                )
                if self._preview_switchkins_type != 1:
                    LOG.info(
                        "VTK preview switchkins: M428 detected -> switchkins_type=1 (seq=%s)",
                        seq,
                    )
                self._preview_switchkins_type = 1
            elif code in (429, 430):
                LOG.warning(
                    "VTK preview switchkins command: M%s encountered (seq=%s)",
                    code,
                    seq,
                )
                if self._preview_switchkins_type != 0:
                    LOG.info(
                        "VTK preview switchkins: M%s detected -> switchkins_type=0 (seq=%s)",
                        code,
                        seq,
                    )
                self._preview_switchkins_type = 0

        # Track the interpreter units mode for load-time scaling.
        # LinuxCNC canonical units: 1=in, 2=mm, 3=cm.
        units = self._coerce_int(getattr(st, 'units', 0) or 0)
        if units in (1, 2, 3):
            self._preview_program_units = units

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
        if text[0] in ('+', '-'):
            digits = text[1:]
        else:
            digits = text
        if digits.isdigit():
            return int(text)
        return None

    @staticmethod
    def _coerce_float_or_default(value, default=1.0):
        if isinstance(value, bool):
            return float(int(value))
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value or '').strip()
        if not text:
            return float(default)
        float_pattern = r'^[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][+-]?\\d+)?$'
        if re.fullmatch(float_pattern, text):
            return float(text)
        return float(default)

    def _program_to_machine_length_factor(self):
        # Convert parsed program coordinates into configured machine units.
        # Avoid deriving from machine units alone: G20/G21 can change per file.
        machine_is_metric = bool(self._datasource.isMachineMetric())

        program_units = self._preview_program_units
        if program_units is None:
            # Fallback to status string when preview state isn't available yet.
            units_text = str(self._datasource.getProgramUnits() or '').strip().lower()
            if units_text in ('in', 'inch', 'inches'):
                program_units = 1
            elif units_text in ('mm', 'metric', 'millimeter', 'millimeters'):
                program_units = 2
            elif units_text in ('cm', 'centimeter', 'centimeters'):
                program_units = 3

        # program_units -> mm
        if program_units == 1:
            to_mm = 25.4
        elif program_units == 3:
            to_mm = 10.0
        else:
            to_mm = 1.0

        # mm -> machine units
        if machine_is_metric:
            factor = float(to_mm)
        else:
            factor = float(to_mm / 25.4)

        fallback_program_units = str(self._datasource.getProgramUnits() or '').strip().lower()
        log_key = (
            bool(machine_is_metric),
            self._preview_program_units,
            fallback_program_units,
            round(float(factor), 9),
        )
        if self._last_units_factor_log != log_key:
            # This function is called for each segment; only log on unit-state change.
            LOG.debug(
                "VTK units factor: machine_is_metric=%s preview_program_units=%s fallback_program_units=%s factor=%.9f",
                machine_is_metric,
                self._preview_program_units,
                fallback_program_units,
                factor,
            )
            self._last_units_factor_log = log_key
        return factor

    @staticmethod
    def _scale_linear_axes(point_values, factor):
        scaled = list(point_values)
        f = VTKCanon._coerce_float_or_default(factor, 1.0)

        for idx in (0, 1, 2, 6, 7, 8):
            if idx < len(scaled):
                scaled[idx] = float(scaled[idx]) * f
        return scaled

    @staticmethod
    def _rotate_point_about_axis(point_xyz, pivot_xyz, axis_name, angle_deg):
        px, py, pz = float(point_xyz[0]), float(point_xyz[1]), float(point_xyz[2])
        ox, oy, oz = float(pivot_xyz[0]), float(pivot_xyz[1]), float(pivot_xyz[2])

        # Shift into pivot-local coordinates.
        x = px - ox
        y = py - oy
        z = pz - oz

        theta = math.radians(float(angle_deg))
        ct = math.cos(theta)
        st = math.sin(theta)

        axis = str(axis_name or '').upper()
        if axis == 'A':
            # Rotate about X
            ry = y * ct - z * st
            rz = y * st + z * ct
            rx = x
        elif axis == 'B':
            # Rotate about Y
            rx = x * ct + z * st
            rz = -x * st + z * ct
            ry = y
        else:
            # Rotate about Z (C)
            rx = x * ct - y * st
            ry = x * st + y * ct
            rz = z

        return (rx + ox, ry + oy, rz + oz)

    @staticmethod
    def _transform_point_to_part_frame(point_xyz, pivots_local, angles_by_axis, active_axes):
        p = (float(point_xyz[0]), float(point_xyz[1]), float(point_xyz[2]))
        # Apply table chain parent-to-child to match live overlay transform
        # composition in vtk_backplot (_overlay_rotary_axis_order).
        # Use positive table angles so load-time geometry follows program
        # direction for table-owned rotary axes.
        for axis in ('A', 'B', 'C'):
            if axis not in active_axes:
                continue
            p = VTKCanon._rotate_point_about_axis(
                p,
                pivots_local[axis],
                axis,
                float(angles_by_axis.get(axis, 0.0)),
            )
        return p

    def _sample_table_rotary_motion_points(
        self,
        start_point,
        end_point,
        wcs_index,
        switchkins_type=0,
        program_to_machine_factor=1.0,
    ):
        # Convert machine-frame path points into part frame using absolute
        # table rotary angles. This handles constant-angle cuts (e.g. A=30)
        # and varying-angle sweeps with one consistent mapping.
        sx, sy, sz = float(start_point[0]), float(start_point[1]), float(start_point[2])
        ex, ey, ez = float(end_point[0]), float(end_point[1]), float(end_point[2])

        axis_owner = self._datasource.getAxisMotionOwners()
        origins = self._datasource.getRotaryAxisOrigins()

        da = float(end_point[3] - start_point[3])
        db = float(end_point[4] - start_point[4])
        dc = float(end_point[5] - start_point[5])
        deltas = {'A': da, 'B': db, 'C': dc}

        start_angles = {
            'A': float(start_point[3]),
            'B': float(start_point[4]),
            'C': float(start_point[5]),
        }
        end_angles = {
            'A': float(end_point[3]),
            'B': float(end_point[4]),
            'C': float(end_point[5]),
        }

        active_axes = []
        for axis in ('A', 'B', 'C'):
            if axis_owner.get(axis, 'head') != 'table':
                continue
            if abs(deltas[axis]) <= 1e-8 and abs(start_angles[axis]) <= 1e-8 and abs(end_angles[axis]) <= 1e-8:
                continue
            if origins.get(axis) is None:
                continue
            active_axes.append(axis)

        # For switchkins runs with no table-owned rotary axes, keep legacy
        # behavior (no additional rotary-part-frame sampling).
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
        if max_delta <= 1e-8:
            steps = 1
        else:
            steps = max(2, int(math.ceil(max_delta / step_deg)))

        sampled = []
        for i in range(0, steps + 1):
            frac = float(i) / float(steps)

            machine_xyz = (
                sx + (ex - sx) * frac,
                sy + (ey - sy) * frac,
                sz + (ez - sz) * frac,
            )

            angles_now = {
                'A': start_angles['A'] + deltas['A'] * frac,
                'B': start_angles['B'] + deltas['B'] * frac,
                'C': start_angles['C'] + deltas['C'] * frac,
            }

            sampled.append(
                self._transform_point_to_part_frame(
                    machine_xyz,
                    pivots_local,
                    angles_now,
                    active_axes,
                )
            )

        return sampled

    def comment(self, comment):
        items = comment.lower().split(',', 1)
        if len(items) > 0 and items[0] in ['axis', 'backplot']:
            cmd = items[1].strip()
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
        
    
    def set_g5x_offset(self, index, x, y, z, a, b, c, u, v, w):
        # ensure the passed values get set on 'self' via super
        super().set_g5x_offset(index, x, y, z, a, b, c, u, v, w)

        # G53 (machine coordinates) is non-modal and should not create a WCS segment.
        if index <= 0:
            return

        new_wcs = index - 1  # this index counts also G53 so we need to do -1
        
        if new_wcs not in self.path_points:
            #self.path_actors[new_wcs] = PathActor(self._datasource)
            self.path_points[new_wcs] = list()
            self.initial_wcs_offsets[new_wcs] = (x, y, z, a, b, c, u, v, w)

        if len(self.path_segments) == 0 or self.path_segments[-1]['wcs_index'] != new_wcs:
            self.path_segments.append({'wcs_index': new_wcs, 'lines': list()})

        self.active_wcs_index = new_wcs

    def set_xy_rotation(self, rotation):
        self.rotation_xy = 0.0
        theta = math.radians(0.0)
        self.rotation_cos = math.cos(theta)
        self.rotation_sin = math.sin(theta)


    def add_path_point(self, line_type, start_point, end_point):
        # As the points come through with the active wcs offsets baked in
        # remove them to allow vtk setusertransforms to work correctly.
        # These transforms apply wcs offsets for us in VTK

        # check to see if active wcs is in the path_actor list.
        if self.active_wcs_index not in self.path_actors:
            self.path_actors[self.active_wcs_index] = PathActor(self._datasource)

        if len(self.path_segments) == 0 or self.path_segments[-1]['wcs_index'] != self.active_wcs_index:
            self.path_segments.append({'wcs_index': self.active_wcs_index, 'lines': list()})

        # Normalize parsed coordinates into machine units at ingest time.
        # This keeps downstream WCS/pivot math unit-consistent regardless of
        # G20/G21 switches or machine/unit mismatches.
        program_to_machine = self._program_to_machine_length_factor()
        start_point_scaled = self._scale_linear_axes(start_point, program_to_machine)
        end_point_scaled = self._scale_linear_axes(end_point, program_to_machine)
        tool_offsets_scaled = self._scale_linear_axes(self.tool_offsets, program_to_machine)
        wcs_offsets_scaled = self._scale_linear_axes(
            self.initial_wcs_offsets[self.active_wcs_index],
            program_to_machine,
        )

        if self._cpp_mode:
            start_xyz = (
                start_point_scaled[0] + tool_offsets_scaled[0] - wcs_offsets_scaled[0],
                start_point_scaled[1] + tool_offsets_scaled[1] - wcs_offsets_scaled[1],
                start_point_scaled[2] - tool_offsets_scaled[2] - wcs_offsets_scaled[2],
            )
            end_xyz = (
                end_point_scaled[0] + tool_offsets_scaled[0] - wcs_offsets_scaled[0],
                end_point_scaled[1] + tool_offsets_scaled[1] - wcs_offsets_scaled[1],
                end_point_scaled[2] - tool_offsets_scaled[2] - wcs_offsets_scaled[2],
            )
            line = (
                start_xyz[0], start_xyz[1], start_xyz[2],
                end_xyz[0], end_xyz[1], end_xyz[2],
            )
            line_type_token = self._cpp_line_type_codes.get(line_type, line_type)
        else:
            adj_start_point = list(start_point_scaled)
            adj_end_point = list(end_point_scaled)

            for i in range(9):
                if i == 2:
                    adj_start_point[i] -= tool_offsets_scaled[i]
                    adj_end_point[i] -= tool_offsets_scaled[i]
                else:
                    adj_start_point[i] += tool_offsets_scaled[i]
                    adj_end_point[i] += tool_offsets_scaled[i]

            for count, value in enumerate(wcs_offsets_scaled):
                adj_start_point[count] -= value
                adj_end_point[count] -= value

            line = [tuple(adj_start_point), tuple(adj_end_point)]
            line_type_token = line_type

        if not self._cpp_mode:
            self.path_points.get(self.active_wcs_index).append(
                (line_type, line, int(self._preview_switchkins_type), float(program_to_machine))
            )
        self.path_segments[-1]['lines'].append((line_type_token, line))

    def draw_lines(self):
        # Used to draw the lines of the loaded program
        # Points are pre-normalized to machine units in add_path_point().
        multiplication_factor = 1.0

        first_cut_wcs_index = None
        for segment in self.path_segments:
            if any(line_type != "traverse" for line_type, _ in segment['lines']):
                first_cut_wcs_index = segment['wcs_index']
                break

        added_segment_count = 0

        for wcs_index, data in self.path_points.items():

            path_actor = self.path_actors.get(wcs_index)

            if path_actor is not None:
                last_point = None
                point_count = 0

                for row in data:
                    if len(row) >= 4:
                        line_type, line_data, switchkins_type, row_program_to_machine = row[0], row[1], row[2], row[3]
                    elif len(row) >= 3:
                        line_type, line_data, switchkins_type = row[0], row[1], row[2]
                        row_program_to_machine = 1.0
                    else:
                        line_type, line_data = row[0], row[1]
                        switchkins_type = 0
                        row_program_to_machine = 1.0

                    start_point = line_data[0]
                    end_point = line_data[1]

                    if self._datasource.isMachineFoam():

                        path_actor.points.InsertNextPoint(start_point[0] * multiplication_factor,
                                                          start_point[1] * multiplication_factor,
                                                          (start_point[8]+(self.foam_z/25.4)) * multiplication_factor)

                        path_actor.points.InsertNextPoint(end_point[0] * multiplication_factor,
                                                          end_point[1] * multiplication_factor,
                                                          (start_point[8]+(self.foam_z/25.4)) * multiplication_factor)


                        path_actor.colors.InsertNextTypedTuple(self.path_colors.get(line_type).getRgb()[:4])

                        line = vtk.vtkLine()
                        line.GetPointIds().SetId(0, point_count)
                        line.GetPointIds().SetId(1, point_count + 1)

                        path_actor.lines.InsertNextCell(line)

                        point_count += 2
                        added_segment_count += 1

                        path_actor.points.InsertNextPoint(start_point[6] * multiplication_factor,
                                                          start_point[7] * multiplication_factor,
                                                          (start_point[8]+(self.foam_w/25.4)) * multiplication_factor)

                        path_actor.points.InsertNextPoint(end_point[6] * multiplication_factor,
                                                          end_point[7] * multiplication_factor,
                                                          (start_point[8]+(self.foam_w/25.4)) * multiplication_factor)

                        path_actor.colors.InsertNextTypedTuple(self.path_colors.get(line_type).getRgb()[:4])

                        line2 = vtk.vtkLine()
                        line2.GetPointIds().SetId(0, point_count)
                        line2.GetPointIds().SetId(1, point_count + 1)

                        path_actor.lines.InsertNextCell(line2)

                        point_count += 2
                        added_segment_count += 1

                    else:
                        # LOG.debug(f"--------- Points:")
                        # The first traverse in a segment has no provable
                        # start point in preview context, so do not render it
                        # as geometry.
                        if (point_count == 0) and (line_type == "traverse"):
                            continue

                        def _insert_xyz_segment(seg_start_xyz, seg_end_xyz):
                            nonlocal point_count, added_segment_count
                            path_actor.points.InsertNextPoint(seg_end_xyz[0] * multiplication_factor,
                                                              seg_end_xyz[1] * multiplication_factor,
                                                              seg_end_xyz[2] * multiplication_factor)

                            path_actor.points.InsertNextPoint(seg_start_xyz[0] * multiplication_factor,
                                                              seg_start_xyz[1] * multiplication_factor,
                                                              seg_start_xyz[2] * multiplication_factor)

                            path_actor.colors.InsertNextTypedTuple(self.path_colors.get(line_type).getRgb())

                            vtk_line = vtk.vtkLine()
                            vtk_line.GetPointIds().SetId(0, point_count)
                            vtk_line.GetPointIds().SetId(1, point_count + 1)
                            path_actor.lines.InsertNextCell(vtk_line)

                            point_count += 2
                            added_segment_count += 1

                        sampled_points = self._sample_table_rotary_motion_points(
                            start_point,
                            end_point,
                            wcs_index,
                            switchkins_type,
                            row_program_to_machine,
                        )
                        if sampled_points and len(sampled_points) > 1:
                            prev = sampled_points[0]
                            for curr in sampled_points[1:]:
                                _insert_xyz_segment(prev, curr)
                                prev = curr
                        else:
                            _insert_xyz_segment(start_point, end_point)

                    last_point = end_point

                # free up memory, lots of it for big files

                self.path_points[wcs_index].clear()
                QApplication.processEvents()

                path_actor.poly_data.SetPoints(path_actor.points)
                path_actor.poly_data.SetLines(path_actor.lines)
                path_actor.poly_data.GetCellData().SetScalars(path_actor.colors)
                path_actor.data_mapper.SetInputData(path_actor.poly_data)
                path_actor.data_mapper.Update()
                path_actor.SetMapper(path_actor.data_mapper)
                # LOG.debug(f"-------- Path Actor Matrix :  {path_actor.GetMatrix()}")

        self.offset_transitions = list()

        if (not self._datasource.isMachineFoam()) and (len(self.path_segments) > 1):
            segment_summaries = list()

            for segment_index, segment in enumerate(self.path_segments):
                segment_wcs_index = segment['wcs_index']
                segment_data = segment['lines']
                segment_start = None
                segment_end = None
                segment_has_cut_motion = False
                first_cut_start = None
                last_cut_end = None

                for segment_line_type, segment_line_data in segment_data:
                    segment_start_point = segment_line_data[0]
                    segment_end_point = segment_line_data[1]

                    if segment_line_type != "traverse":
                        segment_has_cut_motion = True

                        if first_cut_start is None:
                            first_cut_start = [
                                segment_start_point[0] * multiplication_factor,
                                segment_start_point[1] * multiplication_factor,
                                segment_start_point[2] * multiplication_factor,
                            ]

                        last_cut_end = [
                            segment_end_point[0] * multiplication_factor,
                            segment_end_point[1] * multiplication_factor,
                            segment_end_point[2] * multiplication_factor,
                        ]

                    if segment_start is None:
                        segment_start = [
                            segment_start_point[0] * multiplication_factor,
                            segment_start_point[1] * multiplication_factor,
                            segment_start_point[2] * multiplication_factor,
                        ]

                    segment_end = [
                        segment_end_point[0] * multiplication_factor,
                        segment_end_point[1] * multiplication_factor,
                        segment_end_point[2] * multiplication_factor,
                    ]

                segment_summaries.append((
                    segment_wcs_index,
                    segment_start,
                    segment_end,
                    segment_has_cut_motion,
                    first_cut_start,
                    last_cut_end,
                ))

            for transition_index in range(1, len(segment_summaries)):
                prev_wcs_index, _, prev_end, prev_has_cut_motion, _, prev_last_cut_end = segment_summaries[transition_index - 1]
                next_wcs_index, next_start, _, next_has_cut_motion, next_first_cut_start, _ = segment_summaries[transition_index]

                if not prev_has_cut_motion or not next_has_cut_motion:
                    continue

                if prev_wcs_index == next_wcs_index:
                    continue

                if prev_wcs_index < 0 or next_wcs_index < 0:
                    continue

                # Source from the actual end of prior segment (preserves final
                # reposition like G53), but target first cutting point in next
                # segment to avoid linking to an intermediate traverse start.
                transition_from = prev_end
                transition_to = next_first_cut_start if next_first_cut_start is not None else next_start

                if transition_from is None or transition_to is None:
                    continue

                self.offset_transitions.append({
                    'from_wcs': prev_wcs_index,
                    'to_wcs': next_wcs_index,
                    'from_end': transition_from,
                    'to_start': transition_to,
                })

        self.added_segments = added_segment_count

    def get_path_actors(self):
        return self.path_actors

    def get_foam(self):
        return self.foam_z, self.foam_w

    def get_offset_transitions(self):
        return self.offset_transitions

