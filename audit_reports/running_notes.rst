Running Notes Workflow
======================

Purpose
-------

Use this page as the development-side running log for changes that should roll
into release notes. Entries should be concise, technical, and easy to copy
into formal release documentation.

Rules
-----

- Add an entry for any meaningful fix, behavior change, or workflow update.
- Capture user-visible impact first, then implementation details.
- Include verification outcomes so release notes can cite tested behavior.
- List touched files for traceability.
- Keep newest entries at the top.

Entry Template
--------------

Date
   YYYY-MM-DD

Area
   Component or subsystem.

Summary
   Short user-facing result.

Changes
   - implementation detail
   - implementation detail

Validation
   - verification statement

Files
   - src/qtpyvcp/path/to/file.py


2026-10-21
----------

Area
   Qt3D0 active tool body

Summary
   Fixed cases where the active tool was not drawn: machine-type flags that
   explicitly disable LATHE/JET/FOAM were treated as enabled, classic LinuxCNC
   tool tables were not matched by tool number, and the tool started at the
   machine origin until the first position update.

Changes
   - Parse `[DISPLAY] LATHE`, `BACK_TOOL_LATHE`, `FOAM`, `JET` and `ANTIALIAS`
     with a real boolean parser (`0`/`false`/`no`/`off` are false). A mill with
     `JET = 0` or `FOAM = 0` no longer loses its tool body.
   - Resolve tool-table entries by `toolno`/`tool`/`tool_no`/`number`/`id`, so
     LinuxCNC `stat.tool_table` entries and DB tool-table dicts both work.
     Tool lookup no longer falls back to a wrong pocket index.
   - Read LinuxCNC's `offset` pose (`EmcPose.x/y/z`) for classic `.tbl`
     entries, so the cutter bit gets its real stick-out length instead of the
     generic 2-inch body.
   - Seed the live tool position from status at startup instead of leaving it
     at the machine origin.
   - Separated the cutter bit from the spindle: `backplot.show-spindle` now
     only shows/hides the `[VTK] SPINDLE` machine model. The bit stays visible,
     and the spindle model follows the live machine position (non-DH) so the
     bit protrudes below it.
   - Added a debug log line for the resolved tool and info logs when the body
     is hidden by the machine type or `backplot.show-spindle`; added the
     `backplot.show-spindle` default (true).
   - Fixed the tool edit dialog's `LATHE` detection the same way.

Validation
   - `pytest tests`: 124 passed.
   - Xvfb render check with a LinuxCNC-style tool table: T1 resolves to a
     cylinder and renders at the live position.

Files
   - src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/tool.py
   - src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/qtquick3d_backplot.py
   - src/qtpyvcp/widgets/display_widgets/backplot_common/linuxcnc_datasource.py
   - src/qtpyvcp/widgets/dialogs/tool_edit_dialog.py
   - src/qtpyvcp/yaml_lib/default_config.yml
   - tests/widgets/test_qtquick3d_tool.py
   - tests/widgets/test_backplot_common.py


2026-10-21
----------

Area
   Work-coordinate action (WCS dropdowns)

Summary
   Changing the work offset from an ActionComboBox no longer raises
   `AttributeError: 'int' object has no attribute 'upper'`.

Changes
   - `set_work_coord` accepts a WCS index (0..8), a G54..G59.3 label, or combo
     text with a trailing description, validates it, and only then issues MDI.
   - QComboBox bindings can request the selected item text through an action
     `use_text` flag; `machine.set_work_coord` uses it (`textActivated` instead
     of the index-only `activated(int)`).
   - Combo selection is synchronised by normalised label, so items with
     descriptive text still select the right row.

Validation
   - `pytest tests`: 116 passed.
   - Regression tests cover index, label, description, invalid values and the
     combo text binding.

Files
   - src/qtpyvcp/actions/machine_actions.py
   - src/qtpyvcp/actions/__init__.py
   - tests/actions/test_work_coord.py


2026-10-21
----------

Area
   Qt3D0 backplot - work-offset origins

Summary
   Added small work-offset origin markers and G54..G59.3 labels to the 3D view
   for the offsets that are actually relevant.

Changes
   - New `WcsOriginModel` overlay and `plot_data.origins` line geometry.
   - A WCS is shown only when the loaded program has a path in it. An empty or
     unloaded program draws no part origins, and configured-but-unused offsets
     are ignored; floating (G91-only) paths are anchored to the machine and are
     skipped.
   - Marker is a small WCS-aligned square plus a vertical stem; the label is a
     2D overlay projected with `View3D.mapFrom3DScene`, so it faces the operator
     and keeps a fixed readable size. Camera moves bump `cameraRevision` so the
     projection re-evaluates on orbit/pan/zoom.
   - Added the `backplot.show-wcs-origins` setting (default on) and the
     `wcsOriginsVisible` Designer property.

Validation
   - `pytest tests` with the LinuxCNC Python modules on PYTHONPATH: 117 passed.
   - Xvfb render check with G54/G55/G56 paths: three amber markers and labels
     rendered at the configured origins; click-to-line picking still works.

Files
   - src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/wcs_origins.py
   - src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/qtquick3d_backplot.py
   - src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/geometry.py
   - src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/scene.qml
   - src/qtpyvcp/widgets/display_widgets/designer_plugins.py
   - src/qtpyvcp/yaml_lib/default_config.yml
   - tests/widgets/test_qtquick3d_properties.py
   - docs/source/components/qtquick3d_backplot.rst


2026-10-20
----------

Area
   VTK backplot removal / renderer dependency

Summary
   Removed the VTK backplot and the VTK/PyVTK dependency from QtPyVCP. The Qt
   Quick 3D `Qt3D0` is now the only 3D backplot renderer.

Changes
   - Deleted `widgets/display_widgets/vtk_backplot/` (renderer, actors, VTK
     canon, bundled STL models) and `native/backplot_cpp/bridge.py` (PyVTK
     actor wrapper).
   - Moved the renderer-independent `base_canon.py` and
     `linuxcnc_datasource.py` into `backplot_common/`; updated the widget and
     the gcode-properties plugin imports.
   - Removed the VTK widget, plugin and placeholder wiring from
     `register_widgets`, `main_window`, `display_widgets` and
     `designer_plugins`; `Qt3D0` is the sole registered backplot widget.
   - Migrated the repository `.ui` files (`actions`, `brender`,
     `widgets_test`) and their generated `_ui.py` copies from `VTKBackPlot` to
     `Qt3D0`. Historical object names such as `vtkbackplot` and `[VTK]` INI
     sections are kept for configuration compatibility.
   - Removed the `vtk_test` VCP and its entry points; updated the video-test
     messages to reference only `opengl_test`.
   - Removed VTK from `requirements.txt`, `packages.txt` and
     `debian/control`; documented that `[VTK]` INI sections are consumed by
     `Qt3D0` for backward compatibility.
   - Removed remaining VTK-named private helpers/labels from the backplot
     datasource and load-perf summary.

Validation
   - `pytest tests` with the LinuxCNC Python modules on PYTHONPATH: 106 passed.
   - Imported the native package, `backplot_common`, `qtquick3d_backplot` and
     the gcode-properties plugin with `vtk` absent from `sys.modules`.
   - `grep` finds no `vtk` imports or `VTKBackPlot` references in the source
     tree; only `[VTK]` INI keys, the compatibility object name
     `vtkbackplot`, and historical notes remain.

Files
   - src/qtpyvcp/widgets/display_widgets/backplot_common/
   - src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/
   - src/qtpyvcp/native/backplot_cpp/
   - src/qtpyvcp/widgets/{register_widgets.py,form_widgets/main_window.py}
   - src/examples/, src/video_tests/, src/qtpyvcp_examples/,
     src/qtpyvcp_video_tests/
   - requirements.txt, packages.txt, debian/control, pyproject.toml
   - docs/source/components/


2026-10-20
----------

Area
   Qt3D0 backplot (Qt Quick 3D renderer)

Summary
   Removed the legacy Qt 3D renderer and finished the Qt Quick 3D parity work:
   backplot settings/signals are wired, work-offset edits no longer re-upload
   geometry, G91-only programs are anchored to the machine, program lines can be
   highlighted from the editor, and offset transitions are drawn.

Changes
   - Deleted `display_widgets/qt3d_backplot` (Qt 3D entity/buffer renderer);
     `Qt3D0` is now always the Qt Quick 3D implementation.
   - Path geometry is split into per-(WCS, role) rows in
     `qtquick3d_backplot/paths.py`; WCS offsets and the floating anchor are
     scene transforms, so offset edits only emit `dataChanged`.
   - Colour changes update row materials instead of re-parsing the program.
   - Added floating-WCS anchoring (tracking while idle, latched while running)
     and WCS offset-transition lines.
   - Picking now unprojects the click with `View3D.mapTo3DScene` and tests the
     ray against local segment arrays (no dependency on mesh picking for lines).
   - Added `selected_program_line(s)` highlighting and wired
     `runStateChanged`/`activeOffsetChanged`/tool-table plugin signals.
   - Fixed orthographic magnification math (pixels per world unit), the camera
     up-vector invariant, and `MachinePartsModel.set_spindle` row signalling.
   - Restored the two-colour background (gradient behind a transparent View3D)
     and enabled MSAA.
   - Added the missing Qt Quick 3D/QtQuickWidgets Debian dependencies and raised
     the PySide6 minimum; missing Qt3D0 now logs a warning instead of silently
     falling back to the Designer placeholder.
   - Removed the unused `BackplotBuilder` C++ stub and the `BaseBackPlot` mixin
     from `Qt3D0`.
   - Retargeted the legacy renderer tests to the Qt Quick 3D rig/tool and added
     load, WCS, floating-anchor, picking and highlight tests.

Validation
   - `pytest tests` with the LinuxCNC Python modules on PYTHONPATH: 106 passed.
   - Offscreen render check (Xvfb + OpenGL): gradient background samples red at
     the bottom and blue at the top, the program path renders, and a synthetic
     click on a known segment selects the expected G-code line.
   - Synthetic 200k-segment path: initial build ~75 ms; a work-offset edit now
     costs ~0.1 ms (transform-only) instead of a full geometry rebuild.

Files
   - src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/
   - src/qtpyvcp/widgets/display_widgets/designer_plugins.py
   - src/qtpyvcp/widgets/register_widgets.py
   - src/qtpyvcp/widgets/form_widgets/main_window.py
   - src/qtpyvcp/native/backplot_cpp/
   - debian/control
   - pyproject.toml
   - tests/widgets/
   - docs/source/components/qtquick3d_backplot.rst


2026-03-09
----------

Area
   Debian packaging dependency metadata (PySide6 runtime)

Summary
   Added the missing QtUiTools runtime dependency so APT installs include
   `PySide6.QtUiTools` needed by the QtPyVCP error dialog path.

Changes
   - Added `python3-pyside6.qtuitools` to `Build-Depends` for packaging
     consistency in PySide6 builds.
   - Added `python3-pyside6.qtuitools` to `Depends` for `python3-qtpyvcp` so
     runtime imports succeed after plain APT install.

Validation
   - Verified Debian package name exists via `apt-cache search`.
   - Confirmed traceback import target matches provided module package.

Files
   - debian/control


2026-02-20
----------

Area
   Program actions + MDI history queue coordination

Summary
   Corrected MDI queue feedhold/resume handling so cycle start can resume paused
   queued MDI execution in the valid LinuxCNC state paths.

Changes
   - Improved MDI issue path to avoid unnecessary mode switching when already in MDI.
   - Updated run-action logic to allow MDI resume/feedhold recovery cases.
   - Refined queue scheduler gating and failed-dispatch behavior in MDI history widget.

Validation
   - Feedhold on a running queued MDI command resumes from cycle start as expected.
   - Queue pause/resume behavior remains functional.

Files
   - src/qtpyvcp/actions/machine_actions.py
   - src/qtpyvcp/actions/program_actions.py
   - src/qtpyvcp/widgets/input_widgets/mdihistory_widget.py
