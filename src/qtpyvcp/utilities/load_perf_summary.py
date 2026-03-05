import os
from time import perf_counter

from qtpyvcp.utilities import logger


LOG = logger.getLogger(__name__)


class ProgramLoadPerfSummary:
    def __init__(self):
        # Optional verbose phase trace. Summary output remains enabled regardless.
        self._log_phase_details = os.getenv("QTPYVCP_LOAD_PHASE_DETAILS", "0") in (
            "1",
            "true",
            "yes",
            "on",
        )
        self._reset()

    def _reset(self):
        self._file = None
        self._start = None
        self._vtk_cpp_mode = False
        self._vtk_added_segments = None
        self._linuxcnc_open_wait_ms = 0.0
        self._parse_interp_ms = 0.0
        self._pre_backplot_dispatch_ms = 0.0
        self._pre_backplot_entry_ms = None
        self._linuxcnc_file_event_ms = None
        self._has_open_wait = False
        self._has_parse_interp = False
        self._has_pre_backplot_interp = False
        self._vtk_ms = None
        self._gcode_text_edit_ms = None
        self._gcode_editor_ms = None
        self._editor_ms_by_widget = {}
        self._editor_count_by_widget = {}
        self._editor_update_count = 0
        self._phases_emitted = set()
        self._phase_elapsed_ms = {}
        self._printed = False

    def _same_file(self, fname):
        return self._file == os.path.abspath(fname) if fname else False

    def start(self, fname):
        if not fname:
            return

        abs_file = os.path.abspath(fname)
        self._reset()
        self._file = abs_file
        self._start = perf_counter()
        self._emit_phase("load-requested", 0)

    def _emit_phase(self, phase, percent=None, elapsed_ms=None):
        if phase in self._phases_emitted:
            return

        if elapsed_ms is None:
            if self._start is None:
                return
            elapsed_ms = (perf_counter() - self._start) * 1000.0

        if self._log_phase_details:
            file_name = os.path.basename(self._file) if self._file else "n/a"
            LOG.info(
                "[program-load-phase] file=%s phase=%s elapsed_ms=%.2f",
                file_name,
                phase,
                float(elapsed_ms),
            )
        self._phases_emitted.add(phase)
        self._phase_elapsed_ms[phase] = float(elapsed_ms)

    def mark_phase(self, fname, *, phase, percent=None):
        if not fname:
            return

        abs_file = os.path.abspath(fname)
        if self._file is None or self._file != abs_file:
            self.start(abs_file)

        self._emit_phase(phase, percent)

    def add_linuxcnc_interp_time(self, fname, *, interp_ms):
        if not fname:
            return

        abs_file = os.path.abspath(fname)
        if self._file is None or self._file != abs_file:
            self.start(abs_file)

        self._linuxcnc_open_wait_ms += float(interp_ms)
        self._has_open_wait = True
        self._emit_phase("linuxcnc-open-wait-done", 35)
        self._maybe_print()

    def mark_linuxcnc_file_loaded_event(self, fname):
        if not fname:
            return

        abs_file = os.path.abspath(fname)
        if self._file is None or self._file != abs_file:
            self.start(abs_file)

        if self._linuxcnc_file_event_ms is None and self._start is not None:
            self._linuxcnc_file_event_ms = max(0.0, (perf_counter() - self._start) * 1000.0)
            self._emit_phase("linuxcnc-file-loaded-event", 40, self._linuxcnc_file_event_ms)
            self._maybe_print()

    def elapsed_since_start_ms(self, fname):
        if not fname:
            return None

        abs_file = os.path.abspath(fname)
        if self._file is None or self._file != abs_file or self._start is None:
            return None

        return (perf_counter() - self._start) * 1000.0

    def update_backplot(self, fname, *, added_segments, interp_ms, draw_ms, actor_build_ms, cpp_mode=False, pre_backplot_interp_ms=None, parse_done_elapsed_ms=None, draw_done_elapsed_ms=None):
        if not fname:
            return

        abs_file = os.path.abspath(fname)
        if self._file is None or self._file != abs_file:
            self.start(abs_file)

        if pre_backplot_interp_ms is not None and not self._has_pre_backplot_interp:
            elapsed_to_backplot_ms = max(0.0, float(pre_backplot_interp_ms))
            self._pre_backplot_entry_ms = elapsed_to_backplot_ms
            self._emit_phase("backplot-start", 50, elapsed_to_backplot_ms)
            if self._linuxcnc_file_event_ms is not None:
                self._pre_backplot_dispatch_ms = max(0.0, elapsed_to_backplot_ms - self._linuxcnc_file_event_ms)
            else:
                self._pre_backplot_dispatch_ms = max(0.0, elapsed_to_backplot_ms - self._linuxcnc_open_wait_ms)
            self._has_pre_backplot_interp = True

        self._vtk_cpp_mode = bool(cpp_mode)
        self._vtk_added_segments = int(added_segments)
        self._parse_interp_ms += float(interp_ms)
        self._has_parse_interp = True
        self._emit_phase("backplot-parse-done", 70, parse_done_elapsed_ms)
        self._vtk_ms = float(draw_ms) + float(actor_build_ms)
        self._emit_phase("backplot-draw-done", 82, draw_done_elapsed_ms)
        self._maybe_print()

    def update_editor(self, fname, *, widget_name, total_ms):
        if not fname:
            return

        abs_file = os.path.abspath(fname)
        if self._file is None or self._file != abs_file:
            self.start(abs_file)

        ms_val = float(total_ms)
        widget_key = str(widget_name) if widget_name else "UnknownEditor"
        self._editor_update_count += 1
        self._editor_ms_by_widget[widget_key] = self._editor_ms_by_widget.get(widget_key, 0.0) + ms_val
        self._editor_count_by_widget[widget_key] = self._editor_count_by_widget.get(widget_key, 0) + 1

        if widget_name == "GcodeTextEdit":
            self._gcode_text_edit_ms = self._editor_ms_by_widget.get("GcodeTextEdit")
            self._emit_phase("gcodetextedit-done", 90)
        elif widget_name in ("GCodeEditor", "GcodeEditor"):
            self._gcode_editor_ms = (
                self._editor_ms_by_widget.get("GCodeEditor", 0.0)
                + self._editor_ms_by_widget.get("GcodeEditor", 0.0)
            )
            self._emit_phase("gcodeeditor-done", 96)

        self._maybe_print()

    def _is_complete(self):
        return all([
            self._file is not None,
            self._start is not None,
            self._vtk_added_segments is not None,
            self._has_open_wait,
            self._has_parse_interp,
            self._vtk_ms is not None,
            self._editor_update_count >= 2,
        ])

    @staticmethod
    def _fmt_ms(value):
        return f"{value / 1000.0:.3f}s ({value:.2f} ms)"

    @staticmethod
    def _fmt_elapsed(value):
        return f"T+{value / 1000.0:.3f}s ({value:.2f} ms)"

    @staticmethod
    def _fmt_stopwatch(value):
        return f"{value / 1000.0:6.1f}s"

    @staticmethod
    def _fmt_file_size(size_bytes):
        value = float(size_bytes)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024.0 or unit == "TB":
                if unit == "B":
                    return f"{int(value)} {unit}"
                return f"{value:.2f} {unit}"
            value /= 1024.0

    def _maybe_print(self):
        if self._printed or not self._is_complete():
            return

        total_ms = (perf_counter() - self._start) * 1000.0
        file_name = os.path.basename(self._file)
        vtk_data = str(self._vtk_added_segments)
        file_size = "n/a"
        try:
            file_size = self._fmt_file_size(os.path.getsize(self._file))
        except (OSError, TypeError):
            pass

        metadata_rows = [
            ("File Size", file_size),
            ("VTK C++ Mode", "true" if self._vtk_cpp_mode else "false"),
            ("VTK Backplot Data", vtk_data),
        ]

        stage_rows = [
            ("LCNC Open/Wait", self._linuxcnc_open_wait_ms, self._phase_elapsed_ms.get("linuxcnc-open-wait-done")),
            ("LCNC File Event Marker", self._linuxcnc_file_event_ms, self._phase_elapsed_ms.get("linuxcnc-file-loaded-event")),
            ("LCNC Pre-Backplot Dispatch", self._pre_backplot_dispatch_ms, self._phase_elapsed_ms.get("backplot-start")),
            ("LCNC Backplot Parse", self._parse_interp_ms, self._phase_elapsed_ms.get("backplot-parse-done")),
            ("VTK Backplot Time", self._vtk_ms, self._phase_elapsed_ms.get("backplot-draw-done")),
        ]

        if self._gcode_text_edit_ms is not None:
            stage_rows.append(("GcodeTextEdit Time", self._gcode_text_edit_ms, self._phase_elapsed_ms.get("gcodetextedit-done")))

        if self._gcode_editor_ms is not None:
            gcode_editor_count = self._editor_count_by_widget.get("GCodeEditor", 0) + self._editor_count_by_widget.get("GcodeEditor", 0)
            gcode_editor_label = "GcodeEditor Time"
            if gcode_editor_count > 1:
                gcode_editor_label = f"GcodeEditor Time (x{gcode_editor_count})"
            stage_rows.append((gcode_editor_label, self._gcode_editor_ms, self._phase_elapsed_ms.get("gcodeeditor-done")))

        stage_rows = [row for row in stage_rows if row[2] is not None and row[1] is not None]

        key_width = max(
            len(label)
            for label, _ in metadata_rows
            + [("File Name", "")]
            + [(label, "") for label, _, _ in stage_rows]
            + [("Total Program Load Time", "")]
        )

        duration_col_width = max(
            [len(self._fmt_stopwatch(total_ms))]
            + [len(self._fmt_stopwatch(duration_ms)) for _, duration_ms, _ in stage_rows]
        )
        elapsed_col_width = max(
            [len("100%")]
            + [len(self._fmt_stopwatch(elapsed_ms)) for _, _, elapsed_ms in stage_rows]
        )
        metric_col_width = duration_col_width + 1 + elapsed_col_width

        lines = ["------------------------------------------------"]
        lines.append(f"-   File Name: {file_name}")
        lines.append("------------------------------------------------")

        for label, value in metadata_rows:
            lines.append(f"-   {label:<{key_width}} = {value:>{metric_col_width}}")

        for label, duration_ms, elapsed_ms in stage_rows:
            duration_text = self._fmt_stopwatch(duration_ms)
            elapsed_text = self._fmt_stopwatch(elapsed_ms)
            lines.append(
                f"-   {label:<{key_width}} = {duration_text:>{duration_col_width}} {elapsed_text:>{elapsed_col_width}}"
            )

        lines.append("------------------------------------------------")
        lines.append(
            f"-   {'Total Program Load Time':<{key_width}} = {self._fmt_stopwatch(total_ms):>{duration_col_width}} {'100%':>{elapsed_col_width}}"
        )
        lines.append("------------------------------------------------")
        LOG.info("[program-load-summary]\n%s", "\n".join(lines))
        self._emit_phase("load-summary-complete", 100)

        self._printed = True


PROGRAM_LOAD_PERF_SUMMARY = ProgramLoadPerfSummary()
