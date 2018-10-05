# Dependencies

These are the dependencies needed to run QyPyVCP or a VCP built with
it on Debian 9 (Stretch) systems.

In addition you will need to have LinuxCNC ~2.8pre (master) installed, either
system wide or as a Run In Place (RIP) built from source.  

## For production use (non development)

These dependencies are needed for running QtPyVCP, VCPs may have
additional dependencies.

Core dependencies:  
`sudo apt-get install python-pyqt5`  
`sudo apt-get install python-dbus.mainloop.pyqt5`  
`sudo apt-get install python-pyqt5.qtopengl`  
`sudo apt-get install python-pyqt5.qsci`  
`sudo apt-get install python-docopt`  

Required for Camera widget:  
`sudo apt-get install python-pyqt5.qtmultimedia`  
`sudo apt-get install gstreamer1.0-plugins-bad`  
`sudo apt-get install libqt5multimedia5-plugins`  

Required for FileSytem widget:  
`sudo apt-get install python-pyudev`  
`sudo apt-get install python-psutil`  


## Development dependencies

Required for QtPyVCP and VCP development:  
`sudo apt-get install qttools5-dev-tools`  
`sudo apt-get install qttools5.dev`  
`sudo apt-get install pyqt5-dev-tools`  

Required for building documentation:  
`pip install mkdocs`  
`pip install mkdocs-material`  

Run `mkdocs build` or `mkdocs serve` to preview docs.  

**Note:** _We try to keep this up to date, but if additional
dependencies are needed please notify one of the developers
so it can be added._
