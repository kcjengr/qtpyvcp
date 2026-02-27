Project Architecture
====================

This document provides an overview of the structure and major components of the
QtPyVCP project.  It is intended for developers who need to understand how the
code is organised and where to make changes when extending or maintaining the
framework.

.. contents::
   :local:
   :depth: 2

Overview
--------

QtPyVCP is a **Qt and Python based Virtual Control Panel framework** designed to
be used with LinuxCNC.  The repository follows a :term:`src/ layout` with the
Python packages under ``src/`` and a number of supporting directories for
documentation, examples and packaging.

Key pieces of the project include:

- ``qtpyvcp`` package containing the framework code.
- ``examples`` and ``video_tests`` packages providing runnable demos and tests.
- ``docs/`` with Sphinx source documentation.
- Console scripts and plugins declared in ``pyproject.toml``.

The top-level package ``qtpyvcp`` is where most of the action happens; its
subpackages can broadly be grouped as:

* application bootstrap and launcher (``app``)
* plugin system (``plugins``)
* Qt widgets (``widgets``)
* HAL integration (``hal``)
* Utility libraries (``utilities``, ``yaml_lib``)
* Command–line tools (``tools``)
* Example VCPs (under ``src/examples``)

Package Layout
---------------

The structure beneath ``src/qtpyvcp`` is:

```
app/              # main() entrypoint and VCP launcher
plugins/          # plugin registration and base classes
widgets/          # custom Qt widgets used by panels
hal/              # LinuxCNC HAL helpers
tools/            # standalone CLI utilities
utilities/        # miscellaneous helpers (logging, config, etc.)
yaml_lib/         # YAML loader/formats used by the chooser
lib/              # miscellaneous library code (db helpers, etc.)
actions/          # legacy or specialised action modules
vcp_chooser/      # graphical chooser implementation
ops/              # operation definitions used by examples

```

Each directory usually contains its own ``__init__.py`` and may define API
classes, helpers and state.  The project uses an ``examples`` package to hold
runnable VCP demos, and ``video_tests`` for automated GUI recording tests.

Application Bootstrap
^^^^^^^^^^^^^^^^^^^^^

The entry point for the application is ``qtpyvcp.app.main`` which is exposed as
the ``qtpyvcp`` console script (see ``pyproject.toml``).  The argument parser
is generated from the module docstring.  Command‑line options are normalised via
``qtpyvcp.utilities.opt_parser`` before the VCP is launched by
``qtpyvcp.app.launcher``.

``qtpyvcp.app`` also exports ``run()`` which is used by individual VCP
``__init__.py`` files; this allows panels defined as Python packages to start
the framework with a configuration object.

Plugin System
^^^^^^^^^^^^^

Plugins form the backbone of data access and extensible behaviour.  The
``qtpyvcp.plugins`` package provides helpers to register, initialise and
terminate plugins.  A plugin is defined as a subclass of ``Plugin`` (or
``DataPlugin``) in ``qtpyvcp.plugins.base_plugins``.  Useful characteristics of
the plugin system are:

- ``registerPlugin`` and ``registerPluginFromClass`` allow configuration-driven
  registration (YAML spec in ``qtpyvcp/utilities/config_loader.py``).
- Plugins are stored in an ordered dict so initialisation and termination are
  deterministic and in the opposite order.
- ``getPlugin`` returns a plugin instance or a ``NullPlugin`` when running in
  Qt Designer mode, supporting live widget editing.
- Designer-specific plugins are auto-loaded by ``_initializeDesignerPlugins``
  to make the designer usable without a full LinuxCNC backend.

Plugins cover functionality such as status monitors, tool tables, inputs,
notifications, and more.  See ``src/qtpyvcp/plugins`` for available plugin
classes and examples.

Widgets
^^^^^^^^

The ``qtpyvcp.widgets`` package contains custom Qt widgets grouped by their
role, e.g. ``input_widgets``, ``display_widgets``, ``hal_widgets``,
``button_widgets`` and others.  Many of these widgets are backed by plugins and
are the building blocks for VCP user interfaces.  A Qt Designer plugin is also
exported via the ``pyside6.designer`` entry point to enable dragging these
widgets into ``.ui`` files.

HAL Integration
^^^^^^^^^^^^^^^^

The ``hal`` package provides helpers for interacting with LinuxCNC's HAL layer.
Widgets or plugins that need to read or write HAL pins can use utilities from
this package.

CLI Tools
^^^^^^^^^

Small command‑line utilities live in ``qtpyvcp.tools``.  Each module exposes a
``main()`` function and is registered under ``[tool.poetry.scripts]`` in
``pyproject.toml``.  Examples include ``qcompile`` (compile ``.ui`` files),
``plasma_gcode_preprocessor`` and others.  Refer to the module docstrings for
usage details.

Configuration
^^^^^^^^^^^^^

The framework prefers YAML configuration files alongside computed defaults and
INI-derived settings.  ``qtpyvcp.utilities.config_loader`` merges multiple
sources.  A default config file path is defined in ``qtpyvcp.DEFAULT_CONFIG_FILE``.

Examples & Tests
----------------

- ``src/examples`` contains example VCPs such as ``mini`` and ``brender``.  Each
  example package typically defines a minimal ``__init__`` that calls
  ``qtpyvcp.app.run`` after setting up configuration.
- ``src/video_tests`` holds lightweight GUI tests used by the CI pipeline and
  for local smoke testing.  They are also available as console scripts.

Documentation
-------------

Sphinx documentation lives in ``docs/source``.  New pages should be added under
relevant subsections (``development/``, ``widgets/``, ``tools/``, etc.) and
built with ``make -C docs html``.  The ``architecture.rst`` file you are
reading is referenced from ``docs/source/index.rst`` when appropriate.

Versioning & Packaging
----------------------

Version numbers are controlled by ``versioneer`` and
``poetry-dynamic-versioning``.  The package metadata is in ``pyproject.toml``.
New console scripts or plugin entry points should be added there rather than
hard‑coding them in code.

Development Guidelines
----------------------

Refer to the project-specific instructions in
``.github/copilot-instructions.md`` for conventions on editing UI files,
registering plugins, writing tools, and running examples.


----------------------------------

*Generated on 27 February 2026.*
