===============
Machine Buttons
===============

Lets create some jog buttons by adding some `ActionButtons` to a group box. Set
the minimum height to 50 and put the following into the `actionName`.
::

    machine.jog.axis:x,pos
    machine.jog.axis:x,neg
    machine.jog.axis:y,pos
    machine.jog.axis:y,neg
    machine.jog.axis:z,pos
    machine.jog.axis:z,neg

Now when we run the configuration we can jog and set work offsets.

.. image:: images/vcp1run-08.png
   :align: center
   :scale: 80 %

Lets add a `Home All` `ActionButton` with the `actionName` `machine.home.all`.

.. image:: images/vcp1run-09.png
   :align: center
   :scale: 80 %



