=================
Tooltable plugin
=================

In order to enable the tooltable plugin, you need to enable it in your 
VCPs YAML file.

Sample configuration:

.. code-block:: yaml

    data_plugins:
      tooltable:
        kwargs:
          # specify the columns that should be read and writen to the
          # tooltable file. To use all columns set to: TPXYZABCUVWDIJQR
          columns: PTDZR
          # specify text to be added before the tool table data
          file_header_template: |
            LinuxCNC Tool Table
            -------------------

            QtPyVCP will preserve comments before the opening semicolon.


------------------------
*Available datachannels*
------------------------

* :ref:` current_tool < current_tool>`

.. _current_tool:

current_tool
    Gets information of the current tool.
    
    | syntax ``tooltable:current_tool`` returns a dictionary containing 
    all column information 
    | syntax ``tooltable:current_tool?T`` returns the current tool 
    number.
    | syntax ``tooltable:current_tool?P`` returns the current tool 
    pocket number.
    | syntax ``tooltable:current_tool?X`` returns the current tools X 
    offset.
    | syntax ``tooltable:current_tool?Y`` returns the current tools Y 
    offset.
    | syntax ``tooltable:current_tool?Z`` returns the current tools Z 
    offset.
    | syntax ``tooltable:current_tool?A`` returns the current tools A 
    offset.
    | syntax ``tooltable:current_tool?B`` returns the current tools B 
    offset.
    | syntax ``tooltable:current_tool?C`` returns the current tools C 
    offset.
    | syntax ``tooltable:current_tool?U`` returns the current tools U 
    offset.
    | syntax ``tooltable:current_tool?V`` returns the current tools V 
    offset.
    | syntax ``tooltable:current_tool?W`` returns the current tools W 
    offset.
    | syntax ``tooltable:current_tool?I`` returns the current tools 
    front angle.
    | syntax ``tooltable:current_tool?J`` returns the current tools 
    back angle.
    | syntax ``tooltable:current_tool?Q`` returns the current tools 
    orientation.
    | syntax ``tooltable:current_tool?R`` returns the current tools 
    remark.
