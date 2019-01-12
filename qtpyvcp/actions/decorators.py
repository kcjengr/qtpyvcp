
# import the interior decorator :)
from functools import wraps

import linuxcnc
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)

STATUS = getPlugin('status')
STAT = STATUS.stat


def require_homed(func):

    @wraps(func)
    def inner(*args, **kwargs):
        if _all_homed():
            func(*args, **kwargs)
        else:
            LOG.error("action '%s' requires the machine to be homed",
                      func.__name__)

    func.func_dict['homed'] = True
    inner.func_dict = func.func_dict
    return inner


def _all_homed():
    for jnum in range(STAT.joints):
        if not STAT.joint[jnum]['homed']:
            return False
    return True


def require_task_state(task_state):

    enum_to_str = {linuxcnc.STATE_ON: 'on',
                   linuxcnc.STATE_OFF: 'off',
                   linuxcnc.STATE_ESTOP: 'estop',
                   linuxcnc.STATE_ESTOP_RESET: 'reset'}

    def decorator(func):

        @wraps(func)
        def inner(*args, **kwargs):
            print STAT.task_state
            if enum_to_str[STAT.task_state] == task_state:
                func(*args, **kwargs)
            else:
                LOG.error("action '%s' requires task_state of %s but it is %s:",
                          func.__name__, task_state, enum_to_str[STAT.task_state])

        func.func_dict['task_state'] = task_state
        inner.func_dict = func.func_dict
        return inner

    return decorator


def require_task_mode(task_mode):

    enum_to_str = {linuxcnc.MODE_MDI: 'mdi',
                   linuxcnc.MODE_AUTO: 'auto',
                   linuxcnc.MODE_MANUAL: 'manual'}

    def decorator(func):

        @wraps(func)
        def inner(*args, **kwargs):
            print STAT.task_mode
            if enum_to_str[STAT.task_mode] == task_mode:
                func(*args, **kwargs)
            else:
                LOG.error("action '%s' requires task_mode of %s but it is %s:",
                          func.__name__, task_mode, enum_to_str[STAT.task_mode])

        func.func_dict['task_mode'] = task_mode
        inner.func_dict = func.func_dict
        return inner

    return decorator


def require_interp_state(interp_state):

    enum_to_str = {linuxcnc.INTERP_IDLE: 'idle',
                   linuxcnc.INTERP_PAUSED: 'paused',
                   linuxcnc.INTERP_READING: 'reading',
                   linuxcnc.INTERP_WAITING: 'waiting'}

    def decorator(func):
        print "ok_in_state", func.__name__, func.func_dict

        @wraps(func)
        def inner(*args, **kwargs):
            print
            if enum_to_str[STAT.interp_state] in interp_state:
                func(*args, **kwargs)
            else:
                LOG.error("action '%s' requires interp_state of %s but it is %s:",
                          func.__name__, interp_state, enum_to_str[STAT.interp_state])


        func.func_dict['interp_state'] = interp_state
        inner.func_dict = func.func_dict
        return inner

    return decorator


@require_task_state('on')
@require_homed
@require_task_mode('mdi')
@require_interp_state('idle')
def issue_mdi(mdi):
    issue_mdi.__dict__['msg'] = 'hello'
    print "Issuing MDI:", mdi

issue_mdi("M6 T3")

print issue_mdi.func_dict
print issue_mdi.__dict__

issue_mdi("M6 T3")
