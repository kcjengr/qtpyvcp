=================
INI Configuration
=================

To get a list of current INI file options run

.. code-block:: bash

    qtpyvcp -h

Command line options are lower case and use the dash, INI file options are upper
case and use the underscore.

Options available in the INI file are:

.. code-block:: bash

    [DISPLAY]
    VCP = name # The name of the VCP to launch.
    THEME = theme # The Qt theme to use
    STYLESHEET = stylesheet # Path to QSS file containing styles to be applied \
                     to specific Qt and/or QtPyVCP widget classes.
    SIZE = width x height # Initial size of the window in pixels.
    POSITION = Xpos x Ypos # Initial position of the window, specified as the \
                     coordinates of the top left corner of the window \
                     relative to the top left corner of the screen. \

    FULLSCREEN = bool # Flag to start with window fullscreen.
    MAXIMIZE = bool # Flag to start with window maximized.
    HIDE_MENU_BAR = bool  # Hides the menu bar, if present.
    HIDE_STATUS_BAR = bool # Hides the status bar, if present.
    CONFIRM_EXIT = bool # Whether to show dialog to confirm exit.

    [APPLICATION]
    LOG_LEVEL = DEBUG | INFO | WARN | ERROR | CRITICAL
    LOG_FILE = file # Specifies the log file. Overrides INI setting.
    CONFIG_FILE = file # Specifies the YML config file.
    PREF_FILE = file # Specifies the preference file. Overrides INI setting.
    PERFMON = bool # Monitor and log system performance.
    QT_API = pyqt5 | pyqt | pyside2 | pyside # Specify the Qt Python binding to use.
    COMMAND_LINE_ARGS = <args>
