# QtPyVCP — Agent Instructions

## Quick context
- **src/ layout**: packages under `src/` (see `pyproject.toml` `packages` table). Main package: `qtpyvcp`.
- **Build**: Poetry + poetry-dynamic-versioning + versioneer. Version is generated from git tags; never edit `_version.py` or the `version = "0.0.0"` field in `pyproject.toml`.
- **Qt bindings**: PySide6 is an optional extra (`pyside6`). QtPy abstracts PyQt5/PySide2/PySide6/PyQt6. Use qtpy imports, not raw binding imports.

## Install & run
```
pip install -r requirements.txt
python -m pip install -e .
# or: poetry install && poetry run qtpyvcp
```

Run a CLI tool: `poetry run <script-name>` (scripts declared in `pyproject.toml` `[tool.poetry.scripts]`).

Run an example VCP: `poetry run mini`, `poetry run brender`, or `python src/examples/mini/__init__.py`.

Build docs: `make -C docs html` (headless: `make -C docs html-preview`).

## Architecture
- `qtpyvcp.app`: app bootstrap, `main()` entrypoint, launcher, runtime config.
- `qtpyvcp.plugins`: plugin registry and loading (entry points + internal).
- `qtpyvcp.tools/`: small CLI utilities, each with a `main()`.
- `qtpyvcp.widgets/`, `qtpyvcp.actions/`, `qtpyvcp.utilities/`, `qtpyvcp.yaml_lib/`: framework internals.
- `src/examples/`: runnable example VCPs (`.ui` + Python). Also registered as `qtpyvcp.example_vcp` entry points.
- `src/video_tests/`: manual test harnesses (vtk_test, widgets_test, qtpyvcp_test). **No automated test suite.**
- `linuxcnc/configs/`: LinuxCNC configuration files for runtime integration.

VCP launch flow: `qtpyvcp.app.main()` → parse opts → `load_vcp()` or `launch_application()`. VCP `__init__.py` calls `qtpyvcp.app.run(opts, config_file)`.

## Conventions
- **New CLI tools**: add `main()` in `src/qtpyvcp/tools/`, register in `pyproject.toml` `[tool.poetry.scripts]`.
- **New plugins/examples**: register under `[tool.poetry.plugins."qtpyvcp.example_vcp"]` or appropriate namespace in `pyproject.toml`.
- **UI files (`.ui`)**: source artifacts. Preserve relative resource paths when editing. Run the example that uses a `.ui` file to verify it loads.
- **Generated files — do not commit**: `_version.py`, `*_rc.py`, `*_ui.py`, `poetry.lock`.

## Testing & verification
There is **no pytest suite or CI**. Verify changes by:
1. Running example VCPs (`mini`, `brender`, `actions`).
2. Running video test harnesses in `src/video_tests/`.
3. Manual smoke testing of CLI tools via `poetry run <tool> --help`.

## Debian packaging
Debian build files live under `debian/`. Build scripts: `.scripts/build_deb.sh`, `.scripts/publish_pypi_release.sh`, `.scripts/publish_github_release.sh`.

## Running notes
Record meaningful changes in `audit_reports/running_notes.rst` using the entry template on that page (date, area, summary, changes, validation, files).

## Where to look first
- `pyproject.toml` — entry points, packages, extras, plugin registrations.
- `src/qtpyvcp/app/__init__.py` — main entrypoint and launch flow.
- `src/examples/` — runnable VCPs with `.ui` files.
- `docs/source/` — Sphinx documentation.
- `.github/copilot-instructions.md` — supplementary AI guidance.
