import pytest
from unittest.mock import MagicMock

# Register a mock 'status' plugin at module level so VCPButton subclasses
# can be instantiated during tests without LinuxCNC/HAL running.
from qtpyvcp.plugins import _PLUGINS

def _get_mock_status():
    """Get or create the mock status plugin."""
    if 'status' not in _PLUGINS:
        mock = MagicMock()
        mock.isLocked.return_value = False
        _PLUGINS['status'] = mock
    return _PLUGINS['status']


@pytest.fixture(autouse=True)
def mock_status_plugin():
    """Ensure mock status plugin is registered before and after each test.

    This is needed because other test fixtures (like clean_registry in
    test_plugin_registry.py) may clear _PLUGINS, removing our mock.
    """
    _get_mock_status()
    yield _PLUGINS['status']
    # Re-register after the test in case another fixture cleared it
    if 'status' not in _PLUGINS:
        _PLUGINS['status'] = _get_mock_status()


@pytest.fixture
def eval_line_edit(qtbot):
    from qtpy.QtCore import Qt

    from qtpyvcp.widgets.base_widgets.eval_line_edit import EvalLineEdit

    widget = EvalLineEdit()
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def led_widget(qtbot):
    from qtpyvcp.widgets.base_widgets.led_widget import LEDWidget

    widget = LEDWidget()
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def bar_indicator(qtbot):
    from qtpy.QtCore import Qt

    from qtpyvcp.widgets.base_widgets.bar_indicator import BarIndicatorBase

    widget = BarIndicatorBase()
    widget.resize(200, 30)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def status_label(qtbot):
    # Import directly from the module file to avoid triggering
    # display_widgets/__init__.py which imports VTKBackPlot -> machine_actions
    import sys
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "status_label",
        "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/status_label.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["qtpyvcp.widgets.display_widgets.status_label"] = module
    spec.loader.exec_module(module)

    label = module.StatusLabel()
    qtbot.addWidget(label)
    return label


@pytest.fixture
def status_led(qtbot):
    import sys
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "status_led",
        "/home/james/dev/qtpyvcp/src/qtpyvcp/widgets/display_widgets/status_led.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["qtpyvcp.widgets.display_widgets.status_led"] = module
    spec.loader.exec_module(module)

    led = module.StatusLED()
    qtbot.addWidget(led)
    return led


@pytest.fixture
def vcp_frame(qtbot):
    from qtpy.QtWidgets import QFrame

    from qtpyvcp.widgets.containers.frame import VCPFrame

    widget = VCPFrame(None)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def vcp_stacked_widget(qtbot):
    from qtpy.QtWidgets import QStackedWidget

    from qtpyvcp.widgets.containers.stack import VCPStackedWidget

    widget = VCPStackedWidget()
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def base_dialog(qtbot):
    from qtpy.QtWidgets import QDialog

    from qtpyvcp.widgets.dialogs.base_dialog import BaseDialog

    dialog = BaseDialog()
    qtbot.addWidget(dialog)
    return dialog


@pytest.fixture
def error_dialog(qtbot):
    import sys

    from qtpyvcp.widgets.dialogs.error_dialog import ErrorDialog

    try:
        raise ValueError("test error")
    except Exception:
        exc_info = sys.exc_info()

    dialog = ErrorDialog(exc_info)
    qtbot.addWidget(dialog)
    return dialog


@pytest.fixture
def warning_dialog(qtbot):
    import sys

    from qtpyvcp.widgets.dialogs.error_dialog import ErrorDialog

    try:
        raise UserWarning("test warning")
    except Exception:
        exc_info = sys.exc_info()

    dialog = ErrorDialog(exc_info)
    qtbot.addWidget(dialog)
    return dialog


@pytest.fixture
def keyerror_dialog(qtbot):
    import sys

    from qtpyvcp.widgets.dialogs.error_dialog import ErrorDialog

    try:
        raise KeyError("missing_key")
    except Exception:
        exc_info = sys.exc_info()

    dialog = ErrorDialog(exc_info)
    qtbot.addWidget(dialog)
    return dialog


@pytest.fixture
def attrerror_dialog(qtbot):
    import sys

    from qtpyvcp.widgets.dialogs.error_dialog import ErrorDialog

    try:
        raise AttributeError("missing_attr")
    except Exception:
        exc_info = sys.exc_info()

    dialog = ErrorDialog(exc_info)
    qtbot.addWidget(dialog)
    return dialog


@pytest.fixture
def typeerror_dialog(qtbot):
    import sys

    from qtpyvcp.widgets.dialogs.error_dialog import ErrorDialog

    try:
        raise TypeError("bad type")
    except Exception:
        exc_info = sys.exc_info()

    dialog = ErrorDialog(exc_info)
    qtbot.addWidget(dialog)
    return dialog


@pytest.fixture
def empty_msg_dialog(qtbot):
    import sys

    from qtpyvcp.widgets.dialogs.error_dialog import ErrorDialog

    try:
        raise ValueError("")
    except Exception:
        exc_info = sys.exc_info()

    dialog = ErrorDialog(exc_info)
    qtbot.addWidget(dialog)
    return dialog


@pytest.fixture
def long_msg_dialog(qtbot):
    import sys

    from qtpyvcp.widgets.dialogs.error_dialog import ErrorDialog

    long_msg = "This is a very long error message that spans multiple lines and contains a lot of text to test the dialog's ability to handle lengthy exception messages properly." * 5

    try:
        raise ValueError(long_msg)
    except Exception:
        exc_info = sys.exc_info()

    dialog = ErrorDialog(exc_info)
    qtbot.addWidget(dialog)
    return dialog


@pytest.fixture
def designer_error_dialog(qtbot):
    import os
    import sys

    from qtpyvcp.widgets.dialogs.error_dialog import ErrorDialog

    original_designer = os.environ.get("DESIGNER")
    os.environ["DESIGNER"] = "1"

    try:
        raise ValueError("designer test error")
    except Exception:
        exc_info = sys.exc_info()

    dialog = ErrorDialog(exc_info)
    qtbot.addWidget(dialog)

    if original_designer is not None:
        os.environ["DESIGNER"] = original_designer
    else:
        os.environ.pop("DESIGNER", None)

    return dialog


@pytest.fixture
def mock_widget_with_rules():
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.rules = "[]"
    mock.RULE_PROPERTIES = {
        'None': ['None', None],
        'Enable': ['setEnabled', bool],
        'Visible': ['setVisible', bool],
        'Style Class': ['setStyleClass', str],
    }
    mock.DEFAULT_RULE_PROPERTY = 'Visible'
    return mock


@pytest.fixture
def mock_widget_without_rules():
    from unittest.mock import MagicMock

    mock = MagicMock()
    return mock
