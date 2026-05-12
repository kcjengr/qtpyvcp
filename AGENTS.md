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

## Gotchas

- **No test suite.** No pytest, no linting, no typechecking, no pre-commit, no CI. Verification is manual: run example VCPs and inspect visually.
- **`.ui` files are source artifacts.** After editing a `.ui` file, compile it with `qcompile` or reload the app. Preserve relative resource paths used by examples/widgets.
- **YAML config priority:** CLI args > `$VCP_CONFIG_FILES` env var > VCP-specific YAML > `DEFAULT_CONFIG_FILE`. See `qtpyvcp.app.run()`.
- **Qt bindings:** supports PyQt5 or PySide2 via QtPy. Never import from a specific binding directly.
- **LinuxCNC/HAL dependency.** The app expects to run alongside LinuxCNC with HAL available. Without it, widgets that connect to HAL pins will fail at runtime.
- **Python 3.7+** per pyproject.toml (README says 3.11+ — trust pyproject.toml).
- **New console scripts:** add to `[tool.poetry.scripts]` in pyproject.toml. New plugins: add to the appropriate `[tool.poetry.plugins."..."]` section.
- **Travis CI badge** in README is stale/defunct — no `.travis.yml` or other CI config exists.

## Deeper guidance

See `.github/copilot-instructions.md` for more detailed architecture notes and AI agent behavior conventions.
