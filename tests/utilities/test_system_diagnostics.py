import os
import platform
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest


class TestHumanGbFromKb:
    def test_none_returns_unknown(self):
        from qtpyvcp.utilities.system_diagnostics import _human_gb_from_kb
        assert _human_gb_from_kb(None) == "unknown"

    def test_zero_kb(self):
        from qtpyvcp.utilities.system_diagnostics import _human_gb_from_kb
        result = _human_gb_from_kb(0)
        assert result == "0.00 GiB"

    def test_1_gib(self):
        from qtpyvcp.utilities.system_diagnostics import _human_gb_from_kb
        result = _human_gb_from_kb(1024 * 1024)
        assert result == "1.00 GiB"

    def test_half_gib(self):
        from qtpyvcp.utilities.system_diagnostics import _human_gb_from_kb
        result = _human_gb_from_kb(512 * 1024)
        assert result == "0.50 GiB"

    def test_2_gib(self):
        from qtpyvcp.utilities.system_diagnostics import _human_gb_from_kb
        result = _human_gb_from_kb(2 * 1024 * 1024)
        assert result == "2.00 GiB"

    def test_returns_string_with_gib_suffix(self):
        from qtpyvcp.utilities.system_diagnostics import _human_gb_from_kb
        result = _human_gb_from_kb(8 * 1024 * 1024)
        assert result.endswith("GiB")


class TestParseColonKv:
    def test_empty_string(self):
        from qtpyvcp.utilities.system_diagnostics import _parse_colon_kv
        assert _parse_colon_kv("") == {}

    def test_none_input(self):
        from qtpyvcp.utilities.system_diagnostics import _parse_colon_kv
        assert _parse_colon_kv(None) == {}

    def test_single_key_value(self):
        from qtpyvcp.utilities.system_diagnostics import _parse_colon_kv
        result = _parse_colon_kv("key: value")
        assert result == {"key": "value"}

    def test_lowercases_keys(self):
        from qtpyvcp.utilities.system_diagnostics import _parse_colon_kv
        result = _parse_colon_kv("KEY: value")
        assert result["key"] == "value"

    def test_multiple_lines(self):
        from qtpyvcp.utilities.system_diagnostics import _parse_colon_kv
        text = "driver: ethtool\nversion: 1.0\nfirmware: fw-2"
        result = _parse_colon_kv(text)
        assert result == {"driver": "ethtool", "version": "1.0", "firmware": "fw-2"}

    def test_strips_whitespace(self):
        from qtpyvcp.utilities.system_diagnostics import _parse_colon_kv
        result = _parse_colon_kv("  key  :  value  ")
        assert result == {"key": "value"}

    def test_skips_lines_without_colon(self):
        from qtpyvcp.utilities.system_diagnostics import _parse_colon_kv
        text = "good: value\nno_colon_line\nanother: val"
        result = _parse_colon_kv(text)
        assert len(result) == 2

    def test_value_with_colons(self):
        from qtpyvcp.utilities.system_diagnostics import _parse_colon_kv
        result = _parse_colon_kv("url: http://example.com:8080")
        assert result["url"] == "http://example.com:8080"


class TestReadFirstLine:
    def test_existing_file(self, tmp_path):
        from qtpyvcp.utilities.system_diagnostics import _read_first_line
        test_file = tmp_path / "test.txt"
        test_file.write_text("first line\nsecond line\n")
        result = _read_first_line(str(test_file))
        assert result == "first line"

    def test_empty_file(self, tmp_path):
        from qtpyvcp.utilities.system_diagnostics import _read_first_line
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")
        result = _read_first_line(str(test_file))
        assert result is None

    def test_single_line_no_newline(self, tmp_path):
        from qtpyvcp.utilities.system_diagnostics import _read_first_line
        test_file = tmp_path / "single.txt"
        test_file.write_text("only line")
        result = _read_first_line(str(test_file))
        assert result == "only line"

    def test_nonexistent_file(self, tmp_path):
        from qtpyvcp.utilities.system_diagnostics import _read_first_line
        result = _read_first_line(str(tmp_path / "does_not_exist.txt"))
        assert result is None

    def test_whitespace_only(self, tmp_path):
        from qtpyvcp.utilities.system_diagnostics import _read_first_line
        test_file = tmp_path / "ws.txt"
        test_file.write_text("   \n  ")
        result = _read_first_line(str(test_file))
        assert result is None

    def test_trims_whitespace(self, tmp_path):
        from qtpyvcp.utilities.system_diagnostics import _read_first_line
        test_file = tmp_path / "trim.txt"
        test_file.write_text("  trimmed content  \n")
        result = _read_first_line(str(test_file))
        assert result == "trimmed content"


class TestReadTrimmed:
    def test_returns_value_when_present(self, tmp_path):
        from qtpyvcp.utilities.system_diagnostics import _read_trimmed
        test_file = tmp_path / "data.txt"
        test_file.write_text("some value\n")
        result = _read_trimmed(str(test_file))
        assert result == "some value"

    def test_returns_n_a_when_none(self, tmp_path):
        from qtpyvcp.utilities.system_diagnostics import _read_trimmed
        result = _read_trimmed(str(tmp_path / "missing.txt"))
        assert result == "n/a"


class TestRunCommand:
    def test_successful_command(self):
        from qtpyvcp.utilities.system_diagnostics import _run_command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output data\n"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = _run_command(["echo", "hello"])
            assert result == "output data"
            mock_run.assert_called_once()

    def test_returns_none_on_nonzero_returncode(self):
        from qtpyvcp.utilities.system_diagnostics import _run_command
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = _run_command(["false"])
            assert result is None

    def test_returns_none_on_exception(self):
        from qtpyvcp.utilities.system_diagnostics import _run_command
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = _run_command(["nonexistent_cmd"])
            assert result is None

    def test_returns_none_on_timeout(self):
        from qtpyvcp.utilities.system_diagnostics import _run_command
        with patch("subprocess.run", side_effect=TimeoutError()):
            result = _run_command(["sleep", "10"])
            assert result is None

    def test_strips_output(self):
        from qtpyvcp.utilities.system_diagnostics import _run_command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "  stripped output  \n"
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = _run_command(["echo", "test"])
            assert result == "stripped output"

    def test_empty_output_returns_stripped_empty(self):
        from qtpyvcp.utilities.system_diagnostics import _run_command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = _run_command(["echo", "-n"])
            assert result == ""

    def test_uses_default_timeout(self):
        from qtpyvcp.utilities.system_diagnostics import _run_command
        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="ok", stderr="")) as mock_run:
            _run_command(["test"])
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["timeout"] == 2

    def test_custom_timeout(self):
        from qtpyvcp.utilities.system_diagnostics import _run_command
        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="ok", stderr="")) as mock_run:
            _run_command(["test"], timeout=5)
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["timeout"] == 5


class TestCpuModel:
    def test_from_cpuinfo(self):
        from qtpyvcp.utilities.system_diagnostics import _cpu_model
        from io import StringIO

        real_open = open
        def mock_open(path, *args, **kwargs):
            if str(path) == "/proc/cpuinfo":
                return StringIO("processor : 0\nmodel name : Test CPU Model\n")
            raise FileNotFoundError()

        with patch("builtins.open", mock_open):
            result = _cpu_model()
            assert result == "Test CPU Model"

    def test_fallback_to_platform_processor(self):
        from qtpyvcp.utilities.system_diagnostics import _cpu_model
        real_open = open
        def mock_open(path, *args, **kwargs):
            raise FileNotFoundError()
        with patch("builtins.open", mock_open), \
             patch("platform.processor", return_value="x86_64"), \
             patch("platform.machine", return_value="x86_64"):
            result = _cpu_model()
            assert result == "x86_64"

    def test_fallback_to_platform_machine(self):
        from qtpyvcp.utilities.system_diagnostics import _cpu_model
        real_open = open
        def mock_open(path, *args, **kwargs):
            raise FileNotFoundError()
        with patch("builtins.open", mock_open), \
             patch("platform.processor", return_value=""), \
             patch("platform.machine", return_value="arm64"):
            result = _cpu_model()
            assert result == "arm64"

    def test_returns_unknown_when_all_fail(self):
        from qtpyvcp.utilities.system_diagnostics import _cpu_model
        real_open = open
        def mock_open(path, *args, **kwargs):
            raise FileNotFoundError()
        with patch("builtins.open", mock_open), \
             patch("platform.processor", return_value=""), \
             patch("platform.machine", return_value=""):
            result = _cpu_model()
            assert result == "unknown"

    def test_case_insensitive_model_name(self):
        from qtpyvcp.utilities.system_diagnostics import _cpu_model
        from io import StringIO

        real_open = open
        def mock_open(path, *args, **kwargs):
            if str(path) == "/proc/cpuinfo":
                return StringIO("MODEL NAME : Upper Case CPU\n")
            raise FileNotFoundError()

        with patch("builtins.open", mock_open):
            result = _cpu_model()
            assert result == "Upper Case CPU"


class TestNetworkInterfaces:
    def test_returns_sorted_interfaces(self):
        from qtpyvcp.utilities.system_diagnostics import _network_interfaces
        with patch("os.listdir", return_value=["wlan0", "eth0", "lo"]), \
             patch("qtpyvcp.utilities.system_diagnostics._read_first_line", return_value="up"):
            result = _network_interfaces()
            ifaces = [r[0] for r in result]
            assert ifaces == ["eth0", "lo", "wlan0"]

    def test_unknown_state_when_readline_fails(self):
        from qtpyvcp.utilities.system_diagnostics import _network_interfaces
        with patch("os.listdir", return_value=["eth0"]), \
             patch("qtpyvcp.utilities.system_diagnostics._read_first_line", return_value=None):
            result = _network_interfaces()
            assert result[0] == ("eth0", "unknown")

    def test_returns_empty_on_exception(self):
        from qtpyvcp.utilities.system_diagnostics import _network_interfaces
        with patch("os.listdir", side_effect=PermissionError()):
            result = _network_interfaces()
            assert result == []


class TestReadMemTotalKb:
    def test_parses_meminfo(self):
        from qtpyvcp.utilities.system_diagnostics import _read_mem_total_kb
        from io import StringIO

        real_open = open
        def mock_open(path, *args, **kwargs):
            if str(path) == "/proc/meminfo":
                return StringIO("MemTotal:       16384000 kB\nMemFree:        8192000 kB\n")
            raise FileNotFoundError()

        with patch("builtins.open", mock_open):
            result = _read_mem_total_kb()
            assert result == 16384000

    def test_returns_none_on_missing_file(self):
        from qtpyvcp.utilities.system_diagnostics import _read_mem_total_kb
        with patch("builtins.open", side_effect=FileNotFoundError()):
            result = _read_mem_total_kb()
            assert result is None

    def test_skips_non_memtotal_lines(self):
        from qtpyvcp.utilities.system_diagnostics import _read_mem_total_kb
        from io import StringIO

        real_open = open
        def mock_open(path, *args, **kwargs):
            if str(path) == "/proc/meminfo":
                return StringIO("MemFree: 1000 kB\nSwapTotal: 2000 kB\nMemTotal: 4096 kB\n")
            raise FileNotFoundError()

        with patch("builtins.open", mock_open):
            result = _read_mem_total_kb()
            assert result == 4096

    def test_returns_none_when_no_number(self):
        from qtpyvcp.utilities.system_diagnostics import _read_mem_total_kb
        from io import StringIO

        real_open = open
        def mock_open(path, *args, **kwargs):
            if str(path) == "/proc/meminfo":
                return StringIO("MemTotal: not_a_number kB\n")
            raise FileNotFoundError()

        with patch("builtins.open", mock_open):
            result = _read_mem_total_kb()
            assert result is None


class TestLinuxPrettyName:
    def test_from_os_release(self):
        from qtpyvcp.utilities.system_diagnostics import _linux_pretty_name
        from io import StringIO

        real_open = open
        def mock_open(path, *args, **kwargs):
            if str(path) == "/etc/os-release":
                return StringIO('PRETTY_NAME="Ubuntu 22.04 LTS"\nNAME="Ubuntu"\n')
            raise FileNotFoundError()

        with patch("builtins.open", mock_open):
            result = _linux_pretty_name()
            assert result == "Ubuntu 22.04 LTS"

    def test_strips_quotes(self):
        from qtpyvcp.utilities.system_diagnostics import _linux_pretty_name
        from io import StringIO

        real_open = open
        def mock_open(path, *args, **kwargs):
            if str(path) == "/etc/os-release":
                return StringIO('PRETTY_NAME=\'Debian GNU/Linux 11 (bullseye)\'\n')
            raise FileNotFoundError()

        with patch("builtins.open", mock_open):
            result = _linux_pretty_name()
            assert '"' not in result

    def test_fallback_to_lsb_release(self):
        from qtpyvcp.utilities.system_diagnostics import _linux_pretty_name
        real_open = open
        def mock_open(path, *args, **kwargs):
            raise FileNotFoundError()
        with patch("builtins.open", mock_open), \
             patch("qtpyvcp.utilities.system_diagnostics._run_command", return_value="Fedora Linux 38"):
            result = _linux_pretty_name()
            assert result == "Fedora Linux 38"

    def test_fallback_to_platform(self):
        from qtpyvcp.utilities.system_diagnostics import _linux_pretty_name
        real_open = open
        def mock_open(path, *args, **kwargs):
            raise FileNotFoundError()
        with patch("builtins.open", mock_open), \
             patch("qtpyvcp.utilities.system_diagnostics._run_command", return_value=None), \
             patch("platform.platform", return_value="Linux-5.15"):
            result = _linux_pretty_name()
            assert "Linux" in result

    def test_skips_lines_without_pretty_name(self):
        from qtpyvcp.utilities.system_diagnostics import _linux_pretty_name
        from io import StringIO

        real_open = open
        def mock_open(path, *args, **kwargs):
            if str(path) == "/etc/os-release":
                return StringIO('NAME="Ubuntu"\nVERSION="22.04"\nPRETTY_NAME="Ubuntu 22.04 LTS"\n')
            raise FileNotFoundError()

        with patch("builtins.open", mock_open):
            result = _linux_pretty_name()
            assert result == "Ubuntu 22.04 LTS"


class TestNetworkAdapterDetails:
    def test_returns_defaults_without_device_dir(self, tmp_path):
        from qtpyvcp.utilities.system_diagnostics import _network_adapter_details
        with patch("os.path.exists", return_value=False):
            result = _network_adapter_details("eth0")
            assert result["make"] == "n/a"
            assert result["driver"] == "n/a"

    def test_driver_from_ethtool(self, tmp_path):
        from qtpyvcp.utilities.system_diagnostics import _network_adapter_details
        ethtool_out = "driver: mydriver\nversion: 1.2.3\nfirmware-version: fw-abc\nbus-info: pci:00:00.0"
        with patch("os.path.exists", return_value=True), \
             patch("qtpyvcp.utilities.system_diagnostics._read_trimmed", return_value="n/a"), \
             patch("qtpyvcp.utilities.system_diagnostics._run_command", return_value=ethtool_out):
            result = _network_adapter_details("eth0")
            assert result["driver"] == "mydriver"
            assert result["driver_version"] == "1.2.3"
            assert result["firmware"] == "fw-abc"

    def test_bus_info_from_realpath(self, tmp_path):
        from qtpyvcp.utilities.system_diagnostics import _network_adapter_details
        with patch("os.path.exists", return_value=True), \
             patch("qtpyvcp.utilities.system_diagnostics._read_trimmed", return_value="n/a"), \
             patch("qtpyvcp.utilities.system_diagnostics._run_command", return_value=None), \
             patch("os.path.realpath", side_effect=lambda x: x.replace("/device/driver", "/device").replace("/device", "/devices/pci:00:00.0")):
            result = _network_adapter_details("eth0")
            assert "pci" in result["bus_info"] or result["bus_info"] == "n/a"

    def test_driver_version_from_modinfo(self, tmp_path):
        from qtpyvcp.utilities.system_diagnostics import _network_adapter_details
        modinfo_out = "1.2.3\nextra-line"
        ethtool_out = "driver: mydriver\nversion:\nfirmware-version:\nbus-info: pci:00:00.0"
        with patch("os.path.exists", return_value=True), \
             patch("qtpyvcp.utilities.system_diagnostics._read_trimmed", return_value="n/a"), \
             patch("qtpyvcp.utilities.system_diagnostics._run_command") as mock_run:
            def side_effect(cmd, **kwargs):
                if "modinfo" in cmd:
                    return modinfo_out
                return ethtool_out
            mock_run.side_effect = side_effect
            result = _network_adapter_details("eth0")
            assert result["driver_version"] == "1.2.3"


class TestGraphicsLinesFromGlxinfo:
    def test_parses_glxinfo_output(self):
        from qtpyvcp.utilities.system_diagnostics import _graphics_lines_from_glxinfo
        output = """OpenGL vendor string: NVIDIA
OpenGL renderer string: RTX 3080
direct rendering: Yes
some irrelevant line
version: 4.6
"""
        with patch("qtpyvcp.utilities.system_diagnostics._run_command", return_value=output):
            result = _graphics_lines_from_glxinfo()
            assert len(result) >= 3

    def test_filters_by_keys(self):
        from qtpyvcp.utilities.system_diagnostics import _graphics_lines_from_glxinfo
        output = "OpenGL Renderer String: RTX 4090\nVendor: NVIDIA\nUnrelated: stuff"
        with patch("qtpyvcp.utilities.system_diagnostics._run_command", return_value=output):
            result = _graphics_lines_from_glxinfo()
            assert any("RTX" in line for line in result)

    def test_returns_empty_on_none(self):
        from qtpyvcp.utilities.system_diagnostics import _graphics_lines_from_glxinfo
        with patch("qtpyvcp.utilities.system_diagnostics._run_command", return_value=None):
            result = _graphics_lines_from_glxinfo()
            assert result == []

    def test_case_insensitive_matching(self):
        from qtpyvcp.utilities.system_diagnostics import _graphics_lines_from_glxinfo
        output = "VENDOR: NVIDIA"
        with patch("qtpyvcp.utilities.system_diagnostics._run_command", return_value=output):
            result = _graphics_lines_from_glxinfo()
            assert any("NVIDIA" in line for line in result)

    def test_returns_all_matching_lines_no_limit(self):
        from qtpyvcp.utilities.system_diagnostics import _graphics_lines_from_glxinfo
        lines = "\n".join([f"vendor: line{i}" for i in range(30)])
        with patch("qtpyvcp.utilities.system_diagnostics._run_command", return_value=lines):
            result = _graphics_lines_from_glxinfo()
            assert len(result) == 30


class TestLinuxcncVersion:
    def test_returns_version_when_available(self):
        from qtpyvcp.utilities.system_diagnostics import _linuxcnc_version
        mock_linuxcnc = MagicMock()
        mock_linuxcnc.version = "2.8.1"
        with patch.dict("sys.modules", {"linuxcnc": mock_linuxcnc}):
            result = _linuxcnc_version()
            assert result == "2.8.1"

    def test_calls_callable_version(self):
        from qtpyvcp.utilities.system_diagnostics import _linuxcnc_version
        mock_linuxcnc = MagicMock()
        mock_linuxcnc.version = MagicMock(return_value="2.9.0")
        with patch.dict("sys.modules", {"linuxcnc": mock_linuxcnc}):
            result = _linuxcnc_version()
            assert result == "2.9.0"

    def test_returns_unknown_on_exception(self):
        from qtpyvcp.utilities.system_diagnostics import _linuxcnc_version
        mock_linuxcnc = MagicMock()
        del mock_linuxcnc.version
        with patch.dict("sys.modules", {"linuxcnc": mock_linuxcnc}):
            result = _linuxcnc_version()
            assert result == "unknown"

    def test_returns_unknown_when_module_missing(self):
        from qtpyvcp.utilities.system_diagnostics import _linuxcnc_version
        with patch.dict("sys.modules", {"linuxcnc": None}):
            # Set linuxcnc to None so 'import linuxcnc' raises ImportError
            real_modules = sys.modules.copy()
            sys.modules["linuxcnc"] = None
            try:
                result = _linuxcnc_version()
                assert result == "unknown"
            finally:
                sys.modules.update(real_modules)


class TestProbeBasicVersion:
    def test_from_sys_modules(self):
        from qtpyvcp.utilities.system_diagnostics import _probe_basic_version
        mock_module = MagicMock(__version__="1.5.0")
        with patch.dict("sys.modules", {"probe_basic": mock_module}):
            result = _probe_basic_version()
            assert result == "1.5.0"

    def test_from_package_version(self):
        from qtpyvcp.utilities.system_diagnostics import _probe_basic_version
        with patch.dict("sys.modules", {"probe_basic": None}), \
             patch("qtpyvcp.utilities.system_diagnostics.package_version", return_value="2.0.0"):
            result = _probe_basic_version()
            assert result == "2.0.0"

    def test_returns_unknown_when_not_found(self):
        from qtpyvcp.utilities.system_diagnostics import _probe_basic_version
        with patch.dict("sys.modules", {"probe_basic": None}), \
             patch("qtpyvcp.utilities.system_diagnostics.package_version", side_effect=Exception()):
            result = _probe_basic_version()
            assert result == "unknown"

    def test_returns_unknown_when_module_no_version(self):
        from qtpyvcp.utilities.system_diagnostics import _probe_basic_version
        mock_module = MagicMock(__version__=None)
        with patch.dict("sys.modules", {"probe_basic": mock_module}), \
             patch("qtpyvcp.utilities.system_diagnostics.package_version", return_value="1.0.0"):
            result = _probe_basic_version()
            assert result == "1.0.0"


class TestBuildSystemDiagnosticsReportLines:
    def test_returns_list_of_strings(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        result = build_system_diagnostics_report_lines("1.0.0", "5.15.0", "PyQt5")
        assert isinstance(result, list)
        assert all(isinstance(line, str) for line in result)

    def test_contains_version_info(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        result = build_system_diagnostics_report_lines("test-version", "test-qt", "test-api")
        assert any("test-version" in line for line in result)
        assert any("test-qt" in line for line in result)
        assert any("test-api" in line for line in result)

    def test_contains_hostname(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        with patch("socket.gethostname", return_value="myhost"):
            result = build_system_diagnostics_report_lines()
            assert any("myhost" in line for line in result)

    def test_contains_kernel_version(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        with patch("platform.release", return_value="5.15.0-ubuntu"):
            result = build_system_diagnostics_report_lines()
            assert any("5.15.0-ubuntu" in line for line in result)

    def test_contains_architecture(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        with patch("platform.machine", return_value="x86_64"):
            result = build_system_diagnostics_report_lines()
            assert any("x86_64" in line for line in result)

    def test_contains_python_info(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        with patch("sys.version", "3.11.0 (main, Jan  1 2024)"), \
             patch("sys.executable", "/usr/bin/python3"):
            result = build_system_diagnostics_report_lines()
            assert any("3.11.0" in line for line in result)
            assert any("/usr/bin/python3" in line for line in result)

    def test_contains_memory_info(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        with patch("qtpyvcp.utilities.system_diagnostics._read_mem_total_kb", return_value=8388608), \
             patch("qtpyvcp.utilities.system_diagnostics._human_gb_from_kb", return_value="8.00 GiB"):
            result = build_system_diagnostics_report_lines()
            assert any("8.00 GiB" in line for line in result)

    def test_contains_disk_info(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        mock_usage = MagicMock(total=1e12, used=5e11, free=5e11)
        with patch("shutil.disk_usage", return_value=mock_usage):
            result = build_system_diagnostics_report_lines()
            assert any("root_disk_total_gib" in line for line in result)

    def test_contains_cpu_info(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        with patch("qtpyvcp.utilities.system_diagnostics._cpu_model", return_value="Intel i7"), \
             patch("os.cpu_count", return_value=8):
            result = build_system_diagnostics_report_lines()
            assert any("Intel i7" in line for line in result)
            assert any("8" in line for line in result)

    def test_contains_linuxcnc_version(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        with patch("qtpyvcp.utilities.system_diagnostics._linuxcnc_version", return_value="2.8.1"):
            result = build_system_diagnostics_report_lines()
            assert any("2.8.1" in line for line in result)

    def test_contains_probe_basic_version(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        with patch("qtpyvcp.utilities.system_diagnostics._probe_basic_version", return_value="1.5.0"):
            result = build_system_diagnostics_report_lines()
            assert any("1.5.0" in line for line in result)

    def test_includes_network_interfaces_section(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        with patch("qtpyvcp.utilities.system_diagnostics._network_interfaces", return_value=[("eth0", "up")]), \
             patch("qtpyvcp.utilities.system_diagnostics._network_adapter_details", return_value={"make": "Intel", "model": "I219", "driver": "e1000e", "driver_version": "3.8.4", "firmware": "1.5", "bus_info": "pci:00:1f.6"}):
            result = build_system_diagnostics_report_lines()
            assert any("network_interfaces" in line for line in result)

    def test_excludes_lo_interface(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        with patch("qtpyvcp.utilities.system_diagnostics._network_interfaces", return_value=[("lo", "unknown"), ("eth0", "up")]):
            result = build_system_diagnostics_report_lines()
            lo_section = False
            for i, line in enumerate(result):
                if "interface = lo" in line:
                    lo_section = True
            assert not lo_section

    def test_includes_glxinfo_section(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        with patch("qtpyvcp.utilities.system_diagnostics._graphics_lines_from_glxinfo", return_value=["OpenGL Renderer: RTX 4090"]):
            result = build_system_diagnostics_report_lines()
            assert any("graphics_glxinfo" in line for line in result)

    def test_includes_unavailable_glxinfo(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        with patch("qtpyvcp.utilities.system_diagnostics._graphics_lines_from_glxinfo", return_value=[]):
            result = build_system_diagnostics_report_lines()
            assert any("graphics_glxinfo: unavailable" in line for line in result)

    def test_contains_timestamp(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        result = build_system_diagnostics_report_lines()
        assert any("timestamp_utc" in line for line in result)

    def test_default_versions_when_not_provided(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        result = build_system_diagnostics_report_lines()
        assert any("qtpyvcp_version: unknown" in line for line in result)
        assert any("qt_version: unknown" in line for line in result)

    def test_contains_os_info(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        with patch("qtpyvcp.utilities.system_diagnostics._linux_pretty_name", return_value="Ubuntu 22.04 LTS"):
            result = build_system_diagnostics_report_lines()
            assert any("Ubuntu" in line for line in result)

    def test_report_starts_with_header(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        result = build_system_diagnostics_report_lines()
        assert result[0] == "System diagnostics report:"

    def test_returns_multiple_lines(self):
        from qtpyvcp.utilities.system_diagnostics import build_system_diagnostics_report_lines
        result = build_system_diagnostics_report_lines()
        assert len(result) > 15
