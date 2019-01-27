from qtpyvcp import ACTIONS
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


def action(action_id):
    def decorator(func):
        if action_id in ACTIONS:
            old = '{func.__module__}.{func.__name__}'.format(func=ACTIONS[action_id])
            new = '{func.__module__}.{func.__name__}'.format(func=func)
            LOG.warning("%s action method %s being replaced by %s", action_id, old, new)
        ACTIONS[action_id] = func
        func.action_id = action_id
        return func
    return decorator
