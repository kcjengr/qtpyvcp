Native Widgets Consolidation Plan
=================================

Goal
----

Move C++ widget/plugin maintenance into the main ``qtpyvcp`` repository so
Qt Designer widget development and packaging happen in one place.

Proposed layout
---------------

::

   src/qtpyvcp/native/
     backplot_cpp/
       ...
     widgets_cpp/
       CMakeLists.txt
       README.md
       gcode_editor/
         CMakeLists.txt
         gcodeeditor.cpp
         gcodeeditor.h
         gcodehighlighter.cpp
         gcodehighlighter.h
         gcodeeditorplugin.cpp
         gcodeeditorplugin.h
         gcodeeditorplugin.pro
         gcodeeditorplugin.pri

Notes
-----

- ``native`` is an umbrella for compiled modules and bridge code.
- ``backplot_cpp`` remains the performance module for backplot generation.
- ``widgets_cpp`` hosts C++ Qt widgets and Qt Designer plugins.

Current migration status
------------------------

- ``gcode_editor`` sources were copied from the standalone ``editor_widget``
  repository into ``qtpyvcp``.
- Initial CMake build scaffolding was added for local plugin builds.
- ``qnative`` was added as a project tool entrypoint and now builds both
  native targets (widgets plugin + backplot module).
- Debian packaging now invokes both ``qcompile`` and ``qnative`` during
  ``override_dh_install``.
- Packaging build dependencies were updated for the native/CMake path,
  including ``cmake``, ``qt6-base-dev``, ``qt6-tools-dev``, ``pybind11-dev``,
  and ``python3-poetry-dynamic-versioning``.
- Debian package output was validated after migration:

  - Native artifacts are built and staged correctly.
  - Native ``build/`` directories are not shipped in the final ``.deb``
    payload (verified as zero packaged entries).
- Local build output directories are ignored via ``.gitignore``:

  - ``/src/qtpyvcp/native/backplot_cpp/build/``
  - ``/src/qtpyvcp/native/widgets_cpp/**/build/``

Next steps
----------

1. Validate plugin loading/runtime behavior through ``editvcp``/Qt Designer in
   target environments.
2. Standardize ``.ui`` custom widget headers/classes across Probe Basic files.
3. Confirm final plugin installation/discovery path expectations for designers
   on all supported deployment targets.
4. Retire standalone ``editor_widget`` repo dependency once all references are
   migrated.
