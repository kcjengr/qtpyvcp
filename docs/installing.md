# Installing

## Development install using setup.py

!!! note
    At this point only `setup.py develop` is supported. `setup.py install`
    and virtual environments may work but are untested.

You need to have the python 2.7 setup tools installed, if you don't or are not
sure run:  
`sudo apt-get install python-setuptools`

Then install by running:  
`python setup.py develop --user`

This will install QtPyVCP on your PYTHONPATH and will generate command line
scripts for launching QtPyVCP, the example VCPs and the command line tools.

If you used the `--user` flag the scripts will be placed in `~/.local/bin/`,
which is not on the PATH on Debian 9 (Stretch). You can add `~/.local/bin/`
to the current PATH by running:  
`export PATH=$PATH:~/.local/bin/`

You will have to run the above commend for every terminal you wish to run
QtPyVCP from, so a more convenient solution is to append the following line
to your `~/.profile` file:  
`PATH=$PATH:~/.local/bin/`

## Running QtPyVCP
You can check if QtPyVCP installed correctly by saying:  
`qtpyvcp -h`

This should print a list of command line options.  

## Launching a sim config
From the QtPyVCP directory you can launch the included XYZ sim config by sying:  
`linuxcnc sim/xyz.ini`
