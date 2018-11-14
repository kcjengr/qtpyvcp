===========
Quick Start
===========

If you are impatient like me, this is for you!

Install dependencies::

  sudo apt install python-pyqt5 python-dbus.mainloop.pyqt5 python-pyqt5.qtopengl python-pyqt5.qsci python-pyqt5.qtmultimedia gstreamer1.0-plugins-bad libqt5multimedia5-plugins python-pip git

Install QtPyVCP with PIP::

  pip install git+https://github.com/kcjengr/qtpyvcp.git

Edit the INI file::

  [DISPLAY]
  DISPLAY = qtpyvcp
  VCP = brender

Launch LinuxCNC as usual.

Hopefully this works (it should on Debian 9). If not it doesn't make you a bad
person, it just means you should read the full installation document to find
out how to do it right!


.. Note::

    You should un-install using ``pip uninstall qtpyvcp``
    before trying another installation method.
