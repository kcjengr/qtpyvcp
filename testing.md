# QtPyVCP Testing Plan

## Current State

**1813 tests passing**, covering pure Python modules, DB models, plugin infrastructure, and Qt widgets (headless). No HAL/LinuxCNC integration tests yet. The `video_tests/` apps still render widgets visually without assertions.

### Line Coverage

| Metric | Value |
|--------|-------|
| Total statements | 20,718 |
| Covered | 15,627 |
| **Overall coverage** | **25%** |

### Source-to-Test Mapping (168 source files scanned)

| Status | Count |
|--------|-------|
| Directly tested | 52 |
| Transitively loaded | 64 |
| Not tested | 52 |

### Tier Breakdown

| Tier | Description | Total | Tested | Transitive | Not Tested |
|------|-------------|-------|--------|------------|------------|
| Tier 1 | Pure Python, no HAL/LinuxCNC | 61 | 27 | 15 | **19** |
| Tier 2 | Qt widgets, pytest-qt required | 37 | 18 | 9 | **10** |
| Tier 3 | Plugins with some HAL dependency | 18 | 5 | 11 | 2 |
| Tier 4+ | Require LinuxCNC/HAL integration | 52 | 6 | 29 | 17 |

### Coverage Summary

| Phase | Tests | Modules Covered |
|-------|-------|-----------------|
| Phase 1 (Easy) | 620 | `drill_ops`, `gcode_file`, `face_ops`, `misc`, `types`, `colored_formatter`, `runtime_config`, `settings`, `decorators`, `enums`, `yaml_filters`, `load_perf_summary` (52 tests), `dbus_notification` (36 tests), `base_op` + `drill_ops` (71 tests), `encode_utils` (13 tests), `system_diagnostics` (84 tests), `persistent_data_manager` (35 tests), `actions/__init__` (20 tests) |
| Phase 3 (Qt Widgets) | 601 | `LEDWidget`, `BarIndicatorBase`, `StatusLabel`, `EvalLineEdit`, `StatusLED`, `VCPFrame`, `VCPStackedWidget`, `BaseDialog`, `ErrorDialog`, `dialogs/__init__`, `RulesEditor`, `_DesignerPlugin`, `ActionButton`, `MDIButton`, `SubCallButton`, `ActionCheckBox`, `ActionSpinBox`, `VCPLineEdit`, `LEDButton`, `DialogButton`, `AboutDialog`, `ActiveGcodesTable`, `NotificationWidget`, `stylesheet` (14 tests), `shutdown_dialog` (13 tests), `probesim_dialog` (14 tests), `dro_label` (10 tests), `toolchange_dialog` (22 tests) (26 modules, ~601 tests) |
| Phase 2 (DB + Plugins) | 213 | `tool_table`, `plasma_processes`, `base_plugins`, `plugin_registry`, `clock` (39 tests), `settings` (17 tests) |
| Phase 3 (Qt Widgets) | 601 | `LEDWidget`, `BarIndicatorBase`, `StatusLabel`, `EvalLineEdit`, `StatusLED`, `VCPFrame`, `VCPStackedWidget`, `BaseDialog`, `ErrorDialog`, `dialogs/__init__`, `RulesEditor`, `_DesignerPlugin`, `ActionButton`, `MDIButton`, `SubCallButton`, `ActionCheckBox`, `ActionSpinBox`, `VCPLineEdit`, `LEDButton`, `DialogButton`, `AboutDialog`, `ActiveGcodesTable`, `NotificationWidget`, `shutdown_dialog` (13 tests), `probesim_dialog` (14 tests), `dro_label` (10 tests), `toolchange_dialog` (22 tests) (25 modules, ~601 tests) |

### Missing from Phase 1 (Easy tier) — PARTIAL

Note: Many modules listed below no longer exist in the codebase. Updated inventory:

Remaining untested Tier 1/2 modules (verified to exist):
- `lib/native_notification.py` — Qt widget, BaseDialog subclass (Medium)
- `utilities/machine_parameters.py` — .var file parsing (Easy)
- `utilities/obj_status.py` — LinuxCNC STATUS wrapper (Hard - HAL dep)
- `utilities/info.py` — INI file reader (Hard - linuxcnc.ini dep)
- `lib/logger.py` — TTYHandler with pyserial (Medium-Hard)

All Phase 1 modules now have tests:
- `utilities/settings.py` — 65 tests (Medium effort, uses mocked SETTINGS dict) ✅ **COMPLETE**
- `lib/decorators.py` — 22 tests (Easy, uses mocked logger) ✅ **COMPLETE**
- `app/enums.py` — 30 tests (Trivial, constant-value assertions) ✅ **COMPLETE**
- `utilities/yaml_filters.py` — 15 tests (Easy, env-var branching logic) ✅ **COMPLETE**
- `utilities/load_perf_summary.py` — 52 tests (Medium effort, perf_counter mocking, phase tracking state machine) ✅ **COMPLETE**
- `lib/dbus_notification.py` — 36 tests (Medium effort, dbus mocking, notification lifecycle, action callbacks, hint setters, DBus interface mocking) ✅ **COMPLETE**
- `ops/base_op.py` + `ops/drill_ops.py` — 71 tests (Easy-Medium, BaseGenerator init/start/end + DrillOps G-code cycles: drill/dwell/peck/chip_break/tap/rigid_tap/manual/hole_circle) ✅ **COMPLETE**
- `utilities/encode_utils.py` — 13 tests (Trivial, encoding list content verification) ✅ **COMPLETE**
- `utilities/system_diagnostics.py` — 84 tests (Medium effort, pure functions for system info: _run_command, _parse_colon_kv, _read_first_line, _human_gb_from_kb, _cpu_model, _network_interfaces, _linux_pretty_name, _graphics_lines_from_glxinfo, _linuxcnc_version, _probe_basic_version, build_system_diagnostics_report_lines) ✅ **COMPLETE**
- `plugins/persistent_data_manager.py` — 35 tests (Medium effort, JSON/Pickle serialization, getData/setData lifecycle, initialise/terminate with temp files) ✅ **COMPLETE**
- `actions/__init__.py` — 20 tests (Easy-Medium, InvalidAction exception, bindWidget string parsing: hyphen replacement, arg splitting, numeric conversion, toggle/jog-axis detection, IN_DESIGNER flag) ✅ **COMPLETE**

### Missing from Phase 2 (DB + Plugins tier) — PARTIAL

Remaining untested plugins:
- `plugins/clock.py` — 39 tests (Medium effort, QTimer + DataChannel patterns) ✅ **COMPLETE**
- `plugins/settings.py` — 17 tests (Medium effort, requires SETTINGS/CONFIG mocking via module reload) ✅ **COMPLETE**
- `plugins/notifications.py` — Hard (linuxcnc.error_channel dependency) → Phase 4
- `plugins/file_locations.py` — Hard (pyudev, OS calls) → Phase 4
- `plugins/positions.py` — Hard (STATUS/INFO dependencies) → Phase 4
- `plugins/db_tool_table.py` — Hard (linuxcnc.command + DB deps) → Phase 4
- `plugins/exported_hal.py` — Hard (HAL dependency) → Phase 4
- `plugins/gcode_properties.py` — Hard (machine_actions import) → Phase 4
- `plugins/offset_table.py` — Hard (HAL-dependent widget) → Phase 4
- `plugins/tool_table.py` — Hard (LinuxCNC tool table file format) → Phase 4
- `plugins/user_managment.py` — Hard (database + UI logic) → Phase 4
- `plugins/virtual_input_manager.py` — Hard (HAL pin binding) → Phase 4
- `plugins/status.py` — Hard (LinuxCNC STATUS wrapper) → Phase 4

## Testable Boundaries

Out of the 3 packages under `src/`, roughly **40% of qtpyvcp is pure Python** (no HAL/LinuxCNC dependency) and immediately testable:

| Tier | Modules | Effort |
|------|---------|--------|
| **Easy — pure logic** | `ops/drill_ops.py`, `ops/gcode_file.py`, `ops/face_ops.py`, `ops/base_op.py`, `utilities/misc.py`, `utilities/settings.py`, `lib/types.py`, `lib/decorators.py`, `lib/colored_formatter.py`, `app/runtime_config.py`, `app/enums.py`, `utilities/yaml_filters.py`, `utilities/load_perf_summary.py`, `lib/dbus_notification.py` | Assert output strings, value coercion, path normalization, phase tracking state machine, notification lifecycle with mocked DBus, G-code generation logic |
| **Medium — DB logic** | `lib/db_tool/tool_table.py`, `plugins/plasma_processes.py` (SQLAlchemy models) | In-memory SQLite round-trips |
| **Hard — HAL dependent** | `hal/`, plugins with `import linuxcnc`, widgets that bind to HAL pins | Requires mocking `_hal`, or running inside LinuxCNC simulation |
| **Qt widgets** | All UI widgets, VCP chooser, notifications | Requires Xvfb + `pytest-qt` (Phase 3 in progress) |

## Recommended Approach

### Phase 1: Infrastructure + Pure Python (Week 1) — COMPLETED

All modules from the original plan are now tested. Additional modules covered beyond the original scope include `settings.py`, `decorators.py`, `enums.py`, `yaml_filters.py`, `load_perf_summary.py` (52 tests: phase tracking, file matching, timing accumulation, formatting helpers, completeness checks), and `dbus_notification.py` (36 tests: urgency levels, notification lifecycle, action callbacks, hint setters, DBus interface mocking).

Run via:
```bash
poetry run pytest tests/
```

This gives you ~620 tests covering GCode generation (BaseGenerator, DrillOps canned cycles), FaceOps, misc utilities, path normalization, config loading, settings management, decorators, enum values, program load performance summary, DBus notifications, system diagnostics report builder, persistent data manager (JSON/Pickle), and action string parsing.

### Phase 2: DB Models + Plugin Registry (Week 2) — COMPLETED

213 tests covering `ToolTable`/`ToolModel` with in-memory SQLite, plugin registry lifecycle, base plugin CRUD channels, full `plasma_processes` SQLAlchemy model suite (CRUD operations, 11 model classes, CSV seeding), `Clock` plugin (39 tests: init, channels, getChannel URL parsing, tostring formatting, timer lifecycle, signal notifications), and `Settings` plugin (17 tests: init, getChannel with various types, initialise persistence loading, terminate saving logic with persistent/default filtering).

### Phase 3: Qt Widget Testing (Week 3+) — IN PROGRESS

Baseline established with 565+ tests across 21+ widget modules (up from 334):

- **LEDWidget** (31 tests) — Diameter, color, alignment, state, flashing, flashRate properties; size hints; focus policy; toggle/startFlashing/stopFlashing methods
- **BarIndicatorBase** (42 tests) — Value clamping, min/max, orientation, text formatting, gradient parsing, colors, border settings, Qt properties
- **StatusLabel** (33 tests) — setValue with various types, format strings, expression evaluation, invalid expression handling, inheritance
- **EvalLineEdit** (33 tests) — Expression evaluation via simpleeval, operator prefixes (+, *, /, -=, +=), sign toggle with `-`, error handling, return key binding
- **StatusLED** (25 tests) — State/flashing properties inherited from LEDWidget, rule properties (On, Flashing), Qt property access, size hints
- **VCPFrame** (13 tests) — Enable rule property, visibility, sizing, object naming
- **VCPStackedWidget** (35 tests) — Page management (add/remove/setCurrentIndex), setIndexValue with signal blocking, settingName property, currentChanged signal
- **BaseDialog** (22 tests) — Init, modality, window flags, UI loading, combined options
- **ErrorDialog** (25 tests) — Init, display, warning types, ignore list, quit app, exception types, edge cases
- **dialogs/__init__** (19 tests) — getDialog, showDialog, hideActiveDialog, hideDialog, askQuestion, ACTIVE_DIALOGS state
- **RulesEditor** (46 tests) — TableCheckButton, CompleterDelegate, RulesEditor init/UI/actions/validation/callbacks, ChanInfoDialog
- **_DesignerPlugin** (23 tests) — name, objectName, group, domXml, initialize, extensions, createWidget, includeFile
- **ActionButton** (17 tests) — VCPButton base, actionName property, bindWidget integration, click signal, text/icon setters
- **MDIButton** (20 tests) — MDICommand property, variable substitution (#<widget>), issueMDI with mocks, PARSE_VARS regex
- **SubCallButton** (19 tests) — filename property, callSub with file lookup, PARSE_POSITIONAL_ARGS regex, param #31 skip logic
- **ActionCheckBox** (13 tests) — QCheckBox wrapper, actionName binding, no focus policy, toggled signal
- **ActionSpinBox** (12 tests) — QSpinBox wrapper, actionName binding, valueChanged signal, range/step settings
- **VCPLineEdit** (14 tests) — Text rule property, actionName (bind disabled), returnPressed behavior, initialize/terminate
- **LEDButton** (19 tests) — ActionButton subclass, LED positioning, setLedState/setLedFlashing, diameter/color/alignment properties

#### Setup for Qt Widget Testing

Qt binding is configured via `pytest-env` in `pyproject.toml`. No manual setup required — just run:

```bash
# All tests (including widgets) run headlessly with Xvfb
poetry run pytest tests/ -v

# Only widget tests
poetry run pytest tests/widgets/ -v
```

#### Widget Test Patterns Established

1. **Fixtures in `tests/widgets/conftest.py`** — Use `qtbot.addWidget()` for proper cleanup
2. **Direct module imports** — Import directly from file paths (e.g., `importlib.util.spec_from_file_location`) to avoid triggering package `__init__.py` chains that pull in HAL-dependent modules like VTKBackPlot
3. **Property testing** — Use `qtpy.QtCore.Property` (not `pyqtProperty`) for Qt property type checks
4. **Timer signals** — Avoid `qtbot.waitSignal()` for QTimer; test state changes instead since event loop timing is unreliable in headless tests

#### Phase 3 Expansion Plan

Phase 3 covers all Qt widget testing, split into tiers by dependency complexity:

**Tier 1 — Zero workarounds needed (pure Qt widgets, no VCPWidget inheritance)**

| Module | Classes | Est. Tests | Actual | Status |
|--------|---------|------------|--------|--------|
| `dialogs/base_dialog.py` | `BaseDialog` | ~10 | 22 | ✅ Complete |
| `dialogs/error_dialog.py` | `ErrorDialog` | ~15 | 25 | ✅ Complete |
| `dialogs/__init__.py` (functions) | `getDialog()`, `showDialog()`, `hideActiveDialog()` | ~8 | 19 | ✅ Complete |
| `display_widgets/camera/camera.py` | `Camera` | ~20 | — | Deferred (QtMultimedia) |
| `qtdesigner/rules_editor.py` | `RulesEditor`, `ChanInfoDialog` | ~25 | 46 | ✅ Complete |
| `qtdesigner/designer_plugin.py` | `_DesignerPlugin` | ~12 | 23 | ✅ Complete |
| `dialogs/about_dialog.py` | `AboutDialog` | ~15 | 15 | ✅ Complete |

**Tier 2 — Simple patching (`qtpyvcp.hal` + `getPlugin()` mocks in conftest)**

These inherit from `VCPWidget`, which pulls in `from qtpyvcp import hal` at the top of `base_widget.py`. A conftest-level mock makes them testable. Mock plugins for `status`, `position`, and `notifications` are registered as autouse fixtures in `tests/widgets/conftest.py`.

| Module | Classes | Est. Tests | Actual | Status |
|--------|---------|------------|--------|--------|
| `display_widgets/bar_indicator.py` | `BarIndicatorBase` | ~15 | 42 | ✅ Complete |
| `display_widgets/active_gcodes_table.py` | `ActiveGcodesTable`, `ActiveGcodesModel` | ~30 | 31 | ✅ Complete |
| `display_widgets/notification_widget.py` | `NotificationWidget` | ~40 | 54 | ✅ Complete |

**Tier 2 — HAL component mocking (`qtpyvcp.hal.getComponent` pattern)**

These use `hal.getComponent()` to create userspace HAL components with pins and listeners. Mock the return value of `getComponent()` with a MagicMock that has `addPin()` and `addListener()` methods returning mock pin objects with `.value` attributes.

| Module | Classes | Est. Tests | Actual | Status |
|--------|---------|------------|--------|--------|
| `dialogs/shutdown_dialog.py` | `ShutDownDialog` | ~10 | 13 | ✅ Complete |
| `dialogs/probesim_dialog.py` | `ProbeSim` | ~10 | 14 | ✅ Complete |
| `display_widgets/dro_label.py` / `dro_base_widget.py` | `DROLabel`, `DROBaseWidget` | ~8 | 10 | ✅ Complete |
| `dialogs/toolchange_dialog.py` | `ToolChangeDialog` | ~15 | 22 | ✅ Complete |

**Tier 2 — Deferred (requires deeper mocking)**

These have module-level `INFO = Info()` or `linuxcnc.command/stat()` calls that block instantiation. Better suited for Phase 3B/4:

| Module | Classes | Notes | Status |
|--------|---------|-------|--------|
| `form_widgets/probe_widget/probe.py` | `SubCaller` | `linuxcnc.command/stat()`, loads .ui file, needs subroutine path | Phase 4 |

**Tier 3A — VCPButton subclasses with mock status plugin in conftest**

These inherit from `VCPButton`, which calls `getPlugin('status')` in `__init__`. A module-level mock in `tests/widgets/conftest.py` makes them testable. The mock registers a MagicMock as the 'status' plugin with `isLocked()` returning False.

| Module | Classes | Est. Tests | Actual | Status |
|--------|---------|------------|--------|--------|
| `button_widgets/action_button.py` | `ActionButton` | ~12 | 17 | ✅ Complete |
| `button_widgets/mdi_button.py` | `MDIButton` | ~15 | 20 | ✅ Complete |
| `button_widgets/subcall_button.py` | `SubCallButton` | ~15 | 19 | ✅ Complete |
| `button_widgets/action_checkbox.py` | `ActionCheckBox` | ~8 | 13 | ✅ Complete |
| `button_widgets/action_spinbox.py` | `ActionSpinBox` | ~8 | 12 | ✅ Complete |
| `input_widgets/line_edit.py` | `VCPLineEdit` | ~10 | 14 | ✅ Complete |
| `button_widgets/led_button.py` | `LEDButton` | ~15 | 19 | ✅ Complete |
| `button_widgets/dialog_button.py` | `DialogButton` | ~10 | 11 | ✅ Complete |

**Tier 3B — Deep mocking (module-level `Info()` calls, machine_actions imports)**

These have top-level `INFO = Info()` or import `machine_actions` which requires LinuxCNC STATUS. Would need deeper mocking or are better suited for Phase 4 integration tests:

- `hal_widgets/` (12 files) — HAL pin binding → **Phase 4 candidate**
- `display_widgets/dro_widget.py`, `notification_widget.py`, `gcode_properties.py` → **Phase 3B or 4**
- `menus/homing_menu.py`, `recent_files_menu.py` → **Phase 3B or 4**
- `form_widgets/main_window.py` → **Phase 4 candidate**
- `display_widgets/vtk_backplot/` — requires VTK + linuxcnc mock → **Phase 4**

### Phase 2.5: Additional Plugin Testing (Ongoing)

Plugins that are testable with proper mocking (no HAL/LinuxCNC dependency in core logic):

| Module | Est. Tests | Actual | Status |
|--------|------------|--------|--------|
| `plugins/clock.py` | ~30 | 39 | ✅ Complete |
| `plugins/settings.py` | ~15 | 17 | ✅ Complete |
| `plugins/persistent_data_manager.py` | ~20 | 35 | ✅ Complete |
| `actions/__init__.py` | ~15 | 20 | ✅ Complete |
| `utilities/system_diagnostics.py` | ~40 | 84 | ✅ Complete |
| `plugins/notifications.py` | ~40 | — | ⏳ Phase 4 (linuxcnc.error_channel) |
| `plugins/file_locations.py` | ~25 | — | ⏳ Phase 4 (pyudev, OS calls) |
| `plugins/positions.py` | ~30 | — | ⏳ Phase 4 (STATUS/INFO) |

#### Widget Test Setup Notes

A module-level mock of the 'status' plugin is registered in `tests/widgets/conftest.py` to allow `VCPButton` subclasses to be instantiated without LinuxCNC. The fixture re-registers after each test to survive `_PLUGINS.clear()` from other test fixtures (e.g., `clean_registry` in `test_plugin_registry.py`).

### Phase 4: HAL/LinuxCNC Integration Tests (Ongoing) — NOT STARTED

These require a running LinuxCNC sim instance. Consider a separate test suite that spawns `linuxcnc --sim` and validates widget behavior against real HAL signals. This could be gated behind a `pytest.mark.integration` marker so the fast CI path stays clean.

## Key Decisions to Make

1. **Test directory location** — root-level `tests/` (chosen, already in place) vs `src/tests/`. Root-level is more conventional for Poetry and is what we're using now.

2. **CI integration** — GitHub Actions to run pytest on PRs, or keep testing purely local for now?

3. **HAL mocking strategy** — Mock the `_hal` C extension, or spin up LinuxCNC sim in a container/subprocess per test suite?

4. **Qt binding consistency** — Project uses `qtpy` abstraction layer. Tests require PyQt5 (set via `PYTEST_QT_API=pyqt5`). Both PyQt5 and PyQt6 may be installed, but pytest-qt must use the same binding as the application code.
