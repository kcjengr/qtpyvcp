============================
Develop Update Release Notes
============================

Maintainer drafting note: for in-progress session tracking before publishing here,
use the internal running notes file at ``docs/source/development/running_notes.rst``.

February 20, 2026 - 5.0.9-13 Develop Release Notes
---------------------------------------------------

QtPyVCP received fixes to improve MDI queue behavior during feedhold and cycle-start resume scenarios. The result is a more reliable recovery path for queued MDI execution, especially when pause/feedhold states occur during active queue processing.

Summary of updates
------------------

- Improved MDI issue flow to avoid unnecessary mode switching when already in MDI mode.
- Updated program run eligibility to allow valid MDI resume/feedhold recovery paths.
- Refined MDI history queue scheduler gating to better handle paused/feedhold execution states.
- Added safer queue dispatch failure handling to prevent stale "running" queue-row state.

Affected files
--------------

- `src/qtpyvcp/actions/machine_actions.py`
- `src/qtpyvcp/actions/program_actions.py`
- `src/qtpyvcp/widgets/input_widgets/mdihistory_widget.py`

Previous develop updates
------------------------

Add older or future QtPyVCP develop entries here, newest at the top.
