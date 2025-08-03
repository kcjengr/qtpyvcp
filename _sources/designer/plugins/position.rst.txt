===============
Position plugin
===============

This plugin provides datachannels in order to obtain the machine 
position in either machine coordinates, workpiece coordinates or 
distance to go coordinates.

------------------------
*Available datachannels*
------------------------

* :ref:`abs <abs>`
* :ref:`rel <rel>`
* :ref:`dtg <dtg>`

.. _abs:

abs
    Gives the current absolute/machine position.

    | syntax ``position:abs`` returns tuple
    
    In order to get a single axis pass the axis letter like so:

    | syntax ``position:abs?string&axis=x`` returns str

.. _rel:

rel
    Gives the current relative position with all offsets applied.

    | syntax ``position:rel`` returns tuple
    
    In order to get a single axis pass the axis letter like so:

    | syntax ``position:rel?string&axis=x`` returns str
    
.. _dtg:

dtg
    Gives the remaining distance to go for the current move. Useful when 
    testing or debugging your gcode.

    | syntax ``position:dtg`` returns tuple
    
    In order to get a single axis pass the axis letter like so:

    | syntax ``position:dtg?string&axis=x`` returns str
    
    
