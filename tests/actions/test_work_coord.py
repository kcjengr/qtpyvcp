"""Regression tests for the work-coordinate action.

A QComboBox bound to ``machine.set_work_coord`` delivered its row index through
``activated(int)``; that index reached ``issue_mdi`` and failed with
``'int' object has no attribute 'upper'``. The action must accept both an index
and the selected item text and map them to G54 .. G59.3.
"""

import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

QtWidgets = pytest.importorskip("PySide6.QtWidgets")
linuxcnc = pytest.importorskip("linuxcnc")

from qtpyvcp.plugins import _PLUGINS, registerPlugin


class _FakeChannel:
    def onValueChanged(self, callback):
        pass

    def notify(self, callback, *args, **kwargs):
        pass

    def getString(self):
        return "G54"


class _FakeStatus:
    def __init__(self):
        self.stat = SimpleNamespace(
            task_state=linuxcnc.STATE_ON,
            interp_state=linuxcnc.INTERP_IDLE,
        )
        self.interp_state = _FakeChannel()
        self.task_state = _FakeChannel()
        self.homed = _FakeChannel()
        self.g5x_index = _FakeChannel()

    def allHomed(self):
        return True


@pytest.fixture(scope="module")
def machine_actions():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    assert app is not None
    registerPlugin("status", _FakeStatus())
    try:
        import qtpyvcp.actions.machine_actions as module
        yield module
    finally:
        _PLUGINS.pop("status", None)


def test_work_coord_accepts_index(machine_actions, monkeypatch):
    calls = []
    monkeypatch.setattr(machine_actions, "issue_mdi",
                        lambda command: calls.append(command) or True)

    assert machine_actions.set_work_coord(0) is True
    assert machine_actions.set_work_coord(8) is True

    assert calls == ["G54", "G59.3"]


def test_work_coord_accepts_labels_and_descriptions(machine_actions, monkeypatch):
    calls = []
    monkeypatch.setattr(machine_actions, "issue_mdi",
                        lambda command: calls.append(command) or True)

    for value, expected in (
        ("g55", "G55"),
        ("G59.1", "G59.1"),
        ("G54: Part 1", "G54"),
        ("G56 (Work)", "G56"),
    ):
        assert machine_actions.set_work_coord(value) is True
        assert calls[-1] == expected


def test_invalid_work_coord_is_ignored(machine_actions, monkeypatch):
    calls = []
    monkeypatch.setattr(machine_actions, "issue_mdi",
                        lambda command: calls.append(command) or True)

    for value in (9, -1, "bogus", "", None, True):
        assert machine_actions.set_work_coord(value) is False

    assert calls == []


def test_combo_binding_passes_item_text(machine_actions, monkeypatch):
    from qtpyvcp.actions import bindWidget

    calls = []
    monkeypatch.setattr(machine_actions, "issue_mdi",
                        lambda command: calls.append(command) or True)

    combo = QtWidgets.QComboBox()
    combo.addItems(["G54", "G55", "G56"])
    bindWidget(combo, "machine.set_work_coord")

    assert machine_actions.set_work_coord.use_text is True
    combo.setCurrentIndex(1)
    combo.textActivated.emit("G55")
    combo.activated[int].emit(2)      # int path must not be connected

    assert calls == ["G55"]
