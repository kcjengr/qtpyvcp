#!/usr/bin/env python

import os

def normalizePath(path, base):
    if path is None or base is None:
        return
    path = os.path.expandvars(path)
    if path.startswith('~'):
        path = os.path.expanduser(path)
    elif not os.path.isabs(path):
        path = os.path.join(base, path)
    # if os.path.exists(path):
    return os.path.realpath(path)


def insertPath(env_var, index, file):
    files = os.getenv(env_var)
    if files is None:
        files =[]
    else:
        files.strip(':').split(':')
    print files
    files.insert(index, file)
    os.environ[env_var] = ':'.join(files)
    print os.environ[env_var]
