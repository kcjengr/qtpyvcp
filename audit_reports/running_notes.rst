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
