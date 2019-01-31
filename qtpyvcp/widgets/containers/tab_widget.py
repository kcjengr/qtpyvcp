import json

from qtpy.QtCore import Property
from qtpy.QtWidgets import QTabWidget, QTabBar, QLabel
from qtpyvcp.widgets.base_widgets.base_widget import VCPWidget

class VCPTabWidget(QTabWidget, VCPWidget):
    def __init__(self, parent=None):
        super(VCPTabWidget, self).__init__(parent)

        self.tab_bar = QtPyVCPTabBar(self)
        self.setTabBar(self.tab_bar)

    @Property(str)
    def rules(self):
        print "TabWidget: Getting rules ..."
        # return self.tabBar().getCurrentTabRules()
        # return json.loads(self._rules).get(self.currentIndex(), '')

        if self.currentIndex() < 0:
            return ''

        try:
            rules = json.loads(self._rules)[self.currentIndex()]
        except:
            return ''

        return unicode(json.dumps(rules))

    @rules.setter
    def rules(self, tab_rules):
        print "TabWidget: Setting rules ..."
        # self.tabBar().test = str(tab_rules)
        # self.tabBar().setCurrentTabRules(tab_rules)

        print "incoming tab rules", tab_rules
        print self.currentIndex(), type(self.currentIndex())

        try:
            rules = json.loads(self._rules)
            rules[self.currentIndex()] = json.loads(tab_rules)
        except:
            rules = {}

        self._rules = json.dumps(rules)
        print self._rules

    # @Property(str, designable=False)
    # def rules(self):
    #     print "TabWidget: Getting rules ..."
    #     return self._rules
    #
    # @rules.setter
    # def rules(self, rules):
    #     print "TabWidget: Setting rules ..."
    #     self._rules = rules
    #     # self.registerRules(rules)


class QtPyVCPTabBar(QTabBar):
    def __init__(self, parent=None):
        super(QtPyVCPTabBar, self).__init__(parent)

        self.tab_rules = {}

    def getCurrentTabRules(self):
        if self.currentIndex() < 0:
            return
        return self.tab_rules.get(self.currentIndex(), '')

    def setCurrentTabRules(self, tab_rules):
        self.tab_rules[self.currentIndex()] = tab_rules

    # testgejfgh = Property(str, fget=getCurrentTabRules, fset=setCurrentTabRules)
    #
    # def setEnabled(self, enabled):
    #     print "####################"
    #
    # @Property(str)
    # def test(self):
    #     print "getting test"
    #     return self._test
    #
    # @test.setter
    # def test(self, test):
    #     self._test = test

    # @Property(str)
    # def rules(self):
    #     if self.currentIndex() < 0:
    #         return
    #     return self.tab_rules.get(self.currentIndex(), '')
    #
    # @rules.setter
    # def rules(self, tab_rules):
    #     self.tab_rules[self.currentIndex()] = tab_rules

    # # def setTabEnabled(self, index, enabled):