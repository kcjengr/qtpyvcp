# Copyright (c) 2017-2018, SLAC National Accelerator Laboratory

# This file has been adapted from PyDM, and can be redistributed and/or
# modified in accordance with terms in conditions set forth in the BSD
# 3-Clause License. You can find the complete licence text in the LICENCES
# directory.

# Links:
#   PyDM Project: https://github.com/slaclab/pydm
#   PyDM Licence: https://github.com/slaclab/pydm/blob/master/LICENSE.md

from qtpy.QtCore import QObject, QVariant
from qtpy.QtWidgets import QAction
from qtpy.QtDesigner import QExtensionFactory, QPyDesignerTaskMenuExtension, \
    QPyDesignerPropertySheetExtension, QDesignerPropertySheetExtension,\
    QDesignerFormWindowInterface

class ExtensionFactory(QExtensionFactory):
    def __init__(self, parent=None):
        super(ExtensionFactory, self).__init__(parent)

    def createExtension(self, obj, iid, parent):

        print iid

        # For now check the iid for TaskMenu...
        if iid == "org.qt-project.Qt.Designer.TaskMenu":
            return TaskMenuExtension(obj, parent)

        if iid == "org.qt-project.Qt.Designer.PropertySheet":
            return PropertySheetExtension(obj, parent)

        # In the future we can expand to the others such as Property and etc
        # When the time comes...  we will need a new Extension and
        # the equivalent for TaskMenuExtension classes for the
        # property editor and an elif statement in here to instantiate it...


class TaskMenuExtension(QPyDesignerTaskMenuExtension):
    def __init__(self, widget, parent):
        super(TaskMenuExtension, self).__init__(parent)

        self.widget = widget
        self.__actions = None
        self.__extensions = []
        extensions = getattr(widget, 'extensions', None)

        if extensions is not None:
            for ex in extensions:
                extension = ex(self.widget)
                self.__extensions.append(extension)

    def taskActions(self):
        if self.__actions is None:
            self.__actions = []
            for ex in self.__extensions:
                self.__actions.extend(ex.actions())

        return self.__actions

    def preferredEditAction(self):
        if self.__actions is None:
            self.taskActions()
        if self.__actions:
            return self.__actions[0]


class PropertySheetExtension(QPyDesignerPropertySheetExtension):
    def __init__(self, widget, parent):
        super(PropertySheetExtension, self).__init__(parent)

        self.parent = parent
        self.widget = widget

        print "initing propery extentions"

        self.widget = widget
        self.formWindow = QDesignerFormWindowInterface.findFormWindow(self.widget)
        self.propertylist=['objectName', 'geometry', 'text']
    #     self.temp_flag = True
    #     #print dir(self.widget.pyqtConfigure.__sizeof__)
    #     #print self.widget.pyqtConfigure.__sizeof__()
    #     for i in widget.__dict__:
    #         #print i
    #         if 'PyQt4.QtCore.pyqtProperty' in str(widget.__dict__[i]):
    #             self.propertylist.append(i)
    #             print i
    #     #print dir(self.widget)

    def count(self):
        return len(self.propertylist)

    def property(self, index):
        name = self.propertyName(index)
        print 'property index:', index, name
        return QVariant(self.widget.property(name))

    def indexOf(self, name):
        #print 'NAME:', name
        for num, i in enumerate(self.propertylist):
            if i == name:
                return num
        self.propertylist.append(name)
        print 'not found:', name, num + 1
        return num + 1

    def setChanged(self, index, value):
        return

    def isChanged(self, index):
        return False

    def hasReset(self, index):
        return True

    def isAttribute(self, index):
        return False

    def propertyGroup(self, index):
        name = self.propertyName(index)
        if 'geometry' in name:
            return 'QObject'
        if 'objectName' in name:
            return 'QWidget'
        if 'text' in name:
            return 'Text'
        return 'Bool'

    def setProperty(self, index, value):
        name = self.propertyName(index)
        print value
        try:
            value = value.toPyObject()
        except:
            pass
        if self.formWindow:
            self.formWindow.cursor().setProperty(name, QVariant(value))
        return

    def getVisible(self, index, data):
        pass

    def isVisible(self, index):
        prop = self.propertyName(index)
        if 'alt_text' in prop:
            return self.temp_flag
        return True

    def propertyName(self, index):
        return self.propertylist[index]



class _PluginExtension(object):
    def __init__(self, widget):
        self.widget = widget
        self._actions = []

    def addTaskMenuAction(self, action_name, callback):
        action = QAction(action_name, self.widget)
        action.triggered.connect(callback)
        self._actions.append(action)

    def actions(self):
        return self._actions


# I chatted with some of the Tormach reps for a bit at FabTech, but they were
# really hard to get any info out of and acted as if PathPilot was realy
# propritary. given that they