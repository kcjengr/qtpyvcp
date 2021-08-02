=============
Prerequisites for python3
=============

QtPyVCP can be installed and run on most reasonably modern PCs and operating systems.
There are a few requirements that need to be satisfied, however, and it's best to
verify that the system is indeed capable of running QtPyVCP before installing.

These requirements are the same regardless of the install method.


System Requirements
-------------------

* Debian 10 (Buster) and 11 (bullseye) 64 bit
* LinuxCNC **2.9** branch master-gtk3, installed as a Run In Place (RIP) built from source
* Graphics card that supports OpenGL 1.50 or later (for VTK backplot)

.. Note::
    QtPyVCP requires a x86_64 operating systems, x86_32 systems are **not** compatible unless you build VTK with QT support from sources.

    There are VTK builds for Raspberry pi 4 32 bits. https://scottalford75.github.io/LinuxCNC-on-RPi/4.%20VTK%20for%20QtPyVCP.html


LinuxCNC 2.80 ISO available here:

http://linuxcnc.org/downloads/

Software Dependencies
---------------------

These packages should be installed prior to attempting to install QtPyVCP.

::

  sudo apt install python3-pyqt5 python3-dbus.mainloop.pyqt5 python3-pyqt5.qtopengl python3-pyqt5.qsci python3-pyqt5.qtmultimedia python3-pyqt5.qtquick qml-module-qtquick-controls gstreamer1.0-plugins-bad libqt5multimedia5-plugins pyqt5-dev-tools python3-dev python3-setuptools python3-wheel python3-pip git
