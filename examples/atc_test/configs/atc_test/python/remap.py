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
import traceback

import emccanon
from interpreter import INTERP_OK, INTERP_EXECUTE_FINISH
from util import lineno


throw_exceptions = 1 # raises InterpreterException if execute() or read() fail

def queuebuster(self, **words):
    yield INTERP_EXECUTE_FINISH


def change_prolog(self, **words):
    print("CHANGE PROLOG")
    try:
        if self.selected_pocket < 0:
            emccanon.MESSAGE("M6: no tool prepared")
            return

        if self.cutter_comp_side:
            emccanon.MESSAGE("Cannot change tools with cutter radius compensation on")
            return

        self.params["tool_in_spindle"] = self.current_tool
        self.params["selected_tool"] = self.selected_tool
        self.params["current_pocket"] = self.current_pocket
        self.params["selected_pocket"] = self.selected_pocket
        return INTERP_OK

    except Exception as e:
        print(e)
        return


def change_epilog(self, **words):
    print("CHANGE EPILOG")
    try:
        if self.return_value > 0.0:
            # commit change
            self.selected_pocket =  int(self.params["selected_pocket"])
            emccanon.CHANGE_TOOL(self.selected_pocket)
            # cause a sync()
            self.tool_change_flag = True
            self.set_tool_parameters()
            return INTERP_OK
        else:
            emccanon.MESSAGE("M6 aborted (return code {})".format(self.return_value))
            return

    except Exception as e:
        print("M6/change_epilog: {}".format(e))
        return


def m6(self, **words):

    if self.selected_tool == self.current_tool:
        emccanon.MESSAGE("Tool already in spindle")
        return

    emccanon.CLEAR_AUX_OUTPUT_BIT(0)  # reset enable, digital pin 0

    emccanon.SET_AUX_OUTPUT_VALUE(0, self.selected_pocket)  # tell the carousel which pocket to go, analog pin 0
    emccanon.SET_AUX_OUTPUT_BIT(0)  # immediately go to the selected pocket, digital pin 0

    emccanon.CHANGE_TOOL(self.selected_tool)  # put that tool in the spindle

    return INTERP_OK


def m10(self, **words):
    print("m10 called", words)

    return INTERP_OK


def m11(self, **words):
    print("m11 called", words)

    emccanon.SET_AUX_OUTPUT_BIT(5)  # jog carousel forward, digital pin 5

    return INTERP_OK


def m12(self, **words):
    print("m12 called", words)

    emccanon.SET_AUX_OUTPUT_BIT(6)  # jog carousel reverse, digital pin 6

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
