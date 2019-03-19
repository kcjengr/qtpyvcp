===========
Quick Start
===========

These instructions will install the current release of `QtPyVCP` including
sample configurations for LinuxCNC and the GUI builder Qt Designer with the
QtPyVCP widgets as well as the dependencies needed to run QtPyVCP.

**Requirements**

Debian 9 64 bit or Linux Mint 19 64 bit with LinuxCNC 2.8 (master) installed,
either system wide or as a Run In Place (RIP) built from source.

Instructions for installing on Debian 9 (stretch) and other distros can be
found here: https://gnipsel.com/linuxcnc/uspace/debian9-emc.html


**Install dependencies**
::

  sudo apt install python-pyqt5 python-dbus.mainloop.pyqt5 python-pyqt5.qtopengl python-pyqt5.qsci python-pyqt5.qtmultimedia gstreamer1.0-plugins-bad libqt5multimedia5-plugins pyqt5-dev-tools python-dev python-setuptools python-pip git

**Install QtPyVCP**
::

  pip install git+https://github.com/kcjengr/qtpyvcp.git

This will install QtPyVCP along with the examples, and will add
QtPyVCP specific sim configs to ``~/linuxcnc/configs/sim.qtpyvcp``.

.. note::
    On Debian you will need to log out and log back in.

**Upgrade QtPyVCP**

As improvements are made to QtPyVCP you an upgrade your pip install with the
following
::

  pip install git+https://github.com/kcjengr/qtpyvcp.git --upgrade

**Launch a SIM config**

Launch LinuxCNC as usual and select one of the QtPyVCP sims. You should see a
dialog from which you can select one of the example VCPs. Chose one and click
"Launch VCP".

**Edit a VCP**

To edit a VCP you need to install the Qt Designer.
::

    sudo apt install qttools5.dev qttools5-dev-tools

**Notes**

This installation method is tested to work on Debian 9 (Stretch) and Mint 19.1,
it should work on other distros as well. If you intend to contribute to QtPyVCP
you will need to set up a :doc:`development install <installation>`.

.. Note::
    You should un-install using ``pip uninstall qtpyvcp``
    before using one of the other installation methods to avoid conflicts.
