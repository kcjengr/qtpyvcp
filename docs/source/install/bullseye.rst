=========================================
Debian 11 (Bullseye) install for python 3
=========================================

This installation method should be used if you want to run the latest
version of `QtPyVCP` under python 3 and Linuxcnc 2.9pre.

This type of installation is editable, meaning you can make changes to
the source files and the changes will take effect when `QtPyVCP` is next
run, without the need to manually update or reinstall anything.  This also
means you can update the `QtPyVCP` through the use of a git pull within the
`QtPyVCP` source directory.


.. Note::

    If you are **not** interested in development then it is simpler to
    install from PyPi per the :doc:`Standard Install <pypi_install>` guide.


**Note:** *We try to keep this up to date, but if you find additional
dependencies are needed please notify one of the developers so it
can be added.*

.. Note::
    These instructions are intended to support you performing an install
    into a clean Debian 11 (Bullseye) environment. The instructions have
    been crafted specifically with this in mind.


Install Into a Clean Debian-11 Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After you have completed a clean Debian 11 installation, log in and open a terminal window.
Then install the dependencies::

    sudo apt install -y geany grub-customizer git debhelper dh-python libudev-dev tcl8.6-dev tk8.6-dev bwidget tclx libeditreadline-dev asciidoc dblatex docbook-xsl dvipng ghostscript graphviz groff imagemagick inkscape python3-lxml source-highlight w3c-linkchecker xsltproc texlive-extra-utils texlive-font-utils texlive-fonts-recommended texlive-lang-cyrillic texlive-lang-french texlive-lang-german texlive-lang-polish texlive-lang-spanish texlive-latex-recommended asciidoc-dblatex python3-dev python3-tk libxmu-dev libglu1-mesa-dev libgl1-mesa-dev libgtk2.0-dev libgtk-3-dev gettext intltool autoconf libboost-python-dev libmodbus-dev libusb-1.0-0-dev psmisc yapps2 libepoxy-dev python3-xlib python3-pyqt5 python3-dbus.mainloop.pyqt5 python3-pyqt5.qtopengl python3-pyqt5.qsci python3-pyqt5.qtmultimedia python3-pyqt5.qtquick qml-module-qtquick-controls gstreamer1.0-plugins-bad  libqt5multimedia5-plugins pyqt5-dev-tools python3-dev python3-setuptools python3-wheel python3-pip python3-yapps dpkg-dev python3-serial libtk-img qttools5-dev qttools5-dev-tools python3-wheel espeak espeak-data espeak-ng freeglut3 gdal-data gstreamer1.0-tools libaec0 libarmadillo10 libarpack2 libcfitsio9 libcharls2 libdap27 libdapclient6v5 libepsilon1 libespeak1 libfreexl1 libfyba0 libgdal28 libgdcm3.0 libgeos-3.9.0 libgeos-c1v5 libgeotiff5 libgif7 libglew2.1 libgtksourceview-3.0-dev libhdf4-0-alt libhdf5-103-1 libhdf5-hl-100 libimagequant0 libkmlbase1 libkmldom1 libkmlengine1 liblept5 libmariadb3 libminizip1 libnetcdf18 libodbc1 libogdi4.1 libopencv-calib3d4.5 libopencv-contrib4.5 libopencv-core4.5 libopencv-dnn4.5 libopencv-features2d4.5 libopencv-flann4.5 libopencv-highgui4.5 libopencv-imgcodecs4.5 libopencv-imgproc4.5 libopencv-ml4.5 libopencv-objdetect4.5 libopencv-photo4.5 libopencv-shape4.5 libopencv-stitching4.5 libopencv-video4.5 libopencv-videoio4.5 libportaudio2 libpq5 libproj19 libprotobuf23 libqhull8.0 librttopo1 libsocket++1 libspatialite7 libsuperlu5 libsz2 libtbb2 libtesseract4 liburiparser1 libxerces-c3.2 libxml2-dev mariadb-common mesa-utils mysql-common odbcinst odbcinst1debian2 proj-bin proj-data python3-configobj python3-espeak python3-gi-cairo python3-olefile python3-opencv python3-opengl python3-pil python3-pil.imagetk python3-pyqt5.qtsvg python3-pyqt5.qtwebkit tcl-tclreadline geotiff-bin gdal-bin glew-utils libgtksourceview-3.0-doc libhdf4-doc libhdf4-alt-dev hdf4-tools odbc-postgresql tdsodbc ogdi-bin python-configobj-doc libgle3 python-pil-doc python3-pil-dbg python3-pil.imagetk-dbg python3-sqlalchemy

Create the working directories to hold linuxcnc source and qtpyvcp source::

    cd ~
    mkdir dev
    cd dev
    mkdir linuxcnc
    cd linuxcnc
    git clone git://github.com/linuxcnc/linuxcnc.git rip
    cd rip/src
    ./autogen.sh
    ./configure --with-realtime=uspace
    make -j4

To build the debian packages::

    cd ~/dev/linuxcnc/rip/debian
    ./configure uspace
    cd ..
    dpkg-buildpackage -b -uc
    cd ..

All the debain packages will now be in this directory (~/dev/linuxcnc).
To install the packages::

    sudo dpkg -i linuxcnc-uspace_2.9.0~pre0_amd64.deb
    sudo dpkg -i linuxcnc-doc-en_2.9.0~pre0_all.deb

If you wish to have documentation in another language please select the
appropriate .deb file.

Commence the installation of QtPyVCP::

    cd ~/dev
    git clone https://github.com/kcjengr/qtpyvcp
    cd qtpyvcp
    python3 -m pip install --editable .
    cp scripts/.xsessionrc ~/

Log out and log back in again. This is necessary to ensure .local/bin 
is now part of your execution search path.

Testing the Install
^^^^^^^^^^^^^^^^^^^

Confirm that QtPyVCP installed correctly and is available by running::

    qtpyvcp -h
    qtpyvcp -i

Setting up QTDesigner
^^^^^^^^^^^^^^^^^^^^^

To install the qtdesigner plugins::

    cd ~/dev/qtpyvcp/pyqt5designer/Qt5.15.2-64bit/python3.9/
    sudo ./install.sh


Setting up the Sims
^^^^^^^^^^^^^^^^^^^

To install the qtpyvcp sims::

    cp -r ~/dev/qtpyvcp/linuxcnc ~/



DONE!   Enjoy
^^^^^^^^^^^^^

