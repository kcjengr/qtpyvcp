

from simpleeval import simple_eval

from qtpyvcp.plugins import DataPlugin, getPlugin


class Calculator(DataPlugin):
    def __init__(self):
        super(Calculator, self).__init__()

        self.status = getPlugin('status')
        self.positions = getPlugin('position')

    def nameHandler(self, node):
        var_name = node.id.lower()
        if var_name in "xyzabcuvw":
            anum = 'xyzabcuvw'.index(var_name)
            pos = self.positions.rel.getValue(anum=anum)
            return pos
        # elif var_name in "fs":
        #     settings = self.status.settings.getValue()

    def calculate(self, exp):
        return simple_eval(exp, names=self.nameHandler)
