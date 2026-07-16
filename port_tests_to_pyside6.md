# Porting Tests from qtpyvcp (PyQt5) to qtpyvcp_pyside6

## Current State

| | qtpyvcp (PyQt5) | qtpyvcp_pyside6 |
|---|---|---|
| **Tests directory** | `tests/` with 67 files, ~245 tests | **Does not exist** |
| **Test framework** | pytest + pytest-qt + pytest-xvfb + pytest-env | None configured |
| **Dev dependencies** | `pytest ^7.4`, `pytest-qt ^4.2`, `pytest-xvfb ^3.1`, `pytest-env ^1.1` | None |
| **pytest config** | `[tool.pytest.ini_options]` + `[tool.pytest_env]` with `QT_API = "pyqt5"` | Missing entirely |
| **conftest.py** | Root (LinuxCNC/HAL mocking) + widgets/ (widget fixtures) | None |
| **Qt abstraction** | Uses `qtpy` exclusively in tests | Abandons qtpy; source imports `PySide6.*` directly |

---

## Porting Plan

### 1. Infrastructure Setup (copy verbatim, then adapt)

**a) pyproject.toml changes:**
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-qt = "^4.2"
pytest-xvfb = "^3.1"
pytest-env = "^1.1"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.pytest_env]
QT_API = "pyside6"
PYTEST_QT_API = "pyside6"
```

**b) Copy `tests/conftest.py` and `tests/widgets/conftest.py` as-is.** These files mock LinuxCNC/HAL — they don't import Qt bindings directly, so they'll work without modification.

**c) Copy all 67 test files** into the pyside6 project's `tests/` directory with the same structure.

### 2. Code Changes Required in Tests (minimal)

The tests themselves use `qtpy` for imports, but the **pyside6 project source code does not use qtpy** — it imports `PySide6.*` directly. This means two approaches:

**Option A (Recommended): Add qtpy support to pyside6 project.**
- Make the few remaining direct `PySide6` imports in the source conditional via `qtpy`, or add a compatibility shim.
- Then tests import from `qtpy.*` and everything works transparently.
- This is the cleanest path since all 245 existing tests already use `qtpy`.

**Option B: Rewrite test imports to match PySide6 direct imports.**
- Change all `from qtpy.QtWidgets import ...` → `from PySide6.QtWidgets import ...` across 67 test files.
- This is high-effort and loses cross-binding compatibility.

### 3. Test-Specific Adaptations (if Option B, or for any hardcoded Qt behavior)

| Change | Where | PyQt5 | PySide6 |
|---|---|---|---|
| Dialog return values | Tests checking `dialog.exec_()` | `QDialog.Accepted` (int) | `QDialog.DialogCode.Accepted` (enum class) |
| Screen geometry | Widget tests with positioning | `QDesktopWidget().screenGeometry()` | `QApplication.primaryScreen().geometry()` |
| `exec()` return type | Tests asserting dialog results | Returns `int` | Returns `QDialog.DialogCode` |

**Most widget tests won't be affected** — they use `qtbot` signal/blocking utilities and don't assert on exec return values. The ~30 widget tests that open dialogs (error dialogs, about dialog, shutdown dialog, tool change dialog) may need minor enum updates.

### 4. New Tests to Write for pyside6-Only Files

17 files exist only in the pyside6 project and need new test coverage:
- `native/backplot_cpp/bridge.py` — C++ bridge tests
- `utilities/pyside_ui_loader.py` — UI loader tests
- `utilities/qt_safety.py` — Shiboken6 validity checks
- `utilities/runtime_ui_loader.py` — Runtime UI loading with custom widget registration
- `widgets/register_widgets.py` — Widget/Designer plugin registration
- `plugins/var_file_manager.py` — Variable file manager CRUD
- `widgets/button_widgets/vcpvar_button.py` — Variable button widget
- `widgets/input_widgets/var_line_edit.py` — Variable line edit
- `widgets/base_widgets/var_widget_mixin.py` — Mixin tests
- `widgets/taskmenuextension/` (5 files) — Designer task menu extension tests

### 5. Known Test Failures to Anticipate

| Area | Reason | Fix |
|---|---|---|
| `test_designer_plugin.py` | Designer plugin uses PySide6-specific APIs | Already pyside6-native, verify compatibility |
| `test_probesim_widget.py`, `test_probesim_dialog.py` | VTK/OpenGL setup (`QGLFormat` removed in Qt6) | Mock or skip OpenGL-dependent tests |
| `test_action_*` widgets with rules | Rules engine references to `Q_ENUMS` | Source has no-op fallback, should pass |
| `test_virtual_input_manager.py` | Uses `QDesktopWidget` in source | Source already migrated to `primaryScreen()` in pyside6 |

---

## Recommended Order of Operations

1. **Copy the entire `tests/` directory** from qtpyvcp → qtpyvcp_pyside6
2. **Add dev dependencies + pytest config** to pyside6's pyproject.toml
3. **Run `pytest tests/`** — non-Qt tests (lib/, ops/, utilities/, plugins/ non-widget) should pass immediately since they don't depend on Qt bindings
4. **Fix enum/assertion issues** in dialog-related widget tests (~5-10 files)
5. **Mock/skip OpenGL-dependent tests** (probesim, backplot)
6. **Write new tests** for the 17 pyside6-only source files
