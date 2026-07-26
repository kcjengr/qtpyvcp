===========================
Install from apt repository
===========================

Update the System
^^^^^^^^^^^^^^^^^

    .. code-block:: bash

        sudo apt update
        sudo apt upgrade


Add the APT Repository
^^^^^^^^^^^^^^^^^^^^^^

    Run the following command. It detects your Debian release (Bookworm or
    Trixie) and your architecture (AMD64 or ARM64) and configures the
    correct repository and signing key for you:

    .. code-block:: bash

        curl -fsSL https://repository.qtpyvcp.com/install.sh | sudo sh

    .. note::

        Do not add the repository by hand. Adding the wrong suite for your
        Debian release installs packages built for the wrong Qt version,
        and putting the signing key in the wrong place causes
        ``apt update`` to fail with a "Missing key" error.

    .. warning::

        If ``apt update`` already reports::

            Missing key 50F874571F20C5B0BA225E2F0CDFCCE0388CFA48, which is needed to verify signature.

        your machine has an old or incomplete repository configuration.
        Clear it out first, then run the install command above:

        .. code-block:: bash

            curl -fsSL https://repository.qtpyvcp.com/uninstall.sh | sudo sh

        This removes only this repository's configuration, keys and
        packages. Other repositories on your machine and your LinuxCNC
        configs in ``~/linuxcnc`` are left untouched.


Install QtPyVCP
^^^^^^^^^^^^^^^

    .. code-block:: bash

        sudo apt update
        sudo apt install python3-qtpyvcp


Install a VCP
^^^^^^^^^^^^^

    There are three VCPs in the repository. They all come from the same
    repository you just added, so no extra setup is needed:

    .. code-block:: bash

        sudo apt install python3-probe-basic
        sudo apt install python3-monokrom
        sudo apt install python3-turbonc


Updating
^^^^^^^^

    QtPyVCP and the VCPs update through normal APT upgrades:

    .. code-block:: bash

        sudo apt update
        sudo apt upgrade


Uninstall
^^^^^^^^^

    To completely remove QtPyVCP and all VCPs (Probe Basic, TurboNC,
    MonoKrom), along with the APT repository and its signing key, run:

    .. code-block:: bash

        curl -fsSL https://repository.qtpyvcp.com/uninstall.sh | sudo sh

    This works even if ``apt update`` is currently failing. It removes only
    this repository's packages, sources and keys -- other repositories on
    your machine, and your LinuxCNC configs in ``~/linuxcnc``, are left
    untouched.
