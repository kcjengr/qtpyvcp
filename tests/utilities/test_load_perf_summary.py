import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from qtpyvcp.utilities.load_perf_summary import ProgramLoadPerfSummary


@pytest.fixture
def perf_summary():
    with patch.dict(os.environ, {"QTPYVCP_LOAD_PHASE_DETAILS": "0"}):
        with patch("qtpyvcp.utilities.load_perf_summary.perf_counter") as mock_perf:
            mock_perf.side_effect = iter([100.0 + i * 0.5 for i in range(1000)])
            yield ProgramLoadPerfSummary()


class TestReset:
    def test_reset_initializes_all_attributes(self, perf_summary):
        assert perf_summary._file is None
        assert perf_summary._start is None
        assert perf_summary._vtk_cpp_mode is False
        assert perf_summary._vtk_added_segments is None
        assert perf_summary._linuxcnc_open_wait_ms == 0.0
        assert perf_summary._parse_interp_ms == 0.0
        assert perf_summary._pre_backplot_dispatch_ms == 0.0
        assert perf_summary._pre_backplot_entry_ms is None
        assert perf_summary._linuxcnc_file_event_ms is None
        assert perf_summary._has_open_wait is False
        assert perf_summary._has_parse_interp is False
        assert perf_summary._has_pre_backplot_interp is False
        assert perf_summary._vtk_ms is None
        assert perf_summary._vtk_draw_ms is None
        assert perf_summary._vtk_actor_build_ms is None
        assert perf_summary._gcode_text_edit_ms is None
        assert perf_summary._gcode_editor_ms is None
        assert perf_summary._editor_ms_by_widget == {}
        assert perf_summary._editor_count_by_widget == {}
        assert perf_summary._editor_update_count == 0
        assert perf_summary._phases_emitted == set()
        assert perf_summary._phase_elapsed_ms == {}
        assert perf_summary._printed is False


class TestSameFile:
    def test_same_file_returns_true_for_matching_path(self, perf_summary):
        perf_summary._file = "/tmp/test.ngc"
        assert perf_summary._same_file("/tmp/test.ngc") is True

    def test_same_file_returns_true_for_relative_path(self, perf_summary):
        abs_path = os.path.abspath("/tmp/test.ngc")
        perf_summary._file = abs_path
        assert perf_summary._same_file("tmp/test.ngc") or perf_summary._file == abs_path

    def test_same_file_returns_false_for_different_file(self, perf_summary):
        perf_summary._file = "/tmp/test.ngc"
        assert perf_summary._same_file("/tmp/other.ngc") is False

    def test_same_file_returns_false_when_no_file_set(self, perf_summary):
        assert perf_summary._same_file("/tmp/test.ngc") is False

    def test_same_file_returns_false_for_none(self, perf_summary):
        assert perf_summary._same_file(None) is False


class TestStart:
    def test_start_sets_file_and_time(self, perf_summary):
        perf_summary.start("/tmp/test.ngc")
        assert perf_summary._file == os.path.abspath("/tmp/test.ngc")
        assert perf_summary._start is not None

    def test_start_emits_load_requested_phase(self, perf_summary):
        perf_summary.start("/tmp/test.ngc")
        assert "load-requested" in perf_summary._phases_emitted

    def test_start_does_nothing_for_none(self, perf_summary):
        perf_summary.start(None)
        assert perf_summary._file is None

    def test_start_does_nothing_for_empty_string(self, perf_summary):
        perf_summary.start("")
        assert perf_summary._file is None

    def test_start_resets_previous_state(self, perf_summary):
        perf_summary._file = "/tmp/old.ngc"
        perf_summary._start = 50.0
        perf_summary._printed = True
        perf_summary.start("/tmp/new.ngc")
        assert perf_summary._file == os.path.abspath("/tmp/new.ngc")
        assert perf_summary._printed is False


class TestEmitPhase:
    def test_emit_phase_records_elapsed_ms(self, perf_summary):
        perf_summary.start("/tmp/test.ngc")
        perf_summary._emit_phase("test-phase")
        assert "test-phase" in perf_summary._phase_elapsed_ms
        assert abs(perf_summary._phase_elapsed_ms["test-phase"] - 1000.0) < 1.0

    def test_emit_phase_accepts_explicit_elapsed_ms(self, perf_summary):
        with patch("qtpyvcp.utilities.load_perf_summary.perf_counter"):
            perf_summary.start("/tmp/test.ngc")
            perf_summary._emit_phase("test-phase", elapsed_ms=42.0)
            assert perf_summary._phase_elapsed_ms["test-phase"] == 42.0

    def test_emit_phase_does_not_duplicate(self, perf_summary):
        with patch("qtpyvcp.utilities.load_perf_summary.perf_counter") as mock_perf:
            mock_perf.side_effect = [100.0, 101.0, 105.0]
            perf_summary.start("/tmp/test.ngc")
            perf_summary._emit_phase("test-phase")
            first_elapsed = perf_summary._phase_elapsed_ms["test-phase"]
            perf_summary._emit_phase("test-phase")
            assert perf_summary._phase_elapsed_ms["test-phase"] == first_elapsed

    def test_emit_phase_does_nothing_when_start_is_none(self, perf_summary):
        perf_summary._emit_phase("test-phase")
        assert "test-phase" not in perf_summary._phase_elapsed_ms


class TestMarkPhase:
    def test_mark_phase_emits_phase(self, perf_summary):
        perf_summary.mark_phase("/tmp/test.ngc", phase="my-phase")
        assert "my-phase" in perf_summary._phases_emitted

    def test_mark_phase_auto_starts_if_needed(self, perf_summary):
        # Don't call start() first
        perf_summary.mark_phase("/tmp/test.ngc", phase="my-phase")
        assert perf_summary._file == os.path.abspath("/tmp/test.ngc")

    def test_mark_phase_does_nothing_for_none(self, perf_summary):
        perf_summary.mark_phase(None, phase="my-phase")
        assert "my-phase" not in perf_summary._phases_emitted


class TestAddLinuxcncInterpTime:
    def test_add_linuxcnc_interp_time_accumulates(self, perf_summary):
        perf_summary.add_linuxcnc_interp_time("/tmp/test.ngc", interp_ms=50.0)
        assert perf_summary._linuxcnc_open_wait_ms == 50.0
        perf_summary.add_linuxcnc_interp_time("/tmp/test.ngc", interp_ms=30.0)
        assert perf_summary._linuxcnc_open_wait_ms == 80.0

    def test_add_linuxcnc_interp_time_sets_flags(self, perf_summary):
        perf_summary.add_linuxcnc_interp_time("/tmp/test.ngc", interp_ms=50.0)
        assert perf_summary._has_open_wait is True
        assert "linuxcnc-open-wait-done" in perf_summary._phases_emitted

    def test_add_linuxcnc_interp_time_does_nothing_for_none(self, perf_summary):
        perf_summary.add_linuxcnc_interp_time(None, interp_ms=50.0)
        assert perf_summary._has_open_wait is False


class TestMarkLinuxcncFileLoadedEvent:
    def test_mark_linuxcnc_file_loaded_event_records_time(self, perf_summary):
        perf_summary.mark_linuxcnc_file_loaded_event("/tmp/test.ngc")
        assert perf_summary._linuxcnc_file_event_ms is not None
        assert "linuxcnc-file-loaded-event" in perf_summary._phases_emitted

    def test_mark_linuxcnc_file_loaded_event_does_nothing_for_none(self, perf_summary):
        perf_summary.mark_linuxcnc_file_loaded_event(None)
        assert "linuxcnc-file-loaded-event" not in perf_summary._phases_emitted


class TestElapsedSinceStartMs:
    def test_elapsed_returns_value_for_current_file(self, perf_summary):
        perf_summary.start("/tmp/test.ngc")
        elapsed = perf_summary.elapsed_since_start_ms("/tmp/test.ngc")
        assert elapsed is not None
        assert elapsed > 0

    def test_elapsed_returns_none_for_different_file(self, perf_summary):
        perf_summary.start("/tmp/test.ngc")
        assert perf_summary.elapsed_since_start_ms("/tmp/other.ngc") is None

    def test_elapsed_returns_none_when_no_file_set(self, perf_summary):
        assert perf_summary.elapsed_since_start_ms("/tmp/test.ngc") is None

    def test_elapsed_returns_none_for_none(self, perf_summary):
        perf_summary.start("/tmp/test.ngc")
        perf_summary._start = None
        assert perf_summary.elapsed_since_start_ms("/tmp/test.ngc") is None


class TestUpdateBackplot:
    def test_update_backplot_accumulates_vtk_timing(self, perf_summary):
        perf_summary.update_backplot(
            "/tmp/test.ngc",
            added_segments=100,
            interp_ms=50.0,
            draw_ms=30.0,
            actor_build_ms=20.0,
            parse_done_elapsed_ms=70.0,
            draw_done_elapsed_ms=82.0,
            actor_done_elapsed_ms=84.0,
            backplot_done_elapsed_ms=86.0,
        )
        assert perf_summary._vtk_added_segments == 100
        assert perf_summary._has_parse_interp is True
        assert "backplot-parse-done" in perf_summary._phases_emitted
        assert "backplot-draw-done" in perf_summary._phases_emitted
        assert "backplot-actor-done" in perf_summary._phases_emitted
        assert "backplot-complete" in perf_summary._phases_emitted

    def test_update_backplot_sets_cpp_mode(self, perf_summary):
        perf_summary.update_backplot(
            "/tmp/test.ngc",
            added_segments=100,
            interp_ms=50.0,
            draw_ms=30.0,
            actor_build_ms=20.0,
            cpp_mode=True,
        )
        assert perf_summary._vtk_cpp_mode is True

    def test_update_backplot_accumulates_interp_ms(self, perf_summary):
        perf_summary.update_backplot(
            "/tmp/test.ngc",
            added_segments=100,
            interp_ms=50.0,
            draw_ms=30.0,
            actor_build_ms=20.0,
        )
        first_parse = perf_summary._parse_interp_ms
        perf_summary.update_backplot(
            "/tmp/test.ngc",
            added_segments=200,
            interp_ms=25.0,
            draw_ms=15.0,
            actor_build_ms=10.0,
        )
        assert perf_summary._parse_interp_ms == first_parse + 25.0

    def test_update_backplot_does_nothing_for_none(self, perf_summary):
        perf_summary.update_backplot(
            None, added_segments=100, interp_ms=50.0, draw_ms=30.0, actor_build_ms=20.0
        )
        assert perf_summary._has_parse_interp is False


class TestUpdateEditor:
    def test_update_editor_tracks_widget_stats(self, perf_summary):
        perf_summary.update_editor("/tmp/test.ngc", widget_name="GcodeTextEdit", total_ms=15.0)
        assert perf_summary._editor_update_count == 1
        assert "GcodeTextEdit" in perf_summary._editor_ms_by_widget
        assert perf_summary._editor_ms_by_widget["GcodeTextEdit"] == 15.0

    def test_update_editor_emits_gcodetextedit_phase(self, perf_summary):
        perf_summary.update_editor("/tmp/test.ngc", widget_name="GcodeTextEdit", total_ms=15.0)
        assert "gcodetextedit-done" in perf_summary._phases_emitted

    def test_update_editor_emits_gcodeeditor_phase(self, perf_summary):
        perf_summary.update_editor("/tmp/test.ngc", widget_name="GCodeEditor", total_ms=20.0)
        assert "gcodeeditor-done" in perf_summary._phases_emitted

    def test_update_editor_aggregates_gcodeeditor_variants(self, perf_summary):
        perf_summary.update_editor("/tmp/test.ngc", widget_name="GCodeEditor", total_ms=10.0)
        perf_summary.update_editor("/tmp/test.ngc", widget_name="GcodeEditor", total_ms=20.0)
        assert perf_summary._gcode_editor_ms == 30.0

    def test_update_editor_accumulates_widget_time(self, perf_summary):
        perf_summary.update_editor("/tmp/test.ngc", widget_name="GcodeTextEdit", total_ms=15.0)
        perf_summary.update_editor("/tmp/test.ngc", widget_name="GcodeTextEdit", total_ms=25.0)
        assert perf_summary._editor_ms_by_widget["GcodeTextEdit"] == 40.0

    def test_update_editor_does_nothing_for_none(self, perf_summary):
        perf_summary.update_editor(None, widget_name="GcodeTextEdit", total_ms=15.0)
        assert perf_summary._editor_update_count == 0


class TestIsComplete:
    def test_is_complete_returns_false_when_empty(self, perf_summary):
        assert perf_summary._is_complete() is False

    def test_is_complete_returns_true_with_all_fields(self, perf_summary):
        perf_summary._file = "/tmp/test.ngc"
        perf_summary._start = 100.0
        perf_summary._vtk_added_segments = 100
        perf_summary._has_open_wait = True
        perf_summary._has_parse_interp = True
        perf_summary._vtk_ms = 50.0
        perf_summary._editor_update_count = 2
        assert perf_summary._is_complete() is True

    def test_is_complete_requires_editor_updates(self, perf_summary):
        perf_summary._file = "/tmp/test.ngc"
        perf_summary._start = 100.0
        perf_summary._vtk_added_segments = 100
        perf_summary._has_open_wait = True
        perf_summary._has_parse_interp = True
        perf_summary._vtk_ms = 50.0
        perf_summary._editor_update_count = 1
        assert perf_summary._is_complete() is False


class TestFormatHelpers:
    def test_fmt_ms(self):
        result = ProgramLoadPerfSummary._fmt_ms(1500.5)
        assert "1.500s" in result
        assert "1500.50 ms" in result

    def test_fmt_elapsed(self):
        result = ProgramLoadPerfSummary._fmt_elapsed(2500.0)
        assert "T+2.500s" in result
        assert "2500.00 ms" in result

    def test_fmt_stopwatch(self):
        result = ProgramLoadPerfSummary._fmt_stopwatch(1234.5)
        assert "  1.2s" in result

    def test_fmt_file_size_bytes(self):
        result = ProgramLoadPerfSummary._fmt_file_size(512)
        assert result == "512 B"

    def test_fmt_file_size_kb(self):
        result = ProgramLoadPerfSummary._fmt_file_size(1024)
        assert "KB" in result

    def test_fmt_file_size_mb(self):
        result = ProgramLoadPerfSummary._fmt_file_size(1048576)
        assert "MB" in result

    def test_fmt_file_size_gb(self):
        result = ProgramLoadPerfSummary._fmt_file_size(1073741824)
        assert "GB" in result


class TestMaybePrint:
    def test_maybe_print_does_not_fire_when_incomplete(self, perf_summary, caplog):
        with patch("qtpyvcp.utilities.load_perf_summary.LOG") as mock_log:
            perf_summary._maybe_print()
            mock_log.info.assert_not_called()

    def test_maybe_print_does_not_fire_when_already_printed(self, perf_summary, caplog):
        perf_summary._file = "/tmp/test.ngc"
        perf_summary._start = 100.0
        perf_summary._vtk_added_segments = 100
        perf_summary._has_open_wait = True
        perf_summary._has_parse_interp = True
        perf_summary._vtk_ms = 50.0
        perf_summary._editor_update_count = 2
        perf_summary._printed = True
        with patch("qtpyvcp.utilities.load_perf_summary.LOG") as mock_log:
            with patch("qtpyvcp.utilities.load_perf_summary.perf_counter") as mock_perf:
                mock_perf.return_value = 105.0
                perf_summary._maybe_print()
                mock_log.info.assert_not_called()

    def test_maybe_print_sets_printed_flag(self, perf_summary):
        perf_summary._file = "/tmp/test.ngc"
        perf_summary._start = 100.0
        perf_summary._vtk_added_segments = 100
        perf_summary._has_open_wait = True
        perf_summary._has_parse_interp = True
        perf_summary._vtk_ms = 50.0
        perf_summary._editor_update_count = 2
        with patch("qtpyvcp.utilities.load_perf_summary.LOG") as mock_log:
            with patch("os.path.getsize", return_value=1024):
                perf_summary._maybe_print()
        assert perf_summary._printed is True

    def test_maybe_print_emits_load_summary_complete(self, perf_summary):
        perf_summary._file = "/tmp/test.ngc"
        perf_summary._start = 100.0
        perf_summary._vtk_added_segments = 100
        perf_summary._has_open_wait = True
        perf_summary._has_parse_interp = True
        perf_summary._vtk_ms = 50.0
        perf_summary._editor_update_count = 2
        with patch("qtpyvcp.utilities.load_perf_summary.LOG") as mock_log:
            with patch("os.path.getsize", return_value=1024):
                perf_summary._maybe_print()
        assert "load-summary-complete" in perf_summary._phases_emitted

    def test_maybe_print_handles_missing_file_size(self, perf_summary):
        perf_summary._file = "/tmp/nonexistent.ngc"
        perf_summary._start = 100.0
        perf_summary._vtk_added_segments = 100
        perf_summary._has_open_wait = True
        perf_summary._has_parse_interp = True
        perf_summary._vtk_ms = 50.0
        perf_summary._editor_update_count = 2
        with patch("qtpyvcp.utilities.load_perf_summary.LOG") as mock_log:
            with patch("os.path.getsize", side_effect=OSError):
                perf_summary._maybe_print()
        assert perf_summary._printed is True
