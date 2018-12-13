#!/usr/bin/env python

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
import linuxcnc
import subprocess
from pkg_resources import iter_entry_points

from docopt import docopt
from qtpy.QtWidgets import QApplication, QFileDialog

from qtpyvcp.lib.types import DotDict
from qtpyvcp.utilities.logger import initBaseLogger


if not linuxcnc.version.startswith('2.8'):
    print "QtPyVCP only supports LinuxCNC 2.8, current version is", linuxcnc.version
    print "If you have LinuxCNC installed as a RIP make sure you have\n" \
          "activated the run-in-place environment by running:\n"
    print "    $ . <linuxcnc-rip-dir>/scripts/rip-environment\n"
    sys.exit()

LOG = initBaseLogger('qtpyvcp', log_file=os.devnull, log_level='WARNING')

def launch_designer(opts=DotDict()):

    if not opts.vcp and not opts.ui_file:
        fname, _ = QFileDialog.getOpenFileName(
            parent=None,
            caption="Choose VCP to Edit in QtDesigner",
            filter="VCP Config Files (*.yml *.yaml);;VCP UI Files (*.ui);;All Files (*)",
            options=QFileDialog.Options() | QFileDialog.DontUseNativeDialog)

        if not fname:
            sys.exit()

    else:
        fname = opts.vcp or opts.ui_file


    if not '.' in fname or not '/' in fname:
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

    cmd = ['designer']
    ext = os.path.splitext(fname)[1]
    if ext in ['.yml', '.yaml']:

        print "Loading YAML config file:", fname

        from qtpyvcp import CONFIG
        from qtpyvcp.utilities.config_loader import load_config_files

        try:
            CONFIG.update(load_config_files(fname))
            data = CONFIG.get('qtdesigner')
        except:
            print "Error loading YAML config file:"
            raise

        # add to path so that QtDesginer can load it when it starts
        os.environ['VCP_CONFIG_FILES'] = fname + ':' + os.getenv('VCP_CONFIG_FILES', '')

        if data is not None:
            yml_dir = os.path.dirname(fname)

            # prefer command line ui file
            ui_file = opts.ui_file or data.get('ui_file')
            if ui_file is not None:
                ui_file = os.path.realpath(os.path.join(yml_dir, ui_file))
                cmd.append(ui_file)
                print "Loading UI file:", ui_file
            else:
                print "No UI file specified."

            # prefer command line qss file
            qss_file = opts.qss_file or data.get('qss_file')
            if qss_file is not None:
                qss_file = os.path.realpath(os.path.join(yml_dir, qss_file))
                os.environ['QSS_STYLESHEET'] = qss_file
                print "Loading QSS file:", qss_file
            else:
                print "No QSS file specified."

    elif ext == '.ui':
        cmd.append(fname)

        print "Loading UI file:", fname

    else:
        print "No valid file type selected.\n " \
              "File must be a .yaml config file or a .ui file."
        sys.exit()

    base = os.path.dirname(__file__)
    sys.path.insert(0, base)
    os.environ['QTPYVCP_LOG_FILE'] = opts.log_file
    os.environ['QTPYVCP_LOG_LEVEL'] = opts.log_level
    os.environ['QT_SELECT'] = 'qt5'
    os.environ['PYQTDESIGNERPATH'] = os.path.join(base, '../widgets')

    print "\nStarting QtDesigner ..."
    sys.exit(subprocess.call(cmd))


def main():
    raw_args = docopt(__doc__)
    # convert raw argument keys to valid python names
    opts = DotDict({arg.strip('-<>').replace('-', '_'):
                    value for arg, value in raw_args.items()})

    app = QApplication(sys.argv)
    launch_designer(opts)


if __name__ == '__main__':
    main()
