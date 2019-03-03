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
    VCP = name             # Name of the VCP to use, or a .ui or .yml file.
    THEME = theme          # The Qt theme to use, fusion, windows etc.
    STYLESHEET = style.qss # Path to QSS style sheet file.
    SIZE = <W>x<H>         # Initial size of the window in pixels.
    POSITION = <X>x<Y>     # Initial position of the window in pixels.
    FULLSCREEN = bool      # Flag to start with window fullscreen.
    MAXIMIZE = bool        # Flag to start with window maximized.
    HIDE_MENU_BAR = bool   # Hides the menu bar, if present.
    HIDE_STATUS_BAR = bool # Hides the status bar, if present.
    CONFIRM_EXIT = bool    # Whether to show dialog to confirm exit.

    # Application Options
    LOG_LEVEL = level      # One of DEBUG, INFO, WARN, ERROR or CRITICAL.
    LOG_FILE = file        # Specifies the log file.
    CONFIG_FILE = file     # Specifies a machine specific YML config file.
    PREF_FILE = file       # Specifies the preference file.
    PERFMON = bool         # Monitor and log system performance.
    QT_API = api           # Qt Python binding to use, pyqt5 or pyside2.
    COMMAND_LINE_ARGS = <args>

    # VTK_Widget Options
    PROGRAM_BOUNDRY        # Boolean False to hide the program boundry
    MACHINE_BOUNDRY        # Boolean False to hide the machine boundry


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
