#!/usr/bin/env python

import os

def normalizePath(path, base):
    if path is None:
        return
    path = os.path.expandvars(path)
    if path.startswith('~'):
        path = os.path.expanduser(path)
    elif not os.path.isabs(path):
        path = os.path.join(base, path)
    return os.path.realpath(path)
