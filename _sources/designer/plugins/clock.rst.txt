============
Clock plugin
============

This plugin provides the Date and Time

This plugin is not loaded by default, so to use it you will first
need to add it to your VCPs YAML config file.

YAML configuration:

.. code-block:: yaml

    data_plugins:
      clock:
        provider: qtpyvcp.plugins.clock:Clock

------------------------
*Available datachannels*
------------------------

* :ref:`time <time>`
* :ref:`date <date>`

.. _time:

time
    Returns the current date as a formatted string.
    Default format is ``%I:%M:%S %p`` which gives a 12-hour clock in 
    HH:MM:SS AM format.
    
    See http://strftime.org for supported formats.

    | syntax ``clock:time`` returns str
    
    The default formatting can be overridden as follows:
    
    | syntax ``clock:time?string&format=%S`` returns str

.. _date:

date
    Returns the current date as a formatted string.
    Default format is ``%m/%d/%Y`` which gives MM/DD/YYYY 
    
    See http://strftime.org for supported formats.

    | syntax ``clock:date`` returns str
    
    The default formatting can be overridden as follows:
    
    | syntax ``clock:date?string&format=%S`` returns str
