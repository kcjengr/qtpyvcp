# Porting Tests from qtpyvcp_pyqt5 (PyQt5) to qtpyvcp_pyside6 (PySide6)

## Current State

|                      | qtpyvcp_pyqt5 (PyQt5)                                                     | qtpyvcp_pyside6 (PySide6)                                    |
| -------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------ |
| **Tests directory**  | `tests/` with 67 files, ~245 tests                                        | **`tests/` exists with 69 test files**                       |
| **Test framework**   | pytest + pytest-qt + pytest-xvfb + pytest-env                             | **Configured: pytest + pytest-qt + pytest-xvfb + pytest-env** |
| **Dev dependencies** | `pytest ^7.4`, `pytest-qt ^4.2`, `pytest-xvfb ^3.1`, `pytest-env ^1.1`    | **All 4 packages in `[tool.poetry.group.dev.dependencies]`** |
| **pytest config**    | `[tool.pytest.ini_options]` + `[tool.pytest_env]` with `QT_API = "pyqt5"` | **Present with `QT_API = "pyside6"`, `PYTEST_QT_API = "pyside6"`** |
| **conftest.py**      | Root (LinuxCNC/HAL mocking) + widgets/ (widget fixtures)                  | **Both present: root + `tests/widgets/conftest.py`**         |
| **Qt abstraction**   | Uses `qtpy` exclusively in tests                                          | **Tests use `qtpy` exclusively (0 direct PySide6 imports)**  |

---

## Porting Plan

### 1. Infrastructure Setup (copy verbatim, then adapt) ✅ **DONE**

**a) pyproject.toml changes:** ✅ **DONE** — All 4 dev dependencies present in `[tool.poetry.group.dev.dependencies]`, pytest config with `QT_API = "pyside6"` added.

**b) Copy `tests/conftest.py` and `tests/widgets/conftest.py` as-is.** ✅ **DONE** — Both files present with LinuxCNC/HAL mocking (no Qt binding imports).

**c) Copy all 67 test files** ✅ **DONE** — 69 test files copied into `tests/` with structure: `lib/`, `ops/`, `plugins/`, `utilities/`, `widgets/`, `actions/`, `app/`.

### 2. Code Changes Required in Tests (minimal) ✅ **NOT NEEDED**

The tests use `qtpy` for imports and all 1365 Qt import references use `qtpy.*` — zero direct `PySide6` imports in test files. Since the pyside6 source code uses PySide6 directly but tests import from qtpy, pytest-qt with `QT_API=pyside6` resolves qtpy to PySide6 at runtime. No test-side changes required.

**Option A (Recommended): Add qtpy support to pyside6 project.** ✅ **Already the case** — tests use qtpy exclusively, pytest-qt bridges to PySide6 via `QT_API=pyside6` env var.

**Option B: Rewrite test imports to match PySide6 direct imports.** ❌ **Not pursued** — would require changes across all 69 test files and lose cross-binding compatibility.

### 3. Test-Specific Adaptations for PySide6 behavior

| Change               | Where                           | PyQt5                               | PySide6                                    |
| -------------------- | ------------------------------- | ----------------------------------- | ------------------------------------------ |
| Dialog return values | Tests checking `dialog.exec_()` | `QDialog.Accepted` (int)            | `QDialog.DialogCode.Accepted` (enum class) |
| Screen geometry      | Widget tests with positioning   | `QDesktopWidget().screenGeometry()` | `QApplication.primaryScreen().geometry()`  |
| `exec()` return type | Tests asserting dialog results  | Returns `int`                       | Returns `QDialog.DialogCode`               |

**Most widget tests won't be affected** — they use `qtbot` signal/blocking utilities and don't assert on exec return values. The ~30 widget tests that open dialogs (error dialogs, about dialog, shutdown dialog, tool change dialog) may need minor enum updates. **Status: TBD — pending pytest run to identify which tests actually fail.**

### 4. New Tests to Write for pyside6-Only Files

All source files below exist and have no test coverage:

| Source File | Coverage Needed | Test File Status |
|-------------|-----------------|------------------|
| `native/backplot_cpp/bridge.py` | C++ bridge tests | ❌ No test file |
| `utilities/pyside_ui_loader.py` | UI loader tests | ❌ No test file |
| `utilities/qt_safety.py` | Shiboken6 validity checks | ❌ No test file |
| `utilities/runtime_ui_loader.py` | Runtime UI loading with custom widget registration | ❌ No test file |
| `widgets/register_widgets.py` | Widget/Designer plugin registration | ❌ No test file |
| `plugins/var_file_manager.py` | Variable file manager CRUD | ❌ No test file |
| `widgets/button_widgets/vcpvar_button.py` | Variable button widget | ❌ No test file |
| `widgets/input_widgets/var_line_edit.py` | Variable line edit | ❌ No test file |
| `widgets/base_widgets/var_widget_mixin.py` | Mixin tests | ❌ No test file |
| `widgets/taskmenuextension/` (5 files) | Designer task menu extension tests | ❌ No test file |

### 5. Known Test Failures to Anticipate

| Area                                                 | Reason                                        | Fix                                                     | Status        |
| ---------------------------------------------------- | --------------------------------------------- | ------------------------------------------------------- | ------------- |
| `test_designer_plugin.py`                            | Designer plugin uses PySide6-specific APIs    | Already pyside6-native, verify compatibility            | TBD           |
| `test_probesim_widget.py`, `test_probesim_dialog.py` | VTK/OpenGL setup (`QGLFormat` removed in Qt6) | Mock or skip OpenGL-dependent tests                     | TBD           |
| `test_action_*` widgets with rules                   | Rules engine references to `Q_ENUMS`          | Source has no-op fallback, should pass                  | TBD           |
| `test_virtual_input_manager.py`                      | Uses `QDesktopWidget` in source               | Source already migrated to `primaryScreen()` in pyside6 | TBD           |

**Note:** All items marked "TBD" — actual failures will be known after running `pytest tests/`.

---

## Recommended Order of Operations

1. ~~**Copy the entire `tests/` directory** from qtpyvcp → qtpyvcp_pyside6~~ ✅ **DONE** — 69 test files in place
2. ~~**Add dev dependencies + pytest config** to pyside6's pyproject.toml~~ ✅ **DONE** — all 4 pytest packages + config with `QT_API=pyside6`
3. **Run `pytest tests/`** — non-Qt tests (lib/, ops/, utilities/, plugins/ non-widget) should pass immediately since they don't depend on Qt bindings
4. **Fix enum/assertion issues** in dialog-related widget tests (~5-10 files)
5. **Mock/skip OpenGL-dependent tests** (probesim, backplot)
6. **Write new tests** for the 10 pyside6-only source files listed in section 4

(End of file - total 83 lines)
