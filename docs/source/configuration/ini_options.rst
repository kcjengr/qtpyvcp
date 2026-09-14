===========
INI Options
===========

To get a list of current INI file options run

.. code-block:: bash

    qtpyvcp -h

Command line options are lower case and use the dash, INI file options are upper
case and use the underscore. Example: ``--hide-menu-bar`` >> ``HIDE_MENU_BAR``.

Options available in the INI file are:

.. code-block:: ini

    [DISPLAY]
    # Name of the VCP to use, or a .ui or .yml file
    VCP = name

    # The Qt theme to use, fusion, windows etc
    THEME = theme

    # Path to QSS style sheet file
    STYLESHEET = style.qss

    # Initial size of the window in pixels
    SIZE = <W>x<H>

    # Initial position of the window in pixels
    POSITION = <X>x<Y>

    # Flag to start with window fullscreen
    FULLSCREEN = bool

    # Flag to start with window maximized
    MAXIMIZE = bool

    # Hides the menu bar, if present
    HIDE_MENU_BAR = bool

    # Hides the status bar, if present
    HIDE_STATUS_BAR = bool

    # Hides the cursor for touchscreen VCPs
    HIDE_CURSOR = True

    # Whether to show dialog to confirm exit
    CONFIRM_EXIT = bool

    # One of DEBUG, INFO, WARN, ERROR or CRITICAL
    LOG_LEVEL = level

    # Specifies the log file
    LOG_FILE = file

    # Specifies a machine specific YML config file
    CONFIG_FILE = file

    # Monitor and log system performance
    PERFMON = bool

    # Qt Python binding to use, pyside6
    QT_API = api

    # Additional args passed to the QtApplication.
    COMMAND_LINE_ARGS = <args>

    # Default and maximum angular/linear jog velocity in units per second.
    DEFAULT_LINEAR_VELOCITY = <float>
    MAX_LINEAR_VELOCITY = <float>
    DEFAULT_ANGULAR_VELOCITY = <float>
    MAX_ANGULAR_VELOCITY = <float>

    # Provide user defined G code Syntax file
    GCODE_SYNTAX = file

    # Development mode. Reloads the QSS stylesheet live when it changes.
    DEVELOP = bool

    # Log a system diagnostics report at startup, plus backplot graphics
    # diagnostics. Default off.
    ADVANCED_LOGGING = bool

    # Jog with the arrow keys and Page Up/Down while holding Ctrl. On a lathe
    # Up/Down jog X and Left/Right jog Z. Hold Shift to jog at rapid speed.
    # Default off.
    KEYBOARD_JOG = bool

    # Keyboard jog without holding Ctrl. Default off.
    KEYBOARD_JOG_SAFETY_OFF = bool

    # Backplot frame rate. Overrides FPS in [VTK].
    FPS = <int>

    # Draw the machine limits in the backplot as lines instead of a box.
    # The grid is not available with lines.
    BOUNDARIES = line

    # 8x antialiasing in the backplot. Any value turns it on, even false,
    # so leave the line out to keep it off.
    ANTIALIAS = true

    # Plasma, laser or waterjet machine: the backplot hides the Z axis and
    # the tool. Any value turns it on, even false, so leave the line out
    # otherwise.
    JET = true

    # VTK backplot options
    [VTK]
    # Use the fast C++ backplot. Default on. Always off when a rotary
    # axis is on the table (see X to C below).
    CPP_BACKPLOT = bool

    # Backplot frame rate. Default 30. FPS in [DISPLAY] takes priority.
    FPS = <int>

    # Line segments used to draw each arc, 8 to 1024. Default 64.
    ARC_DIVISION = <int>

    # Whether each axis moves the head or the table. Default head.
    # If you set any of these, set one for every axis in [TRAJ] COORDINATES.
    X = head | table
    Y = head | table
    Z = head | table
    A = head | table
    B = head | table
    C = head | table

    # Where the live tool trail is drawn:
    #   world  fixed in machine space ("machine" also works)
    #   tool   moves with the program path, for table-moving machines
    #   auto   tool if any axis is on the table, otherwise world (default)
    BREADCRUMB_FRAME = auto

    # File paths below are relative to the config folder, or absolute.

    # YAML file describing the machine model to draw, including rotary
    # axis origins. See sim.qtpyvcp.machine_parts/machine.yml for an example.
    # A_PIVOT, A_ORIGIN and similar pivot keys are no longer read.
    MACHINE_PARTS = file.yml

    # STL model of the machine table
    TABLE = file.stl

    # STL model drawn at the spindle
    SPINDLE = file.stl

    # Direction the isometric view looks from, as X, Y and Z multipliers.
    # Defaults 1, -1 and 1. 0 keeps the default.
    VIEW_X = <float>
    VIEW_Y = <float>
    VIEW_Z = <float>

    # Log extra detail about axis transforms, for troubleshooting. Default off.
    TRANSFORM_DEBUG = bool

Boolean values can be one of ``true``, ``on``, ``yes`` or ``1`` for **True**,
and one of ``false``, ``off``, ``no`` or ``0`` for **False**.

File paths can be relative to the config dir, relative to the users home, or
absolute. Environment variables are expanded.

.. code-block:: ini

    # File Paths:
    #   File paths can be relative to the config dir:
    #     LOG_FILE = qtpyvcp.log

    #   Or relative to $HOME: (May not be compatible with other GUIs!)
    #     LOG_FILE = ~/qtpyvcp.log

    #   Or at an absolute location:
    #     LOG_FILE = /home/<USER>/qtpyvcp.log

    #   Enviroment vars are also expanded:
    #     LOG_FILE = $CONFIG_DIR/qtpyvcp.log
