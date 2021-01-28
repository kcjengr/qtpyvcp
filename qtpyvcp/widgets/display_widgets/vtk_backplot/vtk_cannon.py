from collections import OrderedDict
from random import choice

import vtk
import vtk.qt

# Fix poligons not drawing correctly on some GPU
# https://stackoverflow.com/questions/51357630/vtk-rendering-not-working-as-expected-inside-pyqt?rq=1

vtk.qt.QVTKRWIBase = "QGLWidget"

# Fix end

from qtpyvcp.widgets.display_widgets.vtk_backplot.base_canon import StatCanon

from path_actor import PathActor
from linuxcnc_wrapper import LinuxCncWrapper
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

COLOR_MAP = {
    'traverse': (188, 252, 201, 255),
    'arcfeed': (255, 255, 255, 128),
    'feed': (255, 255, 255, 128),
    'dwell': (100, 100, 100, 255),
    'user': (100, 100, 100, 255),
}

TOOL_COLOR_MAP = (
    (255, 0, 0, 255),
    (0, 255, 0, 255),
    (0, 0, 255, 255),
    (255, 255, 0, 255),
    (0, 255, 255, 255),
    (255, 0, 255, 255),
)

class VTKCanon(StatCanon):
    def __init__(self, colors=COLOR_MAP, *args, **kwargs):
        super(VTKCanon, self).__init__(*args, **kwargs)
        self._linuxcnc_wrapper = LinuxCncWrapper()

        self.index_map = dict()

        self.index_map[1] = 540
        self.index_map[2] = 550
        self.index_map[3] = 560
        self.index_map[4] = 570
        self.index_map[5] = 580
        self.index_map[6] = 590
        self.index_map[7] = 591
        self.index_map[8] = 592
        self.index_map[9] = 593

        self.path_colors = colors
        self.path_actors = OrderedDict()
        self.path_points = OrderedDict()
        self.tool_path_color = None
        self.prev_tool_path_color = None

        origin = 540

        self.path_actors[origin] = PathActor()
        self.path_points[origin] = list()

        self.origin = origin
        self.previous_origin = origin

        self.ignore_next = False  # hacky way to ignore the second point next to a offset change

        self.multitool_colors = False #TODO: add a signal to set this true, but default it should be false

        self.last_line_type = None

    def change_tool(self, pocket):
        super(VTKCanon, self).change_tool(pocket)

        if self.multitool_colors is True:
            self.tool_path_color = choice(TOOL_COLOR_MAP)

            while self.tool_path_color == self.prev_tool_path_color:
                self.tool_path_color = choice(TOOL_COLOR_MAP)

            self.prev_tool_path_color = self.tool_path_color
        else:
            self.tool_path_color = None

        LOG.debug("TOOL CHANGE {} color {}".format(pocket, self.tool_path_color))

    def comment(self, comment):
        LOG.debug("G-code Comment: %s", comment)
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
        LOG.debug("G-code Message: %s", msg)

    def rotate_and_translate(self, x, y, z, a, b, c, u, v, w):
        # override function to handle it in vtk back plot
        return x, y, z, a, b, c, u, v, w

    def set_g5x_offset(self, index, x, y, z, a, b, c, u, v, w):

        origin = self.index_map[index]
        if origin not in self.path_actors.keys():
            self.path_actors[origin] = PathActor()
            self.path_points[origin] = list()

            self.previous_origin = self.origin
            self.origin = origin

    def add_path_point(self, line_type, start_point, end_point):

        if self.tool_path_color is not None:
            color = self.tool_path_color
        else:
            color = self.path_colors[line_type]

        if line_type != self.last_line_type:
            self.last_line_type = line_type
            LOG.debug("---------line_type: {}, path_color: {}".format(line_type, color))

        if self.ignore_next is True:
            self.ignore_next = False
            return

        if self.previous_origin != self.origin:
            self.previous_origin = self.origin
            self.ignore_next = True
            return

        path_points = self.path_points.get(self.origin)

        if self._linuxcnc_wrapper.isMetric():
            start_point_list = list()
            for point in start_point: # TODO: here it should be start_point not end_point
                point *= 25.4 # TODO: why is this conversion needed for metric? On the else branch, there is no conversion
                start_point_list.append(point)

            end_point_list = list()
            for point in end_point:
                point *= 25.4
                end_point_list.append(point)

            line = list()
            line.append(start_point_list)
            line.append(end_point_list)

            path_points.append((line_type, line, color))

        else:
            line = list()
            line.append(start_point)
            line.append(end_point)

            path_points.append((line_type, line, color))

    def draw_lines(self):

        for origin, data in self.path_points.items():

            path_actor = self.path_actors.get(origin)

            index = 0

            end_point = None
            last_line_type = None

            for line_type, line_data, color in data:
                # LOG.debug("line_type {}, line_data {}".format(line_type, line_data))

                start_point = line_data[0]
                end_point = line_data[1]
                last_line_type = line_type

                path_actor.points.InsertNextPoint(start_point[:3])

                if line_type == "traverse":
                    path_actor.colors.InsertNextTypedTuple(COLOR_MAP.get("traverse"))
                else:
                    path_actor.colors.InsertNextTypedTuple(color)

                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, index)
                line.GetPointIds().SetId(1, index + 1)

                path_actor.lines.InsertNextCell(line)

                index += 1

            if end_point:
                path_actor.points.InsertNextPoint(end_point[:3])
                path_actor.colors.InsertNextTypedTuple(color)

                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, index - 1)
                line.GetPointIds().SetId(1, index)

                path_actor.lines.InsertNextCell(line)

            # free up memory, lots of it for big files

            self.path_points[self.origin] = list()

            if path_actor is not None:
                path_actor.poly_data.SetPoints(path_actor.points)
                path_actor.poly_data.SetLines(path_actor.lines)
                path_actor.poly_data.GetCellData().SetScalars(path_actor.colors)
                path_actor.data_mapper.SetInputData(path_actor.poly_data)
                path_actor.data_mapper.Update()
                path_actor.SetMapper(path_actor.data_mapper)

    def get_path_actors(self):
        return self.path_actors