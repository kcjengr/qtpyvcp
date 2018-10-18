#!/usr/bin/env python

import os

from qtpy.QtWidgets import QLabel
from qtpy.QtCore import Property, pyqtBoundSignal

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

from qtpyvcp.utilities.status import Status, StatusItem
STATUS = Status()
STAT = STATUS.stat

IN_DESIGNER = os.getenv('DESIGNER') != None

class StatusLabel(QLabel):
    """General purpose label for displaying status values.

    Args:
        parent (QWidget) : The parent widget, or None.
    """
    def __init__(self, parent=None):
        super(StatusLabel, self).__init__(parent)

        self._factor = 1
        self._format = '{}'
        self._status_item = ''

        self._rules = ''

        self.setText('n/a')

    @Property(float)
    def factor(self):
        """The multiplication factor to apply to numeric status values.

        Returns:
            float: The current multiplication factor.
        """
        return self._factor

    @factor.setter
    def factor(self, factor):
        """Sets the multiplication factor to apply to numeric status values.

        Args:
            factor (float): The desired multiplication factor.
        """
        self._factor = factor

        # force update of label when in designer
        if IN_DESIGNER:
            self.statusItem = self._status_item

    @Property(str)
    def format(self):
        """The str format specification to use for displaying the value.

        Returns:
            str : The current format specification.
        """
        return self._format

    @format.setter
    def format(self, format):
        """Sets the desired format specification.

        Args:
            format (str): A valid str format specification.
        """

        self._format = format

        # force update of label when in designer
        if IN_DESIGNER:
            self.statusItem = self._status_item

    @Property(str)
    def rules(self):
        """The rules property of the widget.

        Returns:
            str : JSON format of the current rules.
        """
        return self._rules

    @rules.setter
    def rules(self, rules):
        self._rules = rules

    @Property(str)
    def statusItem(self):
        """The name of the linuxcnc.stat item that the label should
            display the value of.

        Returns:
            str : The linuxcnc.stat item.
        """
        return self._status_item

    @statusItem.setter
    def statusItem(self, status_item):
        """Sets the linuxcnc.stat item the label should display the value
            of and binds the label to the items value changed signal.

        Args:
            status_item (str): A linuxcnc.status item.
        """
        if status_item == '' and self._status_item == '':
            return

        self._status_item = status_item

        items = status_item.split('.')
        item = items[0]
        index = None

        try:
            if len(items) == 1:
                value = getattr(STAT, item)
                sig = getattr(STATUS, item)
            elif len(items) == 2:
                index = int(items[1])
                value = getattr(STAT, item)
                sig = getattr(STATUS, item)
            elif len(items) == 3:
                ind = int(items[1])
                key = items[2]
                value = getattr(STAT, item)[ind][key]
                sig = getattr(getattr(STATUS, item)[ind], key)

            if not isinstance(sig, StatusItem):
                raise ValueError('Not a valid signal')

        except:
            LOG.exception("Invalid status item '{}'".format(status_item))
            try:
                self.setText(self._format.format('n/a'))
            except ValueError:
                self.setText(self._format.format(float('nan')))
            except:
                self.setText('n/a')
            return

        try:
            # value = STATUS.STATE_STRING_LOOKUP[item][value]
            if sig.to_str == str:
                sig.onValueChanged(lambda v: self.setText(self._format.format(v)))
                self.setText(self._format.format(sig.value()))
            else:
                sig.onTextChanged(lambda v: self.setText(self._format.format(v)))
                self.setText(self._format.format(sig.text()))

        except KeyError:

            if isinstance(value, (int, float)) and self._factor != 1:
                try:
                    if index is not None:
                        self.setText(self._format.format(value[index] * self._factor))
                        sig.connect(lambda v: self.setText(self._format.format(v[index] * self._factor)))
                    else:
                        self.setText(self._format.format(value * self._factor))
                        sig.connect(lambda v: self.setText(self._format.format(v * self._factor)))

                except:
                    LOG.warning("Invalid format '{}' for data of type '{}'" \
                        .format(format, value.__class__.__name__))
                    self.setText('FRMT error')

            else:
                try:
                    if index is not None:
                        self.setText(self._format.format(value[index]))
                        sig.connect(lambda v: self.setText(self._format.format(v[index])))
                    else:
                        self.setText(self._format.format(value))
                        sig.connect(lambda v: self.setText(self._format.format(v)))

                except:
                    LOG.warning("Invalid format '{}' for data of type '{}'" \
                        .format(format, value.__class__.__name__))
                    self.setText('FRMT error')

        except:
            LOG.exception("Problem connecting update signal for status item '{}'".format(status_item))
