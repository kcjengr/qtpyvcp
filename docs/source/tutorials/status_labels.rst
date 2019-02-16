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

dtg
    remaining distance of current move for each axis, as reported by trajectory planner

    | syntax ``status:dtg`` returns tuple of floats
    | syntax ``status:dtg?string`` returns str

echo_serial_number
    The serial number of the last completed command sent by a UI to task

    | syntax ``status:echo_serial_number`` returns int
    | syntax ``status:echo_serial_number?string`` returns str

enabled
    trajectory planner enabled flag

    | syntax ``status:enabled`` returns bool
    | syntax ``status:enabled?string`` returns str

estop
    status of E Stop, 1 for enabled and 0 for not enabled

    | syntax ``status:estop`` returns int
    | syntax ``status:estop?string`` returns str

exec_state
    task execution state

    === ===========================
    int str
    === ===========================
    1   Error
    2   Done
    3   Waiting for Motion
    4   Waiting for Motion Queue
    5   Waiting for Pause
    6   Not used by LinuxCNC
    7   Waiting for Motion and IO
    8   Waiting for Delay
    9   Waiting for system CMD
    10  Waiting for spindle orient
    === ===========================

    | syntax ``status:exec_state`` returns int
    | syntax ``status:exec_state?string`` returns str

feed_hold_enabled
    status of feed hold

    | syntax ``status:feed_hold_enabled`` returns bool
    | syntax ``status:feed_hold_enabled?string`` returns str

feed_override_enabled
    status of feed override

    | syntax ``status:feed_override_enabled`` returns bool
    | syntax ``status:feed_override_enabled?string`` returns str

feedrate
    current feedrate override, 1.0 = 100%

    | syntax ``status:feedrate`` returns float
    | syntax ``status:feedrate?string`` returns str

file
    currently loaded gcode filename with path

    | syntax ``status:file`` returns str
    | for just the file name use this expression ``ch[0].split('/')[-1]``

flood
    current flood status 0 for off, 1 for on

    | syntax ``status:flood`` returns int
    | syntax ``status:flood?string`` returns str

g5x_index
    currently active coordinate system

    | syntax ``status:g5x_index`` returns int
    | syntax ``status:g5x_index?string`` returns str

    to get the text for the currently active coodinate system use this expression
    ::

    ["G53","G54","G55","G56","G57","G58","G59","G59.1","G59.2","G59.3"][ch[0]]

g5x_offset
    offsets of the currently active coordinate system

    | syntax ``status:g5x_offset`` returns tuple of floats
    | syntax ``status:g5x_offset?string`` returns str

g92_offset
    current g92 offsets

    | syntax ``status:g92_offset`` returns tuple of floats
    | syntax ``status:g92_offset?string`` returns str

gcodes
    active G-codes for each modal group

    | syntax ``status:gcodes`` returns tuple of integers
    | syntax ``status:gcodes?string`` returns str

homed
    currently homed joints, 0 = not homed, 1 = homed

    | syntax ``status:homed`` returns tuple of integers
    | syntax ``status:homed?string`` returns str

id
    currently executing motion id

    | syntax ``status:id`` returns int
    | syntax ``status:id?string`` returns str

inpos
    status machine in position

    | syntax ``status:inpos`` returns bool
    | syntax ``status:inpos?string`` returns str

input_timeout
    flag for M66 timer in progress

    | syntax ``status:input_timeout`` returns bool
    | syntax ``status:input_timeout?string`` returns str

interp_state
    current state of RS274NGC interpreter

    === ======
    int str
    === ======
    1   E-Stop
    2   Reset
    3   Off
    4   On
    === ======

    | syntax ``status:interp_state`` returns int
    | syntax ``status:interp_state?string`` returns str

interpreter_errcode
    current RS274NGC interpreter return code

    === =============
    int str
    === =============
    0   Ok
    1   Exit
    2   Finished
    3   Endfile
    4   File not open
    5   Error
    === =============

    | syntax ``status:interpreter_errcode`` returns int
    | syntax ``status:interpreter_errcode?string`` returns str


joint.n.backlash
    backlash in machine units, reflects [JOINT_n]BACKLASH (`n` is joint number)

    | syntax ``status:joint.n.backlash`` returns float
    | syntax ``status:joint.n.backlash?string`` returns str

joint.n.enabled
    status of joint n enabled, 0 not enabled 1 enabled

    | syntax ``status:joint.n.enabled`` returns int
    | syntax ``status:joint.n.enabled?string`` returns str

joint.n.fault
    status of joint n fault, 0 not faulted 1 faulted

    | syntax ``status:joint.n.fault`` returns int
    | syntax ``status:joint.n.fault?string`` returns str

joint.n.ferror_current
    current joint n following error

    | syntax ``status:joint.n.ferror_current`` returns float
    | syntax ``status:joint.n.ferror_current?string`` returns str

joint.n.ferror_highmark
    joint n magnitude of max following error

    | syntax ``status:joint.n.ferror_highmark`` returns float
    | syntax ``status:joint.n.ferror_highmark?string`` returns str

joint.n.homed
    status of joint n homed, 0 not homed 1 homed

    | syntax ``status:joint.n.homed`` returns int
    | syntax ``status:joint.n.homed?string`` returns str

joint.n.homing
    status of joint n homing in progress, 0 not homing 1 homing

    | syntax ``status:joint.n.homing`` returns int
    | syntax ``status:joint.n.homing?string`` returns str

joint.n.inpos
    status of joint n in position, 0 not in position 1 in position

    | syntax ``status:joint.n.inpos`` returns int
    | syntax ``status:joint.n.inpos?string`` returns str

joint.n.input
    joint n current input position

    | syntax ``status:joint.n.input`` returns float
    | syntax ``status:joint.n.input?string`` returns str

joint.n.jointType
    joint n type of axis, reflects [JOINT_n]TYPE

    | syntax ``status:joint.n.jointType`` returns int
    | syntax ``status:joint.n.jointType?string`` returns str


joint.n.max_ferror
    joint n maximum following error, reflects [JOINT_n]FERROR

    | syntax ``status:joint.n.max_ferror`` returns float
    | syntax ``status:joint.n.max_ferror?string`` returns str

joint.n.max_hard_limit
    status of joint n max hard limit, 0 not exceeded 1 exceeded

    | syntax ``status:joint.n.max_hard_limit`` returns int
    | syntax ``status:joint.n.max_hard_limit?string`` returns str

status:joint.n.max_position_limit
    joint n maximum soft limit, parameter [JOINT_n]MAX_LIMIT

status:joint.n.max_soft_limit
    

status:joint.n.min_ferror
    

status:joint.n.min_hard_limit
    

status:joint.n.min_position_limit
    

status:joint.n.min_soft_limit
    

status:joint.n.output
    

status:joint.n.units
    

status:joint.n.velocity
    

status:joint_actual_position
    

status:joint_position
    

status:joints
    number of joints. Reflects [KINS]JOINTS ini value

    | syntax ``status:joints`` returns int
    | syntax ``status:joints?string`` returns str

status:kinematics_type
    

status:limit
    

status:linear_units
    

status:lube
    

status:lube_level
    

status:max_acceleration
    

status:max_velocity
    

status:mcodes
    

status:mist
    

status:motion_line
    

status:motion_mode
    

status:motion_type
    

status:on
    

status:optional_stop
    

status:paused
    

status:pocket_prepped
    

status:position
    

status:probe_tripped
    

status:probe_val
    

status:probed_position
    

status:probing bool

status:program_units
    

status:queue
    

status:queue_full
    

status:queued_mdi_commands
    

status:rapidrate
    

status:read_line
    

status:recent_files
    

status:rotation_xy
    

status:settings
    

status:spindle.n.brake
    

status:spindle.n.direction
    

status:spindle.n.enabled
    

status:spindle.n.homed
    

status:spindle.n.orient_fault
    

status:spindle.n.orient_state
    

status:spindle.n.override
    

status:spindle.n.override_enabled
    

status:spindle.n.speed
    

status:spindles
    

status:state
    

status:task_mode
    

status:task_paused
    

status:tool_in_spindle
    

status:tool_offset
    

status:tool_table
    

status:velocity
    

