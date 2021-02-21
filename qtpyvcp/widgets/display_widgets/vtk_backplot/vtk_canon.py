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
    'traverse': (200, 35, 35, 255),
    'arcfeed': (110, 110, 255, 255),
    'feed': (210, 210, 255, 255),
    'dwell': (0, 0, 255, 255),
    'user': (0, 100, 255, 255),
}

class VTKCanon(StatCanon):
    def __init__(self, colors=COLOR_MAP, *args, **kwargs):
        super(VTKCanon, self).__init__(*args, **kwargs)
        self._datasource = LinuxCncDataSource()

        self.path_colors = colors
        self.path_actors = OrderedDict()
        self.path_points = OrderedDict()

        self.active_wcs_index = self._datasource.getActiveWcsIndex()

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

    def set_g5x_offset(self, index, x, y, z, a, b, c, u, v, w):
        new_wcs = index - 1  # this index counts also G53 so we need to do -1
        LOG.debug("---------received wcs change: {}".format(new_wcs))
        if new_wcs not in self.path_actors.keys():
            self.path_actors[new_wcs] = PathActor(self._datasource)
            self.path_points[new_wcs] = list()

        self.active_wcs_index = new_wcs

    def add_path_point(self, line_type, start_point, end_point):
        line = [start_point[:3], end_point[:3]]
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

    def get_path_actors(self):
        return self.path_actors
