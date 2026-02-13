========================
Python 2.7 Legacy Notice
========================

.. warning::

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
run `2to3.py` in yor component directory

