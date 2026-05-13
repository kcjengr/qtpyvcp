# QtPyVCP Testing Plan

## Current State

**273 tests passing**, covering pure Python modules, DB models, and plugin infrastructure. No HAL/LinuxCNC or Qt widget tests yet. The `video_tests/` apps still render widgets visually without assertions.

### Coverage Summary

| Phase | Tests | Modules Covered |
|-------|-------|-----------------|
| Phase 1 (Easy) | 137 | `drill_ops`, `gcode_file`, `face_ops`, `misc`, `types`, `colored_formatter`, `runtime_config` |
| Phase 2 (DB + Plugins) | 157 | `tool_table`, `plasma_processes`, `base_plugins`, `plugin_registry` |

### Missing from Phase 1 (Easy tier)

| Module | Effort | Tests Needed | Notes |
|--------|--------|-------------|-------|
| `utilities/settings.py` | Medium | ~15 | Pure functions (`getSetting`, `setSetting`, `addSetting`) testable with mocked `SETTINGS`; `Setting` class requires Qt fixture |
| `lib/decorators.py` | Easy | ~6 | `@deprecated` decorator — needs mocked logger, tests for class vs function branches |
| `app/enums.py` | Trivial | ~5 | Constant-value assertions only, zero dependencies |
| `utilities/yaml_filters.py` | Easy | ~8 | `from_ini()` env-var branching logic, pure Python |

## Testable Boundaries

Out of the 3 packages under `src/`, roughly **40% of qtpyvcp is pure Python** (no HAL/LinuxCNC dependency) and immediately testable:

| Tier | Modules | Effort |
|------|---------|--------|
| **Easy — pure logic** | `ops/drill_ops.py`, `ops/gcode_file.py`, `ops/face_ops.py`, `utilities/misc.py`, `utilities/settings.py`, `lib/types.py`, `lib/decorators.py`, `lib/colored_formatter.py`, `app/runtime_config.py`, `app/enums.py`, `utilities/yaml_filters.py` | Assert output strings, value coercion, path normalization |
| **Medium — DB logic** | `lib/db_tool/tool_table.py`, `plugins/plasma_processes.py` (SQLAlchemy models) | In-memory SQLite round-trips |
| **Hard — HAL dependent** | `hal/`, plugins with `import linuxcnc`, widgets that bind to HAL pins | Requires mocking `_hal`, or running inside LinuxCNC simulation |
| **Hardest — Qt widgets** | All UI widgets, VCP chooser, notifications | Requires Xvfb + `pytest-qt` or similar |

## Recommended Approach

### Phase 1: Infrastructure + Pure Python (Week 1) — COMPLETED

1. **Add pytest to dev deps** in `pyproject.toml`:
    ```toml
    [tool.poetry.group.dev.dependencies]
    pytest = "^7.4"
    pytest-qt = "^4.2"    # for later phases, add now to avoid re-running installs
    ```

2. **Create `src/tests/`** mirroring the source structure:
    ```
    src/tests/
    ├── ops/
    │   ├── test_drill_ops.py
    │   ├── test_face_ops.py
    │   └── test_gcode_file.py
    ├── utilities/
    │   ├── test_settings.py          ← NOT YET WRITTEN
    │   ├── test_misc.py
    │   └── test_yaml_filters.py      ← NOT YET WRITTEN
    ├── lib/
    │   ├── test_types.py
    │   ├── test_decorators.py        ← NOT YET WRITTEN
    │   └── test_colored_formatter.py
    └── app/
        └── test_runtime_config.py
    ```

3. **Run via:** `poetry run pytest tests/`

This gives you ~137 tests covering GCode generation, misc utilities, path normalization, and config loading — all without LinuxCNC running. The ops module is especially low-hanging fruit: each drill cycle produces a deterministic string output that's trivial to assert.

### Phase 2: DB Models + Plugin Registry (Week 2) — COMPLETED

157 tests covering `ToolTable`/`ToolModel` with in-memory SQLite, plugin registry lifecycle, base plugin CRUD channels, and full `plasma_processes` SQLAlchemy model suite (CRUD operations, 11 model classes, CSV seeding).

### Phase 3: Qt Widget Testing (Week 3+) — NOT STARTED

Add `Xvfb` for headless rendering in CI. Use `pytest-qt` to test widget initialization, signal/slot behavior, and HAL pin binding simulation. Convert `video_tests/` apps into automated assertions rather than purely visual checks. This is the next major milestone after the remaining Phase 1 modules above are filled in.

### Phase 4: HAL/LinuxCNC Integration Tests (Ongoing) — NOT STARTED

These require a running LinuxCNC sim instance. Consider a separate test suite that spawns `linuxcnc --sim` and validates widget behavior against real HAL signals. This could be gated behind a `pytest.mark.integration` marker so the fast CI path stays clean.

## Key Decisions to Make

1. **Test directory location** — root-level `tests/` (chosen, already in place) vs `src/tests/`. Root-level is more conventional for Poetry and is what we're using now.

2. **CI integration** — GitHub Actions to run pytest on PRs, or keep testing purely local for now?

3. **HAL mocking strategy** — Mock the `_hal` C extension, or spin up LinuxCNC sim in a container/subprocess per test suite?

4. **Phase 1 completion priority** — `app/enums.py` (trivial) → `lib/decorators.py` (easy) → `utilities/yaml_filters.py` (easy) → `utilities/settings.py` (medium, requires Qt fixture).
