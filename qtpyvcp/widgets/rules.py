import json

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

from qtpyvcp.utilities.status import Status, StatusItem
STATUS = Status()

class ChanList(list):
    def __getitem__(self, index):
        return super(ChanList, self).__getitem__(index)()

def registerRules(widget, rules):
    rules = json.loads(rules)
    for rule in rules:
        # print rule
        ch = ChanList()
        triggers = []
        for chan in rule['channels']:
            print chan['channel']
            try:
                item = eval(chan['channel'], {'status': STATUS})

                trigger = chan.get('trigger', False)
                chan_type = chan.get('type', item.typ.__name__)

                if chan_type == 'str':
                    ch.append(item.text)
                    if trigger:
                        triggers.append(item.onTextChanged)
                else:
                    ch.append(item.value)
                    if trigger:
                        triggers.append(item.onValueChanged)

            except:
                LOG.exception("Error evaluating rule: {}".format(chan['channel']))
                return

        prop = widget.RULE_PROPERTIES[rule['property']]

        evil_env = {'ch': ch, 'widget': widget}
        exp_str = 'lambda: widget.{}({})'.format(prop[0], rule['expression'])
        exp = eval(exp_str, evil_env)
        exp()

        for trigger in triggers:
            trigger(exp)
