import pytest
import sys
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_subcall_button_module():
    """Load SubCallButton with mocked LinuxCNC dependencies."""
    # Mock the Info class and its methods
    mock_info = MagicMock()
    mock_info.getSubroutineSearchDirs.return_value = ['/tmp/mock_subroutines']

    # Mock machine_actions.issue_mdi
    mock_issue_mdi = MagicMock()
    mock_issue_mdi.bindOk = MagicMock()

    # Create mocks for the modules that need LinuxCNC
    mock_machine_actions = MagicMock()
    mock_machine_actions.issue_mdi = mock_issue_mdi

    # Save original modules
    original_modules = {}
    modules_to_mock = [
        'qtpyvcp.utilities.info',
        'qtpyvcp.actions.machine_actions',
        'qtpyvcp.actions.base_actions',
    ]

    for mod_name in modules_to_mock:
        if mod_name in sys.modules:
            original_modules[mod_name] = sys.modules[mod_name]

    # Set up mocks
    sys.modules['qtpyvcp.utilities.info'] = MagicMock()
    sys.modules['qtpyvcp.utilities.info'].Info.return_value = mock_info
    sys.modules['qtpyvcp.actions.machine_actions'] = mock_machine_actions
    sys.modules['qtpyvcp.actions.base_actions'] = MagicMock()

    # Now import SubCallButton
    from qtpyvcp.widgets.button_widgets.subcall_button import SubCallButton
    yield SubCallButton, mock_issue_mdi, mock_info

    # Restore original modules
    for mod_name, orig_mod in original_modules.items():
        sys.modules[mod_name] = orig_mod


class TestSubCallButton:
    """Tests for SubCallButton widget."""

    def test_init(self, qtbot, mock_subcall_button_module):
        SubCallButton, _, _ = mock_subcall_button_module
        btn = SubCallButton()
        qtbot.addWidget(btn)
        assert btn is not None

    def test_init_default_filename(self, qtbot, mock_subcall_button_module):
        SubCallButton, _, _ = mock_subcall_button_module
        btn = SubCallButton()
        qtbot.addWidget(btn)
        assert btn._filename == ''

    def test_init_with_filename(self, qtbot, mock_subcall_button_module):
        SubCallButton, _, _ = mock_subcall_button_module
        btn = SubCallButton(filename='test.ngc')
        qtbot.addWidget(btn)
        assert btn._filename == 'test.ngc'

    def test_init_is_pushbutton(self, qtbot, mock_subcall_button_module):
        from qtpy.QtWidgets import QPushButton
        SubCallButton, _, _ = mock_subcall_button_module
        btn = SubCallButton()
        qtbot.addWidget(btn)
        assert isinstance(btn, QPushButton)

    def test_filename_property_getter(self, qtbot, mock_subcall_button_module):
        SubCallButton, _, _ = mock_subcall_button_module
        btn = SubCallButton(filename='my_sub.ngc')
        qtbot.addWidget(btn)
        assert btn.filename == 'my_sub.ngc'

    def test_filename_property_setter(self, qtbot, mock_subcall_button_module):
        SubCallButton, _, _ = mock_subcall_button_module
        btn = SubCallButton()
        qtbot.addWidget(btn)
        btn.filename = 'new_file.ngc'
        assert btn._filename == 'new_file.ngc'

    def test_filename_is_qt_property(self, qtbot, mock_subcall_button_module):
        SubCallButton, _, _ = mock_subcall_button_module
        btn = SubCallButton()
        qtbot.addWidget(btn)
        meta_obj = btn.metaObject()
        prop_names = [meta_obj.property(i).name() for i in range(meta_obj.propertyCount())]
        assert 'filename' in prop_names

    def test_click_signal(self, qtbot, mock_subcall_button_module):
        SubCallButton, _, _ = mock_subcall_button_module
        btn = SubCallButton()
        qtbot.addWidget(btn)
        clicked_fired = []
        btn.clicked.connect(lambda: clicked_fired.append(True))
        btn.click()
        assert len(clicked_fired) == 1

    def test_parse_positional_args_pattern(self):
        from qtpyvcp.widgets.button_widgets.subcall_button import PARSE_POSITIONAL_ARGS
        result = PARSE_POSITIONAL_ARGS.findall('#<param1> = #1')
        assert len(result) == 1
        assert result[0][0] == 'param1'
        assert result[0][1] == '1'

    def test_parse_positional_args_with_default(self):
        from qtpyvcp.widgets.button_widgets.subcall_button import PARSE_POSITIONAL_ARGS
        result = PARSE_POSITIONAL_ARGS.findall('#<param2> = #2 (=0.125 comment)')
        assert len(result) == 1
        assert result[0][0] == 'param2'
        assert result[0][1] == '2'
        assert result[0][2] == '0.125'
        assert result[0][3] == 'comment'

    def test_parse_positional_args_no_default(self):
        from qtpyvcp.widgets.button_widgets.subcall_button import PARSE_POSITIONAL_ARGS
        result = PARSE_POSITIONAL_ARGS.findall('#<param> = #5')
        assert len(result) == 1
        assert result[0][2] == ''  # No default value

    def test_parse_positional_args_no_match(self):
        from qtpyvcp.widgets.button_widgets.subcall_button import PARSE_POSITIONAL_ARGS
        result = PARSE_POSITIONAL_ARGS.findall('G0 X1 Y2')
        assert result == []


class TestSubCallButtonCallSub:
    """Tests for callSub method."""

    def test_callsub_no_file_found(self, qtbot, mock_subcall_button_module):
        SubCallButton, mock_issue_mdi, _ = mock_subcall_button_module
        btn = SubCallButton(filename='nonexistent.ngc')
        qtbot.addWidget(btn)
        result = btn.callSub()
        assert result is False
        mock_issue_mdi.assert_not_called()

    def test_callsub_with_valid_file_and_no_params(self, qtbot, mock_subcall_button_module, tmp_path):
        SubCallButton, _, _ = mock_subcall_button_module
        # Create a simple subroutine file
        sub_file = tmp_path / 'test.ngc'
        sub_file.write_text('o<test> sub\no<test> endsub\n')

        import qtpyvcp.widgets.button_widgets.subcall_button as submod
        original_dirs = submod.SUBROUTINE_SEARCH_DIRS
        submod.SUBROUTINE_SEARCH_DIRS = [str(tmp_path)]

        try:
            btn = SubCallButton(filename='test.ngc')
            qtbot.addWidget(btn)
            result = btn.callSub()
            # Should find the file and call issue_mdi (even with empty args)
            assert result is not False
        finally:
            submod.SUBROUTINE_SEARCH_DIRS = original_dirs

    def test_callsub_with_missing_param_no_default(self, qtbot, mock_subcall_button_module, tmp_path):
        SubCallButton, _, _ = mock_subcall_button_module
        # Create a subroutine file with required param (no default)
        sub_file = tmp_path / 'required.ngc'
        sub_file.write_text('o<required> sub\n#<myparam> = #1\no<required> endsub\n')

        import qtpyvcp.widgets.button_widgets.subcall_button as submod
        original_dirs = submod.SUBROUTINE_SEARCH_DIRS
        submod.SUBROUTINE_SEARCH_DIRS = [str(tmp_path)]

        try:
            btn = SubCallButton(filename='required.ngc')
            qtbot.addWidget(btn)
            result = btn.callSub()
            # Should return False because myparam has no default and no widget with that name exists
            assert result is False
        finally:
            submod.SUBROUTINE_SEARCH_DIRS = original_dirs

    def test_callsub_param_above_30_skipped(self, qtbot, mock_subcall_button_module, tmp_path):
        SubCallButton, _, _ = mock_subcall_button_module
        # Create a subroutine file with param #31 (should be skipped)
        sub_file = tmp_path / 'high_param.ngc'
        sub_file.write_text('o<high> sub\n#<skipme> = #31\no<high> endsub\n')

        import qtpyvcp.widgets.button_widgets.subcall_button as submod
        original_dirs = submod.SUBROUTINE_SEARCH_DIRS
        submod.SUBROUTINE_SEARCH_DIRS = [str(tmp_path)]

        try:
            btn = SubCallButton(filename='high_param.ngc')
            qtbot.addWidget(btn)
            result = btn.callSub()
            # Should succeed because param #31 is skipped (only #1-#30 are passed)
            assert result is not False
        finally:
            submod.SUBROUTINE_SEARCH_DIRS = original_dirs


class TestSubCallButtonSearchDirs:
    """Tests for subroutine search directory functionality."""

    def test_subroutine_search_dirs_is_list(self, mock_subcall_button_module):
        SubCallButton, _, _ = mock_subcall_button_module
        import qtpyvcp.widgets.button_widgets.subcall_button as submod
        assert isinstance(submod.SUBROUTINE_SEARCH_DIRS, list)
