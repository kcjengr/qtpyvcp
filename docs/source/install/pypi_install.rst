================
Standard Install
================

These instructions will install the current release of `QtPyVCP` from PyPi,
including sample configurations for LinuxCNC and Qt Designer for editing VCPs.

.. Note::

    With the Standard Install you will be able to create and edit third party
    VCPs, but you will **not** be able to edit the example VCPs included with
    `QtPyVCP` or edit the `QtPyVCP` source code itself. If you wish to do this
    you will need to use the :doc:`Development Install <dev_install>` method.


.. Warning::

    Before proceeding make sure you have satisfied the prerequisites listed on
    the :doc:`Prerequisites <prerequisites>` page!


Install QtPyVCP
+++++++++++++++

::

  pip install qtpyvcp

This will install QtPyVCP along with the examples, and will add
QtPyVCP specific sim configs to ``~/linuxcnc/configs/sim.qtpyvcp``.

.. note::
    On Debian you will need to log out and log back in.


Upgrade QtPyVCP
+++++++++++++++

As improvements are made to QtPyVCP you can upgrade the pip install with
::

  pip install --upgrade qtpyvcp
