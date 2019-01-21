=============
Home Controls
=============

In our left tab1 lets add some home controls, drag a grid layout into the tab
then right click in the tab (not the grid layout) and select layout in a grid.
This will cause the grid layout to fill the tab.

.. image:: images/vcp1-designer-11.png
   :align: center
   :scale: 40 %

Make the same changes to the frame as before morph into QFrame, box frame,
line width 2, margins 5.

.. image:: images/vcp1-designer-12.png
   :align: center
   :scale: 40 %

Repeat for the right hand tab.

Now back in the left tab we want the buttons to be 50 x 50 px so open the
stylesheet for the grid layout and add the following::

    .ActionButton {
        min-height: 50px;
        min-width: 50px;
        max-height: 50px;
        max-width: 50px;
    }

.. image:: images/vcp1-designer-13.png
   :align: center
   :scale: 40 %

