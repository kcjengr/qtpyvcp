#!/usr/bin/env python

import remap
import oword


def __init__(self,**words):
    print("{} words passed".format(len(words)))
    for w in words:
        print("{}: {}".format(w, words[w]))
