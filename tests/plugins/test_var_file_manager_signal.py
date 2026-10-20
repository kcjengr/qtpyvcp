"""Regression test for the VarFileManager parameter-change signal.

``parameters_changed`` carries a dict keyed by integer parameter number.
Declaring it as ``Signal(dict)`` makes PySide map it to QVariantMap (string
keys only) and log ``_pythonToCppCopy: Cannot copy-convert (dict) to C++``.
It must be ``Signal(object)``.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

QtCore = pytest.importorskip("PySide6.QtCore")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")

VarFileManager = pytest.importorskip(
    "qtpyvcp.plugins.var_file_manager").VarFileManager


def test_parameters_changed_accepts_int_keyed_dict():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    messages = []
    previous = QtCore.qInstallMessageHandler(
        lambda mode, context, message: messages.append(message))
    try:
        # Build without the heavy plugin __init__ (file watching, Info lookup).
        manager = VarFileManager.__new__(VarFileManager)
        QtCore.QObject.__init__(manager)

        received = []
        manager.parameters_changed.connect(received.append)
        manager.parameters_changed.emit({1: 1.5, 2: -3.0, 7: None})
        app.processEvents()
    finally:
        QtCore.qInstallMessageHandler(previous)

    assert received == [{1: 1.5, 2: -3.0, 7: None}]
    assert not [m for m in messages if "copy-convert" in m], messages
