#!/usr/bin/env python3
"""
PySide6 Designer launcher that ensures custom widgets are registered.
This is called by editvcp.py to launch designer with QtPyVCP plugins.
"""
import os
import sys

# Ensure DESIGNER mode is set
os.environ['DESIGNER'] = '1'

# Initialize and register custom widgets BEFORE launching designer
try:
    from qtpyvcp.widgets import qtdesigner_plugin
    print("✓ QtPyVCP designer plugins initialized", file=sys.stderr, flush=True)
except Exception as e:
    print(f"✗ Error initializing designer plugins: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

# Now launch pyside6-designer with remaining arguments
# The first argument should be the UI file
import subprocess
designer_args = ["pyside6-designer"] + sys.argv[1:]
sys.exit(subprocess.call(designer_args))
