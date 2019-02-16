=============
Status Labels
=============

----------
**Tuples**
----------

If a status item returns a tuple you can get a single value from the tuple by
slicing. For example if the tuple is channel 0 you can convert it to a string
and get the first entry like this ``str(ch[0][0])``. To get the third item in the
tuple you slice at 2 because counting starts at 0 not 1 so ``str(ch[0][2])``
returns the third item in the tuple. For axis items they are in this order
X, Y, Z, A, B, C, U, V, W.

--------------------
**Status Data List**
--------------------

acceleration
    default acceleration, reflects the ini entry [TRAJ]DEFAULT_ACCELERATION

    | syntax ``status:acceleration`` returns float
    | syntax ``status:acceleration?string`` returns str

active_queue
    number of motions blending

    | syntax ``status:active_queue`` returns int
    | syntax ``status:active_queue?string`` returns str

actual_position
    current trajectory position, (x y z a b c u v w) in machine units

    | syntax ``status:actual_position`` returns tuple of floats
    | syntax ``status:actual_position?string`` returns tuple of str


adaptive_feed_enabled
    status of adaptive feedrate override

    | syntax ``status:adaptive_feed_enabled`` returns bool
    | syntax ``status:adaptive_feed_enabled?string`` returns str

ain
    current value of the analog input pins

    | syntax ``status:ain`` returns tuple of floats
    | syntax ``status:ain?string`` returns str


all_axes_homed
    current status of all axes homed, if any axis is not homed it is false

    | syntax ``status:all_axes_homed`` returns bool
    | syntax ``status:all_axes_homed?string`` returns str

angular_units
    machine angular units per deg, reflects [TRAJ]ANGULAR_UNITS ini value

    | syntax ``status:angular_units`` returns float
    | syntax ``status:angular_units?string`` returns str

aout
    current value of the analog output pins

    | syntax ``status:aout`` returns tuple of floats
    | syntax ``status:aout?string`` returns str

axes
    number of axes. Derived from [TRAJ]COORDINATES ini value

    | syntax ``status:axes`` returns int
    | syntax ``status:axes?string`` returns str

axis_mask
    mask of axis available as defined by [TRAJ]COORDINATES in the ini file.

    | the sum of the axes X=1, Y=2, Z=4, A=8, B=16, C=32, U=64, V=128, W=256
    | syntax ``status:axis_mask`` returns int
    | syntax ``status:axis_mask?string`` returns str

block_delete
    block delete curren status

    | syntax ``status:block_delete`` returns bool
    | syntax ``status:block_delete?string`` returns str

call_level
    current nesting level of O-word procedures

    | syntax ``status:call_level`` returns int
    | syntax ``status:call_level?string`` returns str

current_line
    currently executing line

    | syntax ``status:current_line`` returns int
    | syntax ``status:current_line?string`` returns str

current_vel
    current velocity in user units per second

    | syntax ``status:current_vel`` returns float
    | syntax ``status:current_vel?string`` returns str

cycle_time
    thread period

    | syntax ``status:cycle_time`` returns float
    | syntax ``status:cycle_time?string`` returns str

delay_left
    remaining time on the G4 dwell command, seconds

    | syntax ``status:delay_left`` returns float
    | syntax ``status:delay_left?string`` returns str

din
    current value of the digital input pins

    | syntax ``status:din`` returns tuple of integers
    | syntax ``status:din?string`` returns str

distance_to_go
    remaining distance of current move, as reported by trajectory planner

    | syntax ``status:distance_to_go`` returns float
    | syntax ``status:distance_to_go?string`` returns str

dout
    current value of the digital output pins

    | syntax ``status:dout`` returns tuple of integers
    | syntax ``status:dout?string`` returns str

status:dtg tuple

status:echo_serial_number int

status:enabled bool

status:estop int

status:exec_state int

status:feed_hold_enabled bool

status:feed_override_enabled bool

status:feedrate float

status:file str

status:flood int

status:g5x_index int

status:g5x_offset tuple

status:g92_offset tuple

status:gcodes tuple

status:homed tuple

status:id int

status:inpos bool

status:input_timeout bool

status:interp_state int

status:interpreter_errcode int

status:joint.0.backlash float

status:joint.0.enabled int

status:joint.0.fault int

status:joint.0.ferror_current float

status:joint.0.ferror_highmark float

status:joint.0.homed int

status:joint.0.homing int

status:joint.0.inpos int

status:joint.0.input float

status:joint.0.jointType int

status:joint.0.max_ferror float

status:joint.0.max_hard_limit int

status:joint.0.max_position_limit float

status:joint.0.max_soft_limit int

status:joint.0.min_ferror float

status:joint.0.min_hard_limit int

status:joint.0.min_position_limit float

status:joint.0.min_soft_limit int

status:joint.0.output float

status:joint.0.units float

status:joint.0.velocity float

status:joint_actual_position tuple

status:joint_position tuple

status:joints
    number of joints. Reflects [KINS]JOINTS ini value

    | syntax ``status:joints`` returns int
    | syntax ``status:joints?string`` returns str

status:kinematics_type int

status:limit tuple

status:linear_units float

status:lube int

status:lube_level int

status:max_acceleration float

status:max_velocity float

status:mcodes tuple

status:mist int

status:motion_line int

status:motion_mode int

status:motion_type int

status:on bool

status:optional_stop bool

status:paused bool

status:pocket_prepped int

status:position tuple

status:probe_tripped bool

status:probe_val int

status:probed_position tuple

status:probing bool

status:program_units int

status:queue int

status:queue_full bool

status:queued_mdi_commands int

status:rapidrate float

status:read_line int

status:recent_files list

status:rotation_xy float

status:settings tuple

status:spindle.0.brake long

status:spindle.0.direction long

status:spindle.0.enabled long

status:spindle.0.homed long

status:spindle.0.orient_fault long

status:spindle.0.orient_state long

status:spindle.0.override float

status:spindle.0.override_enabled bool

status:spindle.0.speed float

status:spindles int

status:state int

status:task_mode int

status:task_paused int

status:tool_in_spindle int

status:tool_offset tuple

status:tool_table tuple

status:velocity float

