import pytest
from unittest.mock import MagicMock, patch


class TestDROLabel:
    """Tests for DROLabel widget."""

    @pytest.fixture(autouse=True)
    def mock_linuxcnc(self):
        """Mock linuxcnc module to allow importing modules that depend on Info()."""
        mock_ini = MagicMock()
        with patch.dict('sys.modules', {'linuxcnc': MagicMock()}):
            yield

    def test_init_no_parent(self, qtbot):
        with patch('qtpyvcp.utilities.info.Info') as mock_info_cls:
            mock_info = MagicMock()
            mock_info.getIsLathe.return_value = False
            mock_info_cls.return_value = mock_info
            from qtpy.QtWidgets import QLabel
            from qtpyvcp.widgets.base_widgets.dro_base_widget import DROBaseWidget
            from qtpyvcp.widgets.display_widgets.dro_label import DROLabel
            widget = DROLabel()
            qtbot.addWidget(widget)
            assert widget is not None

    def test_inherits_from_qlabel(self, qtbot):
        with patch('qtpyvcp.utilities.info.Info') as mock_info_cls:
            mock_info = MagicMock()
            mock_info.getIsLathe.return_value = False
            mock_info_cls.return_value = mock_info
            from qtpy.QtWidgets import QLabel
            from qtpyvcp.widgets.display_widgets.dro_label import DROLabel
            widget = DROLabel()
            qtbot.addWidget(widget)
            assert isinstance(widget, QLabel)

    def test_inherits_from_drobasewidget(self, qtbot):
        with patch('qtpyvcp.utilities.info.Info') as mock_info_cls:
            mock_info = MagicMock()
            mock_info.getIsLathe.return_value = False
            mock_info_cls.return_value = mock_info
            from qtpyvcp.widgets.base_widgets.dro_base_widget import DROBaseWidget
            from qtpyvcp.widgets.display_widgets.dro_label import DROLabel
            widget = DROLabel()
            qtbot.addWidget(widget)
            assert isinstance(widget, DROBaseWidget)

    def test_has_default_text(self, qtbot):
        with patch('qtpyvcp.utilities.info.Info') as mock_info_cls:
            mock_info = MagicMock()
            mock_info.getIsLathe.return_value = False
            mock_info_cls.return_value = mock_info
            from qtpyvcp.widgets.display_widgets.dro_label import DROLabel
            widget = DROLabel()
            qtbot.addWidget(widget)
            assert "1.0000" in widget.text()

    def test_set_text(self, qtbot):
        with patch('qtpyvcp.utilities.info.Info') as mock_info_cls:
            mock_info = MagicMock()
            mock_info.getIsLathe.return_value = False
            mock_info_cls.return_value = mock_info
            from qtpyvcp.widgets.display_widgets.dro_label import DROLabel
            widget = DROLabel()
            qtbot.addWidget(widget)
            widget.setText("123.456")
            assert widget.text() == "123.456"

    def test_has_axis_number_property(self, qtbot):
        with patch('qtpyvcp.utilities.info.Info') as mock_info_cls:
            mock_info = MagicMock()
            mock_info.getIsLathe.return_value = False
            mock_info_cls.return_value = mock_info
            from qtpyvcp.widgets.display_widgets.dro_label import DROLabel
            widget = DROLabel()
            qtbot.addWidget(widget)
            meta_obj = widget.metaObject()
            prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
            assert 'axisNumber' in prop_names

    def test_has_reference_type_property(self, qtbot):
        with patch('qtpyvcp.utilities.info.Info') as mock_info_cls:
            mock_info = MagicMock()
            mock_info.getIsLathe.return_value = False
            mock_info_cls.return_value = mock_info
            from qtpyvcp.widgets.display_widgets.dro_label import DROLabel
            widget = DROLabel()
            qtbot.addWidget(widget)
            meta_obj = widget.metaObject()
            prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
            assert 'referenceType' in prop_names

    def test_has_inch_format_property(self, qtbot):
        with patch('qtpyvcp.utilities.info.Info') as mock_info_cls:
            mock_info = MagicMock()
            mock_info.getIsLathe.return_value = False
            mock_info_cls.return_value = mock_info
            from qtpyvcp.widgets.display_widgets.dro_label import DROLabel
            widget = DROLabel()
            qtbot.addWidget(widget)
            meta_obj = widget.metaObject()
            prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
            assert 'inchFormat' in prop_names

    def test_has_millimeter_format_property(self, qtbot):
        with patch('qtpyvcp.utilities.info.Info') as mock_info_cls:
            mock_info = MagicMock()
            mock_info.getIsLathe.return_value = False
            mock_info_cls.return_value = mock_info
            from qtpyvcp.widgets.display_widgets.dro_label import DROLabel
            widget = DROLabel()
            qtbot.addWidget(widget)
            meta_obj = widget.metaObject()
            prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
            assert 'millimeterFormat' in prop_names

    def test_has_lathe_mode_property(self, qtbot):
        with patch('qtpyvcp.utilities.info.Info') as mock_info_cls:
            mock_info = MagicMock()
            mock_info.getIsLathe.return_value = False
            mock_info_cls.return_value = mock_info
            from qtpyvcp.widgets.display_widgets.dro_label import DROLabel
            widget = DROLabel()
            qtbot.addWidget(widget)
            meta_obj = widget.metaObject()
            prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
            assert 'latheMode' in prop_names
