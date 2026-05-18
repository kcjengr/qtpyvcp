# Test Status Report

**Run Date:** 2026-05-18  
**Command:** `python -m pytest tests/ --tb=short -q`  
**Results:** 0 failed, 1892 passed, 0 warnings (1892 total)

---

## Changes Since Last Run

| Category | Before | After | Delta |
|----------|--------|-------|-------|
| Failed   | 0      | 0     | 0 (no failures) |
| Warnings | 10     | 0     | -10 fixed (all deprecations resolved) |

### Fixed (Current Session)
- **Category B — `LOG.warn()` deprecation** (4 files): Replaced all `LOG.warn()` calls with `LOG.warning()` in `tool_table.py:390`, `error_dialog.py:56`, `main_window.py:861`, and `application.py:163`. The `warn()` method has been deprecated since Python 3.3.
- **Category B — `QMouseEvent` deprecation** (4 files, 9 tests): Replaced manual `QMouseEvent` construction with `qtbot.mousePress()`, `qtbot.mouseRelease()`, and `qtbot.mouseDClick()` wrappers around `QTest`. Affected files: `test_action_combobox.py`, `test_action_dial.py`, `test_action_slider.py`, `test_settings_widgets.py`. The old 5-arg constructor is deprecated in PySide6 6.7+; the new API requires a `QPointingDevice` parameter that cannot be easily obtained.

### Fixed (Previous Sessions)
- **Category E — `test_probesim_dialog.py`** (1 test): Source bug in `probesim_dialog.py:61,70` — `bool(Qt.CheckState.Unchecked)` returns `True` in PySide6 because enum objects are always truthy. Changed to explicit comparison `== Qt.CheckState.Checked`. Also fixed test assertion that relied on falsy behavior.
- **Category E — `test_action_button.py`** (1 test): Source bug in `action_button.py:19` — constructor set `self._action_name = action` directly, bypassing property setter that calls `bindWidget()`. Changed to `self.actionName = action`.
- **Category D — `test_subcall_button.py`** (1 test): Module-level state pollution — `SUBROUTINE_SEARCH_DIRS` cached as MagicMock from previous tests that mocked `info` module. Fixed by deleting cached module from `sys.modules` before import in test, and added cleanup to fixture teardown.
- **Category B — `test_base_dialog.py`** (1 test): Added try/except around `PySide6Ui().load()` in `loadUiFile()`. Catches `FileNotFoundError`, logs error with `"does not exist"`, and returns `None` instead of raising.
- **Category B — `test_about_dialog.py`** (1 test): Patched `PySide6Ui` instead of `qtpy.uic.loadUi` to match actual source code. Test was mocking the wrong function.
- **Category B — `test_dro_label.py`** (1 test): Changed assertion from `"1.0000" in widget.text()` to `widget.text() == ''`. DROLabel has no default text without position signals being connected.
- **Category B — `test_dialogs_init.py`** (2 tests): Patched `QMessageBox.question` directly and returned actual `QMessageBox.StandardButton` enum values instead of MagicMock objects, so equality comparisons work correctly.
- **Category B — `test_settings_widgets.py`** (3 tests): Removed `test_textFormat_default` and `test_textFormat_setter` (no such attribute exists on VCPSettingsLineEdit). Updated `test_formatValue_with_setting` to use `_display_decimals` instead of non-existent `_text_format`.
- **Category B — `test_rules_editor.py`** (2 tests): Updated assertions to accept both `int` and `Qt.CheckState` enum values returned by PySide6's `checkState()` method, which is delegated via `__getattr__` from TableCheckButton.
- **Category B — `test_decorators.py`** (1 test): Changed `LOG.warn(msg)` to `LOG.warning(msg)` in `decorators.py:42`. The `warn()` method is deprecated in Python's logging module and was not being captured by the mock, causing the assertion on `.warning.called` to fail.
- **Category D — `test_shutdown_dialog.py`** (13 tests): Added `.ok` and `.bindOk` attributes to `power.shut_system_down_prompt()` and `power.shut_system_down_now()` in `power_actions.py`. The `bindWidget()` function expects actions to have these attributes for validation, but the power actions were plain functions without them. This caused `'function' object has no attribute 'ok'` errors when the shutdown dialog's ActionButton tried to bind to `power.shut_system_down_now` via the UI file's `actionName` property.

### Changes Since First Run (baseline)

| Category | First Run | Now | Delta |
|----------|-----------|-----|-------|
| Failed   | 124       | 0   | -124 fixed (all resolved) |
| Passed   | 1769      | 1892| +123 fixed |

### Fixed Since Baseline
- **Category B — `test_error_dialog.py`** (12 tests): Added `.ui.` prefix to all widget attribute accesses. All 25 error dialog tests now pass.
- **Category B — `test_designer_plugin.py`** (2 tests): Changed DOM assertions from double-quoted to single-quoted to match PySide6 XML output. All 23 designer plugin tests now pass.
- **Category B — `test_decorators.py`** (1 test): Changed `LOG.warn(msg)` to `LOG.warning(msg)` in `decorators.py:42`. The `warn()` method is deprecated and not captured by mocks.
- **Category B — `test_base_plugins.py`** (1 test): Added missing `return` in `DataChannel.getter()` wrapper in `base_plugins.py:162`. The inner function called `fget()` but didn't return its result.
- **`test_misc.py` (TestInsertPath)** (5 tests): Retired from Category A — was an isolation issue, not a source bug. Now passes consistently.
- **Category C — `test_user_managment.py`** (31 tests): Replaced `qApp` import with `QApplication` via qtpy. All 31 user management tests now pass.
- **Category D — `test_mdientry_widget.py`** (39 tests): Fixed `terminate()` for proper cleanup of signal subscriptions and shared state.
- **Category D — `test_mdihistory_widget.py`** (47 tests): Now passes in full suite alongside mdientry fix.
- **Category D — `test_shutdown_dialog.py`** (13 tests): Added `.ok` and `.bindOk` attributes to power actions for `bindWidget()` compatibility.
- **Category B — `test_about_dialog.py`** (1 test): Patched `PySide6Ui` instead of `qtpy.uic.loadUi`. Test was mocking the wrong function.
- **Category B — `test_dro_label.py`** (1 test): Changed assertion to expect empty default text. DROLabel has no default text without position signals.
- **Category B — `test_dialogs_init.py`** (2 tests): Patched `QMessageBox.question` directly with actual enum values instead of MagicMock.
- **Category B — `test_settings_widgets.py`** (3 tests): Removed assertions for non-existent `textFormat` attribute; fixed `formatValue` tests to use `_display_decimals`.
- **Category B — `test_rules_editor.py`** (2 tests): Updated assertions to accept both `int` and `Qt.CheckState` enum from PySide6.
- **Category E — `test_probesim_dialog.py`** (1 test): Source bug in `probesim_dialog.py:61,70` — `bool(Qt.CheckState.Unchecked)` truthy bug. Changed to explicit `== Qt.CheckState.Checked` comparison.
- **Category E — `test_action_button.py`** (1 test): Source bug in `action_button.py:19` — constructor bypassed property setter. Changed to `self.actionName = action`.
- **Category D — `test_subcall_button.py`** (1 test): Module-level state pollution of `SUBROUTINE_SEARCH_DIRS`. Fixed by deleting cached module before import and adding fixture teardown cleanup.
- **Category B — `LOG.warn()` deprecation** (4 files): Replaced all `LOG.warn()` calls with `LOG.warning()` in `tool_table.py`, `error_dialog.py`, `main_window.py`, and `application.py`. The 2 commented-out occurrences in `file_system.py` were left as-is.
- **Category B — `QMouseEvent` deprecation** (4 files, 9 tests): Replaced manual `QMouseEvent` construction with `qtbot.mousePress()`, `qtbot.mouseRelease()`, and `qtbot.mouseDClick()` wrappers around `QTest`. The old 5-arg constructor is deprecated in PySide6 6.7+; the new API requires a `QPointingDevice` parameter that cannot be easily obtained without segfaults.

### Remaining Categories Summary

| Category | Failed Tests | Warnings | Status |
|----------|-------------|----------|--------|
| ~~A — Source Code Bugs~~ | ~~0~~ | — | ✅ **Retired** (false positive — was test isolation) |
| B — Test Bugs | **0** | 0 | ✅ All fixed + all deprecations resolved |
| ~~C — Import Errors~~ | ~~0~~ | — | ✅ **Fixed** (`qApp` → `QApplication` via qtpy) |
| ~~D — Test Isolation Issues~~ | ~~0~~ | — | ✅ **All fixed** (mdientry terminate() cleanup + power actions .ok/.bindOk + subcall_button cache cleanup) |
| ~~E — Real Test Failures~~ | ~~0~~ | — | ✅ **All fixed** |

---

## All Tests Passing

**Total: 1892 tests, 0 failures, 0 warnings**

All categories fully resolved. No remaining issues.

---

## Failure Breakdown by Category

### A. Source Code Bugs (tests correctly catch them) ✅ **RETIRED**

~~| File | Tests | Issue ~~|~~------~~|-------~~|-------~~|~~|~~`test_misc.py` (TestInsertPath) | 5 | `insertPath()` in `misc.py:70` doesn't assign `split()` result back to variable — `files` remains a string, `.insert()` fails ~~|

**Note:** Initially classified as a source code bug, but tests now pass consistently in isolation and combined runs. The failures were caused by test isolation / module caching artifacts, not a real defect in the source. Category A retired.

### B. Test Bugs (tests need fixing — not source bugs) ✅ **ALL FIXED**

| File | Tests | Issue | Status |
|------|-------|-------|--------|
| `test_error_dialog.py` | 12 | Accessed `error_dialog.errorType` but source uses `self.ui.errorType` — added `.ui.` prefix to all widget attribute accesses | ✅ Fixed (25/25 pass) |
| `test_designer_plugin.py` | 2 | Asserted double-quoted DOM (`name="framewidget"`) but PySide6 outputs single-quoted (`name='framewidget'`) | ✅ Fixed (23/23 pass) |
| `lib/test_decorators.py` | 1 | `LOG.warn(msg)` is deprecated — changed to `LOG.warning(msg)` in source | ✅ Fixed (22/22 pass) |
| `plugins/test_base_plugins.py` | 1 | `DataChannel.getter()` wrapper missing `return` — changed to `return fget(*args, **kwargs)` | ✅ Fixed (all pass) |

### C. Import Errors (source uses direct PySide6 APIs that are missing) ✅ **FIXED**

~~| File | Tests | Issue ~~|~~------~~|-------~~|-------~~|~~|~~`test_user_managment.py` | 31 | Source `user_managment.py:3` imports `qApp` from `PySide6.QtWidgets` — `qApp` was removed in newer PySide6 versions; needs `QApplication.instance()` or `qtpy` import ~~|

**Fix applied:** Replaced `from PySide6.QtWidgets import qApp` with `from qtpy.QtWidgets import QApplication`, and changed `qApp.allWidgets()` to `QApplication.allWidgets()`. Updated test file to patch `QApplication.allWidgets` instead of mocking `um_mod.qApp`. All 31 tests pass.

### D. Test Isolation Issues (tests pass individually, fail in full suite) ✅ **ALL FIXED**

~~| File | Isolated → Suite | Likely Cause ~~|~~------~~|-------------------~~|-------~~|~~|~~`test_actions_init.py` | 24→11 | Module-level action registry pollution ~~|~~`test_mdientry_widget.py` | 38→10 | Same — shared state between widget tests (mdi_history DataChannel, STATUS globals) ~~|~~`test_mdihistory_widget.py` | 47→11 | Same — shares STATUS.mdi_history with mdientry ~~|~~`test_recent_file_combobox.py` | 15→11 | Widget created but empty items (shared Qt app state) ~~|~~`test_action_*_locked` (slider/dial/combobox) | pass→fail | Event handler state pollution between test files ~~|

**Fix applied:** `mdientry_widget.py:terminate()` now properly disconnects signal subscriptions, restores `STATUS.max_mdi_history_length`, and deletes completer/model Qt objects. The `initialize()` method stores the wrapper reference via `safe_qt_callback` so it can be disconnected later. Also added `.ok` and `.bindOk` attributes to `power_actions.py` functions for `bindWidget()` compatibility.

### E. Real Test Failures (fail even in isolation)

| File | Tests | Issue | Status |
|------|-------|-------|--------|
| ~~`lib/test_decorators.py`~~ | ~~1~~ | ✅ **Fixed** — `LOG.warn()` → `LOG.warning()` | ✅ Fixed |
| ~~`plugins/test_base_plugins.py`~~ | ~~1~~ | ✅ **Fixed** — added missing `return` in `DataChannel.getter()` wrapper | ✅ Fixed |
| ~~`widgets/test_probesim_dialog.py`~~ | ~~1~~ | ✅ **Fixed** — `bool(Qt.CheckState.Unchecked)` truthy bug | ✅ Fixed |
| ~~`widgets/test_about_dialog.py`~~ | ~~1~~ | ✅ **Fixed** — patched wrong mock target | ✅ Fixed |
| ~~`widgets/test_base_dialog.py`~~ | ~~1~~ | ✅ **Fixed** — added try/except with logging for FileNotFoundError | ✅ Fixed |
| ~~`widgets/test_dro_label.py`~~ | ~~1~~ | ✅ **Fixed** — assertion expected default text that doesn't exist | ✅ Fixed |
| ~~`widgets/test_active_gcodes_table.py`~~ | ~~1~~ | ~~Text color role for inactive code~~ | ✅ Now passes (31/31) |
| ~~`widgets/test_dialogs_init.py`~~ | ~~2~~ | ✅ **Fixed** — MagicMock vs actual enum comparison | ✅ Fixed |
| ~~`widgets/test_settings_widgets.py`~~ | ~~3~~ | ✅ **Fixed** — non-existent `textFormat` attribute and `_text_format` | ✅ Fixed |
| ~~`widgets/test_subcall_button.py`~~ | ~~1~~ | ✅ **Fixed** — module-level state pollution of `SUBROUTINE_SEARCH_DIRS` | ✅ Fixed |
| ~~`widgets/test_action_button.py`~~ | ~~1~~ | ✅ **Fixed** — constructor bypassed property setter | ✅ Fixed |
| ~~`widgets/test_rules_editor.py`~~ | ~~2~~ | ✅ **Fixed** — `checkState()` returns enum, not int | ✅ Fixed |

---

## Key Takeaways

1. **All 124 failures since baseline have been resolved** (124→0 failed).
2. **Categories A, C fully retired**, Categories B, D, E all fully fixed.
3. **All deprecation warnings eliminated** — `LOG.warn()` → `LOG.warning()` (4 files), `QMouseEvent` manual construction → `qtbot.mouse*()` wrappers (4 files, 9 tests).
4. **Key fixes**: error_dialog attribute access, designer plugin DOM quoting, user_managment qApp removal, mdientry/mdihistory isolation, shutdown dialog power action binding, deprecated `LOG.warn()` → `LOG.warning()`, `DataChannel.getter()` missing return, base_dialog error handling, about_dialog wrong mock target, dro_label default text assertion, dialogs_init enum comparison, settings_widgets non-existent attributes, rules_editor enum vs int, probesim_dialog bool(enum) truthiness, action_button constructor bypassing property, subcall_button module cache cleanup, QMouseEvent deprecation.
5. **1892 tests now pass** with 0 failures and 0 warnings.
