===========
Quick Start
===========

If you are impatient, this is for you!

**Install dependencies**
::

  sudo apt install python-pyqt5 python-dbus.mainloop.pyqt5 python-pyqt5.qtopengl python-pyqt5.qsci python-pyqt5.qtmultimedia gstreamer1.0-plugins-bad libqt5multimedia5-plugins pyqt5-dev-tools python-pip git

**Install QtPyVCP**
::

  sudo pip install git+https://github.com/kcjengr/qtpyvcp.git

This will install QtPyVCP along with the examples, and will add
QtPyVCP specific sim configs to ``~/linuxcnc/configs/sim.qtpyvcp``.

**Launch a SIM config**

Launch LinuxCNC as usual and select one of the QtPyVCP sims. You should see a
dialog from which you can select one of the example VCPs. Chose one and click
"Launch VCP".

This installation method is tested to work on Debian 9 (Stretch), it will
probably work on other distros as well. If you intend to make your own VCPs
or contribute to QtPyVCP you will need to set up a development environment.

.. Note::

    You should un-install using ``sudo pip uninstall qtpyvcp``
    before using one of the other installation methods to avoid conflicts.
