====================
Notifications plugin
====================

Plugin to handle error and status notifications.
Supports evaluating arbitrary python expressions placed in gcode DEBUG 
statements.

------------------------
*Available datachannels*
------------------------

* :ref:`info_message <info_message>`
* :ref:`error_message <error_message>`
* :ref:`debug_message <debug_message>`
* :ref:`warn_message <warn_message>`

.. _info_message:

info_message
    Shows any message from GCode the statements (MSG, ...) or (DEBUG, 
    ...)
    
    If the message is wrapped in eval[], the plugin will first evaluate 
    the inside string as python code. Any round brackets required in the 
    python code have to be replaced with {} so the interpreter doesn't 
    see the round bracket as the end of the statement.

    | syntax ``notifications:info_message`` returns str

.. _error_message:

error_message
    Shows any error messages from LinuxCNC.
    
    | syntax ``notifications:debug_message`` returns str

.. _debug_message:

debug_message
    Shows any debug messages from LinuxCNC.
    
    | syntax ``notifications:debug_message`` returns str

.. _warn_message:

warn_message
    Shows any warning messages from LinuxCNC.
    
    | syntax ``notifications:debug_message`` returns str
