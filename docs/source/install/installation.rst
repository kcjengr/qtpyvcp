===================
Development Install
===================

If you wish to contribute to the project you need to do a develpment install.

**Requirements**

Debian 9 64 bit or Linux Mint 19 64 bit with LinuxCNC 2.8 (master) installed,
either system wide or as a Run In Place (RIP) built from source.

Instructions for installing on Debian 9 (stretch) and other distros can be
found here: https://gnipsel.com/linuxcnc/uspace/debian9-emc.html

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

Development dependencies (in addition to those listed in the :doc:`Quick Start <quick_start>`) ::

  sudo apt install qttools5.dev qttools5-dev-tools wheel

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
    If the pip install fails make sure you uninstall before trying to install
    again. ``pip uninstall qtpyvcp``

.. note ::
    On Debian 9 (Stretch) ``~/.local/bin/`` is not on the PATH due to a regression in bash.
    This prevents being able to launch qtpyvcp from the command line or being able to use it
    as the ``[DISPLAY]DISPLAY`` directive in the LinuxCNC INI file. For a single shell session
    you can get around this by running ``export PATH=$PATH:~/.local/bin/`` before launching
    linuxcnc or any qtpyvcp commands.

    A more permanent solution is to copy the `.xsessionrc` file from the
    `qtpyvcp/scripts` directory into your home direcotry, then log out and log
    back in. This will add ``~/.local/bin/`` to your PATH each time xwindows
    starts. In the file manager select View > Show Hidden Files in order to see
    files that start with a dot like `.xsessionrc`.


Testing the Install
^^^^^^^^^^^^^^^^^^^

Confirm that QtPyVCP installed correctly and is available by running::

  qtpyvcp -h

This will print a list of command line options if the installation was
successful.

QtDesigner Plug-ins
^^^^^^^^^^^^^^^^^^^

If you want to edit a VCP or create one from a template you need to have the
QtDesigner plugins installed. To load, you must have the correct version of
`libpyqt5.so` in `/usr/lib/x86_64-linux-gnu/qt5/plugins/designer/`. Precompiled
libraries suitable for 64Bit Debian Stretch (or other system with Qt v5.7.1 and
Py v2.7) are included in the `QtDesigner` directory. The easiest way to install
the libs to the correct location is to use the `install.sh` script located in
the `qtpyvcp/pyqt5designer/Qt5.7.1-64bit` directory with this command.
::

    sudo ./install.sh

If you are using a different architecture or Qt version you may need to compile PyQt5 from
source to get the proper `libpyqt5.so` file. The steps should be similar those listed
`here <https://gist.github.com/KurtJacobson/34a2e45ea2227ba58702fc1cb0372c40>`_.

Trouble shooting
^^^^^^^^^^^^^^^^

If you get an error about `Make sure that you have the correct version of the
libpyqt5.so` you probably installed the stock version of Qt Designer over the
QtPyVCP version. To fix that just install libpyqt5 with the install script.
