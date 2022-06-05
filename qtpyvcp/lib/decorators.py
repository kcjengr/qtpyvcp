
import inspect

from qtpy.QtWidgets import QWidget
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)


def deprecated(reason='Not Specified', replaced_by='Not Specified'):

    def decorator(obj):

        if inspect.isclass(obj) and issubclass(obj, QWidget):
            msg_temp = 'Deprecation Warning: The widget "{mod}.{cls}" has ' \
                       'been deprecated and will be removed in the future. ' \
                       'Reason: {reason}. ' \
                       'Replaced by: {replaced_by}.'

            msg = msg_temp.format(mod=obj.__module__,
                                  cls=obj.__name__,
                                  reason=reason,
                                  replaced_by=replaced_by)

            LOG.warning(msg)

            return obj

        elif inspect.isfunction(obj):

            msg_temp = 'Deprecation Warning: The function {mod}.{func}() has ' \
                       'been deprecated and will be removed in the future. ' \
                       'Reason: {reason}. ' \
                       'Replaced by: {replaced_by}.'

            msg = msg_temp.format(mod=obj.__module__,
                                  func=obj.__name__,
                                  reason=reason,
                                  replaced_by=replaced_by)

            def inner(*args, **kwargs):
                LOG.warn(msg)
                return obj(*args, **kwargs)

            return inner

        else:
            return obj

    return decorator
