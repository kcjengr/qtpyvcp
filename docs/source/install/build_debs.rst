=====================
Build debian packages
=====================


In this example we are going show how to build debian packages for qtpyvcp, it uses poetry to configure the build and installation and debian config files



Upgrade the system


.. code:: sh

	$ sudo apt update
	$ sudo apt upgrade


Requirements


.. code:: sh

	$ sudo apt install git python3-poetry pybuild-plugin-pyproject debhelper dh-python devscripts libqt5multimedia5-plugins --no-install-recommends --no-install-suggests


Download qtpyvcp sources


.. code:: sh

   $ git clone https://github.com/kcjengr/qtpyvcp/
   $ git clone https://github.com/kcjengr/monokrom/
   
 

Create a changelog file


.. code:: sh

   $ cd qtpyvcp
   $ dch --create --distribution unstable --package qtpyvcp --newversion 0.1-2 Experimental Release version.


Build the deb file


.. code:: sh

   $ dpkg-buildpackage -b -uc


If all went ok deb should be in the parent directory


Install debs


.. code:: sh

   $ sudo dpkg -i python3-qtpyvcp-0.1-2.deb

