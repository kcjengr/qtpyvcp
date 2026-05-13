# Running Tests

## Prerequisites

All test dependencies are declared in `pyproject.toml` under `[tool.poetry.group.dev.dependencies]`:

```toml
pytest = "^7.4"
pytest-qt = "^4.2"
pytest-xvfb = "^3.1"
pytest-cov = "*"          # for coverage reporting (install separately)
```

Install them:

```bash
poetry install
```

## Running All Tests

```bash
poetry run pytest tests/ -v
```

This runs 516 tests across pure-Python modules. No display or LinuxCNC required.

### Filter by Category

```bash
# Run only ops tests
poetry run pytest tests/ops/ -v

# Run only plugin tests
poetry run pytest tests/plugins/ -v

# Run only utilities tests
poetry run pytest tests/utilities/ -v

# Run only lib tests
poetry run pytest tests/lib/ -v

# Run only app tests
poetry run pytest tests/app/ -v
```

### Filter by Marker

Tests can be marked with `pytest.mark.<name>` for selective execution. Add markers to test functions:

```python
@pytest.mark.widget
def test_something(): ...

@pytest.mark.hal
def test_with_hal(): ...
```

Then run subsets:

```bash
poetry run pytest tests/ -m "widget"
poetry run pytest tests/ -m "not hal"
```

## Qt Widget Testing (Headless)

Qt widget tests require an X display. `pytest-xvfb` handles this automatically by spawning a virtual framebuffer before tests start.

### Auto X Display (Default)

```bash
poetry run pytest tests/ -v
```

pytest-xvfb spawns Xvfb, sets `DISPLAY`, runs all tests, then tears down the display when done.

### Custom Display Size

```bash
poetry run pytest tests/ --xvfb-width=1920 --xvfb-height=1080 -v
```

### Alternative Backends

```bash
# Use Xephyr instead of Xvfb
poetry run pytest tests/ --xvfb-backend=xephyr -v

# Use Xvnc instead of Xvfb
poetry run pytest tests/ --xvfb-backend=xvnc -v
```

### Disable X Display

If you have a real display and want to use it directly:

```bash
poetry run pytest tests/ --no-xvfb -v
```

### Qt-Specific Options

pytest-qt provides additional options for widget testing (see `pytest --help | grep qt`):

```bash
# Show only warnings from Qt
poetry run pytest tests/ -v --tb=short

# Capture Qt messages
poetry run pytest tests/ -v --qt-log-mode=errorsonly
```

## Coverage Reporting

Install coverage tool:

```bash
poetry run pip install pytest-cov
```

### Terminal Report

```bash
poetry run pytest tests/ --cov=qtpyvcp --cov-report=term-missing -v
```

Outputs per-file coverage with line numbers of uncovered code.

### HTML Report

```bash
poetry run pytest tests/ --cov=qtpyvcp --cov-report=html
```

Opens an interactive report at `htmlcov/index.html`.

### XML Report (CI Integration)

```bash
poetry run pytest tests/ --cov=qtpyvcp --cov-report=xml
```

Generates `coverage.xml` compatible with CI tools (GitHub Actions, Codecov, Coveralls).

### Minimum Coverage Threshold

Fail the build if coverage drops below a threshold:

```bash
poetry run pytest tests/ --cov=qtpyvcp --cov-fail-under=80 -v
```

## Test Structure

Tests mirror the source layout under `tests/`:

```
tests/
├── app/
│   ├── test_enums.py
│   └── test_runtime_config.py
├── lib/
│   ├── test_colored_formatter.py
│   ├── test_db_base.py
│   ├── test_decorators.py
│   └── test_tool_table.py
├── ops/
│   ├── test_face_ops.py
│   └── test_gcode_file.py
├── plugins/
│   ├── test_base_plugins.py
│   ├── test_plasma_processes.py
│   └── test_plugin_registry.py
├── utilities/
│   ├── test_config_loader.py
│   ├── test_machine_parameters.py
│   ├── test_opt_parser.py
│   ├── test_settings.py
│   └── test_yaml_filters.py
├── test_drill_ops.py
├── test_misc.py
├── test_runtime_config.py
├── test_types.py
└── __init__.py
```

## Current Coverage Summary

| Area | Lines Covered | % | Status |
|------|--------------|---|--------|
| **app** | 93/436 | 21.3% | Good |
| **lib** | 111/400 | 27.8% | Good |
| **plugins** | 512/2,687 | 19.1% | Partial (HAL-dependent plugins not tested) |
| **utilities** | 400/1,480 | 27.0% | Good |
| **ops** | ~250/300+ | ~85%+ | Excellent |
| **actions** | 0/1,399 | 0% | Needs HAL at runtime |
| **widgets** | 0/12,120 | 0% | Phase 3 target — Qt widget tests |
| **hal** | 0/137 | 0% | Needs LinuxCNC |

**Overall: 6.2%** (1,294 / 20,720 lines, 516 tests)

## CI Integration Example

Add to `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Poetry
        run: pip install poetry

      - name: Install dependencies
        run: poetry install

      - name: Run tests with coverage
        run: |
          poetry run pytest tests/ \
            --cov=qtpyvcp \
            --cov-report=xml \
            --cov-fail-under=20 \
            -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Notes

- Tests do **not** require LinuxCNC or HAL to run — they target pure-Python modules only.
- Qt widget tests (Phase 3) will be added under `tests/widgets/` once the testing plan reaches that milestone.
- HAL/LinuxCNC integration tests (Phase 4) will require a separate test suite with a running LinuxCNC sim instance, gated behind `pytest.mark.integration`.
- The Python requirement was bumped from `^3.7` to `^3.9` in `pyproject.toml` to support `pytest-xvfb >= 3.1`.
