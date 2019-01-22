from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)


def deprecated(reason='', replaced_by=''):
    msg_temp = 'Deprecation Warning: {mod}.{func}() has been deprecated ' \
               '{reason}and will be removed in the future.'
    if replaced_by:
        msg_temp += ' Use {}() instead'.format(replaced_by)

    def decorator(func):

        msg = msg_temp.format(mod=func.__module__,
                              func=func.__name__,
                              reason=reason if reason == '' else reason + ', ')

        def inner(*args, **kwargs):
            LOG.warn(msg)
            return func(*args, **kwargs)

        return inner

    return decorator
