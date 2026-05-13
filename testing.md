# QtPyVCP Testing Plan

## Current State

**715 tests passing**, covering pure Python modules, DB models, plugin infrastructure, and Qt widgets (headless). No HAL/LinuxCNC integration tests yet. The `video_tests/` apps still render widgets visually without assertions.

### Coverage Summary

| Phase | Tests | Modules Covered |
|-------|-------|-----------------|
| Phase 1 (Easy) | 260 | `drill_ops`, `gcode_file`, `face_ops`, `misc`, `types`, `colored_formatter`, `runtime_config`, `settings`, `decorators`, `enums`, `yaml_filters` |
| Phase 2 (DB + Plugins) | 157 | `tool_table`, `plasma_processes`, `base_plugins`, `plugin_registry` |
| Phase 3 (Qt Widgets) | 199 | `LEDWidget`, `BarIndicatorBase`, `StatusLabel`, `EvalLineEdit`, `StatusLED`, `VCPFrame`, `VCPStackedWidget` |

### Missing from Phase 1 (Easy tier) — ALL COMPLETE

All Phase 1 modules now have tests:
- `utilities/settings.py` — 65 tests (Medium effort, uses mocked SETTINGS dict)
- `lib/decorators.py` — 22 tests (Easy, uses mocked logger)
- `app/enums.py` — 30 tests (Trivial, constant-value assertions)
- `utilities/yaml_filters.py` — 15 tests (Easy, env-var branching logic)

## Testable Boundaries

Out of the 3 packages under `src/`, roughly **40% of qtpyvcp is pure Python** (no HAL/LinuxCNC dependency) and immediately testable:

| Tier | Modules | Effort |
|------|---------|--------|
| **Easy — pure logic** | `ops/drill_ops.py`, `ops/gcode_file.py`, `ops/face_ops.py`, `utilities/misc.py`, `utilities/settings.py`, `lib/types.py`, `lib/decorators.py`, `lib/colored_formatter.py`, `app/runtime_config.py`, `app/enums.py`, `utilities/yaml_filters.py` | Assert output strings, value coercion, path normalization |
| **Medium — DB logic** | `lib/db_tool/tool_table.py`, `plugins/plasma_processes.py` (SQLAlchemy models) | In-memory SQLite round-trips |
| **Hard — HAL dependent** | `hal/`, plugins with `import linuxcnc`, widgets that bind to HAL pins | Requires mocking `_hal`, or running inside LinuxCNC simulation |
| **Qt widgets** | All UI widgets, VCP chooser, notifications | Requires Xvfb + `pytest-qt` (Phase 3 in progress) |

## Recommended Approach

### Phase 1: Infrastructure + Pure Python (Week 1) — COMPLETED

All modules from the original plan are now tested. Additional modules covered beyond the original scope include `settings.py`, `decorators.py`, `enums.py`, and `yaml_filters.py`.

Run via:
```bash
poetry run pytest tests/
```

This gives you ~260 tests covering GCode generation, misc utilities, path normalization, config loading, settings management, decorators, and enum values.

### Phase 2: DB Models + Plugin Registry (Week 2) — COMPLETED

157 tests covering `ToolTable`/`ToolModel` with in-memory SQLite, plugin registry lifecycle, base plugin CRUD channels, and full `plasma_processes` SQLAlchemy model suite (CRUD operations, 11 model classes, CSV seeding).

### Phase 3: Qt Widget Testing (Week 3+) — IN PROGRESS

Baseline established with 199 tests across 7 widget modules:

- **LEDWidget** (31 tests) — Diameter, color, alignment, state, flashing, flashRate properties; size hints; focus policy; toggle/startFlashing/stopFlashing methods
- **BarIndicatorBase** (42 tests) — Value clamping, min/max, orientation, text formatting, gradient parsing, colors, border settings, Qt properties
- **StatusLabel** (33 tests) — setValue with various types, format strings, expression evaluation, invalid expression handling, inheritance
- **EvalLineEdit** (33 tests) — Expression evaluation via simpleeval, operator prefixes (+, *, /, -=, +=), sign toggle with `-`, error handling, return key binding
- **StatusLED** (25 tests) — State/flashing properties inherited from LEDWidget, rule properties (On, Flashing), Qt property access, size hints
- **VCPFrame** (13 tests) — Enable rule property, visibility, sizing, object naming
- **VCPStackedWidget** (35 tests) — Page management (add/remove/setCurrentIndex), setIndexValue with signal blocking, settingName property, currentChanged signal

#### Setup for Qt Widget Testing

Qt widget tests require `PYTEST_QT_API=pyqt5` to be set before pytest starts. This is handled automatically via `usercustomize.py` in the Poetry venv.

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

### Phase 4: HAL/LinuxCNC Integration Tests (Ongoing) — NOT STARTED

These require a running LinuxCNC sim instance. Consider a separate test suite that spawns `linuxcnc --sim` and validates widget behavior against real HAL signals. This could be gated behind a `pytest.mark.integration` marker so the fast CI path stays clean.

## Key Decisions to Make

1. **Test directory location** — root-level `tests/` (chosen, already in place) vs `src/tests/`. Root-level is more conventional for Poetry and is what we're using now.

2. **CI integration** — GitHub Actions to run pytest on PRs, or keep testing purely local for now?

3. **HAL mocking strategy** — Mock the `_hal` C extension, or spin up LinuxCNC sim in a container/subprocess per test suite?

4. **Qt binding consistency** — Project uses `qtpy` abstraction layer. Tests require PyQt5 (set via `PYTEST_QT_API=pyqt5`). Both PyQt5 and PyQt6 may be installed, but pytest-qt must use the same binding as the application code.
