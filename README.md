![](https://www.qtpyvcp.com/_static/qtpyvcp_logo_small.png)

# QtPyVCP - QtPy Virtual Control Panel
[![Travis CI][Travis-badge]](https://travis-ci.org/kcjengr/qtpyvcp)
[![pypi version][pypi-badge]](https://pypi.org/project/QtPyVCP/)
[![LinuxCNC 2.8][linuxcnc-badge]](https://github.com/LinuxCNC/linuxcnc)


QtPyVCP is a Qt and Python based framework for building virtual control panels
for the LinuxCNC machine control.

The goal is to provide a no-code, drag-and-drop system for making simple VCPs,
as well as a straightforward, flexible and extensible framework to aid in
building complex VCPs.

## Warning Python2.7

QtPyVCP master branch is now python 3 only

Requires debian 11

Do I need to install master branch?

Only if you want to use linuxcnc 2.9.0~pre or help porting qtpyvcp to python3

Master branch is our develop channel, we offer stable releases but none yet for Python3,
latest python2 release is 0.3.19

a maintenance branch for python2.7 is keept until linuxcnc 2.9 is released

to install it you need to run as user

```
python2.7 -m pip install -U git+https://github.com/kcjengr/qtpyvcp@python2_maintenance
```



How does affect your VCP?
  You only need to run `2to3.py` in your VCP root directory

In runtime mode how does affect my configs?

Nothing it should be transparent

I have python component
run `2to3.py`in yor component directory


## Installation and Usage

What I need to install?
You may need a linuxcnc 2.9.0~pre or latter
detailed packages requiered for `runtime` or `develop` are described here:
https://www.qtpyvcp.com/install/prerequisites.html

See the [documentation](https://www.qtpyvcp.com/).


## Development

* [GitHub Repo](https://github.com/kcjengr/qtpyvcp/)
* [Issue Tracker](https://github.com/kcjengr/qtpyvcp/issues)

## Documentation and Help

* [Documentation](https://www.qtpyvcp.com)
* [LinuxCNC Forum](https://forum.linuxcnc.org/qtpyvcp)
* [libera.chat IRC](http://web.libera.chat/) (#qtpyvcp)
* [The Matrix](https://app.element.io/#/room/#qtpyvcp:matrix.org) (#qtpyvcp:matrix.org)
* [Discord](https://discord.gg/463hMhd)


## Dependencies

* LinuxCNC 2.9-pre^
* Python 3.9^
* Qt 5.12^
* PyQt5 or PySide2

QtPyVCP is developed and tested using the Debian 11 x64 (bullseye).
It should run on any system that can have PyQt5 installed, but Debian 11 x64 is the only OS
that is officially supported.


## DISCLAIMER

THE AUTHORS OF THIS SOFTWARE ACCEPT ABSOLUTELY NO LIABILITY FOR
ANY HARM OR LOSS RESULTING FROM ITS USE.  IT IS _EXTREMELY_ UNWISE
TO RELY ON SOFTWARE ALONE FOR SAFETY.  Any machinery capable of
harming persons must have provisions for completely removing power
from all motors, etc, before persons enter any danger area.  All
machinery must be designed to comply with local and national safety
codes, and the authors of this software can not, and do not, take
any responsibility for such compliance.

This software is released under the GPLv2.
