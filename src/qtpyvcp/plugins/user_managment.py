import os

from PySide6.QtWidgets import qApp
from qtpyvcp.utilities.misc import normalizePath
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import DataPlugin, DataChannel, getPlugin

LOG = getLogger(__name__)


class UserManagement(DataPlugin):
    def __init__(self, serialization_method='pickle', persistence_file=None):
        super(UserManagement, self).__init__()

        self.users = {}
        self.user_levels = {}

    def checkPermissions(self, required_user_level):
        """Check permission based on current user level.

        Args:
            required_user_level (int) : The required user level.

        :returns: Whether current user has permission.
        :rtype: bool
        """
        return self.currentUserLevel.getValue() >= required_user_level

    def setWidgetEnablementPerPermission(self, widget_root):
        """Set a widgets enable state based on the permission level
        of the currently set user.
        
        This should be re-run on each user change and as part of the UI startup.
        
        Any rules that change a widget enable status need to handle the security
        considerations themselves via the datachannel methods below.
        """
        for w in qApp.allWidgets():
            if hasattr(w, 'security') and hasattr(w, 'setEnabled'):
                # test security level and enablement
                w.setEnabled(self.checkPermissions(w.security))

    def loginUser(self, username, password):
        """Login a user

        Args:
            username (str) : The username to log in
            password (str) : The user's password

        Returns:
            True if the user was logged in successfully.
        """
        # Test password and user
        if not username in self.users:
            LOG.debug(f'User: {username} not found')
            return False
        
        if self.users[username] != password:
            LOG.debug(f'User: {username} password wrong')
            return False
        
        self.currentUserName.setValue(username)
        # user is real and has correct password, get access level
        self.currentUserLevel.setValue(self.user_levels[username])
        LOG.debug(f'User: {username} logged in and lvl set to: {self.user_levels[username]}')
        
        return True

    def logoffUser(self):
        self.currentUserLevel.setValue(-1)
        self.currentUserName.setValue('')

    @DataChannel
    def currentUserName(self, chan):
        return chan.value or 'No User'

    @DataChannel
    def currentUserLevel(self, chan):
        # split out test from single line as a chan.value of 0 was causing a
        # -1 return which was not the desired behaviour.
        if chan.value == None:
            rtn_val = -1
        else:
            rtn_val = chan.value
        return rtn_val

    def cacheUsers(self):
        """Cache Users, Passwords and Security Levels
        
        Expects a file "user.txt" in the linuxcnc/config director of the
        specific machine config.  The text file is of the format:
        Username, password, security level.
        Columns are separate by spaces. Any line starting with # isignored.
        
        Example file:
        
        # Username    Password   SecurityLevel
          james       1234       10
          brian       4321       0
          john        5678      5

        """
        user_file_name = normalizePath(path='users.txt',
                                        base=os.getenv('CONFIG_DIR', '~/'))
        user_file = open(user_file_name)
        for line in user_file:
            if not line.startswith('#'):
                try:
                    user, password, security = line.split()
                    self.users[user] = password
                    self.user_levels[user] = int(security)
                except:
                    LOG.debug('User file may have blank line at the end. Or is not the correct format,')
        user_file.close()

    def initialise(self):
        self.cacheUsers()

    def terminate(self):
        pass
