# Qt6 / PySide6 Comprehensive Fix List (2026-03-02)

## Scope
- Repository scanned: `qtpyvcp/src/qtpyvcp`
- Focus areas:
  - Qt5/Qt6 API incompatibilities
  - PyQt5 hard dependencies left in runtime paths
  - callback lifecycle issues (`Internal C++ object ... already deleted`)
  - signal/slot signature mismatches (`TypeError` from callbacks)

---

## ✅ Applied in this sweep

### 1) Global callback safety hardening (high impact)
- File: `qtpyvcp/src/qtpyvcp/plugins/base_plugins.py`
- Change:
  - `DataChannel.notify(...)` now wraps connected slots with `safe_qt_callback(...)`
  - lambda wrappers now accept signal args (`*sig_args, **sig_kwargs`) before deriving channel value
- Why:
  - Prevents widespread deleted-object callback crashes and signature mismatch errors in all channel subscribers.

### 2) Global settings callback safety hardening
- File: `qtpyvcp/src/qtpyvcp/utilities/settings.py`
- Change:
  - `Setting.notify(...)` now wraps slots with `safe_qt_callback(...)`
  - initial `update=True` callback path now also goes through wrapper
- Why:
  - Prevents stale QObject-bound setting callbacks from crashing after widget teardown.

### 3) Remove hard PyQt5 dependency in deprecated DRO widget
- File: `qtpyvcp/src/qtpyvcp/widgets/display_widgets/dro_widget.py`
- Change:
  - Replaced `from PyQt5.QtCore import Q_ENUMS` with PySide6-safe shim fallback
- Why:
  - Eliminates import-time PyQt5 dependency in PySide6 runtime.

### 4) Camera UI import path compatibility guard
- File: `qtpyvcp/src/qtpyvcp/widgets/display_widgets/camera/camera_ui.py`
- Change:
  - PySide6-first import fallback for camera view widget class
- Why:
  - Prevents immediate import failure if PyQt5 is unavailable.

---

## ⚠️ Remaining high-priority items (recommended next)

### A) Camera widget implementation is still Qt5 API-based
- File: `qtpyvcp/src/qtpyvcp/widgets/display_widgets/camera/camera.py`
- Symptoms:
  - Uses legacy Qt5 camera API style (`setViewfinder`, old capture workflow) that is not a direct Qt6/PySide6 equivalent.
- Risk:
  - Runtime failure or partial non-functionality if camera widget is instantiated.
- Recommended fix:
  - Full Qt6 multimedia port:
    - replace viewfinder path with Qt6 video sink/output model
    - update capture/record flow to current PySide6 API classes
    - update error/lock/status handling to Qt6 enums and states

### B) Legacy CLI help text still advertises old bindings
- Files:
  - `qtpyvcp/src/qtpyvcp/app/__init__.py`
  - `qtpyvcp/src/qtpyvcp/utilities/opt_parser.py`
- Symptoms:
  - `--qt-api` help text lists only `pyqt5|pyqt|pyside2|pyside`
- Risk:
  - User confusion; possible misconfiguration expectations.
- Recommended fix:
  - Update docs/help text to include/reflect `pyside6` behavior (or deprecate option explicitly).

---

## 🟡 Medium-priority cleanup items

### C) Legacy package-name hints/messages
- Files include:
  - `qtpyvcp/src/qtpyvcp/widgets/input_widgets/gcode_editor.py`
  - `qtpyvcp/src/qtpyvcp/widgets/display_widgets/camera/camera.py`
  - `qtpyvcp/src/qtpyvcp/lib/dbus_notification.py`
- Symptoms:
  - Error messages still reference PyQt5-era package names.
- Risk:
  - Troubleshooting friction, but not usually a functional failure.
- Recommended fix:
  - Update package guidance strings for current PySide6 install paths.

---

## Verification notes
- Edited files passed syntax diagnostics after patching.
- Callback-risk scans for `actions/*` no longer show unsafe lambda channel subscriptions in current code.

---

## Suggested review sequence
1. Approve/plan full `camera.py` Qt6 port (largest remaining runtime risk).
2. Approve CLI/help text cleanup for `--qt-api`.
3. Approve message-string modernization pass.
4. Run targeted runtime test checklist after camera port.
