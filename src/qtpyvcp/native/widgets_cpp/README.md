# QtPyVCP C++ Widgets

This directory hosts C++ Qt widgets and their Qt Designer plugin modules that
are maintained as part of the main `qtpyvcp` repository.

## Initial migration

The `gcode_editor/` sources were migrated from the standalone `editor_widget`
repository so widget/plugin development can happen in one place.

## Build the GCode editor plugin (manual)

```bash
cd qtpyvcp/src/qtpyvcp/native/widgets_cpp/gcode_editor
cmake -S . -B build
cmake --build build -j
```

The resulting plugin module can be added to Qt Designer plugin search paths for
local development and testing.
