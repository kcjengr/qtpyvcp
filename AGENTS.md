# QtPyVCP — Agent Instructions

## Setup & Commands

**Install (Poetry):** `poetry install`
**Fallback:** `pip install -r requirements.txt && pip install -e .`
**Run app:** `qtpyvcp --ini <path>` or `poetry run qtpyvcp --ini <path>`
**Run example VCP:** `poetry run mini` / `poetry run brender` / `poetry run actions`
**Run tool:** `poetry run <script-name>` — see `[tool.poetry.scripts]` in pyproject.toml
**Compile .ui → .py:** `poetry run qcompile <file.ui>`
**Build docs:** `make -C docs html`

## Architecture

- **src/ layout**, 3 packages: `qtpyvcp`, `examples`, `video_tests` (declared in `pyproject.toml` `packages` with `from = "src"`)
- **`qtpyvcp.app:main`** — CLI entrypoint; accepts `--ini <path>` for LinuxCNC INI files. VCPs launch via `qtpyvcp.app.run()` from their own `__init__.py`.
- **`qtpyvcp.plugins/`** — plugin definitions. Entrypoints registered under `[tool.poetry.plugins."qtpyvcp.example_vcp"]` and `"qtpyvcp.test_vcp"` in pyproject.toml.
- **`qtpyvcp.tools/`** — standalone CLI utilities, each exposes `main()`; registered as console scripts in pyproject.toml.
- **`qtpyvcp.widgets/`** — HAL-connected widgets, displays, inputs, dialogs, containers.
- **`linuxcnc/configs/`** — LinuxCNC config examples (`sim.qtpyvcp`, `sim.qtpyvcp.foam`, `sim.qtpyvcp.machine_parts`).
- **`debian/`** — Debian packaging for distro builds.
- **`versioneer.py`** at root + `src/qtpyvcp/_version.py` — version generation, never hand-edit.

## Testing

- **pytest** is configured via `[tool.pytest.ini_options]` in `pyproject.toml`. Tests live at root-level `tests/`.
- **Run all tests:** `poetry run pytest tests/`
- **Dev deps:** `pytest ^7.4`, `pytest-qt ^4.2` (in `[tool.poetry.group.dev.dependencies]`)
- **Phase 1 complete** — 47 tests covering `drill_ops`, `misc`, `runtime_config`, `types`.
- **Phase 2 easy tier complete** — 62 tests covering `gcode_file`, `face_ops` (+`BaseGenerator`), and plugin registry.
- **Phase 2 DB models complete** — 21 tests covering `ToolTable`, `Tool`, `ToolModel` CRUD + relationships (in-memory SQLite).
- **Phase 2 base_plugins complete** — 40 tests covering `Plugin` lifecycle, `DataPlugin` channel discovery/getChannel/setLogLevel, `DataChannel` getValue/setValue/signals/descriptors/decorators(fget/fset/fstr)/notify/str/docstring.
- **Phase 2 plasma_processes complete** — 75 tests covering `crudMixin` CRUD (create/update/delete/get_all/get_by_key), all 11 model classes (Gas, Machine, Material, LinearSystem, Thickness, PressureSystem, Operation, Quality, Consumable, HoleCut, Cutchart) with FK relationships and custom classmethods, `PlasmaProcesses` plugin CRUD wrapper methods, and `seed_data_base()` CSV import (DESIGNER=1 bypass + in-memory SQLite).
- Total: **245 tests**, all passing, zero HAL/LinuxCNC dependencies.
- See `testing.md` for the full phased plan (Phases 3+ cover Qt widgets and HAL integration).

## Gotchas

- No linting, no typechecking, no pre-commit, no CI. Verification is manual: run example VCPs and inspect visually.
- **`.ui` files are source artifacts.** After editing a `.ui` file, compile it with `qcompile` or reload the app. Preserve relative resource paths used by examples/widgets.
- **YAML config priority:** CLI args > `$VCP_CONFIG_FILES` env var > VCP-specific YAML > `DEFAULT_CONFIG_FILE`. See `qtpyvcp.app.run()`.
- **Qt bindings:** supports PyQt5 or PySide2 via QtPy. Never import from a specific binding directly.
- **LinuxCNC/HAL dependency.** The app expects to run alongside LinuxCNC with HAL available. Without it, widgets that connect to HAL pins will fail at runtime.
- **Python 3.7+** per pyproject.toml (README says 3.11+ — trust pyproject.toml).
- **New console scripts:** add to `[tool.poetry.scripts]` in pyproject.toml. New plugins: add to the appropriate `[tool.poetry.plugins."..."]` section.
- **Travis CI badge** in README is stale/defunct — no `.travis.yml` or other CI config exists.

## Deeper guidance

See `.github/copilot-instructions.md` for more detailed architecture notes and AI agent behavior conventions.
