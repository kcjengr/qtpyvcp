#!/usr/bin/env python

""""Utility to handle importing the global stylesheet for QtPyVCP widgets."""

import os

from qtpy.QtWidgets import QApplication

# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

# Fallback global stylesheet if there is no global stylesheet provided via env
# variable or command line parameter
GLOBAL_STYLESHEET = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '..',
        'default_stylesheet.qss'
    )
)

__style_data = None


def clear_cache():
    """Clear the cache for stylesheet data"""
    global __style_data
    __style_data = None


def apply_stylesheet(stylesheet_file_path=None, widget=None):
    """Apply a stylesheet to the current Qt Designer form (a .ui file).

    Args:
        stylesheet_file_path (str) : The full path to a global CSS stylesheet file
        widget (QWidget) : The widget in which we want to apply the stylesheet.
    """
    # Load style data from the stylesheet file. Otherwise, the fallback is
    # already in place, i.e. QtPyVCP will be using the data from the global
    # stylesheet
    style = _get_style_data(stylesheet_file_path)

    if not style:
        return

    if not widget:
        widget = QApplication.instance()

    widget.setStyleSheet(style)


def _get_style_data(stylesheet_file_path=None):
    """Read the global stylesheet file and provide the style data as a str.

    Args:
        stylesheet_file_path (str) : The path to the global stylesheet.

    Returns:
        str : The style data read from the stylesheet file
    """
    global __style_data

    if not stylesheet_file_path:
        stylesheet_file_path = os.getenv("QSS_STYLESHEET", None)

    if stylesheet_file_path == "":
        stylesheet_file_path = None

    if __style_data:
        return __style_data

    __style_data = None
    load_default = True

    if stylesheet_file_path is not None:
        try:
            with open(stylesheet_file_path, 'r') as stylesheet_file:
                LOG.info(
                    "Opening style file '{0}'...".format(stylesheet_file_path))
                __style_data = stylesheet_file.read()
                load_default = False
        except Exception as ex:
            __style_data = None
            LOG.error(
                "Error reading the stylesheet file '{0}'. Exception: {1}".format(
                    stylesheet_file_path,
                    str(ex)))

    if load_default:
        try:
            with open(GLOBAL_STYLESHEET, 'r') as default_stylesheet:
                LOG.info("Opening the default stylesheet '{0}'...".format(
                    GLOBAL_STYLESHEET))
                __style_data = default_stylesheet.read()
        except Exception as ex:
            __style_data = None
            LOG.exception("Cannot find the default stylesheet file '{0}'.".format(GLOBAL_STYLESHEET))
    return __style_data
