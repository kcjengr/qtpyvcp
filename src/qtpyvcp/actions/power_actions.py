import linuxcnc

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

from qtpyvcp.plugins import getPlugin

STATUS = getPlugin('status')
STAT = STATUS.stat

CMD = linuxcnc.command()

#==============================================================================
# Coolent actions
#==============================================================================

class power:
    @staticmethod
    def shut_system_down_prompt():
        import subprocess
        try:
            try:
                subprocess.call('xfce4-session-logout', shell=True)
            except:
                try:
                    subprocess.call('systemctl poweroff', shell=True)
                except:
                    raise
        except Exception as e:
            LOG.warning("Couldn't shut system down: {}".format(e))

    @staticmethod
    def shut_system_down_now():
        import subprocess
        try:
            try:
                subprocess.call('xfce4-session-logout -h', shell=True)
            except:
                try:
                    subprocess.call('systemctl poweroff', shell=True)
                except:
                    raise
        except Exception as e:
            LOG.warning("Couldn't shut system down: {}".format(e))
