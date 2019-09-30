===========
Quick Start
===========

These instructions will install the current release of `QtPyVCP`, including
sample configurations for LinuxCNC and Qt Designer for editing VCPs.

**Requirements**

* Debian 9 (Stretch) or Linux Mint 19, 64 bit
* LinuxCNC 2.8 or later, installed either system wide or as a Run In Place (RIP) built from source.
* Graphics card that supports at least OpenGL 1.50

.. Note::
    QtPyVCP requires a 64bit operating systems, 32bit systems are **not** supported.

Instructions for installing LinuxCNC on Debian 9 (stretch) and other distros
can be found here: https://gnipsel.com/linuxcnc/uspace/debian9-emc.html


**Install dependencies**
::

  sudo apt install python-pyqt5 python-dbus.mainloop.pyqt5 python-pyqt5.qtopengl python-pyqt5.qsci python-pyqt5.qtmultimedia qml-module-qtquick-controls gstreamer1.0-plugins-bad libqt5multimedia5-plugins pyqt5-dev-tools python-dev python-setuptools python-pip git python-pyqtgraph

**Install QtPyVCP**
::

  pip install qtpyvcp

This will install QtPyVCP along with the examples, and will add
QtPyVCP specific sim configs to ``~/linuxcnc/configs/sim.qtpyvcp``.

.. note::
    On Debian you will need to log out and log back in.

**Upgrade QtPyVCP**

As improvements are made to QtPyVCP you can upgrade the pip install with
::

  pip install --upgrade qtpyvcp

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
