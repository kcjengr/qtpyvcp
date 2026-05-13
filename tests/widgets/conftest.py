import pytest


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
