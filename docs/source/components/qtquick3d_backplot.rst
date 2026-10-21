====================
Qt Quick 3D Backplot
====================

Qt Quick 3D is the Qt-based backplot renderer. It is hosted in the existing
QWidget panels through ``QQuickWidget`` and uses a QML ``View3D`` for the
camera, scene, and materials. The widget is named ``Qt3D0`` in Python, Qt
Designer, and ``.ui`` files. The earlier Qt 3D entity/buffer implementation has
been removed; ``Qt3D0`` now always means the Qt Quick 3D renderer.

Architecture
------------

The G-code parser and CNC coordinate calculations are renderer-independent in
``display_widgets/backplot_common``. Programs are parsed by the native C++
canon (``native/backplot_cpp``) when available, with the Python canon as a
fallback for table-rotary machines, foam/jet machines, or a missing build.

The shared layer produces geometry in **WCS-local machine coordinates**. The
renderer keeps it that way:

* ``qtquick3d_backplot/paths.py`` builds one ``Model`` per
  (work-offset, motion-role) pair. The row holds a ``QQuick3DGeometry`` in the
  local frame plus a scene transform. Editing a G54..G59 offset, changing the
  active WCS, or editing the offset table only emits ``dataChanged`` for the
  transform roles -- vertex buffers are never rewritten and the program is not
  re-parsed.
* Motion-role colours are material properties of those rows, so changing a
  path colour is also a material update rather than a reload.
* Incremental-only programs (G91 with no absolute move) are *floating*: the
  shared layer reports the affected WCS indices and the widget anchors them to
  the live machine position (latched while a program is running), matching the
  historical renderer instead of drawing them at WCS zero.

The CNC's Z-up points are converted to Qt Quick 3D's Y-up scene coordinates at
the renderer boundary. A work-offset rotation is mapped to a rotation about the
scene's +Y axis.

Picking
-------

A left click is unprojected by ``View3D.mapTo3DScene`` into a scene-space ray
and handed to Python. The ray is transformed into each row's local frame and
tested against the segment endpoints; the nearest segment within a small
world-space tolerance wins, and ties are resolved by distance along the ray.
This is independent of Qt Quick 3D's mesh picking support for line primitives.
``programLineSelected`` / ``programLinesSelected`` are emitted with the G-code
line, and the editor's selected line(s) (``selected_program_line`` /
``selected_program_lines``) are highlighted in the plot.

Features
--------

* Coloured rapid/feed/arc/dwell/user paths, per-WCS placement, offset
  transitions between WCS paths.
* Program and machine bounds, a machine-size XY grid, axis indicators, and the
  live position trail.
* View presets, orthographic/perspective projection, zoom/orbit/pan with the
  classic mouse model (left orbit, middle pan, right dolly, wheel zoom,
  pan-mode swap).
* Two-colour background (``backgroundColor`` at the bottom,
  ``backgroundColor2`` at the top; equal colours give a solid background) and
  MSAA.
* Active tool bit sized from the QtPyVCP tool table (cylinder by diameter and
  Z offset, or a cone marker when no tool is loaded), following the live
  position with the runtime tool-length offset applied. The bit is drawn
  independently of the spindle: ``backplot.show-spindle`` only controls the
  ``[VTK] SPINDLE`` machine model, which follows the live machine position so
  the bit protrudes below it.
* ``MACHINE_PARTS`` YAML: STL and glTF/GLB parts are parsed in Python and loaded
  as custom ``QQuick3DGeometry`` (Qt Quick 3D resolves ``Model.source`` only to
  ``.mesh`` at runtime), with node world transforms baked in for glTF. Each part
  is a ``Model`` fed by a list model, with the nested hierarchy composed into a
  world transform in Python; ``showMachine`` toggles the whole assembly.
* Robot-arm ``MACHINE_PARTS`` (parts with ``mount`` DH fields) are animated with
  modified-DH forward kinematics, driven by live joint feedback, so the arm
  follows the tool path.
* ``[VTK] SPINDLE`` replaces any ``spindle``-named machine-parts entry and is
  attached to the deepest joint's DH frame.
* Solid meshes are lit by a key and fill ``DirectionalLight`` (flat normals for
  STL, vertex-averaged for glTF). Path lines stay unlit so colours remain exact.
* Settings: grid, program/machine bounds, WCS origins, machine, spindle,
  machine ticks/labels, multi-colour path, points surface, FPS, view, and
  perspective.
* Work-offset origins: a small amber square (aligned with the WCS rotation) and
  a ``G54`` .. ``G59.3`` label at every work offset the loaded program actually
  uses. An empty (or unloaded) program draws no part origins, and configured
  offsets that the program does not use are ignored. Labels are 2D overlays
  projected from the 3D scene, so they stay readable at any zoom. Toggle with
  the ``backplot.show-wcs-origins`` setting.

Known limitations
-----------------

* Qt Quick 3D custom line geometry is always one pixel wide; there is no
  line-width control for it. MSAA is enabled to keep it crisp, but a thicker
  path option is still to be designed.
* Machine ticks/labels (``showMachineTicks`` / ``showMachineLabels``) store
  state only, and ``enableProgramTicks`` does not draw bounds ticks (they are
  not implemented for line geometry yet).
* The height-field surface (``showSurface``) and the camera nav-helper gizmo are
  not rendered; the ``navHelper*`` properties are retained for API/Designer
  compatibility.
* ``enableMultiTouch``, ``enableBreadcrumbs`` and
  ``setProgramViewWhenLoadingProgram`` are API-compatibility no-ops.

Migrating from VTKBackPlot
--------------------------

The existing ``Qt3D0`` widget can be dropped into a panel exactly like the old
VTK widget. ``.ui`` files that still reference the removed ``VTKBackPlot``
class must change the widget class to ``Qt3D0``; keeping the historical object
name (for example ``vtkbackplot``) is fine and keeps existing signal/slot
wiring and panel code working.

Packaging
---------

Qt Quick 3D is provided by the PySide6 Qt Quick 3D modules. Runtime packages
must include ``python3-pyside6.qtquickwidgets``,
``python3-pyside6.qtquick3d`` and the ``qml6-module-qtquick3d`` QML module (see
``debian/control``). The QML scene is installed alongside the Python package.
The Designer custom widget is named ``Qt3D0``; its object name is ``qt3d0``.
