
# import the interior decorator :)
from functools import wraps

import linuxcnc

from qtpyvcp.lib.decorators import action, ACTIONS
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.logger import getLogger

LOG = getLogger(__name__)

STATUS = getPlugin('status')
STAT = STATUS.stat

MAPPING = {
    'task_state': {
        'on': linuxcnc.STATE_ON,
        'off': linuxcnc.STATE_OFF,
        'estop': linuxcnc.STATE_ESTOP,
        'reset': linuxcnc.STATE_ESTOP_RESET,
        linuxcnc.STATE_ON: 'on',
        linuxcnc.STATE_OFF: 'off',
        linuxcnc.STATE_ESTOP: 'estop',
        linuxcnc.STATE_ESTOP_RESET: 'reset'
        },

    'task_mode': {
        'mdi': linuxcnc.MODE_MDI,
        'auto': linuxcnc.MODE_AUTO,
        'manual': linuxcnc.MODE_MANUAL,
        linuxcnc.MODE_MDI: 'mdi',
        linuxcnc.MODE_AUTO: 'auto',
        linuxcnc.MODE_MANUAL: 'manual'
        },

    'interp_state': {
        'idle': linuxcnc.INTERP_IDLE,
        'paused': linuxcnc.INTERP_PAUSED,
        linuxcnc.INTERP_PAUSED: 'paused',
        linuxcnc.INTERP_IDLE: 'idle',
        }
}

def generateRules(requires):
    for k, v in requires.iteritems():
        requires[k] = MAPPING[k].get(v, v)

    print requires

    chans = []
    exp = ''
    for i, k in enumerate(requires):
        chans.append({'url': 'status:%s' % k, 'trigger': True})
        exp += 'ch[%s] == %s' % (i, requires[k])
        print i, len(requires)
        if i < len(requires) - 1:
            exp += ' and '

    rules = [{'channels': chans,
             "expression": exp,
             "name": "",
             "property": "Enabled"
             }]

    print chans
    print exp

    import json
    print json.dumps(rules, indent=4, sort_keys=True)
    return rules


def require(**requires):
    print requires
    generateRules(requires)
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            for key, value in requires.iteritems():
                print key, value
                if getattr(STAT, key) != MAPPING[key][value]:
                    LOG.error("%s requires %s='%s' but it is '%s'",
                              func.__name__, key, value, MAPPING[key][getattr(STAT, key)])
            func(*args, **kwargs)
        inner.requires = requires
        return inner

    return decorator


@action('machine.issue-mdi')
@require(task_state='on', interp_state='idle')
def issue_mdi(mdi):
    """Issue an MDI command."""
    print "Issuing MDI:", mdi

ACTIONS['machine.issue-mdi']('M6 T3')
print ACTIONS['machine.issue-mdi'].requires
print ACTIONS['machine.issue-mdi'].__doc__
