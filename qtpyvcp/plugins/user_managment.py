import os

from qtpyvcp.utilities.misc import normalizePath
from qtpyvcp.utilities.logger import getLogger
from qtpyvcp.plugins import DataPlugin, DataChannel, getPlugin

LOG = getLogger(__name__)


class UserManagement(DataPlugin):
    def __init__(self, serialization_method='pickle', persistence_file=None):
        super(UserManagement, self).__init__()

        self.users = []
        self.user_levels = {}

    def checkPermissions(self, required_user_level):
        """Check permission based on current user level.

        Args:
            required_user_level (int) : The required user level.

        :returns: Whether current user has permission.
        :rtype: bool
        """
        return self.currentUserLevel.getValue() >= required_user_level

    def loginUser(self, username, password):
        """Login a user

        Args:
            username (str) : The username to log in
            password (str) : The user's password

        Returns:
            True if the user was logged in successfully.
        """
        # TODO Handle user lookup
        self.currentUserName.setValue('Kurt')
        self.currentUserLevel.setValue(10)
        return True

    def logoffUser(self):
        self.currentUserLevel.setValue(0)
        self.currentUserName.setValue('')

    @DataChannel
    def currentUserName(self, chan):
        return chan.value or 'No User'

    @DataChannel
    def currentUserLevel(self, chan):
        return chan.value or 0

    def initialise(self):
        pass

    def terminate(self):
        pass
