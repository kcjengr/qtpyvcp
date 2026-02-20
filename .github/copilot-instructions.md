Purpose
-------
This file gives concise, actionable guidance for AI coding agents working in the QtPyVCP repository. Focus on being deterministic, referencing repository files, and preserving existing packaging/versioning behavior.

Quick context
-------------
- Project root uses `src/` layout: Python packages live under `src/` (see `pyproject.toml`).
- Main package: `qtpyvcp` under `src/qtpyvcp/` — this contains `app/`, `plugins/`, `tools/`, `widgets/`, and `yaml_lib/`.
- Entry points and CLI scripts are declared in `pyproject.toml` under `[tool.poetry.scripts]` (examples: `qtpyvcp`, `qcompile`, `plasma_gcode_preprocessor`). Do not hard-edit installed entry-points; update `pyproject.toml` for new CLI tools.
- UI files and examples live in `src/examples/` (many `.ui` files) and `docs/` contains the Sphinx documentation source.

Big-picture architecture (what to know fast)
------------------------------------------
- `qtpyvcp` provides a VCP framework. Responsibility boundaries:
  - `qtpyvcp.app`: application bootstrap and `main()` entrypoint.
  - `qtpyvcp.plugins`: plugin definitions and plugin-loading patterns (entrypoints and internal plugin registry).
  - `qtpyvcp.tools`: small CLI utilities (each exposes `main()`; see `pyproject.toml` for mappings).
  - `src/examples/` and `video_tests/`: runnable examples and test harnesses—useful for manual verification.
- Versioning: versioneer + `poetry-dynamic-versioning` control package version; avoid manual edits to `_version.py` or `version` in `pyproject.toml`.

Developer workflows & commands
----------------------------
- Typical dev install (Poetry-aware):

  - Install deps and editable install:

    pip install -r requirements.txt
    python -m pip install -e .

  - Or, using Poetry (preferred if available):

    poetry install
    poetry run qtpyvcp

- Run a tool directly (example):

    poetry run plasma_gcode_preprocessor --help

- Build docs locally:

    make -C docs html

- Run example VCPs: use console scripts defined in `pyproject.toml` (e.g., `mini`, `brender`) or run example python files in `src/examples/`.

Project-specific conventions and patterns
---------------------------------------
- Source layout: packages are specified with `from = "src"` in `pyproject.toml`. Always add new modules under `src/` and include them in the package table when necessary.
- CLI/tool pattern: any script under `src/qtpyvcp/tools/` should expose a `main()` function and be registered in `pyproject.toml` for a console script.
- Plugin registration: plugin entry points appear under `[tool.poetry.plugins]` in `pyproject.toml`. Plugins and example VCPs are registered via these entry points (look at `qtpyvcp.example_vcp`).
- UI workflow: `.ui` files (Qt Designer) are source artifacts. Edits to `.ui` may require regenerating or reloading in the app; preserve formatting and relative resource paths used in `src/examples` and `src/qtpyvcp/widgets`.
- Version updates: handled automatically by `poetry-dynamic-versioning` + git tags; do not hand-edit generated version files.

Integration points & external dependencies
----------------------------------------
- LinuxCNC: runtime integration with LinuxCNC is expected — configuration files live in `linuxcnc/configs/`.
- Qt bindings: supports PyQt5 or PySide2; Qt 5.15 is targeted in docs. UI code often uses QtPy abstractions.
- Packaging: Debian packaging exists under `debian/` for building distro packages.

Where to look for concrete examples
----------------------------------
- CLI tools: `src/qtpyvcp/tools/plasma_gcode_preprocessor.py` (tool pattern: `main()`)
- App bootstrap: `src/qtpyvcp/app/` (search for `main()` and application init)
- Plugins and examples: `src/qtpyvcp/plugins/` and `src/examples/`
- Docs and usage examples: `docs/source/` and `README.md`

How an AI agent should behave here (do/don't)
-------------------------------------------
- Do: prefer modifying `pyproject.toml` for packaging and console scripts; run local manual smoke tests using example VCPs.
- Do: preserve `.ui` resources and relative references; when changing UI, run the example that uses it to verify visual load.
- Do: avoid editing generated files (e.g., `_version.py`), and prefer updating source code that drives generation or the build metadata.
- Do: keep running notes current for every meaningful Probe Basic or QtPyVCP change:

  - Update `probe_basic/docs_src/source/running_notes.rst` for cross-repo sessions and Probe Basic-side work.
  - Update `qtpyvcp/docs/source/development/running_notes.rst` for QtPyVCP-side work.
  - Record concise release-note-ready entries with date, area, summary, changes, validation, and touched files.
- Don't: assume tests exist — there is no standard pytest suite; rely on example scripts and `video_tests` for manual verification.

If unsure, check these files first
---------------------------------
- `pyproject.toml` (entry points, packages)
- `src/qtpyvcp/app/` (app bootstrap)
- `src/qtpyvcp/tools/` (small CLI tools)
- `src/examples/` (runnable examples and `.ui` files)
- `docs/source/` (Sphinx docs and docs examples)

Feedback
--------
If any of these areas are unclear or missing details you need, mention which commands or files to expand and I'll update this guidance.
