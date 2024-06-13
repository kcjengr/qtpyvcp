import sys
from collections import OrderedDict

import math
from pprint import pprint

import vtk


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

        self._datasource = LinuxCncDataSource()
        self.empty_path = True
        self.path_colors = colors

        self.path_actors = OrderedDict()
        self.path_points = OrderedDict()

        self.paths_start_point = OrderedDict()
        self.paths_angle_point = OrderedDict()
        self.paths_end_point = OrderedDict()

        self.path_start_point = OrderedDict()
        self.paths_angle_points = OrderedDict()
        self.path_end_point = OrderedDict()

        self.active_wcs_index = self._datasource.getActiveWcsIndex()
        self.active_rotation = self._datasource.getRotationOfActiveWcs()

        self.foam_z = 0.0
        self.foam_w = 0.0

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
        new_wcs = index - 1  # this index counts also G53 so we need to do -1
        LOG.debug("---------received wcs change: {}".format(new_wcs))
        if new_wcs not in self.path_actors.keys():
            self.path_actors[new_wcs] = PathActor(self._datasource)
            self.path_points[new_wcs] = list()

        self.active_wcs_index = new_wcs

    def set_xy_rotation(self, rotation):
        self.rotation_xy = 0.0
        theta = math.radians(0.0)
        self.rotation_cos = math.cos(theta)
        self.rotation_sin = math.sin(theta)

    def add_path_point(self, line_type, start_point, end_point):
        line = start_point, end_point
        self.path_points[self.active_wcs_index].append([line_type, line])

    def draw_lines(self):
        # Used to draw the lines of the loaded program
        LOG.debug("---------path points size: {}".format(sys.getsizeof(self.path_points)))
        LOG.debug("---------path points length: {}".format(len(self.path_points)))

        # TODO: for some reason, we need to multiply for metric, find out why!
        multiplication_factor = 25.4 if self._datasource.isMachineMetric() else 1

        paths_count = 0
        prev_wcs_index = 0

        for wcs_index, data in self.path_points.items():

            path_actor = self.path_actors.get(wcs_index)

            if path_actor is not None:

                first_point = False
                angle_point = None
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
                        if len(self.path_actors) > 1:
                            # skip rapids from original path offsets
                            if (paths_count > 0) and (point_count == 0) and (line_type == "traverse"):
                                continue

                            if point_count == 0:
                                position = [start_point[0] * multiplication_factor,
                                            start_point[1] * multiplication_factor,
                                            start_point[2] * multiplication_factor]

                                self.path_start_point[prev_wcs_index] = position

                        path_actor.points.InsertNextPoint(end_point[0] * multiplication_factor,
                                                          end_point[1] * multiplication_factor,
                                                          end_point[2] * multiplication_factor)

                        path_actor.points.InsertNextPoint(start_point[0] * multiplication_factor,
                                                          start_point[1] * multiplication_factor,
                                                          start_point[2] * multiplication_factor)

                        path_actor.colors.InsertNextTypedTuple(self.path_colors.get(line_type).getRgb())

                        line = vtk.vtkLine()
                        line.GetPointIds().SetId(0, point_count)
                        line.GetPointIds().SetId(1, point_count + 1)

                        path_actor.lines.InsertNextCell(line)

                        point_count += 2
                        self.empty_path = False

                    last_point = end_point

                if len(self.path_actors) > 1 and point_count > 0:
                    # Store the last point of the part as first point of the rapid line
                    position = [last_point[0] * multiplication_factor,
                                last_point[1] * multiplication_factor,
                                last_point[2] * multiplication_factor]

                    self.path_end_point[wcs_index] = position

                # free up memory, lots of it for big files

                self.path_points[wcs_index].clear()
                QApplication.processEvents()

                path_actor.poly_data.SetPoints(path_actor.points)
                path_actor.poly_data.SetLines(path_actor.lines)
                path_actor.poly_data.GetCellData().SetScalars(path_actor.colors)
                path_actor.data_mapper.SetInputData(path_actor.poly_data)
                path_actor.data_mapper.Update()
                path_actor.SetMapper(path_actor.data_mapper)
                
                path_actor.is_empyt =  self.empty_path

            paths_count += 1

            prev_wcs_index = wcs_index
            
    def get_path_actors(self):
        return self.path_actors

    def get_offsets_start_point(self):
        return self.path_start_point

    def get_offsets_end_point(self):
        return self.path_end_point

    def get_foam(self):
        return self.foam_z, self.foam_w
    
