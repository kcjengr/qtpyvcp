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

    # Specifies the preference file
    PREF_FILE = file

    # Monitor and log system performance
    PERFMON = bool

    # Qt Python binding to use, pyqt5 or pyside2
    QT_API = api

    # Additional args passed to the QtApplication.
    COMMAND_LINE_ARGS = <args>

    # VTK_BackPlot Options
    [VTK]
    # Boolean False to hide the machine boundry
    MACHINE_BOUNDRY = bool

    # Boolean False to hide the machine boundry ticks
    MACHINE_TICKS = bool

    # Boolean False to hide the machine labels
    MACHINE_LABELS = bool

    # Boolean False to hide the program boundry
    PROGRAM_BOUNDRY = bool

    # Boolean False to hide the program boundry ticks
    PROGRAM_TICKS = bool

    # Boolean False to hide the program labels
    PROGRAM_LABELS = bool

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
