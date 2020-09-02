import os
import linuxcnc
from pyqtgraph import Qt

from qtpy import uic
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget, QMessageBox

from qtpyvcp.actions.program_actions import load as loadProgram
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities import logger
from qtpyvcp.widgets.conversational.ops.gcode_file import GCodeFile

LOG = logger.getLogger(__name__)

STATUS = getPlugin('status')
TOOL_TABLE = getPlugin('tooltable')

INI_FILE = linuxcnc.ini(os.getenv('INI_FILE_NAME'))
PROGRAM_PREFIX = os.path.expandvars(os.path.expanduser(INI_FILE.find('DISPLAY', 'PROGRAM_PREFIX') or '/tmp'))
DEFAULT_SPINDLE_SPEED = float(INI_FILE.find('DISPLAY', 'DEFAULT_SPINDLE_SPEED') or 0.000)
DEFAULT_LINEAR_VELOCITY = float(INI_FILE.find('DISPLAY', 'DEFAULT_LINEAR_VELOCITY') or 0.000)


class ConversationalBaseWidget(QWidget):
    def __init__(self, parent=None, ui_file=''):
        super(ConversationalBaseWidget, self).__init__(parent)
        uic.loadUi(os.path.join(os.path.dirname(__file__), ui_file), self)

        self._tool_is_valid = False

        self.wcs_input.addItem('G54')
        self.wcs_input.addItem('G55')
        self.wcs_input.addItem('G56')
        self.wcs_input.addItem('G57')
        self.wcs_input.addItem('G58')
        self.wcs_input.addItem('G59')
        self.wcs_input.addItem('G59.1')
        self.wcs_input.addItem('G59.2')
        self.wcs_input.addItem('G59.3')

        self.drill_type_input.addItem('DRILL')
        self.drill_type_input.addItem('PECK')
        self.drill_type_input.addItem('BREAK')
        self.drill_type_input.addItem('DWELL')
        self.drill_type_input.addItem('TAP')
        self.drill_type_input.addItem('RIGID TAP')

        self.unit_input.addItem('IN')
        self.unit_input.addItem('MM')
        self.update_selected_unit()

        self.coolant_input.addItem('OFF')
        self.coolant_input.addItem('MIST')
        self.coolant_input.addItem('FLOOD')

        self.spindle_direction_input.addItem('CW')
        self.spindle_direction_input.addItem('CCW')

        self.xy_feed_rate_input.setText('{0:.3f}'.format(DEFAULT_LINEAR_VELOCITY))
        self.spindle_rpm_input.setText('{0:.3f}'.format(DEFAULT_SPINDLE_SPEED))

        self.drill_type_param_value.setVisible(False)
        self.drill_type_param_label.setVisible(False)

        self.post_to_file.clicked.connect(self.on_post_to_file)
        self.drill_type_input.currentIndexChanged.connect(self.set_drill_type_params)

        self.tool_number_input.editingFinished.connect(self.set_tool_description_from_tool_num)
        self.tool_number_input.editingFinished.connect(self._validate_tool_number)
        self.z_start_input.editingFinished.connect(self._validate_z_heights)
        self.z_end_input.editingFinished.connect(self._validate_z_heights)
        self.spindle_rpm_input.editingFinished.connect(self._validate_spindle_rpm)
        self.xy_feed_rate_input.editingFinished.connect(self._validate_xy_feed_rate)
        self.z_feed_rate_input.editingFinished.connect(self._validate_z_feed_rate)

        STATUS.g5x_index.onValueChanged(self.update_wcs)
        STATUS.program_units.onValueChanged(self.update_selected_unit)
        STATUS.tool_in_spindle.onValueChanged(self.update_tool_number)

    def update_wcs(self):
        self.wcs_input.setCurrentIndex(STATUS.g5x_index() - 1)

    def update_selected_unit(self):
        self.unit_input.setCurrentIndex(STATUS.program_units() - 1)

    def update_tool_number(self):
        self.tool_number_input.setText('{}'.format(STATUS.tool_in_spindle))
        self.set_tool_description_from_tool_num()

    def set_drill_type_params(self, _):
        self.z_feed_rate_input.setEnabled(True)
        if self.drill_type() == 'DWELL':
            self.drill_type_param_label.setText('DWELL TIME (SEC.)')
            self.drill_type_param_value.setText('0.00')
            self.drill_type_param_value.setVisible(True)
            self.drill_type_param_label.setVisible(True)
        elif self.drill_type() == 'PECK':
            self.drill_type_param_label.setText('PECK DEPTH')
            self.drill_type_param_value.setText('0.0000')
            self.drill_type_param_value.setVisible(True)
            self.drill_type_param_label.setVisible(True)
        elif self.drill_type() == 'BREAK':
            self.drill_type_param_label.setText('BREAK DEPTH')
            self.drill_type_param_value.setText('0.0000')
            self.drill_type_param_value.setVisible(True)
            self.drill_type_param_label.setVisible(True)
        elif self.drill_type() in ['TAP', 'RIGID TAP']:
            self.z_feed_rate_input.setEnabled(False)
            self.drill_type_param_label.setText('PITCH')
            self.drill_type_param_value.setText('0.00')
            self.drill_type_param_value.setVisible(True)
            self.drill_type_param_label.setVisible(True)
        else:
            self.drill_type_param_value.setVisible(False)
            self.drill_type_param_label.setVisible(False)

    def set_tool_description_from_tool_num(self):
        tool_table = TOOL_TABLE.getToolTable()
        tool_number = self.tool_number()
        try:
            desc = tool_table[tool_number]['R']
            self.tool_description.setText((desc[:30] + '...') if len(desc) > 30 else desc)
            self.tool_description.setToolTip(desc)
            self._tool_is_valid = (tool_number > 0)
        except KeyError:
            self._tool_is_valid = False
            self.tool_description.setText('TOOL NOT IN TOOL TABLE')
            self.tool_description.setToolTip('TOOL NOT IN TOOL TABLE')

    def name(self):
        return self.name_input.text()

    def wcs(self):
        return self.wcs_input.currentText()

    def unit(self):
        return self.unit_input.currentText()

    def drill_type(self):
        return self.drill_type_input.currentText()

    def drill_peck_depth(self):
        return self.drill_type_param_value.value()

    def drill_break_depth(self):
        return self.drill_type_param_value.value()

    def drill_dwell_time(self):
        return self.drill_type_param_value.value()

    def tap_pitch(self):
        return self.drill_type_param_value.value()

    def tool_number(self):
        return self.tool_number_input.value()

    def spindle_rpm(self):
        return self.spindle_rpm_input.value()

    def spindle_direction(self):
        return self.spindle_direction_input.currentText()

    def coolant(self):
        return self.coolant_input.currentText()

    def xy_feed_rate(self):
        return self.xy_feed_rate_input.value()

    def z_feed_rate(self):
        return self.z_feed_rate_input.value()

    def clearance_height(self):
        return self.clearance_height_input.value()

    def retract_height(self):
        return self.retract_height_input.value()

    def z_start(self):
        return self.z_start_input.value()

    def z_end(self):
        return self.z_end_input.value()

    def on_post_to_file(self):
        ok, errors = self.is_valid()
        if ok:
            f = GCodeFile()
            f.ops.append(self.create_op())

            program_path = self._get_next_available_file_name()

            f.write_to_file(program_path)

            msg = QMessageBox(QMessageBox.Question,
                              'GCode Generated', 'The file has been created.\n'
                                                 'Would you like to load it into the viewer?',
                              QMessageBox.Yes | QMessageBox.No, self, Qt.FramelessWindowHint)

            if msg.exec_() == QMessageBox.Yes:
                loadProgram(program_path)

        else:
            msg = QMessageBox(QMessageBox.Critical,
                              'GCode Error', '\n'.join(errors),
                              QMessageBox.Ok, self, Qt.FramelessWindowHint)
            msg.exec_()

    def is_valid(self):
        errors = []
        funcs = [self._validate_z_heights,
                 self._validate_spindle_rpm,
                 self._validate_xy_feed_rate,
                 self._validate_z_feed_rate,
                 self._validate_tool_number,]

        for f in funcs:
            ok, error = f()
            if not ok:
                errors.append(error)

        return len(errors) == 0, errors

    def _get_next_available_file_name(self):
        if self.name() == '':
            self.name_input.setText('Untitled')

        program_base = os.path.join(PROGRAM_PREFIX, self.name())
        program_path = program_base + '.ngc'

        i = 1
        while os.path.exists(program_path):
            program_path = '%s_%i.ngc' % (program_base, i)
            i += 1

        return program_path

    def _validate_z_heights(self):
        if not self.z_start() > self.z_end():
            self.z_start_input.setStyleSheet("background-color: rgb(205, 141, 123)")
            self.z_end_input.setStyleSheet("background-color: rgb(205, 141, 123)")
            error = 'Start position must be greater than end position.'
            self.z_end_input.setToolTip(error)
            return False, error
        else:
            self.z_start_input.setStyleSheet('')
            self.z_end_input.setStyleSheet('')
            return True, None

    def _validate_spindle_rpm(self):
        if self.spindle_rpm() > 0:
            self.spindle_rpm_input.setStyleSheet('')
            return True, None
        else:
            self.spindle_rpm_input.setStyleSheet('background-color: rgb(205, 141, 123)')
            error = 'Spindle RPM must be greater than 0.'
            self.spindle_rpm_input.setToolTip(error)
            return False, error

    def _validate_xy_feed_rate(self):
        if self.xy_feed_rate() > 0:
            self.xy_feed_rate_input.setStyleSheet('')
            return True, None
        else:
            self.xy_feed_rate_input.setStyleSheet('background-color: rgb(205, 141, 123)')
            error = 'XY feed rate must be greater than 0.'
            self.xy_feed_rate_input.setToolTip(error)
            return False, error

    def _validate_z_feed_rate(self):
        if self.z_feed_rate() > 0:
            self.z_feed_rate_input.setStyleSheet('')
            return True, None
        else:
            self.z_feed_rate_input.setStyleSheet('background-color: rgb(205, 141, 123)')
            error = 'Z feed rate must be greater than 0.'
            self.z_feed_rate_input.setToolTip(error)
            return False, error

    def _validate_tool_number(self):
        if self._tool_is_valid:
            self.tool_number_input.setStyleSheet('')
            return True, None
        else:
            self.tool_number_input.setStyleSheet('background-color: rgb(205, 141, 123)')
            error = 'Tool is not valid.'
            self.tool_number_input.setToolTip(error)
            return False, error

