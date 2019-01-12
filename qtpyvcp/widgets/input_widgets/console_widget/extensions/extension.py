# -*- coding: utf-8 -*-
class ExtensionManager(object):
    def __init__(self, owner):
        self._owner = owner
        self._extension_dict = {}

    def install(self, ext_cls):
        ext = ext_cls()
        ext._ext_mngr = self
        ext.install()
        self._extension_dict[id(ext)] = ext


class Extension(object):
    #Abstract
    def install(self):
        pass

    def owner(self):
        return self._ext_mngr._owner
