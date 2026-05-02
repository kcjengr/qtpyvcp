import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version as package_version


def _run_command(command, timeout=2):
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            return None
        return (result.stdout or "").strip()
    except Exception:
        return None


def _read_first_line(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            line = handle.readline().strip()
            return line or None
    except Exception:
        return None


def _read_mem_total_kb():
    try:
        with open("/proc/meminfo", "r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        return int(parts[1])
    except Exception:
        pass
    return None


def _human_gb_from_kb(kb_value):
    if kb_value is None:
        return "unknown"
    return f"{(kb_value / (1024.0 * 1024.0)):.2f} GiB"


def _cpu_model():
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                if line.lower().startswith("model name"):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        return parts[1].strip()
    except Exception:
        pass

    uname_proc = platform.processor() or platform.machine()
    return uname_proc or "unknown"


def _linux_pretty_name():
    try:
        with open("/etc/os-release", "r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass

    lsb = _run_command(["lsb_release", "-ds"])
    if lsb:
        return lsb.strip().strip('"')
    return platform.platform()


def _network_interfaces():
    interfaces = []
    try:
        for iface in sorted(os.listdir("/sys/class/net")):
            operstate = _read_first_line(f"/sys/class/net/{iface}/operstate") or "unknown"
            interfaces.append((iface, operstate))
    except Exception:
        pass
    return interfaces


def _parse_colon_kv(text):
    values = {}
    if not text:
        return values
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip().lower()] = value.strip()
    return values


def _read_trimmed(path):
    val = _read_first_line(path)
    if val is None:
        return "n/a"
    return val.strip()


def _network_adapter_details(interface_name):
    base = f"/sys/class/net/{interface_name}"
    details = {
        "make": "n/a",
        "model": "n/a",
        "driver": "n/a",
        "driver_version": "n/a",
        "firmware": "n/a",
        "bus_info": "n/a",
    }

    if not os.path.exists(f"{base}/device"):
        return details

    vendor_id = _read_trimmed(f"{base}/device/vendor")
    device_id = _read_trimmed(f"{base}/device/device")

    try:
        device_path = os.path.realpath(f"{base}/device")
        bus_name = os.path.basename(device_path)
        if bus_name and ":" in bus_name:
            details["bus_info"] = bus_name
    except Exception:
        pass

    try:
        driver_link = os.path.realpath(f"{base}/device/driver")
        if driver_link and os.path.basename(driver_link):
            details["driver"] = os.path.basename(driver_link)
    except Exception:
        pass

    ethtool_out = _run_command(["ethtool", "-i", interface_name], timeout=2)
    ethtool_info = _parse_colon_kv(ethtool_out)
    if ethtool_info:
        details["driver"] = ethtool_info.get("driver", details["driver"])
        details["driver_version"] = ethtool_info.get("version", details["driver_version"])
        details["firmware"] = ethtool_info.get("firmware-version", details["firmware"])
        details["bus_info"] = ethtool_info.get("bus-info", details["bus_info"])

    if details["driver"] not in ("", "n/a", "N/A") and details["driver_version"] in ("", "n/a", "N/A"):
        module_version = _run_command(["modinfo", "-F", "version", details["driver"]], timeout=2)
        if module_version:
            details["driver_version"] = module_version.splitlines()[0].strip()

    bus_info = details["bus_info"]
    if bus_info not in ("", "n/a", "N/A"):
        lspci_mm_line = _run_command(["lspci", "-s", bus_info, "-nnmm"], timeout=2)
        if lspci_mm_line:
            first = lspci_mm_line.splitlines()[0].strip()
            fields = re.findall(r'"([^"]+)"', first)
            # lspci -nnmm: slot, class, vendor, device, ...
            if len(fields) >= 4:
                details["make"] = fields[2].strip() or details["make"]
                details["model"] = fields[3].strip() or details["model"]

        if details["make"] == "n/a" and details["model"] == "n/a":
            lspci_line = _run_command(["lspci", "-s", bus_info, "-nn"], timeout=2)
            if lspci_line:
                line = lspci_line.splitlines()[0].strip()
                if ": " in line:
                    tail = line.split(": ", 1)[1]
                else:
                    tail = line
                if " Corporation " in tail:
                    details["make"], details["model"] = tail.split(" Corporation ", 1)
                    details["make"] = details["make"].strip() + " Corporation"
                    details["model"] = details["model"].strip()
                else:
                    details["model"] = tail

    if details["model"] != "n/a" and vendor_id != "n/a" and device_id != "n/a":
        vid = vendor_id.replace("0x", "")
        did = device_id.replace("0x", "")
        if f"[{vid}:{did}]" not in details["model"]:
            details["model"] = f"{details['model']} [{vid}:{did}]"

    return details


def _linuxcnc_version():
    try:
        import linuxcnc

        value = getattr(linuxcnc, "version", None)
        if callable(value):
            value = value()
        if value:
            return str(value)
    except Exception:
        pass
    return "unknown"


def _probe_basic_version():
    try:
        module = sys.modules.get("probe_basic")
        if module is not None:
            version_value = getattr(module, "__version__", None)
            if version_value:
                return str(version_value)
    except Exception:
        pass

    try:
        return package_version("probe-basic")
    except PackageNotFoundError:
        return "unknown"
    except Exception:
        return "unknown"


def _graphics_lines_from_glxinfo():
    output = _run_command(["glxinfo", "-B"], timeout=3)
    if not output:
        return []

    keys = (
        "direct rendering:",
        "vendor:",
        "device:",
        "version:",
        "accelerated:",
        "opengl vendor string:",
        "opengl renderer string:",
        "opengl core profile version string:",
        "opengl core profile shading language version string:",
        "opengl version string:",
        "opengl shading language version string:",
    )

    selected = []
    for line in output.splitlines():
        lower = line.strip().lower()
        if any(lower.startswith(key) for key in keys):
            selected.append(line.strip())
    return selected


def build_system_diagnostics_report_lines(qtpyvcp_version="unknown", qt_version="unknown", qt_api="unknown"):
    hostname = socket.gethostname()
    kernel = platform.release()
    arch = platform.machine() or "unknown"
    cpu_count = os.cpu_count() or "unknown"
    mem_total = _human_gb_from_kb(_read_mem_total_kb())
    root_disk = shutil.disk_usage("/")

    lines = [
        "System diagnostics report:",
        f"  - timestamp_utc: {datetime.now(timezone.utc).isoformat()}",
        f"  - hostname: {hostname}",
        f"  - os: {_linux_pretty_name()}",
        f"  - kernel: {kernel}",
        f"  - architecture: {arch}",
        f"  - python: {sys.version.split()[0]}",
        f"  - python_executable: {sys.executable}",
        f"  - qtpyvcp_version: {qtpyvcp_version}",
        f"  - linuxcnc_version: {_linuxcnc_version()}",
        f"  - probe_basic_version: {_probe_basic_version()}",
        f"  - qt_version: {qt_version}",
        f"  - qt_api: {qt_api}",
        f"  - cpu_model: {_cpu_model()}",
        f"  - cpu_logical_cores: {cpu_count}",
        f"  - memory_total: {mem_total}",
        f"  - root_disk_total_gib: {root_disk.total / (1024.0 ** 3):.2f}",
        f"  - root_disk_used_gib: {root_disk.used / (1024.0 ** 3):.2f}",
        f"  - root_disk_free_gib: {root_disk.free / (1024.0 ** 3):.2f}",
    ]

    interfaces = _network_interfaces()
    if interfaces:
        lines.append("  - network_interfaces:")
        for iface, operstate in interfaces:
            if iface == "lo":
                continue
            details = _network_adapter_details(iface)
            lines.append("      - Ethernet controller:")
            lines.append(f"          - interface = {iface}")
            lines.append(f"          - state = {operstate}")
            lines.append(f"          - make = {details['make']}")
            lines.append(f"          - model = {details['model']}")
            lines.append(f"          - driver = {details['driver']}")
            lines.append(f"          - driver_version = {details['driver_version']}")
            lines.append(f"          - firmware = {details['firmware']}")
            lines.append(f"          - bus = {details['bus_info']}")

    glx_lines = _graphics_lines_from_glxinfo()
    if glx_lines:
        lines.append("  - graphics_glxinfo:")
        for line in glx_lines[:20]:
            lines.append(f"      - {line}")
    else:
        lines.append("  - graphics_glxinfo: unavailable")

    return lines
