# Installing

## Getting the source code
The easiest way to get QtPyVCP is to clone the
[QtPyVCP repository](https://github.com/kcjengr/qtpyvcp) with git.
If you don't have git installed you can simply download the QtPyVCP .zip file
using the green **Clone or download** button, but this will make it harder
to update in the future.

To clone the repository open a terminal at the desired location and say:  
`git clone https://github.com/kcjengr/qtpyvcp qtpyvcp`  


Enter the newly cloned directory:  
`cd qtpyvcp`


## Install using setup.py

!!! note
    At this point only `setup.py develop` is supported. `setup.py install`
    and virtual environments may work but are untested.

You need to have the python 2.7 setup tools installed, if you don't or are
not sure run:  
`sudo apt-get install python-setuptools`

Then install by running:  
`python setup.py develop --user`

This will install QtPyVCP on your PYTHONPATH and will generate command line
scripts for launching QtPyVCP, the example VCPs and the command line tools.

If you used the `--user` flag the scripts will be placed in `~/.local/bin/`,
which is not on the PATH on Debian 9 (Stretch). You can add `~/.local/bin/`
to the current PATH by running:  
`export PATH=$PATH:~/.local/bin/`

!!! tip
    You will have to run the above commend for every terminal you wish to run
    QtPyVCP from, a more convenient solution is to append the following line
    to your bash `~/.profile`:  
    `PATH=$PATH:~/.local/bin/`

## Testing the install
Confirm that QtPyVCP installed correctly and is available by saying:  
`qtpyvcp -h`  

This will print a list of command line options it the installation was
successful.  

## QtDesigner Plug-ins (development only)
In order for the QtDesigner plugins to load, you must have the correct version
of `libpyqt5.so` in `/usr/lib/x86_64-linux-gnu/qt5/plugins/designer/`. This library
must be compiled for the specific architecture, Qt version and Python version you
are using. One way to get this file is to build PyQt5 from source, following the
procedure here: https://gist.github.com/KurtJacobson/34a2e45ea2227ba58702fc1cb0372c40

If you can find a pre-compiled version, then you should be able simply place it
in `/usr/lib/x86_64-linux-gnu/qt5/plugins/designer/` and be good to go. A compiled
 version of `libpyqt5.so` suitable for use on a 64bit Debian stretch system
with Python2.7 and Qt 5.7.1 is included in the QtDesigner directory.
