import importlib
import os
import sys
import xml.etree.ElementTree as ET

from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget


def register_ui_custom_widgets(loader, ui_path):
    try:
        tree = ET.parse(ui_path)
        root = tree.getroot()
    except Exception:
        return

    customwidgets = root.find('customwidgets')
    if customwidgets is None:
        return

    ui_dir = os.path.dirname(os.path.abspath(ui_path))

    for customwidget in customwidgets.findall('customwidget'):
        class_name = customwidget.findtext('class')
        header = customwidget.findtext('header')

        if not class_name or not header:
            continue

        module_path = header.strip()
        if module_path.endswith('.h'):
            continue

        try:
            module = importlib.import_module(module_path)
            widget_class = getattr(module, class_name, None)
            if widget_class is not None:
                loader.registerCustomWidget(widget_class)
            continue
        except Exception:
            pass

        added_to_path = False
        if ui_dir and ui_dir not in sys.path:
            sys.path.insert(0, ui_dir)
            added_to_path = True

        try:
            module = importlib.import_module(module_path)
            widget_class = getattr(module, class_name, None)
            if widget_class is not None:
                loader.registerCustomWidget(widget_class)
        except Exception:
            continue
        finally:
            if added_to_path:
                try:
                    sys.path.remove(ui_dir)
                except ValueError:
                    pass


def load_ui(ui_path, parent):
    ui_file = QFile(ui_path)
    if not ui_file.open(QFile.ReadOnly):
        raise RuntimeError(f"Unable to open UI file: {ui_path}")

    try:
        loader = QUiLoader()
        register_ui_custom_widgets(loader, ui_path)
        loaded = loader.load(ui_file, parent)
    finally:
        ui_file.close()

    if loaded is None:
        raise RuntimeError(f"Unable to load UI file: {ui_path}")

    if (
        isinstance(parent, QWidget)
        and isinstance(loaded, QWidget)
        and loaded is not parent
        and not isinstance(parent, QMainWindow)
        and not isinstance(loaded, QMainWindow)
    ):
        if loaded.parent() is not parent:
            loaded.setParent(parent)

        layout = parent.layout()
        if layout is None:
            layout = QVBoxLayout(parent)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)

        if layout.indexOf(loaded) < 0:
            layout.addWidget(loaded)

    return loaded