=================
Developer Install
=================

The developer install puts the QtPyVCP source code in ``~/dev/qtpyvcp`` and
runs it from a Python virtual environment in ``~/dev/venv``. Changes you make
to the source take effect the next time QtPyVCP starts.

An installer script does the work. Use the one for your Debian release:

==================  ==============================  ====================  ========
Debian release      Installer                       QtPyVCP branch        Python
==================  ==============================  ====================  ========
13 Trixie           ``qtpyvcp-trixie-installer``    ``pyside6`` (Qt 6)    3.13
12 Bookworm         ``qtpyvcp-bookworm-installer``  ``main`` (Qt 5)       3.11
==================  ==============================  ====================  ========

The virtual environment is built from the Python the Debian release
ships, so there is nothing to choose.

Both installers ask whether to install **QtPyVCP** only, or **both** QtPyVCP
and Probe Basic.

.. note::

    If you only want to run QtPyVCP or Probe Basic, the
    :doc:`apt install <apt_install>` is simpler and updates with your system.


Debian 13 Trixie
----------------

1. Install LinuxCNC
^^^^^^^^^^^^^^^^^^^

On a new machine the easiest start is the LinuxCNC 2.9.10 ISO. It installs
Debian 13 Trixie with LinuxCNC and the realtime kernel:

https://www.linuxcnc.org/iso/linuxcnc_2.9.10-amd64.hybrid.iso

If Debian 13 is already installed without LinuxCNC, the installer offers to
install it for you.

2. Get the installer
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo apt install git
    mkdir -p ~/dev
    cd ~/dev
    git clone https://github.com/Lcvette/qtpyvcp-trixie-installer.git

3. Run the installer
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    cd ~/dev/qtpyvcp-trixie-installer
    ./install_for_qtpyvcp.sh

It asks for your password, then:

- If QtPyVCP or Probe Basic is installed from apt, it offers to remove them.
  Choose **REMOVE AND CONTINUE** -- the two installs conflict.
- If LinuxCNC is missing, it offers to install it.
- Choose **QTPYVCP** for QtPyVCP only, or **BOTH** to add Probe Basic.
- At the end it asks to reboot. Reboot before using QtPyVCP.


Debian 12 Bookworm
------------------

1. Install LinuxCNC
^^^^^^^^^^^^^^^^^^^

Download the LinuxCNC package for your machine:

- PC (amd64):
  https://www.linuxcnc.org/dists/bookworm/2.9-uspace/binary-amd64/linuxcnc-uspace_2.9.10_amd64.deb
- Raspberry Pi 4/5 (arm64):
  https://www.linuxcnc.org/dists/bookworm/2.9-uspace/binary-arm64/linuxcnc-uspace_2.9.10_arm64.deb

Install it, then restart your computer. On a Pi use the ``arm64`` file name:

.. code-block:: bash

    cd ~/Downloads
    sudo apt install ./linuxcnc-uspace_2.9.10_amd64.deb

2. Remove any apt install of QtPyVCP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Skip this if you have never used the QtPyVCP apt repository.

The apt install and the developer install conflict, so remove the apt one
first. This also removes Probe Basic, TurboNC and MonoKrom if they came from
apt:

.. code-block:: bash

    curl -fsSL https://repository.qtpyvcp.com/uninstall.sh | sudo sh

3. Get the installer
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo apt install git zenity
    mkdir -p ~/dev
    cd ~/dev
    git clone https://github.com/Lcvette/qtpyvcp-bookworm-installer.git

4. Run the installer
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    cd ~/dev/qtpyvcp-bookworm-installer
    ./install_for_qtpyvcp.sh

- Choose **QTPYVCP** for QtPyVCP only, or **BOTH** to add Probe Basic.
- At the end it asks to reboot. Reboot before using QtPyVCP.

If you chose **QTPYVCP**, run this once so new terminals use the virtual
environment. **BOTH** does it for you:

.. code-block:: bash

    echo "source ~/dev/venv/bin/activate" >> ~/.bashrc


Check the Install
-----------------

Open a new terminal and run:

.. code-block:: bash

    qtpyvcp -h

It prints the command line options. If it says ``command not found``, the
virtual environment is not active in that terminal. Run
``source ~/dev/venv/bin/activate`` and try again.


Using the Developer Install
---------------------------

- **Start LinuxCNC from a terminal.** The terminal has the virtual environment
  active. The desktop menu does not, so LinuxCNC started from the menu cannot
  find your development copy of QtPyVCP.
- **Sim configs** to try it with: see :doc:`basic_usage`.
- **Edit a VCP** in Qt Designer with ``editvcp``: see :doc:`/tools/editvcp`.


Updating
--------

From the installer folder:

.. code-block:: bash

    cd ~/dev/qtpyvcp-trixie-installer
    ./updater.sh

On Bookworm use ``qtpyvcp-bookworm-installer``. This pulls the latest source
and rebuilds it.


Uninstall
---------

Delete the folders the installer created, and remove its line from
``~/.bashrc``:

.. code-block:: bash

    rm -rf ~/dev/venv ~/dev/qtpyvcp ~/dev/qtpyvcp-trixie-installer
    sed -i '/[Dd]ev\/venv\/bin\/activate/d' ~/.bashrc

On Bookworm use ``qtpyvcp-bookworm-installer`` in the first line. If you also
installed Probe Basic, add ``~/dev/probe_basic`` to it.

Anything else in ``~/dev``, LinuxCNC itself, and your configs in
``~/linuxcnc`` are not touched.
