import sys
from collections import OrderedDict
import math
import vtk
import vtk.qt
from .linuxcnc_datasource import LinuxCncDataSource
from .path_actor import PathActor
from qtpyvcp.utilities import logger
from qtpyvcp.widgets.display_widgets.vtk_backplot.base_canon import StatCanon

LOG = logger.getLogger(__name__)

COLOR_MAP = {
    'traverse': (200, 35, 35, 255),
    'arcfeed': (110, 110, 255, 255),
    'feed': (210, 210, 255, 255),
    'dwell': (0, 0, 255, 255),
    'user': (0, 100, 255, 255),
}

class VTKCanon(StatCanon):
    def __init__(self, colors=COLOR_MAP, *args, **kwargs):
        super(VTKCanon, self).__init__(*args, **kwargs)
        
        self.feedrate = 1
        self.dwell_time = 0

        self.seq_num = -1
        self.last_pos = (0,) * 9

        self.first_move = True
        self.in_arc = False
        self.suppress = 0

        self.plane = 1
        self.arcdivision = 64

        # extents
        self.min_extents = [9e99, 9e99, 9e99]
        self.max_extents = [-9e99, -9e99, -9e99]
        self.min_extents_notool = [9e99, 9e99, 9e99]
        self.max_extents_notool = [-9e99, -9e99, -9e99]

        # tool length offsets
        self.tlo_x = 0.0
        self.tlo_y = 0.0
        self.tlo_z = 0.0
        self.tlo_a = 0.0
        self.tlo_b = 0.0
        self.tlo_c = 0.0
        self.tlo_u = 0.0
        self.tlo_v = 0.0
        self.tlo_w = 0.0

        self.tool_offsets = (0.0,) * 9

        # G92/G52 offsets
        self.g92_offset_x = 0.0
        self.g92_offset_y = 0.0
        self.g92_offset_z = 0.0
        self.g92_offset_a = 0.0
        self.g92_offset_b = 0.0
        self.g92_offset_c = 0.0
        self.g92_offset_u = 0.0
        self.g92_offset_v = 0.0
        self.g92_offset_w = 0.0

        # g5x offsets
        self.g5x_offset_x = 0.0
        self.g5x_offset_y = 0.0
        self.g5x_offset_z = 0.0
        self.g5x_offset_a = 0.0
        self.g5x_offset_b = 0.0
        self.g5x_offset_c = 0.0
        self.g5x_offset_u = 0.0
        self.g5x_offset_v = 0.0
        self.g5x_offset_w = 0.0

        # XY rotation (degrees)
        self.rotation_xy = 0
        self.rotation_cos = 1
        self.rotation_sin = 0
        
        self._datasource = LinuxCncDataSource()

        self.path_colors = colors
        self.path_actors = OrderedDict()
        self.path_points = OrderedDict()

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
        if new_wcs not in list(self.path_actors.keys()):
            self.path_actors[new_wcs] = PathActor(self._datasource)
            self.path_points[new_wcs] = list()

        self.active_wcs_index = new_wcs

    # def set_xy_rotation(self, rotation):
    #     self.rotation_xy = rotation
    #     theta = math.radians(rotation)
    #     self.rotation_cos = math.cos(theta)
    #     self.rotation_sin = math.sin(theta)


    def add_path_point(self, line_type, start_point, end_point):
        line = [start_point, end_point]
        self.path_points.get(self.active_wcs_index).append((line_type, line))

    def draw_lines(self):
        # Used to draw the lines of the loaded program
        LOG.debug("---------path points size: {}".format(sys.getsizeof(self.path_points)))
        LOG.debug("---------path points length: {}".format(len(self.path_points)))

        # TODO: for some reason, we need to multiply for metric, find out why!
        multiplication_factor = 25.4 if self._datasource.isMachineMetric() else 1

        for wcs_index, data in list(self.path_points.items()):
            index = 0

            path_actor = self.path_actors.get(wcs_index)
            if path_actor is not None:
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
                        line.GetPointIds().SetId(0, index)
                        line.GetPointIds().SetId(1, index + 1)

                        path_actor.lines.InsertNextCell(line)


                        index += 2


                        path_actor.points.InsertNextPoint(start_point[6] * multiplication_factor,
                                                          start_point[7] * multiplication_factor,
                                                          (start_point[8]+(self.foam_w/25.4)) * multiplication_factor)

                        path_actor.points.InsertNextPoint(end_point[6] * multiplication_factor,
                                                          end_point[7] * multiplication_factor,
                                                          (start_point[8]+(self.foam_w/25.4)) * multiplication_factor)

                        path_actor.colors.InsertNextTypedTuple(self.path_colors.get(line_type).getRgb()[:4])

                        line2 = vtk.vtkLine()
                        line2.GetPointIds().SetId(0, index)
                        line2.GetPointIds().SetId(1, index + 1)

                        path_actor.lines.InsertNextCell(line2)

                        index += 2

                    else:

                        path_actor.points.InsertNextPoint(start_point[0] * multiplication_factor,
                                                          start_point[1] * multiplication_factor,
                                                          start_point[2] * multiplication_factor)

                        path_actor.points.InsertNextPoint(end_point[0] * multiplication_factor,
                                                          end_point[1] * multiplication_factor,
                                                          end_point[2] * multiplication_factor)


                        path_actor.colors.InsertNextTypedTuple(self.path_colors.get(line_type).getRgb()[:4])

                        line = vtk.vtkLine()
                        line.GetPointIds().SetId(0, index)
                        line.GetPointIds().SetId(1, index + 1)

                        path_actor.lines.InsertNextCell(line)


                        index += 2

                # free up memory, lots of it for big files
                self.path_points[wcs_index] = list()

                path_actor.poly_data.SetPoints(path_actor.points)
                path_actor.poly_data.SetLines(path_actor.lines)
                path_actor.poly_data.GetCellData().SetScalars(path_actor.colors)
                path_actor.data_mapper.SetInputData(path_actor.poly_data)
                path_actor.data_mapper.Update()
                path_actor.SetMapper(path_actor.data_mapper)

    def translate(self, x, y, z, a, b, c, u, v, w):
        
        x += self.g92_offset_x
        y += self.g92_offset_y
        z += self.g92_offset_z
        a += self.g92_offset_a
        b += self.g92_offset_b
        c += self.g92_offset_c
        u += self.g92_offset_u
        v += self.g92_offset_v
        w += self.g92_offset_w
        
        x += self.g5x_offset_x
        y += self.g5x_offset_y
        z += self.g5x_offset_z
        a += self.g5x_offset_a
        b += self.g5x_offset_b
        c += self.g5x_offset_c
        u += self.g5x_offset_u
        v += self.g5x_offset_v
        w += self.g5x_offset_w

        return [x, y, z, a, b, c, u, v, w]      
    
    def straight_feed(self, x, y, z, a, b, c, u, v, w):
        if self.suppress > 0:
            return

        self.first_move = False
        
        pos = self.rotate_and_translate(x, y, z, a, b, c, u, v, w)

        self.add_path_point('feed', self.last_pos, pos)
        self.last_pos = pos
        
    straight_probe = straight_feed
    
    def straight_traverse(self, x, y, z, a, b, c, u, v, w):
        if self.suppress > 0:
            return

        pos = self.rotate_and_translate(x, y, z, a, b, c, u, v, w)
        
        if not self.first_move:
            self.add_path_point('traverse', self.last_pos, pos)

        self.last_pos = pos

    def rigid_tap(self, x, y, z):
        if self.suppress > 0:
            return

        self.first_move = False
        pos = self.translate(x, y, z, 0, 0, 0, 0, 0, 0)[:3]
        pos += self.last_pos[3:]

        self.add_path_point('feed', self.last_pos, pos)
        
    
    def get_path_actors(self):
        return self.path_actors

    def get_foam(self):
        return self.foam_z, self.foam_w
