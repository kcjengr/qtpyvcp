import os
import pytest


class TestClearCache:
    def test_clear_cache_resets_style_data(self):
        from qtpyvcp.widgets.qtdesigner import stylesheet
        result = stylesheet._get_style_data(None)
        assert result is not None
        assert getattr(stylesheet, '__style_data') is not None
        stylesheet.clear_cache()
        assert getattr(stylesheet, '__style_data') is None


class TestGetStyleData:
    def test_returns_string(self):
        from qtpyvcp.widgets.qtdesigner import stylesheet
        result = stylesheet._get_style_data(None)
        assert isinstance(result, str)

    def test_returns_non_empty(self):
        from qtpyvcp.widgets.qtdesigner import stylesheet
        result = stylesheet._get_style_data(None)
        assert len(result) > 0

    def test_contains_stylesheet_content(self):
        from qtpyvcp.widgets.qtdesigner import stylesheet
        result = stylesheet._get_style_data(None)
        assert 'color' in result.lower() or 'pushbutton' in result.lower()

    def test_caches_result(self):
        from qtpyvcp.widgets.qtdesigner import stylesheet
        stylesheet.clear_cache()
        result1 = stylesheet._get_style_data(None)
        result2 = stylesheet._get_style_data(None)
        assert result1 is result2


class TestApplyStylesheet:
    def test_apply_stylesheet_no_exception_with_none_widget(self, qtbot):
        from qtpyvcp.widgets.qtdesigner import stylesheet
        stylesheet.clear_cache()
        from qtpy.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        stylesheet.apply_stylesheet(None, None)

    def test_apply_stylesheet_with_custom_path(self, tmp_path, qtbot):
        from qtpyvcp.widgets.qtdesigner import stylesheet
        stylesheet.clear_cache()
        custom_css = tmp_path / "custom.qss"
        custom_css.write_text("QWidget { background-color: blue; }")
        from qtpy.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        stylesheet.apply_stylesheet(str(custom_css), None)

    def test_apply_stylesheet_with_invalid_path(self, qtbot):
        from qtpyvcp.widgets.qtdesigner import stylesheet
        stylesheet.clear_cache()
        from qtpy.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        stylesheet.apply_stylesheet("/nonexistent/path/style.qss", None)

    def test_apply_stylesheet_with_empty_path_uses_default(self, qtbot):
        from qtpyvcp.widgets.qtdesigner import stylesheet
        stylesheet.clear_cache()
        from qtpy.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        stylesheet.apply_stylesheet("", None)


class TestGlobalStylesheetPath:
    def test_global_stylesheet_is_absolute_path(self):
        from qtpyvcp.widgets.qtdesigner import stylesheet
        assert os.path.isabs(stylesheet.GLOBAL_STYLESHEET)

    def test_global_stylesheet_exists(self):
        from qtpyvcp.widgets.qtdesigner import stylesheet
        assert os.path.isfile(stylesheet.GLOBAL_STYLESHEET)


class TestEnvVarStylesheet:
    def test_env_var_qss_stylesheet_is_used(self, tmp_path, monkeypatch):
        custom_css = tmp_path / "env_style.qss"
        custom_css.write_text("QWidget { background-color: green; }")
        monkeypatch.setenv("QSS_STYLESHEET", str(custom_css))
        from qtpyvcp.widgets.qtdesigner import stylesheet
        stylesheet.clear_cache()
        result = stylesheet._get_style_data(None)
        assert "green" in result.lower()

    def test_empty_env_var_uses_default(self, monkeypatch):
        monkeypatch.setenv("QSS_STYLESHEET", "")
        from qtpyvcp.widgets.qtdesigner import stylesheet
        stylesheet.clear_cache()
        result = stylesheet._get_style_data(None)
        assert len(result) > 0

    def test_missing_env_var_uses_default(self, monkeypatch):
        monkeypatch.delenv("QSS_STYLESHEET", raising=False)
        from qtpyvcp.widgets.qtdesigner import stylesheet
        stylesheet.clear_cache()
        result = stylesheet._get_style_data(None)
        assert len(result) > 0
