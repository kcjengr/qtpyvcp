# import to get true floating point division even if the arguments are ints (ex. 1/2 => 0.5, not 0)
from __future__ import division
from qtpy.QtWidgets import QLineEdit
from qtpyvcp.utilities import logger

from simpleeval import simple_eval

LOG = logger.getLogger(__name__)


class EvalLineEdit(QLineEdit):
    """EvalLineEdit

    This control adds support for evaluating mathematical expressions.

    Any valid expression will be evaluated (ex. -(10+5)*(1.0/2.0) will be evaluated to -2.5).

    Any expression that begins with an operator (except -, see below), will be applied to the current value
    (ex. if current position is 20 and the user enters /2, then the resulting value will be 10).

    Any entry that consists of a single - will invert the sign of the current value.

    NB: If the expression starts with '-' it will be interpreted as negating the value following it.
        This means that you cannot enter -10 and have that value subtract from the current value
        because there is no way to determine if the you wanted to subtract 10, or set the current
        value to -10. In order to subtract from the current value you must use '-=' instead of
        just '-'. This syntax may be used with all operators (ex. +=, /=, *=), but it is only
        required for subtraction.
    """

    def __init__(self, parent=None):
        super(EvalLineEdit, self).__init__(parent)
        self.orig_value = ''
        self.returnPressed.connect(self.evaluate_)

    def focusInEvent(self, event):
        self.orig_value = self.text()

    def evaluate_(self):
        if self.text().strip() == '-':
            # change sign if entry is just a '-'
            self.setText('-' + self.orig_value)
        elif self.text().startswith(('+', '*', '/', '-=')):
            self.setText(self.orig_value + self.text().replace('=', ''))
        try:
            self.setText("{}".format(simple_eval(self.text())))
        except Exception:
            LOG.exception('Error evaluating numeric expression "{}".'.format(self.text()))
