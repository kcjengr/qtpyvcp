===========================
Install from apt repository
===========================



Add the APT Repository for the Installation type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    **AMD64 for PC Installation Repository:**
    
        Run the following commands in the main terminal one at a time:

        .. code-block:: bash

            sudo apt install curl


            echo 'deb [arch=amd64] https://repository.qtpyvcp.com/apt stable main' | sudo tee /etc/apt/sources.list.d/kcjengr.list


            curl -sS https://repository.qtpyvcp.com/repo/kcjengr.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/kcjengr.gpg


            gpg --keyserver keys.openpgp.org --recv-key 2DEC041F290DF85A



    
    **NEW - ARM64 Raspberry Pi 4 and 5 Installation Repository:**
    
        Run the following commands in the main terminal one at a time:

        .. code-block:: bash

            sudo apt install curl


            echo 'deb [arch=arm64] https://repository.qtpyvcp.com/apt stable main' | sudo tee /etc/apt/sources.list.d/kcjengr.list


            curl -sS https://repository.qtpyvcp.com/repo/kcjengr.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/kcjengr.gpg


            gpg --keyserver keys.openpgp.org --recv-key 2DEC041F290DF85A



.. code:: sh

	$ sudo apt update


Install qtpyvcp


.. code:: sh

	$ sudo apt install python3-qtpyvcp


Install some vcps, for now there are 3 in the repository

Probe Basic
Monokrom
Turbonc

to install them just run


.. code:: sh
	
	$ sudo apt install python3-probe-basic
	$ sudo apt install python3-monokrom
	$ sudo apt install python3-turbonc


