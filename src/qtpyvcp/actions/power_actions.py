import linuxcnc

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

#==============================================================================
# Power actions
#==============================================================================

def shut_system_down_prompt():
    import subprocess
    try:
        try:
            subprocess.check_call('xfce4-session-logout', shell=True)
        except:
            try:
                subprocess.check_call('systemctl poweroff', shell=True)
            except:
                raise
    except Exception as e:
        LOG.warning("Couldn't shut system down: {}".format(e))

def shut_system_down_now():
    import subprocess
    try:
        try:
            subprocess.check_call('xfce4-session-logout -h', shell=True)
        except:
            try:
                subprocess.check_call('systemctl poweroff', shell=True)
            except:
                raise
    except Exception as e:
        LOG.warning("Couldn't shut system down: {}".format(e))
