=============
Installation
=============

.. Note ::
    In order to use QtPyVCP you will need to have LinuxCNC ~2.8pre (master)
    installed, either system wide or as a Run In Place (RIP) built from source.

The are multiply ways to install QtPyVCP, which one is best depends on how
you intend to use QtPyVCP. If all you intend to do is try the examples,
your best bet is to install with pip per the :doc:`Quick Start <quick_start>` guide.

Installing with PIP
^^^^^^^^^^^^^^^^^^^

See the :doc:`Quick Start <quick_start>` guide.


Installing from Debian package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Download the latest release here: https://github.com/kcjengr/qtpyvcp/releases

Install by saying::

    sudo apt instal /path/to/download.deb

All dependencies should be automatically installed.


Installing from Source
^^^^^^^^^^^^^^^^^^^^^^

This is best if you intend to contribute to QtPyVCP or make your own VCPs.


Install Dependencies
++++++++++++++++++++

These are the dependencies needed to run QyPyVCP on Debian 9 (Stretch) systems.

Core dependencies::

  sudo apt install python-pyqt5 python-pyqt5.qtopengl python-pyqt5.qsci python-dbus.mainloop.pyqt5

Required for Camera widget::

  sudo apt install python-pyqt5.qtmultimedia gstreamer1.0-plugins-bad libqt5multimedia5-plugins


Required for QtPyVCP and VCP development::

  sudo apt install qttools5-dev-tools qttools5.dev pyqt5-dev-tools

Required for building documentation::

  sudo apt install python-sphinx
  pip install sphinx_rtd_theme mock

From the docs dir run ``make html`` to build the HTML documentation.

**Note:** *We try to keep this up to date, but if you find additional
dependencies are needed please notify one of the developers so it
can be added.*


Getting the QtPyVCP Source Code
+++++++++++++++++++++++++++++++

The easiest way to get QtPyVCP is to clone the
`QtPyVCP repository <https://github.com/kcjengr/qtpyvcp>`_ with git.
If you don't have git you can simply download the QtPyVCP .zip file
using the green *Clone or download* button, but this will make it harder
to update in the future.

To clone the repository open a terminal at the desired location and run::

  git clone https://github.com/kcjengr/qtpyvcp qtpyvcp

Enter the newly cloned directory::

  cd qtpyvcp


Install with setup.py
+++++++++++++++++++++

You need to have the python 2.7 setup tools installed::

  sudo apt install python-setuptools

Install QtPyVCP by running::

  sudo python setup.py develop

This will install QtPyVCP on your PYTHONPATH and will generate command line
scripts for launching QtPyVCP, the example VCPs and the command line tools.

If you used the ``--user`` flag the scripts will be placed in ``~/.local/bin/``,
which is not on the PATH on Debian 9 (Stretch). You can add ``~/.local/bin/``
to the current PATH by running::

  export PATH=$PATH:~/.local/bin/

.. Tip::
    You will have to run the above commend for every terminal you wish to launch
    QtPyVCP from, a more convenient solution is to append the following line
    to your bash ``~/.profile``:
    ``PATH=$PATH:~/.local/bin/``


Testing the Install
^^^^^^^^^^^^^^^^^^^

Confirm that QtPyVCP installed correctly and is available by running::

  qtpyvcp -h

This will print a list of command line options it the installation was
successful.

QtDesigner Plug-ins (development only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order for the QtDesigner plugins to load, you must have the correct version
of ``libpyqt5.so`` in ``/usr/lib/x86_64-linux-gnu/qt5/plugins/designer/``. This library
must be compiled for the specific architecture, Qt version and Python version you
are using. One way to get this file is to build PyQt5 from source, following the
procedure `here <https://gist.github.com/KurtJacobson/34a2e45ea2227ba58702fc1cb0372c40>`_.

If you can find a pre-compiled version, then you should be able simply place it
in ``/usr/lib/x86_64-linux-gnu/qt5/plugins/designer/`` and be good to go. A
compiled version of ``libpyqt5.so`` suitable for use on a 64bit Debian stretch
system with Python2.7 and Qt 5.7.1 is included in the QtDesigner directory.
