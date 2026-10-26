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


2026-10-26
----------

Area
   Qt3D0 (Qt Quick 3D backplot) - known limitations

Summary
   Closed most of the documented renderer gaps: lathe insert silhouettes and
   per-tool models, machine/program ticks and labels, touch navigation, a
   clickable orientation gizmo, breadcrumb and post-load-view controls, and
   label decluttering.

Changes
   - Lathe tool bits now use the DB insert silhouette
     (`insert_profile.compute_insert_profile()`), triangulated in Python and
     drawn as a double-sided Quick 3D mesh in the XZ plane. Holder/ISO
     orientation, handedness and anchor selection follow the tool-table
     editor. Per-tool STL/glTF models are resolved from a `model`/`stl`/`mesh`
     field on the tool row or DB extras.
   - Added machine and program bounds tick geometry plus projected,
     decluttered numeric labels; `showMachineTicks`, `showMachineLabels` and
     `enableProgramTicks` now have visible effects.
   - Implemented the camera-orientation "nav helper" as a clickable 2D overlay
     driven by the live camera basis. `navHelperEnabled`, anchor/size/padding,
     labels, pickability and X/Y/Z colours are honoured.
   - `enableMultiTouch` now enables pinch zoom, two-finger pan and twist orbit
     in QML. `enableBreadcrumbs` toggles the live trail, and
     `setProgramViewWhenLoadingProgram` selects whether/which view is fitted
     after a load. The gesture surface uses `MultiPointTouchArea`, not
     `PinchArea`: Qt 6.12 emits a `qt.qml.propertyCache.append` warning for
     `QQuickPinchArea` from the QML loader thread, and QtPyVCP's Python Qt
     message handler deadlocks when that thread needs the GIL while
     `QQuickWidget.setSource()` holds it. This was the LinuxCNC startup hang
     after `simulated_home.hal`.
   - Added greedy 2D label collision avoidance for WCS and tick labels.
   - `showSurface` is retained for configuration compatibility but documented
     as deprecated; the old VTK implementation was a hard-coded probe demo.
   - No-tool cone: the model origin is moved up by the full cone length so the
     cone tip, not its centre, sits at the tool position.
   - Live trail ("breadcrumbs") now follows the cutter tip: it applies the
     active `stat.tool_offset`, so G43/G43.1 is honoured and G49 returns the
     trail to the raw machine position. The spindle model still uses the raw
     machine position.
   - Breadcrumbs snap to the currently executing G-code segment (with the
     previous/adjacent line as a fallback), matching the old VTK path-cache
     behaviour. Zero-length samples are dropped. This suppresses the
     following-error/encoder wander that made the yellow trail look erratic at
     high feed rates.
   - Decoupled live position/trail sampling from the status plugin. The widget
     polls its own `linuxcnc.stat` every 16 ms (60 Hz) and uses the same object
     for `motion_line` and `tool_offset`; the status plugin's 75 ms
     `positionChanged` signal is no longer connected. At high feed rates the
     trail is no longer limited to one coarse segment per status poll.
   - Added screen-space ambient occlusion (SSAO) and a low-intensity
     camera-follow fill light. The two fixed key/fill lights left front-facing
     machine/tool surfaces dark; the camera light keeps them readable without
     flattening the scene.
   - Nav-helper axis colours no longer repaint the world X/Y/Z axes.

Validation
   - `pytest tests`: 137 passed.
   - `ruff check` clean on the touched packages/tests.
   - Xvfb/OpenGL render check: nav-helper axes/labels draw; T1 lathe insert
     builds a 37-point mesh and reaches the QML `toolMeshModel`.
   - `linuxcnc xyz-metric.ini` (sim.qtpyvcp) starts the TNC window instead of
     stalling at `Found file(REL): ./hallib/simulated_home.hal`.

Files
   - src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/geometry.py
   - src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/qtquick3d_backplot.py
   - src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/tool.py
   - src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/wcs_origins.py
   - src/qtpyvcp/widgets/display_widgets/qtquick3d_backplot/scene.qml
   - tests/widgets/test_qtquick3d_tool.py
   - tests/widgets/test_qtquick3d_properties.py
   - docs/source/components/qtquick3d_backplot.rst
   - audit_reports/QT3D0_WIDGET_REPORT_2026-10-26.md


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
