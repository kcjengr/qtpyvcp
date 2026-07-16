from qtpyvcp.app.enums import Axis, ReferenceType, Units, Permission


class TestAxis:
    def test_all_is_negative_one(self):
        assert Axis.ALL == -1

    def test_x_value(self):
        assert Axis.X == 0

    def test_y_value(self):
        assert Axis.Y == 1

    def test_z_value(self):
        assert Axis.Z == 2

    def test_a_value(self):
        assert Axis.A == 3

    def test_b_value(self):
        assert Axis.B == 4

    def test_c_value(self):
        assert Axis.C == 5

    def test_u_value(self):
        assert Axis.U == 6

    def test_v_value(self):
        assert Axis.V == 7

    def test_w_value(self):
        assert Axis.W == 8

    def test_all_x_values_are_unique(self):
        values = [Axis.X, Axis.Y, Axis.Z, Axis.A, Axis.B, Axis.C, Axis.U, Axis.V, Axis.W]
        assert len(values) == len(set(values))

    def test_axis_range_starts_at_zero(self):
        assert Axis.X == 0


class TestReferenceType:
    def test_absolute_is_zero(self):
        assert ReferenceType.Absolute == 0

    def test_relative_is_one(self):
        assert ReferenceType.Relative == 1

    def test_distance_to_go_is_two(self):
        assert ReferenceType.DistanceToGo == 2

    def test_all_values_are_unique(self):
        values = [ReferenceType.Absolute, ReferenceType.Relative, ReferenceType.DistanceToGo]
        assert len(values) == len(set(values))


class TestUnits:
    def test_program_is_zero(self):
        assert Units.Program == 0

    def test_inch_is_one(self):
        assert Units.Inch == 1

    def test_metric_is_two(self):
        assert Units.Metric == 2

    def test_all_values_are_unique(self):
        values = [Units.Program, Units.Inch, Units.Metric]
        assert len(values) == len(set(values))


class TestPermission:
    def test_always_is_zero(self):
        assert Permission.Always == 0

    def test_when_running_is_one(self):
        assert Permission.WhenRunning == 1

    def test_when_moving_is_two(self):
        assert Permission.WhenMoving == 2

    def test_when_homing_is_three(self):
        assert Permission.WhenHoming == 3

    def test_when_idle_is_four(self):
        assert Permission.WhenIdle == 4

    def test_all_values_are_unique(self):
        values = [Permission.Always, Permission.WhenRunning, Permission.WhenMoving,
                  Permission.WhenHoming, Permission.WhenIdle]
        assert len(values) == len(set(values))


class TestEnumClassTypes:
    def test_axis_is_object(self):
        assert isinstance(Axis(), object)

    def test_reference_type_is_object(self):
        assert isinstance(ReferenceType(), object)

    def test_units_is_object(self):
        assert isinstance(Units(), object)

    def test_permission_is_object(self):
        assert isinstance(Permission(), object)
