import sys
from collections import OrderedDict

import vtk
import vtk.qt
from linuxcnc_datasource import LinuxCncDataSource
from path_actor import PathActor
from qtpyvcp.utilities import logger
from qtpyvcp.widgets.display_widgets.vtk_backplot.base_canon import StatCanon

LOG = logger.getLogger(__name__)

COLOR_MAP = {
    'traverse': (188, 252, 201, 255),
    'arcfeed': (255, 0, 0, 128),
    'feed': (255, 255, 255, 128),
    'dwell': (100, 100, 100, 255),
    'user': (100, 100, 100, 255),
}

class VTKCanon(StatCanon):
    def __init__(self, colors=COLOR_MAP, *args, **kwargs):
        super(VTKCanon, self).__init__(*args, **kwargs)
        self._datasource = LinuxCncDataSource()

        self.path_colors = colors
        self.path_actors = OrderedDict()
        self.path_points = OrderedDict()
        self.tool_path_color = None
        self.prev_tool_path_color = None

        LOG.debug("---------VTKCanon init")
        #TODO: figure the correct way to do this
        active_wcs_index = self._datasource.getActiveWcsIndex()

        self.path_actors[active_wcs_index] = PathActor(self._datasource)
        self.path_points[active_wcs_index] = list()

        self.active_wcs_index = active_wcs_index
        self.previous_wcs_index = active_wcs_index

        self.ignore_next = False  # hacky way to ignore the second point next to a offset change

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

    def message(self, msg):
        LOG.debug("G-code Message: {}".format(msg))

    def rotate_and_translate(self, x, y, z, a, b, c, u, v, w):
        # override function to handle it in vtk back plot
        return x, y, z, a, b, c, u, v, w

    def set_g5x_offset(self, index, x, y, z, a, b, c, u, v, w):
        LOG.debug("---------received offset change {}".format(index))
        new_wcs = index - 1 #this index counts also G53 so we need to do -1
        if new_wcs not in self.path_actors.keys():
            self.path_actors[new_wcs] = PathActor(self._datasource)
            self.path_points[new_wcs] = list()

            self.previous_wcs_index = self.active_wcs_index
            self.active_wcs_index = new_wcs

    def add_path_point(self, line_type, start_point, end_point):
        if self.ignore_next is True:
            self.ignore_next = False
            return

        if self.previous_wcs_index != self.active_wcs_index:
            self.previous_wcs_index = self.active_wcs_index
            self.ignore_next = True
            return

        line = list()
        line.append(start_point[:3]) # add only the xyz components
        line.append(end_point[:3]) # add only the xyz components

        self.path_points.get(self.active_wcs_index).append((line_type, line))

    def draw_lines(self):
        LOG.debug("---------path points size: {}".format(sys.getsizeof(self.path_points)))
        LOG.debug("---------path points length: {}".format(len(self.path_points)))

        # TODO: for some reason, we need to multiply for metric, find out why!
        multiplication_factor = 25.4 if self._datasource.isMachineMetric() else 1

        for wcs_index, data in self.path_points.items():
            index = 0

            path_actor = self.path_actors.get(wcs_index)
            if path_actor is not None:
                for line_type, line_data in data:
                    start_point = line_data[0]
                    end_point = line_data[1]

                    path_actor.points.InsertNextPoint(start_point[0] * multiplication_factor,
                                                      start_point[1] * multiplication_factor,
                                                      start_point[2] * multiplication_factor)

                    path_actor.points.InsertNextPoint(end_point[0] * multiplication_factor,
                                                      end_point[1] * multiplication_factor,
                                                      end_point[2] * multiplication_factor)

                    path_actor.colors.InsertNextTypedTuple(COLOR_MAP.get(line_type))

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

    def get_path_actors(self):
        return self.path_actors
