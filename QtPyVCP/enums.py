#!/usr/bin/env python

class Axis(object):
    ALL = -1
    X, Y, Z, A, B, C, U, V, W = range(9)

class ReferenceType(object):
    Absolute = 0
    Relative = 1
    DistanceToGo = 2

class Units(object):
    Program = 0 # Use program units
    Inch = 1    # CANON_UNITS_INCHES=1
    Metric = 2  # CANON_UNITS_MM=2

class Permission(object):
    Always = 0
    WhenRunning = 1
    WhenMoving = 2
    WhenHoming = 3
    WhenIdle = 4
