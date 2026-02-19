import sys
from collections import OrderedDict

import math

import vtk
import vtk.qt
from .linuxcnc_datasource import LinuxCncDataSource
from .path_actor import PathActor

from qtpy.QtGui import QColor
from qtpy.QtWidgets import QApplication

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
        super(VTKCanon, self).__init__(*args, **kwargs)
        LOG.debug("VTKCanon --- Init ---")
        self._datasource = LinuxCncDataSource()

        self.path_colors = colors
        self.path_actors = OrderedDict()
        self.path_points = OrderedDict()
        self.initial_wcs_offsets = OrderedDict()

        self.paths_start_point = OrderedDict()
        self.paths_angle_point = OrderedDict()
        self.paths_end_point = OrderedDict()

        self.path_start_point = OrderedDict()
        self.paths_angle_points = OrderedDict()
        self.path_end_point = OrderedDict()
        self.path_segments = list()
        self.offset_transitions = list()

        self.active_wcs_index = self._datasource.getActiveWcsIndex()
        self.active_rotation = self._datasource.getRotationOfActiveWcs()
        self.tool_offset = self._datasource.getToolOffset()

        g5x = self._datasource.getActiveWcsOffsets()
        LOG.debug(f" G5x offsets = {g5x}")
        LOG.debug(f"XY Rotation = {self.active_rotation}")

        # ensure Canon has correct starting offsets per var file
        super().set_g5x_offset(self.active_wcs_index, g5x[0],g5x[1],g5x[2],g5x[3],g5x[4],g5x[5],g5x[6],g5x[7],g5x[8])
        
        self.foam_z = 0.0
        self.foam_w = 0.0

        LOG.debug("VTKCanon --- Init Done ---")

    def comment(self, comment):
        LOG.debug("G-code Comment: {}".format(comment))
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
        LOG.debug("G-code Message: {}".format(msg))
        
    
    def set_g5x_offset(self, index, x, y, z, a, b, c, u, v, w):
        # ensure the passed values get set on 'self' via super
        LOG.debug("----------------------------------")
        LOG.debug("--------- set_g5x_offset ---------")
        LOG.debug("----------------------------------")
        super().set_g5x_offset(index, x, y, z, a, b, c, u, v, w)
        new_wcs = index - 1  # this index counts also G53 so we need to do -1
        LOG.debug("---------received wcs change: {}".format(new_wcs))
        LOG.debug("--------- wcs values: x, y, z, a, b, c, u, v, w")
        LOG.debug(f"--------- wcs values: {x}, {y}, {z}, {a}, {b}, {c}, {u}, {v}, {w}")
        
        if new_wcs not in list(self.path_points.keys()):
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
        # LOG.debug("----------------------------------")
        # LOG.debug("--------- add_path_point ---------")
        # LOG.debug("----------------------------------")
        # As the points come through with the active wcs offsets baked in
        # remove them to allow vtk setusertransforms to work correctly.
        # These transforms apply wcs offsets for us in VTK
        # LOG.debug(f"--------- wcs values to back out: {self.initial_wcs_offsets[self.active_wcs_index]}")
        # LOG.debug(f"--------- Raw line_type={line_type}, start={start_point}, end={end_point}")
        #try:
        adj_start_point = list(start_point)
        adj_end_point = list(end_point)

        for i in range(9):
            if i == 2:
                adj_start_point[i] -= self.tool_offsets[i]
                adj_end_point[i] -= self.tool_offsets[i]
            else:
                adj_start_point[i] += self.tool_offsets[i]
                adj_end_point[i] += self.tool_offsets[i]

        # check to see if active wcs is in the path_actor list.
        if self.active_wcs_index not in list(self.path_actors.keys()):
            self.path_actors[self.active_wcs_index] = PathActor(self._datasource)

        if len(self.path_segments) == 0 or self.path_segments[-1]['wcs_index'] != self.active_wcs_index:
            self.path_segments.append({'wcs_index': self.active_wcs_index, 'lines': list()})

        for count, value in enumerate(self.initial_wcs_offsets[self.active_wcs_index]):
            adj_start_point[count] -= value
            adj_end_point[count] -= value
        

        line = [tuple(adj_start_point), tuple(adj_end_point)]
        self.path_points.get(self.active_wcs_index).append((line_type, line))
        self.path_segments[-1]['lines'].append((line_type, line))
        # LOG.debug(f"--------- Adjusted line_type={line_type}, start={adj_start_point}, end={adj_end_point}")
        #except Exception as error:
        #    LOG.debug(f"add_path_point - Exception raised: {type(error).__name__} - {error}")

    def draw_lines(self):
        # Used to draw the lines of the loaded program
        LOG.debug("------------------------------")
        LOG.debug("--------- draw_lines ---------")
        LOG.debug("------------------------------")
        LOG.debug("--------- path points size: {}".format(sys.getsizeof(self.path_points)))
        LOG.debug("--------- path points length: {}".format(len(self.path_points)))

        # Metric programs require this scale factor so VTK path points render in machine units.
        multiplication_factor = 25.4 if self._datasource.isMachineMetric() else 1

        paths_count = 0
        prev_wcs_index = 0

        for wcs_index, data in self.path_points.items():

            path_actor = self.path_actors.get(wcs_index)

            if path_actor is not None:
                last_point = None
                point_count = 0

                for line_type, line_data in data:
                    
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

                    else:
                        # LOG.debug(f"--------- Points:")
                        if len(self.path_actors) > 1:
                            # skip rapids from original path offsets. This actually means previous wcs
                            # >1 path_actors means more than one g5x in use in the file.
                            if (paths_count > 0) and (point_count == 0) and (line_type == "traverse"):
                                continue

                            if point_count == 0:
                                position = [start_point[0] * multiplication_factor,
                                            start_point[1] * multiplication_factor,
                                            start_point[2] * multiplication_factor]

                                # Get start point for a transition line between different WCS
                                self.path_start_point[prev_wcs_index] = position
                                # LOG.debug(f"--------- Point position if point_count==0: {position} ; wcs index: {prev_wcs_index}")

                        path_actor.points.InsertNextPoint(end_point[0] * multiplication_factor,
                                                          end_point[1] * multiplication_factor,
                                                          end_point[2] * multiplication_factor)

                        path_actor.points.InsertNextPoint(start_point[0] * multiplication_factor,
                                                          start_point[1] * multiplication_factor,
                                                          start_point[2] * multiplication_factor)
                        # LOG.debug(f"--------- Path Actor Start Point : {start_point[0] * multiplication_factor} {start_point[1] * multiplication_factor} {start_point[2] * multiplication_factor}")
                        # LOG.debug(f"--------- Path Actor End Point : {end_point[0] * multiplication_factor} {end_point[1] * multiplication_factor} {end_point[2] * multiplication_factor}")

                        path_actor.colors.InsertNextTypedTuple(self.path_colors.get(line_type).getRgb())

                        line = vtk.vtkLine()
                        line.GetPointIds().SetId(0, point_count)
                        line.GetPointIds().SetId(1, point_count + 1)

                        path_actor.lines.InsertNextCell(line)

                        point_count += 2

                    last_point = end_point

                # LOG.debug(f"Length of path_actors {len(self.path_actors)}")
                # LOG.debug(f"last_point: {last_point}")
                
                if (len(self.path_actors) > 1) and (last_point is not None):
                    # Store the last point of the part as first point of the rapid line

                    position = [last_point[0] * multiplication_factor,
                                last_point[1] * multiplication_factor,
                                last_point[2] * multiplication_factor]

                    # LOG.debug(f"--------- Path Actor Last Point : {last_point[0] * multiplication_factor} {last_point[1] * multiplication_factor} {last_point[2] * multiplication_factor}")
                    # Get end point for a transition line between different WCS
                    self.path_end_point[wcs_index] = position
                else:
                    self.path_end_point[wcs_index] = None

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

            paths_count += 1

            prev_wcs_index = wcs_index

        self.offset_transitions = list()
        self.path_start_point.clear()
        self.path_end_point.clear()

        if (not self._datasource.isMachineFoam()) and (len(self.path_segments) > 1):
            segment_summaries = list()

            for segment_index, segment in enumerate(self.path_segments):
                segment_wcs_index = segment['wcs_index']
                segment_data = segment['lines']
                segment_start = None
                segment_end = None
                segment_point_count = 0

                for segment_line_type, segment_line_data in segment_data:
                    segment_start_point = segment_line_data[0]
                    segment_end_point = segment_line_data[1]

                    if (segment_index > 0) and (segment_point_count == 0) and (segment_line_type == "traverse"):
                        continue

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
                    segment_point_count += 2

                segment_summaries.append((segment_wcs_index, segment_start, segment_end))

            for transition_index in range(1, len(segment_summaries)):
                prev_wcs_index, _, prev_end = segment_summaries[transition_index - 1]
                next_wcs_index, next_start, _ = segment_summaries[transition_index]

                if prev_end is None or next_start is None:
                    continue

                if prev_wcs_index == next_wcs_index:
                    continue

                self.path_start_point[prev_wcs_index] = next_start
                self.path_end_point[prev_wcs_index] = prev_end
                self.offset_transitions.append({
                    'from_wcs': prev_wcs_index,
                    'to_wcs': next_wcs_index,
                    'from_end': prev_end,
                    'to_start': next_start,
                })

        LOG.debug("----------------------------------")
        LOG.debug("--------- draw_lines END ---------")
        LOG.debug("----------------------------------")

    def get_path_actors(self):
        return self.path_actors

    # Methods get_offsets_start_point and get_offsets_end_point provide
    # the start and end points for a transition line between different WCS
    def get_offsets_start_point(self):
        return self.path_start_point

    def get_offsets_end_point(self):
        return self.path_end_point

    def get_foam(self):
        return self.foam_z, self.foam_w

    def get_offset_transitions(self):
        return self.offset_transitions
