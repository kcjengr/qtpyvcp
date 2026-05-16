import os
import tempfile
from qtpyvcp.utilities.yaml_filters import from_ini, INIFilterModule


class TestFromIniNoEnvVar:
    def test_returns_default_dict(self):
        old_val = os.environ.pop("INI_FILE_NAME", None)
        try:
            result = from_ini()
            assert isinstance(result, dict)
        finally:
            if old_val is not None:
                os.environ["INI_FILE_NAME"] = old_val

    def test_default_has_traj_section(self):
        old_val = os.environ.pop("INI_FILE_NAME", None)
        try:
            result = from_ini()
            assert "traj" in result
        finally:
            if old_val is not None:
                os.environ["INI_FILE_NAME"] = old_val

    def test_default_has_machine_section(self):
        old_val = os.environ.pop("INI_FILE_NAME", None)
        try:
            result = from_ini()
            assert "machine" in result
        finally:
            if old_val is not None:
                os.environ["INI_FILE_NAME"] = old_val

    def test_default_has_display_section(self):
        old_val = os.environ.pop("INI_FILE_NAME", None)
        try:
            result = from_ini()
            assert "display" in result
        finally:
            if old_val is not None:
                os.environ["INI_FILE_NAME"] = old_val

    def test_default_traj_coordinates(self):
        old_val = os.environ.pop("INI_FILE_NAME", None)
        try:
            result = from_ini()
            assert result["traj"]["coordinates"] == "XYZ"
        finally:
            if old_val is not None:
                os.environ["INI_FILE_NAME"] = old_val

    def test_default_machine_name(self):
        old_val = os.environ.pop("INI_FILE_NAME", None)
        try:
            result = from_ini()
            assert result["machine"]["name"] == "My Machine"
        finally:
            if old_val is not None:
                os.environ["INI_FILE_NAME"] = old_val

    def test_default_display_cycle_time(self):
        old_val = os.environ.pop("INI_FILE_NAME", None)
        try:
            result = from_ini()
            assert result["display"]["cycle_time"] == 100
        finally:
            if old_val is not None:
                os.environ["INI_FILE_NAME"] = old_val


class TestFromIniWithEnvVar:
    def test_nonexistent_file_returns_empty(self):
        os.environ["INI_FILE_NAME"] = "/nonexistent/path/file.ini"
        try:
            result = from_ini()
            assert isinstance(result, dict)
            assert len(result) == 0
        finally:
            os.environ.pop("INI_FILE_NAME", None)

    def test_valid_ini_file_parsed(self):
        ini_content = "[traj]\ncoordinates = XYZABC\n\n[machine]\nname = Test Machine\n\n[display]\ncycle_time = 50\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(ini_content)
            ini_path = f.name

        os.environ["INI_FILE_NAME"] = ini_path
        try:
            result = from_ini()
            assert "traj" in result
            assert "machine" in result
            assert "display" in result
            assert result["traj"]["coordinates"] == "XYZABC"
            assert result["machine"]["name"] == "Test Machine"
            assert result["display"]["cycle_time"] == "50"
        finally:
            os.environ.pop("INI_FILE_NAME", None)
            import os as _os
            _os.unlink(ini_path)

    def test_ini_file_with_extra_sections(self):
        ini_content = "[custom]\nkey1 = value1\nkey2 = value2\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(ini_content)
            ini_path = f.name

        os.environ["INI_FILE_NAME"] = ini_path
        try:
            result = from_ini()
            assert "custom" in result
            assert result["custom"]["key1"] == "value1"
            assert result["custom"]["key2"] == "value2"
        finally:
            os.environ.pop("INI_FILE_NAME", None)
            import os as _os
            _os.unlink(ini_path)

    def test_ini_file_values_are_strings(self):
        ini_content = "[section]\nnumber = 42\nbool_val = true\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(ini_content)
            ini_path = f.name

        os.environ["INI_FILE_NAME"] = ini_path
        try:
            result = from_ini()
            assert isinstance(result["section"]["number"], str)
            assert isinstance(result["section"]["bool_val"], str)
        finally:
            os.environ.pop("INI_FILE_NAME", None)
            import os as _os
            _os.unlink(ini_path)


class TestINIFilterModule:
    def test_filters_method_returns_dict(self):
        module = INIFilterModule()
        result = module.filters()
        assert isinstance(result, dict)

    def test_filters_contains_from_ini_key(self):
        module = INIFilterModule()
        filters = module.filters()
        assert "from-ini" in filters

    def test_from_ini_filter_is_callable(self):
        module = INIFilterModule()
        filters = module.filters()
        assert callable(filters["from-ini"])

    def test_from_ini_filter_returns_same_result(self):
        old_val = os.environ.pop("INI_FILE_NAME", None)
        try:
            module = INIFilterModule()
            result = module.filters()["from-ini"]()
            assert "traj" in result
        finally:
            if old_val is not None:
                os.environ["INI_FILE_NAME"] = old_val
