from enum import IntEnum


class TestAxis:
    """Tests for DROBaseWidget Axis enum."""

    def test_axis_is_intenum(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert issubclass(Axis, IntEnum)

    def test_axis_all_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert Axis.ALL == -1

    def test_axis_x_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert Axis.X == 0

    def test_axis_y_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert Axis.Y == 1

    def test_axis_z_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert Axis.Z == 2

    def test_axis_a_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert Axis.A == 3

    def test_axis_b_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert Axis.B == 4

    def test_axis_c_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert Axis.C == 5

    def test_axis_u_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert Axis.U == 6

    def test_axis_v_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert Axis.V == 7

    def test_axis_w_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert Axis.W == 8

    def test_axis_iteration(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        all_values = list(Axis)
        assert len(all_values) == 10
        assert Axis.ALL in all_values
        assert Axis.X in all_values
        assert Axis.W in all_values

    def test_axis_from_int(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert Axis(0) is Axis.X
        assert Axis(4) is Axis.B
        assert Axis(8) is Axis.W

    def test_axis_all_negative(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert Axis(-1) is Axis.ALL

    def test_axis_name_access(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Axis
        assert Axis.X.name == 'X'
        assert Axis.Z.name == 'Z'
        assert Axis.A.name == 'A'


class TestUnits:
    """Tests for DROBaseWidget Units enum."""

    def test_units_is_intenum(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Units
        assert issubclass(Units, IntEnum)

    def test_units_program_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Units
        assert Units.Program == 0

    def test_units_inch_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Units
        assert Units.Inch == 1

    def test_units_metric_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Units
        assert Units.Metric == 2

    def test_units_from_int(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import Units
        assert Units(0) is Units.Program
        assert Units(1) is Units.Inch
        assert Units(2) is Units.Metric


class TestRefType:
    """Tests for DROBaseWidget RefType enum."""

    def test_ref_type_is_intenum(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import RefType
        assert issubclass(RefType, IntEnum)

    def test_ref_type_absolute_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import RefType
        assert RefType.Absolute == 0

    def test_ref_type_relative_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import RefType
        assert RefType.Relative == 1

    def test_ref_type_distance_to_go_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import RefType
        assert RefType.DistanceToGo == 2

    def test_ref_type_from_int(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import RefType
        assert RefType(0) is RefType.Absolute
        assert RefType(1) is RefType.Relative
        assert RefType(2) is RefType.DistanceToGo


class TestLatheMode:
    """Tests for DROBaseWidget LatheMode enum."""

    def test_lathe_mode_is_intenum(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import LatheMode
        assert issubclass(LatheMode, IntEnum)

    def test_lathe_mode_auto_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import LatheMode
        assert LatheMode.Auto == 0

    def test_lathe_mode_radius_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import LatheMode
        assert LatheMode.Radius == 1

    def test_lathe_mode_diameter_value(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import LatheMode
        assert LatheMode.Diameter == 2

    def test_lathe_mode_from_int(self):
        from qtpyvcp.widgets.base_widgets.dro_base_widget import LatheMode
        assert LatheMode(0) is LatheMode.Auto
        assert LatheMode(1) is LatheMode.Radius
        assert LatheMode(2) is LatheMode.Diameter
