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
    QtPyVCP requires a x86_64 operating systems, x86_32 systems are **not** compatible unless you build VTK with QT support from sources.

    There are VTK builds for Raspberry pi 4 32 bits. https://scottalford75.github.io/LinuxCNC-on-RPi/4.%20VTK%20for%20QtPyVCP.html


Instructions for installing LinuxCNC on Debian 10 (buster) and Linuxmint 19 can be found here:

https://gnipsel.com/linuxcnc/uspace/debian10-emc.html
https://gnipsel.com/linuxcnc/uspace/linuxmint19-emc.html

LinuxCNC 2.80 ISO available here:

http://linuxcnc.org/downloads/

Software Dependencies
---------------------

These packages should be installed prior to attempting to install QtPyVCP.

::

  sudo apt install python-pyqt5 python-dbus.mainloop.pyqt5 python-pyqt5.qtopengl python-pyqt5.qsci python-pyqt5.qtmultimedia python-pyqt5.qtquick qml-module-qtquick-controls gstreamer1.0-plugins-bad libqt5multimedia5-plugins pyqt5-dev-tools python-dev python-setuptools python-wheel python-pip git
