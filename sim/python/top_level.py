#   This is a component of LinuxCNC
#   Copyright 2011, 2013, 2014 Dewey Garrett <dgarrett@panix.com>,
#   Michael Haberler <git@mah.priv.at>, Norbert Schechner <nieson@web.de>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import imp
import os
import sys

import emccanon
import interpreter


def __init__(self):
    print("__init__")

    print(imp.find_module('emccanon'))
    print(imp.find_module('interpreter'))

    print(sys.modules['emccanon'])
    print(sys.modules['interpreter'])

    print(sys.builtin_module_names)

    print(interpreter.__dict__)

    print('\n'.join(sys.path))

    print(sys.exec_prefix)
    print("Python version")
    print (sys.version)
    print("Version info.")
    print (sys.version_info)

    emc_methods = [name for name, val in emccanon.__dict__.iteritems() if callable(val)]
    interp_methods = [name for name, val in interpreter.__dict__.iteritems() if callable(val)]

    print(emc_methods)
    print(interp_methods)

    print(self.params[5190])
    print(self.params[5191])
    print(self.params[5192])
    print(self.params[5193])
    print(self.params[5194])
    print(self.params[5195])
    print(self.params[5196])
    print(self.params[5197])
    print(self.params[5198])
    print(self.params[5199])
    print(self.params[5200])
    print(self.params[5201])

    if hasattr(interpreter, 'this'):
        if self is not interpreter.this:
            print("__init__: self not is this")
    else:
        print("__init__: no 'this' attribute")
