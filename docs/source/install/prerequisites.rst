=============
Prerequisites
=============

QtPyVCP can be installed and run on most reasonably modern PCs and operating systems.
There are a few requirements that need to be satisfied, however, and it's best to
verify that the system is indeed capable of running QtPyVCP before installing.

These requirements are the same regardless of the install method.


System Requirements
-------------------

* Debian 9 (Stretch) and 10 (buster) or Linux Mint 19, 64 bit
* LinuxCNC **2.8** or later, installed either system wide or as a Run In Place (RIP) built from source
* Graphics card that supports OpenGL 1.50 or later (for VTK backplot)

.. Note::
    QtPyVCP requires a 64bit operating systems, 32bit systems are **not** supported.

Instructions for installing LinuxCNC on Debian 9 (stretch) and other distros
can be found here: https://gnipsel.com/linuxcnc/uspace/debian9-emc.html


Software Dependencies
---------------------

These packages should be installed prior to attempting to install QtPyVCP.

::

  sudo apt install python-pyqt5 python-dbus.mainloop.pyqt5 python-pyqt5.qtopengl python-pyqt5.qsci python-pyqt5.qtmultimedia python-pyqt5.qtquick qml-module-qtquick-controls gstreamer1.0-plugins-bad libqt5multimedia5-plugins pyqt5-dev-tools python-dev python-setuptools python-wheel python-pip git
