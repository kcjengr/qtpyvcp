============
Installation
============

.. toctree::
   :maxdepth: 1
   :titlesonly:

   apt_install
   dev_install

There are two ways to install QtPyVCP. Use one or the other on a machine,
not both.


Requirements
------------

==================  ==============  ==================  ================
Debian release      Python          Qt binding          QtPyVCP branch
==================  ==============  ==================  ================
13 Trixie           3.13            Qt 6 / PySide6      ``pyside6``
12 Bookworm         3.11            Qt 5 / PyQt5        ``main``
==================  ==============  ==================  ================

The Python and Qt versions are whatever the Debian release ships. You do
not install them separately, and you should not mix versions between
releases.

Also needed:

* LinuxCNC 2.9
* A 64 bit machine, ``amd64`` or ``arm64``. These are the only
  architectures packages are built for.
* A graphics card with working OpenGL, for the VTK backplot.


Install from apt
----------------

Recommended for most users. Installs QtPyVCP and the VCPs built on it, and
updates them along with the rest of your system.

See :doc:`Install from apt repository <apt_install>`.


Developer Install
-----------------

For working on the QtPyVCP source code. An installer script clones the
source, sets up a Python virtual environment and builds everything for you.

See :doc:`Developer Install <dev_install>`.
