#!/usr/bin/env python3

"""
Command line tool to set up and launch QtDesigner for editing VCPs::

 Usage:
   editvcp [<vcp>] [--ui-file=PATH] [--qss-file=PATH] [--yaml-file=PATH]
           [--log-level=LEVEL] [--log-file=PATH]
   editvcp (-h | --help)

 File Options:
   --vcp VCP          Name of an installed VCP, or a path to either a
                      YAML or UI file. If a YAML file will load any UI
                      and QSS files specified in the qtdesigner section.
   --ui-file PATH     Path to a UI file. Overrides any file specified in
                      the YAML config file.
   --qss-file PATH    Path to a QSS file. Overrides any file specified in
                      the YAML config file.
   --yaml-file = PATH Path to a YAML file to load QtPyVCP config from.
                      Useful for specifying custom plugins etc.

 Logging Options:
   --log-level (DEBUG | INFO | WARN | ERROR | CRITICAL)
                      Sets the log level. [default: ERROR]
   --log-file PATH    Specifies the log file. [default: ~/qtpyvcp-designer.log]

 Other Options:
   -h --help          Show this help and exit.
   --designer-args <args>...
"""

import os
import sys
import distro
# enable remote debug on kernel
# ➜  ~ sudo echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope

# eclipse plugins
# sys.path.append(r'~/.p2/pool/plugins/org.python.pydev.core_12.0.0.202402010911/pysrc')
# import pydevd; pydevd.settrace()


from io import TextIOWrapper

from subprocess import Popen, PIPE, STDOUT
from pkg_resources import iter_entry_points

from docopt import docopt
from PySide6.QtWidgets import QApplication, QFileDialog

from qtpyvcp.lib.types import DotDict
from qtpyvcp.utilities.logger import initBaseLogger

from linuxcnc import version as lcnc_version

LOG = initBaseLogger('EditVCP',
                     log_file=None,
                     log_level='DEBUG')

DESIGNER_LOG = initBaseLogger('Designer',
                              log_file=None,
                              log_level='DEBUG')


LCNC_VERSION_ERROR_MSG = """
\033[31mERROR:\033[0m Unsupported LinuxCNC version

QtPyVCP only supports LinuxCNC 2.8, current version is {}.
If you have LinuxCNC installed as a RIP make sure you have
activated the run-in-place environment by running:\n"

    $ . <linuxcnc-rip-dir>/scripts/rip-environment

Otherwise you will need to install LinuxCNC 2.8, info on how
to do that can be found here: https://gnipsel.com/linuxcnc/uspace/
""".strip()

INSTALLED_ERROR_MSG = """
\033[31mERROR:\033[0m Can not edit an installed VCP

The specified VCP appears to be installed in the `python2.7/site-packages`
directory. Please set up a development install to edit the VCP.
""".strip()

if lcnc_version.startswith('2.7'):
    LOG.info(LCNC_VERSION_ERROR_MSG.format(lcnc_version))
    sys.exit(1)


def log_subprocess_output(stdout):
    for line in TextIOWrapper(stdout, encoding="utf-8"):
        DESIGNER_LOG.info(line.rstrip('\n'))


def launch_designer(opts=DotDict()) -> None:

    if not opts.vcp and not opts.ui_file:
        fname, _ = QFileDialog.getOpenFileName(
            parent=None,
            caption="Choose VCP to Edit in QtDesigner",
            filter="VCP Config Files (*.yml *.yaml);;VCP UI Files (*.ui);;All Files (*)",
            options=QFileDialog.Options() | QFileDialog.DontUseNativeDialog)

        if not fname:
            sys.exit(1)

    else:
        fname = opts.vcp or opts.ui_file

    if '.'not in fname or '/' not in fname:
        entry_points = {}
        for entry_point in iter_entry_points(group='qtpyvcp.example_vcp'):
            entry_points[entry_point.name] = entry_point
        for entry_point in iter_entry_points(group='qtpyvcp.vcp'):
            entry_points[entry_point.name] = entry_point

        try:
            vcp = entry_points[fname.lower()].load()
            fname = vcp.VCP_CONFIG_FILE
        except KeyError:
            pass

        if 'lib/python2.7/site-packages' in fname:
            LOG.error(INSTALLED_ERROR_MSG)
            sys.exit(1)

    if distro.id() == 'gentoo' or distro.id() == 'arch':
        cmd = ['pyside6-designer']
    else:
        cmd = ["pyside6-designer"]

    ext = os.path.splitext(fname)[1]
    if ext in ['.yml', '.yaml']:

        LOG.info(f"Loading YAML config file: {fname}")

        from qtpyvcp import CONFIG, DEFAULT_CONFIG_FILE
        from qtpyvcp.utilities.config_loader import load_config_files

        try:
            CONFIG.update(load_config_files(fname, DEFAULT_CONFIG_FILE))
            data = CONFIG.get('qtdesigner')
        except Exception as e:
            LOG.error("Error loading YAML config file:")
            LOG.error(e)
            raise

        from qtpyvcp.utilities.settings import addSetting
        for k, v in list(CONFIG['settings'].items()):
            addSetting(k, **v)

        # add to path so that QtDesginer can load it when it starts
        config_file = f"{fname}:{os.getenv('VCP_CONFIG_FILES', '')}"
        os.environ['VCP_CONFIG_FILES'] = config_file

        if data is not None:
            yml_dir = os.path.realpath(os.path.dirname(fname))

            # prefer command line ui file
            ui_file = opts.ui_file or data.get('ui_file')
            if ui_file is not None:
                ui_file = os.path.join(yml_dir, ui_file)
                cmd.append(ui_file)
                LOG.info(f"Loading UI file: {ui_file}")
            else:
                LOG.info("No UI file specified.")

            # prefer command line qss file
            qss_file = opts.qss_file or data.get('qss_file')
            if qss_file is not None:
                qss_file = os.path.join(yml_dir, qss_file)
                os.environ['QSS_STYLESHEET'] = qss_file
                LOG.info(f"Loading QSS file: {qss_file}")
            else:
                LOG.info("No QSS file specified.")

    elif ext == '.ui':
        cmd.append(fname)

        LOG.info(f"Loading UI file: {fname}")

    else:
        LOG.error("""No valid file type selected.\n
                  File must be a .yaml config file or a .ui file.""")
        sys.exit()

    base = os.path.dirname(__file__)
    sys.path.insert(0, base)
    os.environ['QTPYVCP_LOG_FILE'] = opts.log_file
    os.environ['QTPYVCP_LOG_LEVEL'] = opts.log_level
    os.environ['QT_SELECT'] = 'qt6'
    os.environ['DESIGNER'] = '1'

    widgets_path =  os.path.join(base, "..", "widgets")

    os.environ['PYSIDE_DESIGNER_PLUGINS'] = widgets_path


    LOG.info("Starting QtDesigner ...")

    try:
        process = Popen(cmd, stdout=PIPE, stderr=STDOUT)

        with process.stdout:
            log_subprocess_output(process.stdout)

        exitcode = process.wait()  # 0 means success

    except OSError as exception:
        LOG.error("""Designer not found, Install with\n
                  sudo apt install qttools5-dev qttools5-dev-tools""")
        LOG.error(f'Exception occured: {exception}')
        LOG.error('Subprocess failed')
        os.environ.pop('DESIGNER')
        return False
    else:
        # no exception was raised
        LOG.info('EditVCP finished')
        os.environ.pop('DESIGNER')


def main() -> None:
    raw_args = docopt(__doc__)
    # convert raw argument keys to valid python names
    opts = DotDict({arg.strip('-<>').replace('-', '_'):
                    value for arg, value in list(raw_args.items())})

    app = QApplication(sys.argv)
    launch_designer(opts)


if __name__ == '__main__':
    main()
