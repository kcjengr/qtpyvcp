============
Status Items
============

Status Items can be used in :doc:`../tutorials/widget_rules` to control and
display status data for LinuxCNC.


----------
**Tuples**
----------

If a status item returns a tuple you can get a single value from the tuple by
slicing. For example if the tuple is channel 0 ``ch[0]`` you can convert it to a
string and get the first entry like this ``str(ch[0][0])``. To get the third
item in the tuple you slice at 2 because counting starts at 0 not 1 so
``str(ch[0][2])`` returns the third item in the tuple. For axis items they are
in this order X, Y, Z, A, B, C, U, V, W.

.. _status_list:

---------------------
**Status Items List**
---------------------

* :ref:`acceleration <acceleration>`
* :ref:`active queue <active_queue>`
* :ref:`actual position <actual_position>`
* :ref:`adaptive feed enabled <adaptive_feed_enabled>`
* :ref:`analog inputs <ain>`
* :ref:`all axes homed <all_axes_homed>`
* :ref:`angular units <angular_units>`
* :ref:`analog outputs <aout>`
* :ref:`axes configured <axes>`
* :ref:`axis mask <axis_mask>`
* :ref:`block delete <block_delete>`
* :ref:`o word call level <call_level>`
* :ref:`currently executing line <current_line>`
* :ref:`current velocity <current_vel>`
* :ref:`cycle time <cycle_time>`
* :ref:`G4 delay left <delay_left>`
* :ref:`digital inputs <din>`
* :ref:`distance to go <distance_to_go>`
* :ref:`digital outputs <dout>`
* :ref:`distance to go by axis <dtg>`
* :ref:`serial number <echo_serial_number>`
* :ref:`enabled <enabled>`
* :ref:`estop <estop>`
* :ref:`task execution state <exec_state>`
* :ref:`feed hold <feed_hold_enabled>`
* :ref:`feed override enabled <feed_override_enabled>`
* :ref:`feedrate override <feedrate>`
* :ref:`filename <file>`
* :ref:`flood <flood>`
* :ref:`G5x index <g5x_index>`
* :ref:`G5x offset <g5x_offset>`
* :ref:`G92 offset <g92_offset>`
* :ref:`gcodes <gcodes>`
* :ref:`homed <homed>`
* :ref:`id <id>`
* :ref:`in position <inpos>`
* :ref:`input timer <input_timeout>`
* :ref:`interpreter state <interp_state>`
* :ref:`interpreter return code <interpreter_errcode>`
* :ref:`joint n backlash <joint.n.backlash>`
* :ref:`joint n enabled <joint.n.enabled>`
* :ref:`joint n fault <joint.n.fault>`
* :ref:`joint n following error <joint.n.ferror_current>`
* :ref:`joint n maximum following error <joint.n.ferror_highmark>`
* :ref:`joint n homed <joint.n.homed>`
* :ref:`joint n homing <joint.n.homing>`
* :ref:`joint n in position <joint.n.inpos>`
* :ref:`joint n input position <joint.n.input>`
* :ref:`joint n type of axis <joint.n.jointType>`
* :ref:`joint n maximum following error rapid <joint.n.max_ferror>`
* :ref:`joint n maximum hard limit <joint.n.max_hard_limit>`
* :ref:`joint n maximum soft limit setting <joint.n.max_position_limit>`
* :ref:`joint n maximum soft limit <joint.n.max_soft_limit>`
* :ref:`joint n maximum following error feed <joint.n.min_ferror>`
* :ref:`joint n minimum hard limit <joint.n.min_hard_limit>`
* :ref:`joint n minimum soft limit <joint.n.min_position_limit>`
* :ref:`joint n minimum soft limit exceeded <joint.n.min_soft_limit>`
* :ref:`joint n commanded output position <joint.n.output>`
* :ref:`joint n override limits <joint.n.override_limits>`
* :ref:`joint n units <joint.n.units>`
* :ref:`joint n velocity <joint.n.velocity>`
* :ref:`joint actual positions <joint_actual_position>`
* :ref:`commanded joint positions <joint_position>`
* :ref:`joints <joints>`
* :ref:`kinematics type <kinematics_type>`
* :ref:`limit masks <limit>`
* :ref:`linear units <linear_units>`
* :ref:`lube status <lube>`
* :ref:`lube level <lube_level>`
* :ref:`maximum acceleration <max_acceleration>`
* :ref:`maximum velocity <max_velocity>`
* :ref:`m codes <mcodes>`
* :ref:`mist status <mist>`
* :ref:`motion line <motion_line>`
* :ref:`motion mode<motion_mode>`
* :ref:`motion type <motion_type>`
* :ref:`machine power <on>`
* :ref:`optional stop <optional_stop>`
* :ref:`motion paused <paused>`
* :ref:`pocket prepped <pocket_prepped>`
* :ref:`trajectory position <position>`
* :ref:`probe tripped <probe_tripped>`
* :ref:`probe input value <probe_val>`
* :ref:`probed position <probed_position>`
* :ref:`probing status <probing>`
* :ref:`program units <program_units>`
* :ref:`trajectory planner queue <queue>`
* :ref:`trajectory planner queue full <queue_full>`
* :ref:`queued mdi commands <queued_mdi_commands>`
* :ref:`rapid override scale <rapidrate>`
* :ref:`interperter read line <read_line>`
* :ref:`recent files <recent_files>`
* :ref:`rotation XY <rotation_xy>`
* :ref:`interpreter settings <settings>`
* :ref:`spindle brake <spindle.n.brake>`
* :ref:`spindle direction <spindle.n.direction>`
* :ref:`spindle enabled <spindle.n.enabled>`
* :ref:`spindle homed <spindle.n.homed>`
* :ref:`spindle orient fault <spindle.n.orient_fault>`
* :ref:`spindle n orient state <spindle.n.orient_state>`
* :ref:`spindle speed override <spindle.n.override>`
* :ref:`spindle speed override enabled <spindle.n.override_enabled>`
* :ref:`spindle speed <spindle.n.speed>`
* :ref:`spindles <spindles>`
* :ref:`command execution status <state>`
* :ref:`task mode <task_mode>`
* :ref:`task paused <task_paused>`
* :ref:`task state <task_state>`
* :ref:`tool in spindle <tool_in_spindle>`
* :ref:`tool offset <tool_offset>`
* :ref:`tool table <tool_table>`
* :ref:`velocity <velocity>`


.. _acceleration:

acceleration
    default acceleration, ini parameter [TRAJ]DEFAULT_ACCELERATION

    | syntax ``status:acceleration`` returns float
    | syntax ``status:acceleration?string`` returns str

:ref:`return to the status items list <status_list>`

.. _active_queue:

active_queue
    number of motions blending

    | syntax ``status:active_queue`` returns int
    | syntax ``status:active_queue?string`` returns str

:ref:`return to the status items list <status_list>`

.. _actual_position:

actual_position
    current trajectory position, (x y z a b c u v w) in machine units

    | syntax ``status:actual_position`` returns tuple of floats
    | syntax ``status:actual_position?string`` returns tuple of str

:ref:`return to the status items list <status_list>`

.. _adaptive_feed_enabled:

adaptive_feed_enabled
    status of adaptive feedrate override

    | syntax ``status:adaptive_feed_enabled`` returns bool
    | syntax ``status:adaptive_feed_enabled?string`` returns str

:ref:`return to the status items list <status_list>`

.. _ain:

ain
    current value of the analog input pins

    | syntax ``status:ain`` returns tuple of floats
    | syntax ``status:ain?string`` returns str

:ref:`return to the status items list <status_list>`

.. _all_axes_homed:

all_axes_homed
    current status of all axes homed, if any axis is not homed it is false

    | syntax ``status:all_axes_homed`` returns bool
    | syntax ``status:all_axes_homed?string`` returns str

:ref:`return to the status items list <status_list>`

.. _angular_units:

angular_units
    machine angular units per deg, ini parameter [TRAJ]ANGULAR_UNITS

    | syntax ``status:angular_units`` returns float
    | syntax ``status:angular_units?string`` returns str

:ref:`return to the status items list <status_list>`

.. _aout:

aout
    current value of the analog output pins

    | syntax ``status:aout`` returns tuple of floats
    | syntax ``status:aout?string`` returns str

:ref:`return to the status items list <status_list>`

.. _axes:

axes
    number of axes. derived from [TRAJ]COORDINATES ini parameter

    | syntax ``status:axes`` returns int
    | syntax ``status:axes?string`` returns str

:ref:`return to the status items list <status_list>`

.. _axis_mask:

axis_mask
    mask of axis available [TRAJ]COORDINATES ini parameter

    | the sum of the axes X=1, Y=2, Z=4, A=8, B=16, C=32, U=64, V=128, W=256
    | syntax ``status:axis_mask`` returns int
    | syntax ``status:axis_mask?string`` returns str

:ref:`return to the status items list <status_list>`

.. _block_delete:

block_delete
    block delete curren status

    | syntax ``status:block_delete`` returns bool
    | syntax ``status:block_delete?string`` returns str

:ref:`return to the status items list <status_list>`

.. _call_level:

call_level
    current nesting level of O-word procedures

    | syntax ``status:call_level`` returns int
    | syntax ``status:call_level?string`` returns str

:ref:`return to the status items list <status_list>`

.. _current_line:

current_line
    currently executing line

    | syntax ``status:current_line`` returns int
    | syntax ``status:current_line?string`` returns str

:ref:`return to the status items list <status_list>`

.. _current_vel:

current_vel
    current velocity in user units per second

    | syntax ``status:current_vel`` returns float
    | syntax ``status:current_vel?string`` returns str

:ref:`return to the status items list <status_list>`

.. _cycle_time:

cycle_time
    thread period

    | syntax ``status:cycle_time`` returns float
    | syntax ``status:cycle_time?string`` returns str

:ref:`return to the status items list <status_list>`

.. _delay_left:

delay_left
    remaining time on the G4 dwell command, seconds

    | syntax ``status:delay_left`` returns float
    | syntax ``status:delay_left?string`` returns str

:ref:`return to the status items list <status_list>`

.. _din:

din
    current value of the digital input pins

    | syntax ``status:din`` returns tuple of integers
    | syntax ``status:din?string`` returns str

:ref:`return to the status items list <status_list>`

.. _distance_to_go:

distance_to_go
    remaining distance of current move, as reported by trajectory planner

    | syntax ``status:distance_to_go`` returns float
    | syntax ``status:distance_to_go?string`` returns str

:ref:`return to the status items list <status_list>`

.. _dout:

dout
    current value of the digital output pins

    | syntax ``status:dout`` returns tuple of integers
    | syntax ``status:dout?string`` returns str

:ref:`return to the status items list <status_list>`

.. _dtg:

dtg
    remaining distance of current move for each axis, as reported by trajectory planner

    | syntax ``status:dtg`` returns tuple of floats
    | syntax ``status:dtg?string`` returns str

:ref:`return to the status items list <status_list>`

.. _echo_serial_number:

echo_serial_number
    The serial number of the last completed command sent by a UI to task

    | syntax ``status:echo_serial_number`` returns int
    | syntax ``status:echo_serial_number?string`` returns str

:ref:`return to the status items list <status_list>`

.. _enabled:

enabled
    trajectory planner enabled flag

    | syntax ``status:enabled`` returns bool
    | syntax ``status:enabled?string`` returns str

:ref:`return to the status items list <status_list>`

.. _estop:

estop
    status of E Stop, 1 for enabled and 0 for not enabled

    | syntax ``status:estop`` returns int
    | syntax ``status:estop?string`` returns str

:ref:`return to the status items list <status_list>`

.. _exec_state:

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

:ref:`return to the status items list <status_list>`

.. _feed_hold_enabled:

feed_hold_enabled
    status of feed hold

    | syntax ``status:feed_hold_enabled`` returns bool
    | syntax ``status:feed_hold_enabled?string`` returns str

:ref:`return to the status items list <status_list>`

.. _feed_override_enabled:

feed_override_enabled
    status of feed override

    | syntax ``status:feed_override_enabled`` returns bool
    | syntax ``status:feed_override_enabled?string`` returns str

:ref:`return to the status items list <status_list>`

.. _feedrate:

feedrate
    current feedrate override, 1.0 = 100%

    | syntax ``status:feedrate`` returns float
    | syntax ``status:feedrate?string`` returns str

:ref:`return to the status items list <status_list>`

.. _file:

file
    currently loaded gcode filename with path

    | syntax ``status:file`` returns str
    | for just the file name use this expression ``ch[0].split('/')[-1]``

:ref:`return to the status items list <status_list>`

.. _flood:

flood
    current flood status 0 for off, 1 for on

    | syntax ``status:flood`` returns int
    | syntax ``status:flood?string`` returns str

:ref:`return to the status items list <status_list>`

.. _g5x_index:

g5x_index
    currently active coordinate system

    === ======
    int string
    === ======
    0   G53
    1   G54
    2   G55
    3   G56
    4   G57
    5   G58
    6   G59
    7   G59.1
    8   G59.2
    9   G59.3
    === ======

    | syntax ``status:g5x_index`` returns int
    | syntax ``status:g5x_index?string`` returns str

:ref:`return to the status items list <status_list>`

.. _g5x_offset:

g5x_offset
    offsets of the currently active coordinate system

    | syntax ``status:g5x_offset`` returns tuple of floats
    | syntax ``status:g5x_offset?string`` returns str

:ref:`return to the status items list <status_list>`

.. _g92_offset:

g92_offset
    current g92 offsets

    | syntax ``status:g92_offset`` returns tuple of floats
    | syntax ``status:g92_offset?string`` returns str

:ref:`return to the status items list <status_list>`

.. _gcodes:

gcodes
    active G-codes for each modal group

    | syntax ``status:gcodes`` returns tuple of integers
    | syntax ``status:gcodes?string`` returns str

:ref:`return to the status items list <status_list>`

.. _homed:

homed
    currently homed joints, 0 = not homed, 1 = homed

    | syntax ``status:homed`` returns tuple of integers
    | syntax ``status:homed?string`` returns str

:ref:`return to the status items list <status_list>`

.. _id:

id
    currently executing motion id

    | syntax ``status:id`` returns int
    | syntax ``status:id?string`` returns str

:ref:`return to the status items list <status_list>`

.. _inpos:

inpos
    status machine in position

    | syntax ``status:inpos`` returns bool
    | syntax ``status:inpos?string`` returns str

:ref:`return to the status items list <status_list>`

.. _input_timeout:

input_timeout
    flag for M66 timer in progress

    | syntax ``status:input_timeout`` returns bool
    | syntax ``status:input_timeout?string`` returns str

:ref:`return to the status items list <status_list>`

.. _interp_state:

interp_state
    current state of RS274NGC interpreter

    === =======
    int str
    === =======
    1   Idle
    2   Reading
    3   Paused
    4   Waiting
    === =======

    | syntax ``status:interp_state`` returns int
    | syntax ``status:interp_state?string`` returns str

:ref:`return to the status items list <status_list>`

.. _interpreter_errcode:

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

:ref:`return to the status items list <status_list>`

.. _joint.n.backlash:

joint.n.backlash
    backlash in machine units, ini parameter [JOINT_n]BACKLASH (`n` is joint number)

    | syntax ``status:joint.n.backlash`` returns float
    | syntax ``status:joint.n.backlash?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.enabled:

joint.n.enabled
    status of joint n enabled, 0 not enabled 1 enabled

    | syntax ``status:joint.n.enabled`` returns int
    | syntax ``status:joint.n.enabled?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.fault:

joint.n.fault
    status of joint n fault, 0 not faulted 1 faulted

    | syntax ``status:joint.n.fault`` returns int
    | syntax ``status:joint.n.fault?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.ferror_current:

joint.n.ferror_current
    current joint n following error

    | syntax ``status:joint.n.ferror_current`` returns float
    | syntax ``status:joint.n.ferror_current?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.ferror_highmark:

joint.n.ferror_highmark
    joint n magnitude of maximum following error

    | syntax ``status:joint.n.ferror_highmark`` returns float
    | syntax ``status:joint.n.ferror_highmark?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.homed:

joint.n.homed
    status of joint n homed, 0 not homed 1 homed

    | syntax ``status:joint.n.homed`` returns int
    | syntax ``status:joint.n.homed?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.homing:

joint.n.homing
    status of joint n homing in progress, 0 not homing 1 homing

    | syntax ``status:joint.n.homing`` returns int
    | syntax ``status:joint.n.homing?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.inpos:

joint.n.inpos
    status of joint n in position, 0 not in position 1 in position

    | syntax ``status:joint.n.inpos`` returns int
    | syntax ``status:joint.n.inpos?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.input:

joint.n.input
    joint n current input position

    | syntax ``status:joint.n.input`` returns float
    | syntax ``status:joint.n.input?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.jointType:

joint.n.jointType
    joint n type of axis, ini parameter [JOINT_n]TYPE

    | syntax ``status:joint.n.jointType`` returns int
    | syntax ``status:joint.n.jointType?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.max_ferror:

joint.n.max_ferror
    joint n maximum following error rapid, ini parameter [JOINT_n]FERROR

    | syntax ``status:joint.n.max_ferror`` returns float
    | syntax ``status:joint.n.max_ferror?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.max_hard_limit:

joint.n.max_hard_limit
    status of joint n maximum hard limit, 0 not exceeded 1 exceeded

    | syntax ``status:joint.n.max_hard_limit`` returns int
    | syntax ``status:joint.n.max_hard_limit?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.max_position_limit:

joint.n.max_position_limit
    joint n maximum soft limit, ini parameter [JOINT_n]MAX_LIMIT

    | syntax ``status:joint.n.max_position_limit`` returns float
    | syntax ``status:joint.n.max_position_limit?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.max_soft_limit:

joint.n.max_soft_limit
    status of joint n maximum soft limit, 0 not exceeded 1 exceeded

    | syntax ``status:joint.n.max_soft_limit`` returns int
    | syntax ``status:joint.n.max_soft_limit?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.min_ferror:

joint.n.min_ferror
    maximum following error feed, ini parameter [JOINT_n]MIN_FERROR

    | syntax ``status:joint.n.min_ferror`` returns float
    | syntax ``status:joint.n.min_ferror?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.min_hard_limit:

joint.n.min_hard_limit
    non-zero means min hard limit exceeded

    | syntax ``status:joint.n.min_hard_limit`` returns int
    | syntax ``status:joint.n.min_hard_limit?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.min_position_limit:

joint.n.min_position_limit
    minimum soft limit ini parameter [JOINT_n]MIN_LIMIT

    | syntax ``status:joint.n.min_position_limit`` returns float
    | syntax ``status:joint.n.min_position_limit?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.min_soft_limit:

joint.n.min_soft_limit
    non-zero means min_position_limit was exceeded

    | syntax ``status:joint.n.min_soft_limit`` returns int
    | syntax ``status:joint.n.min_soft_limit?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.output:

joint.n.output
    commanded output position

    | syntax ``status:joint.n.output`` returns float
    | syntax ``status:joint.n.output?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.override_limits:

joint.n.override_limits
    non-zero means limits are overridden

    | syntax ``status:joint.n.override_limits`` returns int
    | syntax ``status:joint.n.override_limits?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.units:

joint.n.units
    joint units

    | syntax ``status:joint.n.units`` returns float
    | syntax ``status:joint.n.units?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint.n.velocity:

joint.n.velocity
    current velocity

    | syntax ``status:joint.n.velocity`` returns float
    | syntax ``status:joint.n.velocity?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint_actual_position:

joint_actual_position
    joint actual positions

    | syntax ``status:joint_actual_position`` returns tuple of floats
    | syntax ``status:joint_actual_position?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joint_position:

joint_position
    commanded joint positions

    | syntax ``status:joint_position`` returns tuple of floats
    | syntax ``status:joint_position?string`` returns str

:ref:`return to the status items list <status_list>`

.. _joints:

joints
    number of joints, ini parameter [KINS]JOINTS

    | syntax ``status:joints`` returns int
    | syntax ``status:joints?string`` returns str

:ref:`return to the status items list <status_list>`

.. _kinematics_type:

kinematics_type
    kinematics type

    | syntax ``status:kinematics_type`` returns int
    | syntax ``status:kinematics_type?string`` returns str

:ref:`return to the status items list <status_list>`

.. _limit:

limit
    axis limit masks

    | syntax ``status:limit`` returns tuple of integers
    | syntax ``status:limit?string`` returns str

:ref:`return to the status items list <status_list>`

.. _linear_units:

linear_units
    machine linear units,  ini parameter [TRAJ]LINEAR_UNITS

    | syntax ``status:linear_units`` returns float
    | syntax ``status:linear_units?string`` returns str

:ref:`return to the status items list <status_list>`

.. _lube:

lube
    lube status

    | syntax ``status:lube`` returns int
    | syntax ``status:lube?string`` returns str

:ref:`return to the status items list <status_list>`

.. _lube_level:

lube_level
    status of iocontrol.0.lube_level

    | syntax ``status:lube_level`` returns int
    | syntax ``status:lube_level?string`` returns str

:ref:`return to the status items list <status_list>`

.. _max_acceleration:

max_acceleration
    maximum acceleration,  ini parameter [TRAJ]MAX_ACCELERATION

    | syntax ``status:max_acceleration`` returns float
    | syntax ``status:max_acceleration?string`` returns str

:ref:`return to the status items list <status_list>`

.. _max_velocity:

max_velocity
    maximum velocity,  ini parameter [TRAJ]MAX_VELOCITY

    | syntax ``status:max_velocity`` returns float
    | syntax ``status:max_velocity?string`` returns str

:ref:`return to the status items list <status_list>`

.. _mcodes:

mcodes
    currently active M codes

    | syntax ``status:mcodes`` returns tuple of integers
    | syntax ``status:mcodes?string`` returns str

:ref:`return to the status items list <status_list>`

.. _mist:

mist
    mist status

    | syntax ``status:mist`` returns int
    | syntax ``status:mist?string`` returns str

:ref:`return to the status items list <status_list>`

.. _motion_line:

motion_line
    source line number motion is currently executing

    | syntax ``status:motion_line`` returns int
    | syntax ``status:motion_line?string`` returns str

:ref:`return to the status items list <status_list>`

.. _motion_mode:

motion_mode
    mode of the motion controller

    === ======
    int string
    === ======
    0   N/A
    1   Free
    2   Coord
    3   Teleop
    === ======

    | syntax ``status:motion_mode`` returns int
    | syntax ``status:motion_mode?string`` returns str

:ref:`return to the status items list <status_list>`

.. _motion_type:

motion_type
    motion type of move currently executing

    === ============
    int string
    === ============
    0   None
    1   Traverse
    2   Linear Feed
    3   Arc Feed
    4   Tool Change
    5   Probing
    6   Rotary Index
    === ============

    | syntax ``status:motion_type`` returns int
    | syntax ``status:motion_type?string`` returns str

:ref:`return to the status items list <status_list>`

.. _on:

on
    status of machine power

    | syntax ``status:on`` returns bool
    | syntax ``status:on?string`` returns str

:ref:`return to the status items list <status_list>`

.. _optional_stop:

optional_stop
    status of optional stop

    | syntax ``status:optional_stop`` returns int
    | syntax ``status:optional_stop?string`` returns str

:ref:`return to the status items list <status_list>`

.. _paused:

paused
    motion paused

    | syntax ``pstatus:aused`` returns bool
    | syntax ``status:paused?string`` returns str

:ref:`return to the status items list <status_list>`

.. _pocket_prepped:

pocket_prepped
    pocket prepped from last Tn commaned

    | syntax ``status:pocket_prepped`` returns int
    | syntax ``status:pocket_prepped?string`` returns str

:ref:`return to the status items list <status_list>`

.. _position:

position
    trajectory position

    | syntax ``status:position`` returns tuple of floats
    | syntax ``status:position?string`` returns str

:ref:`return to the status items list <status_list>`

.. _probe_tripped:

probe_tripped
    probe tripped

    | syntax ``status:probe_tripped`` returns bool
    | syntax ``status:probe_tripped?string`` returns str

:ref:`return to the status items list <status_list>`

.. _probe_val:

probe_val
    value of the motion.probe-input pin

    | syntax ``status:probe_val`` returns int
    | syntax ``status:probe_val?string`` returns str

:ref:`return to the status items list <status_list>`

.. _probed_position:

probed_position
    position where probe tripped

    | syntax ``status:probed_position`` returns tuple of floats
    | syntax ``status:probed_position?string`` returns str

:ref:`return to the status items list <status_list>`

.. _probing:

probing
    probe operation is in progress

    | syntax ``status:probing`` returns bool
    | syntax ``status:probing?string`` returns str

:ref:`return to the status items list <status_list>`

.. _program_units:

program_units
    program units

    === ===== ============
    int short long
    === ===== ============
    0   N/A   N/A
    1   in    Inches
    2   mm    Millimeters
    3   cm    Centimeters
    === ===== ============

    | syntax ``status:program_units`` returns int
    | syntax ``status:rogram_units?string`` returns short str
    | syntax ``status:rogram_units?string&format=long`` returns long str

:ref:`return to the status items list <status_list>`

.. _queue:

queue
    current size of the trajectory planner queue

    | syntax ``status:queue`` returns int
    | syntax ``status:queue?string`` returns str

:ref:`return to the status items list <status_list>`

.. _queue_full:

queue_full
    status of the trajectory planner queue

    | syntax ``status:queue_full`` returns bool
    | syntax ``status:queue_full?string`` returns str

:ref:`return to the status items list <status_list>`

.. _queued_mdi_commands:

queued_mdi_commands
    queued mdi commands

    | syntax ``status:queued_mdi_commands`` returns int
    | syntax ``status:queued_mdi_commands?string`` returns str

:ref:`return to the status items list <status_list>`

.. _rapidrate:

rapidrate
    rapid override scale

    | syntax ``status:rapidrate`` returns float
    | syntax ``status:rapidrate?string`` returns str

:ref:`return to the status items list <status_list>`

.. _read_line:

read_line
    current line the interperter is reading

    | syntax ``status:read_line`` returns int
    | syntax ``status:read_line?string`` returns str

:ref:`return to the status items list <status_list>`

.. _recent_files:

recent_files
    recent files opened including file path

    | syntax ``status:recent_files`` returns list
    | syntax ``status:recent_files?string`` returns str

:ref:`return to the status items list <status_list>`

.. _rotation_xy:

rotation_xy
    current XY rotation angle around Z axis

    | syntax ``status:rotation_xy`` returns float
    | syntax ``status:rotation_xy?string`` returns str

:ref:`return to the status items list <status_list>`

.. _settings:

settings
    current interpreter settings

    | syntax ``status:settings`` returns tuple of floats
    | syntax ``status:settings?string`` returns str

:ref:`return to the status items list <status_list>`

.. _spindle.n.brake:

spindle.n.brake
    status of spindle n brake

    | syntax ``status:spindle.n.brake`` returns int
    | syntax ``status:spindle.n.brake?string`` returns str

:ref:`return to the status items list <status_list>`

.. _spindle.n.direction:

spindle.n.direction
    rotational direction of the spindle. forward=1, reverse=-1

    | syntax ``status:spindle.n.direction`` returns int
    | syntax ``status:spindle.n.direction?string`` returns str

:ref:`return to the status items list <status_list>`

.. _spindle.n.enabled:

spindle.n.enabled
    spindle enabled status

    | syntax ``status:spindle.n.enabled`` returns int
    | syntax ``status:spindle.n.enabled?string`` returns str

:ref:`return to the status items list <status_list>`

.. _spindle.n.homed:

spindle.n.homed
    spindle n homed

    | syntax ``status:spindle.n.homed`` returns bool
    | syntax ``status:spindle.n.homed?string`` returns str

:ref:`return to the status items list <status_list>`

.. _spindle.n.orient_fault:

spindle.n.orient_fault
    spindle n orient fault status

    | syntax ``status:spindle.n.orient_fault`` returns int
    | syntax ``status:spindle.n.orient_fault?string`` returns str

:ref:`return to the status items list <status_list>`

.. _spindle.n.orient_state:

spindle.n.orient_state
    unknown

    | syntax ``status:spindle.n.orient_state`` returns int
    | syntax ``status:spindle.n.orient_state?string`` returns str

:ref:`return to the status items list <status_list>`

.. _spindle.n.override:

spindle.n.override
    spindle n speed override scale

    | syntax ``status:spindle.n.override`` returns float
    | syntax ``status:spindle.n.override?string`` returns str

:ref:`return to the status items list <status_list>`

.. _spindle.n.override_enabled:

spindle.n.override_enabled
    spindle n override enabled

    | syntax ``status:spindle.n.override_enabled`` returns bool
    | syntax ``status:spindle.n.override_enabled?string`` returns str

:ref:`return to the status items list <status_list>`

.. _spindle.n.speed:

spindle.n.speed
    spindle n speed rpm, > 0 clockwise, < 0 counterclockwise

    | syntax ``status:spindle.n.speed`` returns float
    | syntax ``status:spindle.n.speed?string`` returns str

:ref:`return to the status items list <status_list>`

.. _spindles:

spindles
    number of spindles, ini parameter [TRAJ]SPINDLES

    | syntax ``status:spindles`` returns int
    | syntax ``status:spindles?string`` returns str

:ref:`return to the status items list <status_list>`

.. _state:

state
    current command execution status

    | syntax ``status:state`` returns int
    | syntax ``status:state?string`` returns str

:ref:`return to the status items list <status_list>`

.. _task_mode:

task_mode
    current task mode

    === ======
    int string
    === ======
    0   N/A
    1   Manual
    2   Auto
    3   MDI
    === ======

    | syntax ``status:task_mode`` returns int
    | syntax ``status:task_mode?string`` returns str

:ref:`return to the status items list <status_list>`

.. _task_paused:

task_paused
    task paused status

    | syntax ``status:task_paused`` returns int
    | syntax ``status:task_paused?string`` returns str

:ref:`return to the status items list <status_list>`

.. _task_state:

task_state
    current task state

    === ======
    int string
    === ======
    0   N/A
    1   E-Stop
    2   Reset
    3   Off
    4   On
    === ======

    | syntax ``status:task_state`` returns int
    | syntax ``status:task_state?string`` returns str

:ref:`return to the status items list <status_list>`

.. _tool_in_spindle:

tool_in_spindle
    current tool number

    | syntax ``status:tool_in_spindle`` returns int
    | syntax ``status:tool_in_spindle?string`` returns str

:ref:`return to the status items list <status_list>`

.. _tool_offset:

tool_offset
    offset values of the current tool

    | syntax ``status:tool_offset`` returns tuple of floats
    | syntax ``status:tool_offset?string`` returns str

:ref:`return to the status items list <status_list>`

:ref:`return to the status items list <status_list>`

.. _tool_table:

tool_table
    list of tool entries

    | syntax ``status:tool_table`` returns tuple of tool_results
    | syntax ``status:tool_table?string`` returns str

:ref:`return to the status items list <status_list>`

.. _velocity:

velocity
    This property is defined, but it does not have a useful interpretation

    | syntax ``status:velocity`` returns float
    | syntax ``status:velocity?string`` returns str

:ref:`return to the status items list <status_list>`

