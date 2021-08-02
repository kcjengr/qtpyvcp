# Building PyQt5 to support Python2 based QtDesigner Plugins

As far as I can tell, the reason Qt5 Designer does not load custom PyQt5 widgets
is due to the 'stock' shared library `libpyqt5.so` (which comes with PyQt5) not
being built for the correct combination of the Python and Qt versions.  It seems
the only way to get around this is to build PyQt5 from source so we will have a
`libpyqt5.so` that is correct and will be able to load the custom widgets.


## Install Python dev tools

I don't know if this is necessary, I already had it installed  
`$ sudo apt-get install libpython-dev`


## Build and install SIP

SIP is a Python/C++ bindings generator used to build the bindings for PyQt.
Stretch seems to have SIP 4.18, but PyQt5.7.1 needs SIP 4.19, so build from source.

```
$ wget https://sourceforge.net/projects/pyqt/files/sip/sip-4.19/sip-4.19.tar.gz
$ tar xzvf sip-4.19.tar.gz
$ cd sip-4.19
$ python configure.py
$ make
$ sudo make install
```

## Set the right Qt version

On my system I have both Qt4 and Qt5 installed. But on stretch Qt4 is the default
so we have to set up the environment to use Qt5 before trying to build PyQt5.

Make sure Qt5 is installed:  
`$ qtchooser -list-versions`

Select the Qt version:  
`$ export QT_SELECT=qt5`

Check qmake version:  
`$ qmake --version`

This should say
```
QMake version 3.0
Using Qt version 5.7.1 in /usr/lib/x86_64-linux-gnu
```

## Build and install PyQt5
```
$ wget https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.7.1/PyQt5_gpl-5.7.1.tar.gz
$ tar xzvf PyQt5_gpl-5.7.1.tar.gz
$ cd PyQt5_gpl-5.7.1
$ python configure.py
$ make
$ sudo make install
```

## Launch Qt5 Designer

Use the `PYQTDESIGNERPATH` environment variable to tell QtDesiner where to look
for the plugins  
`$ export PYQTDESIGNERPATH='/path/to/plugin/directory/'`  

Launch Qt5 Designer  
`$ qtchooser -run-tool=designer -qt=5`  


## References
https://www.ics.com/blog/integrating-python-based-custom-widget-qt-designer  
https://harishnavnit.wordpress.com/2014/03/24/handling-multiple-versions-of-qt