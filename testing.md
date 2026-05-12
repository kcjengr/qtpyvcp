# QtPyVCP Testing Plan

## Current State

Zero test infrastructure — no pytest, linting, typecheckers, CI, or pre-commit hooks. The only "tests" are three `video_tests/` apps that render widgets visually but have no assertions.

## Testable Boundaries

Out of the 3 packages under `src/`, roughly **40% of qtpyvcp is pure Python** (no HAL/LinuxCNC dependency) and immediately testable:

| Tier | Modules | Effort |
|------|---------|--------|
| **Easy — pure logic** | `ops/drill_ops.py`, `ops/gcode_file.py`, `ops/face_ops.py`, `utilities/misc.py`, `utilities/settings.py`, `lib/types.py`, `lib/decorators.py`, `lib/colored_formatter.py`, `app/runtime_config.py`, `app/enums.py` | Assert output strings, value coercion, path normalization |
| **Medium — DB logic** | `lib/db_tool/tool_table.py`, `plugins/plasma_processes.py` (SQLAlchemy models) | In-memory SQLite round-trips |
| **Hard — HAL dependent** | `hal/`, plugins with `import linuxcnc`, widgets that bind to HAL pins | Requires mocking `_hal`, or running inside LinuxCNC simulation |
| **Hardest — Qt widgets** | All UI widgets, VCP chooser, notifications | Requires Xvfb + `pytest-qt` or similar |

## Recommended Approach

### Phase 1: Infrastructure + Pure Python (Week 1)

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
   │   ├── test_settings.py
   │   ├── test_misc.py
   │   └── test_yaml_filters.py
   ├── lib/
   │   ├── test_types.py
   │   ├── test_decorators.py
   │   └── test_colored_formatter.py
   └── app/
       └── test_runtime_config.py
   ```

3. **Run via:** `poetry run pytest src/tests/`

This gives you ~50-80 tests covering GCode generation, settings lifecycle, path normalization, and config loading — all without LinuxCNC running. The ops module is especially low-hanging fruit: each drill cycle produces a deterministic string output that's trivial to assert.

### Phase 2: DB Models + Plugin Registry (Week 2)

Test `ToolTable`/`ToolModel` with in-memory SQLite, and the plugin registry lifecycle. These are self-contained with clear CRUD semantics.

### Phase 3: Qt Widget Testing (Week 3+)

Add `Xvfb` for headless rendering in CI. Use `pytest-qt` to test widget initialization, signal/slot behavior, and HAL pin binding simulation. This is where you'd start converting `video_tests/` into automated assertions rather than purely visual checks.

### Phase 4: HAL/LinuxCNC Integration Tests (Ongoing)

These require a running LinuxCNC sim instance. Consider a separate test suite that spawns `linuxcnc --sim` and validates widget behavior against real HAL signals. This could be gated behind a `pytest.mark.integration` marker so the fast CI path stays clean.

## Key Decisions to Make

1. **Test directory location** — `src/tests/` (co-located with source) vs root-level `tests/`. Co-located keeps it alongside packages; root-level is more conventional for Poetry.

2. **CI integration** — GitHub Actions to run pytest on PRs, or keep testing purely local for now?

3. **HAL mocking strategy** — Mock the `_hal` C extension, or spin up LinuxCNC sim in a container/subprocess per test suite?
