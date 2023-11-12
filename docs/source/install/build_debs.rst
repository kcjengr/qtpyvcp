=====================
Build debian packages
=====================


In this example we are gona show how to build debian packages for qtpyvcp, it uses poetry to configure the build and installation and debian config files



Upgrade the system


.. code:: sh

	$ sudo apt update
	$ sudo apt upgrade


Requirements


.. code:: sh

	$ sudo apt install python3-poetry pybuild-plugin-pyproject git debhelper dh-python libudev-dev tcl8.6-dev tk8.6-dev bwidget tclx libeditreadline-dev asciidoc dblatex docbook-xsl dvipng ghostscript graphviz groff imagemagick inkscape python3-lxml source-highlight w3c-linkchecker xsltproc texlive-extra-utils texlive-font-utils texlive-fonts-recommended texlive-lang-cyrillic texlive-lang-french texlive-lang-german texlive-lang-polish texlive-lang-spanish texlive-latex-recommended asciidoc-dblatex python3-dev python3-tk libxmu-dev libglu1-mesa-dev libgl1-mesa-dev libgtk2.0-dev libgtk-3-dev gettext intltool autoconf libboost-python-dev libmodbus-dev libusb-1.0-0-dev psmisc yapps2 libepoxy-dev python3-xlib python3-pyqt5 python3-dbus.mainloop.pyqt5 python3-pyqt5.qtopengl python3-pyqt5.qsci python3-pyqt5.qtmultimedia python3-pyqt5.qtquick qml-module-qtquick-controls gstreamer1.0-plugins-bad  libqt5multimedia5-plugins pyqt5-dev-tools python3-dev python3-setuptools python3-wheel python3-pip python3-yapps dpkg-dev python3-serial libtk-img qttools5-dev qttools5-dev-tools python3-wheel espeak espeak-data espeak-ng freeglut3 gdal-data gstreamer1.0-tools libaec0 libarmadillo10 libarpack2 libcfitsio9 libcharls2 libdap27 libdapclient6v5 libespeak1 libfreexl1 libfyba0 libgdcm3.0 libgeos-c1v5 libgeotiff5 libgif7 libgtksourceview-3.0-dev libhdf4-0-alt libhdf5-103-1 libhdf5-hl-100 libimagequant0 libkmlbase1 libkmldom1 libkmlengine1 liblept5 libmariadb3 libminizip1 libodbc1 libogdi4.1 libportaudio2 libpq5 libprotobuf23 libqhull8.0 librttopo1 libsocket++1 libspatialite7 libsuperlu5 libsz2 libtbb2 libtesseract4 liburiparser1 libxerces-c3.2 libxml2-dev mariadb-common mesa-utils mysql-common odbcinst odbcinst1debian2 proj-bin proj-data python3-configobj python3-espeak python3-gi-cairo python3-olefile python3-opencv python3-opengl python3-pil python3-pil.imagetk python3-pyqt5.qtsvg python3-pyqt5.qtwebkit tcl-tclreadline geotiff-bin gdal-bin glew-utils libgtksourceview-3.0-doc libhdf4-doc libhdf4-alt-dev hdf4-tools odbc-postgresql tdsodbc ogdi-bin python-configobj-doc libgle3 python-pil-doc python3-sqlalchemy


Download qtpyvcp sources


.. code:: sh

   $ git clone https://github.com/kcjengr/qtpyvcp/
   $ git clone https://github.com/kcjengr/monokrom/
   
 

Create a changelog file


.. code:: sh

   $ cd qtpyvcp
   $ dch --create --distribution unstable --package qtpyvcp --newversion 0.1-2 Experimental Release version."


Build the deb file


.. code:: sh

   $ dpkg-buildpackage", "-b", "-uc


If all went ok deb should be in the parent directory


Install debs


.. code:: sh

   $ sudo dpkg -i python3-qtpyvcp-0.1-2.deb

