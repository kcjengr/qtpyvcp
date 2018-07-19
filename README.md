# QtPyVCP

Qt5 based LinuxCNC interface

![](docs/screenshots/demo.png)

## Dependencies
  * Python 2.7
  * Qt 5
  * PyQt 5

### For use only
`sudo apt-get install python-pyqt5`  

### For development/screen editing
`sudo apt-get install qttools5-dev-tools`  
`sudo apt-get install qttools5.dev`  
`sudo apt-get install pyqt5-dev-tools`  


In order for the QtDesigner plugins to load, you must have the correct version
of `libpyqt5.so` in `/usr/lib/x86_64-linux-gnu/qt5/plugins/designer/`. This library
must be compiled for the specific architecture, Qt version and Python version you
are using. One way to get this file is to build PyQt5 from source, following the
procedure here: https://gist.github.com/KurtJacobson/34a2e45ea2227ba58702fc1cb0372c40

If you can find a pre-compiled version, then you should be able simply place it
in `/usr/lib/x86_64-linux-gnu/qt5/plugins/designer/` and be good to go. A compiled
 version of `libpyqt5.so` suitable for use on a 64bit Debian stretch system
with Python2.7 and Qt 5.7.1 is included in the QtDesigner directory.
