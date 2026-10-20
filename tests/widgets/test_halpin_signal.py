"""HALPin conversion and signal coverage without a running LinuxCNC instance."""

import importlib.util
import logging
import sys
import types
import warnings
from pathlib import Path

import pytest

OBJ_STATUS_PATH = (
    Path(__file__).resolve().parents[2]
    / "src/qtpyvcp/utilities/obj_status.py"
)


@pytest.fixture
def obj_status_module(monkeypatch):
    """Load obj_status with lightweight LinuxCNC/logger module stubs."""
    linuxcnc = types.ModuleType("linuxcnc")
    linuxcnc.stat = lambda: object()

    qtpyvcp = types.ModuleType("qtpyvcp")
    qtpyvcp.__path__ = []
    utilities = types.ModuleType("qtpyvcp.utilities")
    utilities.__path__ = []
    logger = types.ModuleType("qtpyvcp.utilities.logger")
    logger.getLogger = logging.getLogger
    utilities.logger = logger

    monkeypatch.setitem(sys.modules, "linuxcnc", linuxcnc)
    monkeypatch.setitem(sys.modules, "qtpyvcp", qtpyvcp)
    monkeypatch.setitem(sys.modules, "qtpyvcp.utilities", utilities)
    monkeypatch.setitem(sys.modules, "qtpyvcp.utilities.logger", logger)

    spec = importlib.util.spec_from_file_location("obj_status_signal_test", OBJ_STATUS_PATH)
    module = importlib.util.module_from_spec(spec)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("hal_type", "initial", "initial_expected", "updated", "expected"),
    [
        ("bool", "0", False, "true", True),
        ("bit", "0", False, "1", True),
        ("real", "0", 0.0, "1.25", 1.25),
        ("float", "0", 0.0, "-0.5", -0.5),
        ("sint", "0", 0, "-5", -5),
        ("s32", "0", 0, "5", 5),
        ("s64", "0", 0, "-5000000000", -5000000000),
        ("signed", "0", 0, "5", 5),
        ("uint", "0", 0, "5", 5),
        ("u32", "0", 0, "5", 5),
        ("u64", "0", 0, "18446744073709551615", 18446744073709551615),
        ("unsigned", "0", 0, "5", 5),
        ("port", "0", 0, "256", 256),
    ],
)
def test_halpin_supports_linuxcnc_master_and_legacy_type_names(
        obj_status_module, hal_type, initial, initial_expected, updated, expected):
    pin = obj_status_module.HALPin("test.pin", hal_type, "OUT", initial)
    assert pin.value == initial_expected
    values = []
    pin.connect(values.append)

    pin.update(updated)

    assert pin.value == expected
    assert values == [expected]


def test_halpin_rejects_unknown_types(obj_status_module):
    with pytest.raises(ValueError, match="Unsupported HAL pin type"):
        obj_status_module.HALPin("test.pin", "unknown", "OUT", "0")


def test_halpin_treats_port_as_a_queue_not_a_scalar(obj_status_module):
    pin = obj_status_module.HALPin("test.port", "port", "IN", "0")
    with pytest.raises(TypeError, match="HAL_PORT is a byte queue"):
        pin.setValue(1)
