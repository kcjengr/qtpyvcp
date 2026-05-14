import configparser
import os
import sys
import types
from unittest.mock import MagicMock, patch


class _FakeInfo:
    """Minimal Info singleton mock to avoid INI file dependencies."""

    COORDINATES = ['x', 'y', 'z']
    NUM_JOINTS = 3
    AXIS_LETTER_LIST = []
    AXIS_NUMBER_LIST = [0, 1, 2]
    JOINT_AXIS_DICT = {0: 0, 1: 1, 2: 2}
    ALETTER_JNUM_DICT = {'x': 0, 'y': 1, 'z': 2}

    def __call__(self, *args, **kwargs):
        return self

    def getJogVelocity(self):
        return 100.0

    def getMaxJogVelocity(self):
        return 100.0

    def getJogAngularVelocity(self):
        return 100.0

    def getMaxJogAngularVelocity(self):
        return 100.0

    def maxFeedOverride(self):
        return 1.0

    def maxVelocity(self):
        return 100.0

    def getIncrements(self):
        return [0.1, 0.01, 0.001]

    def spindles(self):
        return 1

    def __getattr__(self, name):
        # Return a MagicMock for any unknown attribute to avoid AttributeError
        return MagicMock()


class _MockINI:
    """Minimal INI object mock that can parse real INI files."""

    def __init__(self, path):
        self._parser = configparser.RawConfigParser()
        self._parser.read(path)

    def find(self, section, option):
        try:
            return self._parser.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return None


def _ensure_linuxcnc_mock():
    """Ensure linuxcnc module is mocked before any qtpyvcp modules import it."""
    if 'linuxcnc' not in sys.modules:
        mock = MagicMock()
        mock.INTERP_IDLE = 0
        mock.INTERP_RUNNING = 1
        mock.INI_IDLE = 0
        mock.INI_ERROR = -1
        # Mock STAT object used by various modules
        mock.stat = MagicMock()
        mock.stat.feed_hold_enabled = False
        mock.stat.paused = False
        mock.stat.interp_state = mock.INTERP_IDLE
        mock.stat.state = 0
        mock.stat.task_mode = 0
        # Mock ini() to actually parse INI files for tests that need it
        mock.ini = _MockINI
        sys.modules['linuxcnc'] = mock

    # Mock Info singleton to avoid INI file dependencies during module loading
    info_mock = _FakeInfo()
    if 'qtpyvcp.utilities.info' in sys.modules:
        sys.modules['qtpyvcp.utilities.info'].Info = info_mock
    else:
        # Create a fake module and inject it before any qtpyvcp modules load
        fake_info_mod = types.ModuleType('qtpyvcp.utilities.info')
        fake_info_mod.Info = info_mock
        fake_info_mod.LOGGER = MagicMock()
        sys.modules['qtpyvcp.utilities.info'] = fake_info_mod


def _ensure_status_mock():
    """Ensure status plugin is mocked before any qtpyvcp modules import it."""
    from qtpyvcp.plugins import _PLUGINS
    if 'status' not in _PLUGINS:
        mock = MagicMock()
        mock.isLocked.return_value = False
        mock.stat = MagicMock()
        mock.stat.feed_hold_enabled = False
        mock.stat.paused = False
        mock.stat.interp_state = 0
        mock.stat.state = 0
        mock.stat.task_mode = 0
        mock.program_units.__str__.return_value = 'in'
        mock.program_units.getValue.return_value = 'in'
        mock.mdi_history = MagicMock()
        mock.mdi_history.value = []
        mock.mdi_remove_entry = MagicMock()
        mock.mdi_remove_all = MagicMock()
        mock.max_mdi_history_length = MagicMock()
        _PLUGINS['status'] = mock


import pytest


@pytest.fixture(autouse=True)
def mock_linuxcnc():
    """Mock linuxcnc module so all qtpyvcp modules can be imported."""
    _ensure_linuxcnc_mock()
    yield
    import sys
    if 'linuxcnc' in sys.modules:
        del sys.modules['linuxcnc']


@pytest.fixture(autouse=True)
def mock_status_plugin():
    """Ensure status plugin is mocked for all tests."""
    _ensure_status_mock()
    from qtpyvcp.plugins import _PLUGINS
    yield _PLUGINS.get('status', MagicMock())
