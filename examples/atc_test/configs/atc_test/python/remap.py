#   This is a component of LinuxCNC
#   Copyright 2011, 2012, 2013, 2014 Dewey Garrett <dgarrett@panix.com>,
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

import linuxcnc

from interpreter import *
import emccanon

# from stdglue import *

COMMAND = linuxcnc.command()



def change_prolog(self, **words):
    print("change_prolog", words)

    return INTERP_OK


def change_epilog(self, **words):
    print("change_epilog", words)

    return INTERP_OK


def m6(self, **words):
    print("m6 called", words)

    return INTERP_OK


def m10(self, **words):
    print("m10 called", words)

    return INTERP_OK


def m11(self, **words):
    print("m11 called", words)

    COMMAND.set_digital_output(4, 1)

    return INTERP_OK


def m12(self, **words):
    print("m12 called", words)

    COMMAND.set_digital_output(4, 0)

    return INTERP_OK


def m13(self, **words):
    print("m13 called Homing ATC", words)

    return INTERP_OK


def m21(self, **words):
    print("m21 called", words)

    return INTERP_OK


def m22(self, **words):
    print("m22 called", words)

    return INTERP_OK


def m23(self, **words):
    print("m23 called", words)

    return INTERP_OK


def m24(self, **words):
    print("m24 called")

    return INTERP_OK


def m25(self, **words):
    print("m25 called")

    return INTERP_OK


def m26(self, **words):
    print("m26 called")

    return INTERP_OK
