=============
Installation
=============

.. Note ::
    In order to use QtPyVCP you will need to have LinuxCNC ~2.8pre (master)
    installed, either system wide or as a Run In Place (RIP) built from source.

The are multiple ways to install QtPyVCP, which one is best depends on how
you intend to use QtPyVCP. If you are not interested in development then
it is best is to install with pip per the :doc:`Quick Start <quick_start>` guide.


Installing from Debian package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning ::
    The QtPyVCP Debian packages are experimental, and may be missing some
    dependencies. Installing via pip is the preferred installation method.

Download the latest release here: https://github.com/kcjengr/qtpyvcp/releases

Install by saying::

  sudo apt install /path/to/download.deb

or::

  sudo dpkg -i /path/to/download.deb


Development Install
^^^^^^^^^^^^^^^^^^^

If you intend to contribute to QtPyVCP or make your own VCPs
then you will need a development install. This type of installation
is editable, meaning you can make changes to the source files and the
changes will take effect when QtPyVCP is next run, without the need to
reinstall.


Getting the QtPyVCP Source Code
+++++++++++++++++++++++++++++++

If you intend to contribute to QtPyVCP you should clone the
`QtPyVCP repository <https://github.com/kcjengr/qtpyvcp>`_ with git::

  git clone https://github.com/kcjengr/qtpyvcp qtpyvcp

Otherwise you can simply download the source code archive:
:download:`qtpyvcp-master.tar.gz <https://github.com/kcjengr/qtpyvcp/tarball/master>`


Install Dev Dependencies
++++++++++++++++++++++++

Development dependencies::

  sudo apt install python-pyqt5 python-pyqt5.qtopengl python-pyqt5.qsci python-dbus.mainloop.pyqt5 qttools5-dev-tools qttools5.dev pyqt5-dev-tools python-pyqt5.qtmultimedia gstreamer1.0-plugins-bad libqt5multimedia5-plugins python-pip git


For building documentation::

  pip install sphinx sphinx_rtd_theme mock

(From the docs dir run ``make html`` to build the HTML documentation.)


**Note:** *We try to keep this up to date, but if you find additional
dependencies are needed please notify one of the developers so it
can be added.*


Install with pip
+++++++++++++++++++++

From the qtpyvcp source directory install QtPyVCP by running::

  pip install --editable .

This will create a setup.py development install and will add command line scripts to
``~/.local/bin/`` for launching QtPyVCP, the example VCPs and the command line tools.

.. note ::
    On Debian 9 (Stretch) ``~/.local/bin/`` is not on the PATH due to a regression in bash.
    This prevents being able to launch qtpyvcp from the command line or being able to use it
    as the ``[DISPLAY]DISPLAY`` directive in the LinuxCNC INI file. For a single shell session
    you can get around this by running ``export PATH=$PATH:~/.local/bin/`` before launching
    linuxcnc or any qtpyvcp commands.

    A more permanent solution is to copy the `.xsessionrc` file from the `qtpyvcp/scripts`
    directory into your home direcotry, then log out and log back in. This will add
    ``~/.local/bin/`` to your PATH each time xwindows starts.


Testing the Install
^^^^^^^^^^^^^^^^^^^

Confirm that QtPyVCP installed correctly and is available by running::

  qtpyvcp -h

This will print a list of command line options if the installation was
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
