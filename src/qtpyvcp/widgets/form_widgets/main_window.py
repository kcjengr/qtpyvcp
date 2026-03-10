import os
import sys
from time import perf_counter

IN_DESIGNER = os.getenv('DESIGNER', False)

import linuxcnc

from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QKeySequence, QAction, QShortcut, QActionGroup
from PySide6.QtCore import Qt, Slot, QTimer, QFile, QObject, QCoreApplication
from PySide6.QtWidgets import QMainWindow, QApplication, QMessageBox, \
    QMenu, QMenuBar, QLineEdit, QVBoxLayout, QButtonGroup, QWidget, QGridLayout, QBoxLayout

import qtpyvcp
from qtpyvcp import actions
from qtpyvcp.utilities import logger
from qtpyvcp.utilities.info import Info
from qtpyvcp.plugins import getPlugin
from qtpyvcp.utilities.settings import getSetting
from qtpyvcp.widgets.dialogs import showDialog as _showDialog
from qtpyvcp.app.launcher import _initialize_object_from_dict
from qtpyvcp.utilities.pyside_ui_loader import PySide6Ui
from qtpyvcp.utilities.encode_utils import allEncodings
from qtpyvcp.utilities.load_perf_summary import PROGRAM_LOAD_PERF_SUMMARY
from qtpyvcp.utilities.qt_safety import safe_qt_callback

LOG = logger.getLogger(__name__)
INFO = Info()
STATUS = getPlugin('status')

class VCPMainWindow(QMainWindow):

    def __init__(self, parent=None, opts=None, ui_file=None, stylesheet=None,
                 maximize=False, fullscreen=False, position=None, size=None,
                 confirm_exit=True, title=None, menu='default'):

        super(VCPMainWindow, self).__init__(parent)

        if IN_DESIGNER:
            # In designer mode, do minimal initialization needed for proper display
            if title is not None:
                self.setWindowTitle(title)
            # DON'T apply stylesheet to self in Designer mode - it would be saved to .ui file
            # The designer_hooks will apply it at QApplication level for preview
            # The QSS_STYLESHEET env var (set by editvcp) is handled by designer_hooks
            return

        if opts is None:
            opts = qtpyvcp.OPTIONS

        self._inifile = linuxcnc.ini(os.getenv("INI_FILE_NAME"))
        self._keyboard_jog = self._inifile.find("DISPLAY", "KEYBOARD_JOG") or "false"
        self._keyboard_jog_ctrl_off = self._inifile.find("DISPLAY", "KEYBOARD_JOG_SAFETY_OFF") or "false"
        lathe_val = (self._inifile.find("DISPLAY", "LATHE") or "0").strip().lower()
        back_tool_val = (self._inifile.find("DISPLAY", "BACK_TOOL_LATHE") or "0").strip().lower()
        self._lathe_mode = (lathe_val not in ["0", "false", "no", "n", ""]) or (back_tool_val not in ["0", "false", "no", "n", ""])
        self._back_tool_lathe = back_tool_val not in ["0", "false", "no", "n", ""]
        # keyboard jogging multi key press tracking
        # Key   Purpose
        # ---   ---------------------------------------------
        #  -    Slow jog speed to a fixed %.  e.g. 30%
        #  +    Max rapid speed for jog
        # Ctl   ctrl key needs to be pushed to enable jog
        self.slow_jog = False
        self.rapid_jog = False

        self._explicit_window_title = title

        self.setWindowTitle(title)

        self.app = QApplication.instance()

        self.confirm_exit = confirm_exit if opts.confirm_exit is None else opts.confirm_exit

        # Load the UI file AFTER defining variables, otherwise the values
        # set in QtDesigner get overridden by the default values
        if ui_file is not None:
            self.loadUi(ui_file)
            # self.initUi()

        if menu is not None:
            try:
                # delete any preexisting menuBar added in QtDesigner
                # because it shadows the QMainWindow.menuBar() method
                del self.menuBar
            except AttributeError:
                pass

            if menu == 'default':
                menu = qtpyvcp.CONFIG.get('default_menubar', [])

            self.setMenuBar(self.buildMenuBar(menu))

        if title is not None:
            self.setWindowTitle(title)

        if stylesheet is not None:
            self.loadStylesheet(stylesheet)

        maximize = opts.maximize if opts.maximize is not None else maximize
        if maximize:
            QTimer.singleShot(0, self.showMaximized)

        fullscreen = opts.fullscreen if opts.fullscreen is not None else fullscreen
        if fullscreen:
            QTimer.singleShot(0, self.showFullScreen)

        if opts.hide_menu_bar:
            self.menuBar().hide()

        size = opts.size or size
        if size:
            try:
                width, height = size.lower().split('x')
                self.resize(int(width), int(height))
            except:
                LOG.exception('Error parsing --size argument: %s', size)

        pos = opts.position or position
        if pos:
            try:
                xpos, ypos = pos.lower().split('x')
                self.move(int(xpos), int(ypos))
            except:
                LOG.exception('Error parsing --position argument: %s', pos)

        QShortcut(QKeySequence("F11"), self, self.toggleFullscreen)
        self.app.focusChanged.connect(self.focusChangedEvent)

        # Add a timer to periodically check for focus and stop jogging if not active
        self._jog_active = False  # Track if keyboard jog is currently active
        self._jog_safety_timer = QTimer(self)
        self._jog_safety_timer.timeout.connect(self._jogSafetyCheck)
        self._jog_safety_timer.start(100)  # check every 100ms

    def loadUi(self, ui_file):
        """Loads a window layout from a QtDesigner .ui file.

        Args:
            ui_file (str) : Path to a .ui file to load.
        """
        def _apply_widget_attributes():
            for obj in self.findChildren(QObject):
                if hasattr(obj, 'objectName') and obj.objectName():
                    name = obj.objectName()
                    if not hasattr(self, name):
                        setattr(self, name, obj)

        def _wire_gcode_editor_status_hooks():
            decode_cache = {
                'fname': None,
                'mtime': None,
                'size': None,
                'bytes_data': None,
                'text': None,
                'encoding': None,
                'bytes': 0,
            }
            shared_doc_state = {
                'active_file': None,
                'source_editor': None,
            }

            def _share_document_from_source(target_editor, source_editor):
                if source_editor is None or source_editor is target_editor:
                    return False

                try:
                    if hasattr(target_editor, 'use_shared_document_from'):
                        return bool(target_editor.use_shared_document_from(source_editor))

                    if (
                        hasattr(target_editor, 'setDocument')
                        and hasattr(target_editor, 'document')
                        and hasattr(source_editor, 'document')
                    ):
                        source_doc = source_editor.document()
                        if source_doc is None:
                            return False
                        if target_editor.document() is source_doc:
                            return True
                        target_editor.setDocument(source_doc)
                        return True
                except Exception:
                    LOG.debug("Unable to share editor document", exc_info=True)

                return False

            def _bytes_from_cache(fname):
                try:
                    stat = os.stat(fname)
                except Exception:
                    return None, 0.0, 0, False

                cache_hit = (
                    decode_cache['fname'] == fname and
                    decode_cache['mtime'] == stat.st_mtime_ns and
                    decode_cache['size'] == stat.st_size and
                    decode_cache['bytes_data'] is not None
                )
                if cache_hit:
                    return decode_cache['bytes_data'], 0.0, decode_cache['bytes'], True

                read_start = perf_counter()
                with open(fname, 'rb') as handle:
                    data = handle.read()
                read_ms = (perf_counter() - read_start) * 1000.0

                decode_cache['fname'] = fname
                decode_cache['mtime'] = stat.st_mtime_ns
                decode_cache['size'] = stat.st_size
                decode_cache['bytes_data'] = data
                decode_cache['text'] = None
                decode_cache['encoding'] = 'raw-bytes'
                decode_cache['bytes'] = len(data)

                return data, read_ms, len(data), False

            def _decode_file_with_cache(fname):
                try:
                    stat = os.stat(fname)
                except Exception:
                    return None, None, 0.0, 0, False

                cache_hit = (
                    decode_cache['fname'] == fname and
                    decode_cache['mtime'] == stat.st_mtime_ns and
                    decode_cache['size'] == stat.st_size and
                    decode_cache['text'] is not None
                )
                if cache_hit:
                    return decode_cache['text'], decode_cache['encoding'], 0.0, decode_cache['bytes'], True

                decode_ms = 0.0
                gcode_text = None
                used_encoding = None
                for encoding in allEncodings():
                    dec_start = perf_counter()
                    try:
                        with open(fname, 'r', encoding=encoding) as handle:
                            gcode_text = handle.read()
                        used_encoding = encoding
                        decode_ms = (perf_counter() - dec_start) * 1000.0
                        break
                    except Exception:
                        continue

                if gcode_text is None:
                    return None, None, decode_ms, 0, False

                decode_cache['fname'] = fname
                decode_cache['mtime'] = stat.st_mtime_ns
                decode_cache['size'] = stat.st_size
                decode_cache['text'] = gcode_text
                decode_cache['encoding'] = used_encoding
                decode_cache['bytes'] = len(gcode_text.encode('utf-8', errors='ignore'))

                return gcode_text, used_encoding, decode_ms, decode_cache['bytes'], False

            for obj in self.findChildren(QObject):
                if obj.metaObject().className() not in ('GCodeEditor', 'GcodeEditor'):
                    continue
                if not (hasattr(obj, 'set_text_fast') or hasattr(obj, 'setText') or hasattr(obj, 'setPlainText')):
                    continue
                if getattr(obj, '_qtpyvcp_status_wired', False):
                    continue

                def _load_program_file(fname=None, editor=obj):
                    if not fname or not os.path.isfile(fname):
                        return

                    editor_class = editor.metaObject().className()
                    t0 = perf_counter()

                    if shared_doc_state['active_file'] != fname:
                        shared_doc_state['active_file'] = fname
                        shared_doc_state['source_editor'] = None

                    used_encoding = None
                    decode_ms = 0.0
                    bytes_len = 0
                    cache_hit = False

                    bytes_payload = None
                    gcode_text = None

                    source_editor = shared_doc_state.get('source_editor')
                    if (
                        source_editor is not None
                        and source_editor is not editor
                    ):
                        _, _, bytes_len, cache_hit = _bytes_from_cache(fname)
                        apply_start = perf_counter()
                        shared_ok = _share_document_from_source(editor, source_editor)
                        apply_ms = (perf_counter() - apply_start) * 1000.0
                        if shared_ok:
                            total_ms = (perf_counter() - t0) * 1000.0
                            LOG.debug(
                                "[gcode-load-perf] widget=%s bytes=%d encoding=%s decode_ms=%.2f apply_ms=%.2f total_ms=%.2f cache_hit=%s file=%s",
                                editor_class,
                                bytes_len,
                                'shared-doc',
                                0.0,
                                apply_ms,
                                total_ms,
                                cache_hit,
                                fname,
                            )

                            PROGRAM_LOAD_PERF_SUMMARY.update_editor(
                                fname,
                                widget_name=editor_class,
                                total_ms=total_ms,
                            )
                            return

                    if hasattr(editor, 'set_text_fast'):
                        bytes_payload, decode_ms, bytes_len, cache_hit = _bytes_from_cache(fname)
                        used_encoding = 'raw-bytes'
                        if bytes_payload is None:
                            LOG.warning("Unable to read program file for GCodeEditor: %s", fname)
                            return
                    else:
                        gcode_text, used_encoding, decode_ms, bytes_len, cache_hit = _decode_file_with_cache(fname)
                        if gcode_text is None:
                            LOG.warning("Unable to decode program file for GCodeEditor: %s", fname)
                            return

                    apply_start = perf_counter()
                    if hasattr(editor, 'set_text_fast'):
                        editor.set_text_fast(bytes_payload)
                    elif hasattr(editor, 'setText'):
                        editor.setText(gcode_text)
                    else:
                        editor.setPlainText(gcode_text)

                    try:
                        if hasattr(editor, 'setFilename'):
                            editor.setFilename(fname)
                        elif hasattr(editor, 'setFilePath'):
                            editor.setFilePath(fname)
                    except Exception:
                        LOG.debug("Unable to set filename/filepath on GCodeEditor", exc_info=True)

                    apply_ms = (perf_counter() - apply_start) * 1000.0
                    total_ms = (perf_counter() - t0) * 1000.0

                    if shared_doc_state.get('source_editor') is None:
                        shared_doc_state['source_editor'] = editor

                    LOG.debug(
                        "[gcode-load-perf] widget=%s bytes=%d encoding=%s decode_ms=%.2f apply_ms=%.2f total_ms=%.2f cache_hit=%s file=%s",
                        editor_class,
                        bytes_len,
                        used_encoding,
                        decode_ms,
                        apply_ms,
                        total_ms,
                        cache_hit,
                        fname,
                    )

                    PROGRAM_LOAD_PERF_SUMMARY.update_editor(
                        fname,
                        widget_name=editor_class,
                        total_ms=total_ms,
                    )

                def _set_current_line(line, editor=obj):
                    try:
                        line_number = max(0, int(line) - 1)
                        if hasattr(editor, 'setCursorPosition'):
                            editor.setCursorPosition(line_number, 0)
                            if hasattr(editor, 'ensureCursorVisible'):
                                editor.ensureCursorVisible()
                            return

                        if not hasattr(editor, 'document'):
                            return

                        block = editor.document().findBlockByLineNumber(line_number)
                        if not block.isValid():
                            return
                        cursor = editor.textCursor()
                        cursor.setPosition(block.position())
                        editor.setTextCursor(cursor)
                        if hasattr(editor, 'centerCursor'):
                            editor.centerCursor()
                    except Exception:
                        LOG.debug("Unable to set current line for GCodeEditor", exc_info=True)

                STATUS.file.notify(safe_qt_callback(obj, _load_program_file))
                STATUS.motion_line.onValueChanged(safe_qt_callback(obj, _set_current_line))

                current_file = str(STATUS.file)
                if current_file:
                    _load_program_file(current_file)

                setattr(obj, '_qtpyvcp_status_wired', True)

        def _wire_button_group_slots():
            for group in self.findChildren(QButtonGroup):
                group_name = group.objectName()
                if not group_name:
                    continue

                slot_name = f'on_{group_name}_buttonClicked'
                slot = getattr(self, slot_name, None)
                if slot is None:
                    continue

                if getattr(group, '_qtpyvcp_button_group_wired', False):
                    continue

                try:
                    group.buttonClicked.connect(slot)
                    setattr(group, '_qtpyvcp_button_group_wired', True)
                except Exception:
                    LOG.exception("Failed wiring button group slot: %s", slot_name)

        def _register_ui_custom_widgets(loader, path):
            import importlib
            import xml.etree.ElementTree as ET

            try:
                tree = ET.parse(path)
                root = tree.getroot()
            except Exception:
                LOG.exception("Unable to parse UI for custom widget registration: %s", path)
                return

            customwidgets = root.find('customwidgets')
            if customwidgets is None:
                return

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
                except Exception:
                    LOG.debug("Skipping custom widget registration for %s from %s", class_name, module_path)

        def _replace_vtk_placeholders_runtime(root_widget):
            """Replace any designer placeholder VTK widgets with the real runtime widget."""
            placeholders = root_widget.findChildren(QWidget, "vtkbackplotplaceholder")
            # Also detect class-based placeholders regardless of object name.
            placeholders_by_class = [
                w for w in root_widget.findChildren(QWidget)
                if w.metaObject().className() == "VTKBackPlotPlaceholder"
            ]

            # Merge preserving object identity order.
            seen = set()
            all_placeholders = []
            for w in placeholders + placeholders_by_class:
                wid = id(w)
                if wid in seen:
                    continue
                seen.add(wid)
                all_placeholders.append(w)

            if not all_placeholders:
                return

            try:
                from qtpyvcp.widgets.display_widgets.vtk_backplot.vtk_backplot import VTKBackPlot as RealVTKBackPlot
            except Exception:
                LOG.exception("Failed importing runtime VTKBackPlot for placeholder replacement")
                return

            for placeholder in all_placeholders:
                placeholder_name = placeholder.objectName()
                placeholder_parent = placeholder.parentWidget()
                layout = placeholder_parent.layout() if placeholder_parent is not None else None

                if placeholder_parent is None or layout is None:
                    continue

                try:
                    real_vtk = RealVTKBackPlot(placeholder_parent)
                    # Keep wiring stable: normalize placeholder names to runtime names.
                    normalized_name = placeholder_name or "vtk"
                    if normalized_name.endswith("placeholder"):
                        normalized_name = normalized_name[: -len("placeholder")]
                    if not normalized_name:
                        normalized_name = "vtk"
                    real_vtk.setObjectName(normalized_name)

                    # Prefer Qt's built-in replacement API, which can resolve
                    # nested layout ownership better than indexOf() alone.
                    replaced_item = None
                    try:
                        replaced_item = layout.replaceWidget(placeholder, real_vtk)
                    except Exception:
                        replaced_item = None

                    if replaced_item is not None:
                        placeholder.hide()
                        placeholder.deleteLater()
                        continue

                    if isinstance(layout, QGridLayout):
                        index = layout.indexOf(placeholder)
                        if index >= 0:
                            row, col, row_span, col_span = layout.getItemPosition(index)
                            layout.removeWidget(placeholder)
                            layout.addWidget(real_vtk, row, col, row_span, col_span)
                        else:
                            # Fallback if placeholder is not a direct item in this layout.
                            layout.addWidget(real_vtk)
                            real_vtk.setGeometry(placeholder.geometry())
                    elif isinstance(layout, QBoxLayout):
                        index = layout.indexOf(placeholder)
                        if index >= 0:
                            layout.removeWidget(placeholder)
                            layout.insertWidget(index, real_vtk)
                        else:
                            # Fallback if placeholder is nested or wrapped in another item.
                            layout.addWidget(real_vtk)
                            real_vtk.setGeometry(placeholder.geometry())
                    else:
                        layout.removeWidget(placeholder)
                        layout.addWidget(real_vtk)

                    placeholder.deleteLater()
                except Exception:
                    LOG.exception("Failed replacing VTK placeholder: name=%s", placeholder_name)

        def _ui_uses_gcode_editor(path):
            try:
                with open(path, 'r', encoding='utf-8') as ui_file_handle:
                    ui_xml = ui_file_handle.read()
                return ('<class>GcodeEditor</class>' in ui_xml or
                        '<widget class="GcodeEditor"' in ui_xml or
                        '<class>GCodeEditor</class>' in ui_xml or
                        '<widget class="GCodeEditor"' in ui_xml)
            except Exception:
                LOG.exception("Unable to inspect UI file for GcodeEditor usage: %s", path)
                return False

        # Use QUiLoader for UI loading (PySide6-native path).

        LOG.debug(f"Loading UI with QUiLoader: {ui_file}")

        # Import all QtPyVCP widgets to ensure they're available
        from qtpyvcp.widgets import register_widgets  # noqa: F401


        ui_file_obj = QFile(ui_file)
        ui_file_obj.open(QFile.ReadOnly)
        
        loader = QUiLoader()

        # Make runtime plugin loading explicit for custom C++ widgets declared
        # in .ui files (notably GCodeEditor from gcodeeditor.h).
        package_root = os.path.dirname(qtpyvcp.__file__)
        packaged_plugin_root = os.path.join(package_root, 'qt_plugins')
        packaged_designer_dir = os.path.join(packaged_plugin_root, 'designer')
        dev_widgets_dir = os.path.join(package_root, 'native', 'widgets_cpp', 'gcode_editor')

        plugin_roots = [packaged_plugin_root]
        plugin_roots.extend([p for p in os.environ.get('QT_PLUGIN_PATH', '').split(os.pathsep) if p])

        designer_paths = [packaged_designer_dir, dev_widgets_dir]
        designer_paths.extend([p for p in os.environ.get('QT_DESIGNER_PLUGIN_PATH', '').split(os.pathsep) if p])
        for root in plugin_roots:
            if root:
                designer_paths.append(os.path.join(root, 'designer'))

        seen_paths = set()
        for root in plugin_roots:
            if os.path.isdir(root):
                QCoreApplication.addLibraryPath(root)

        for plugin_dir in designer_paths:
            if not plugin_dir or plugin_dir in seen_paths or not os.path.isdir(plugin_dir):
                continue
            try:
                loader.addPluginPath(plugin_dir)
                seen_paths.add(plugin_dir)
            except Exception:
                LOG.debug("Failed to add QUiLoader plugin path: %s", plugin_dir, exc_info=True)

        LOG.info("QUiLoader plugin paths: %s", ', '.join(loader.pluginPaths()))

        _register_ui_custom_widgets(loader, ui_file)

        # Register essential QtPyVCP custom widgets
        try:
            from qtpyvcp.widgets.button_widgets.action_button import ActionButton
            loader.registerCustomWidget(ActionButton)
        except ImportError:
            pass
        try:
            from qtpyvcp.widgets.display_widgets.status_label import StatusLabel
            loader.registerCustomWidget(StatusLabel)
        except ImportError:
            pass
        try:
            from qtpyvcp.widgets.hal_widgets.hal_label import HalLabel
            loader.registerCustomWidget(HalLabel)
        except ImportError:
            pass
        try:
            from qtpyvcp.widgets.input_widgets.file_system import FileSystemTable
            loader.registerCustomWidget(FileSystemTable)
        except ImportError:
            pass
        try:
            from qtpyvcp.widgets.input_widgets.gcode_text_edit import GcodeTextEdit
            loader.registerCustomWidget(GcodeTextEdit)
        except ImportError:
            pass
        try:
            from qtpyvcp.widgets.display_widgets.vtk_backplot.vtk_backplot import VTKBackPlot
            loader.registerCustomWidget(VTKBackPlot)
        except ImportError:
            pass

        # Backward compatibility for .ui files saved with the designer-only
        # placeholder class name.
        try:
            from qtpyvcp.widgets.display_widgets.designer_plugins import VTKBackPlotPlaceholder
            loader.registerCustomWidget(VTKBackPlotPlaceholder)
        except ImportError:
            pass

        
        loaded_ui = loader.load(ui_file_obj, self)

        if isinstance(loaded_ui, QMainWindow) and loaded_ui is not self:
            loaded_title = loaded_ui.windowTitle()
            if self._explicit_window_title in (None, '') and loaded_title:
                self.setWindowTitle(loaded_title)

            loaded_icon = loaded_ui.windowIcon()
            if loaded_icon is not None and not loaded_icon.isNull():
                self.setWindowIcon(loaded_icon)

            loaded_central = loaded_ui.centralWidget()
            if loaded_central is not None:
                loaded_central.setParent(None)
                self.setCentralWidget(loaded_central)

            loaded_status = loaded_ui.statusBar()
            if loaded_status is not None:
                loaded_status.setParent(None)
                self.setStatusBar(loaded_status)

            loaded_menu = loaded_ui.menuBar()
            if loaded_menu is not None:
                loaded_menu.setParent(None)
                self.setMenuBar(loaded_menu)

            for child in list(loaded_ui.children()):
                if child in (loaded_central, loaded_status, loaded_menu):
                    continue
                if child.parent() is not loaded_ui:
                    continue
                if not isinstance(child, QButtonGroup):
                    continue
                try:
                    child.setParent(self)
                except Exception:
                    LOG.debug("Unable to reparent loaded button group: %s", child, exc_info=True)

            loaded_ui.deleteLater()
            self.ui = self
        else:
            self.ui = loaded_ui

        _replace_vtk_placeholders_runtime(self)
        
        _apply_widget_attributes()
        _wire_button_group_slots()
        _wire_gcode_editor_status_hooks()
        self.loadSplashGcode()
        
    def loadStylesheet(self, stylesheet):
        """Loads a QSS stylesheet containing styles to be applied
        to specific Qt and/or QtPyVCP widget classes.

        Args:
            stylesheet (str) : Path to a .qss stylesheet
        """
        LOG.info("Loading QSS stylesheet file: yellow<{}>".format(stylesheet))
        
        # Read the actual file contents instead of using file:/// reference
        # This is required for Qt Designer preview to work
        try:
            with open(stylesheet, 'r', encoding='utf-8') as f:
                qss_content = f.read()
            self.setStyleSheet(qss_content)
        except Exception as e:
            LOG.error(f"Failed to load stylesheet {stylesheet}: {e}")
            # Fallback to file:/// method (works at runtime but not in Designer)
            self.setStyleSheet("file:///" + stylesheet)

    def stopAllJogAxes(self):
        # Stop all axes (X, Y, Z, and optionally A, B, C)
        for axis in ['X', 'Y', 'Z', 'A', 'B', 'C']:
            try:
                actions.machine.jog.axis(axis, 0)
            except Exception:
                pass
        # Also reset jog state so keyReleaseEvent doesn't expect a key to be held
        self.slow_jog = False
        self.rapid_jog = False

    def showModalDialog(self, dialog_func, *args, **kwargs):
        # Stop all jog axes before showing any modal dialog
        self.stopAllJogAxes()
        return dialog_func(*args, **kwargs)

    def getMenuAction(self, menu, title='notitle', action_name='noaction',
                      shortcut="", args=[], kwargs={}):
        # ToDo: Clean this up, it is very hacky
        env = {'app': QApplication.instance(),
               'win': self,
               'action': actions,
               }

        if action_name is not None:

            if action_name.startswith('settings.'):
                setting_id = action_name[len('settings.'):]
                setting = getSetting(setting_id)

                if setting:
                    if setting.enum_options is not None:
                        submenu = QMenu(parent=self, title=title)

                        group = QActionGroup(self)
                        group.setExclusive(True)
                        group.triggered.connect(lambda a: setting.setValue(a.data()))

                        def update(group, val):
                            for act in group.actions():
                                if act.data() == val:
                                    act.setChecked(True)
                                    break

                        for num, opt in enumerate(setting.enum_options):

                            menu_action = QAction(parent=self, text=opt)
                            menu_action.setCheckable(True)
                            if setting.value == num:
                                menu_action.setChecked(True)

                            menu_action.setData(num)
                            setting.notify(safe_qt_callback(menu_action, lambda v: update(group, v)))

                            menu_action.setActionGroup(group)
                            submenu.addAction(menu_action)
                        menu.addMenu(submenu)

                    elif setting.value_type == bool:
                        # works for bool settings
                        menu_action = QAction(parent=self, text=title)
                        menu_action.setCheckable(True)
                        menu_action.triggered.connect(setting.setValue)
                        menu_action.setShortcut(shortcut)
                        setting.notify(safe_qt_callback(menu_action, menu_action.setChecked))
                        menu.addAction(menu_action)

                    return

            try:
                menu_action = QAction(parent=self, text=title)

                mod, action = action_name.split('.', 1)
                method = getattr(env.get(mod, self), action)
                if menu_action.isCheckable():
                    menu_action.triggered.connect(method)
                else:
                    menu_action.triggered.connect(lambda checked: method(*args, **kwargs))

                menu_action.setShortcut(shortcut)
                menu.addAction(menu_action)
                return
            except:
                pass

            try:
                menu_action = QAction(parent=self, text=title)
                actions.bindWidget(menu_action, action_name)
                menu_action.setShortcut(shortcut)
                menu.addAction(menu_action)
                return
            except actions.InvalidAction:
                LOG.exception('Error binding menu action %s', action_name)

        menu_action = QAction(parent=self, text=title)
        msg = "The <b>{}</b> action specified for the " \
              "<b>{}</b> menu item could not be triggered. " \
              "Check the YAML config file for errors." \
              .format(action_name or '', title.replace('&', ''))
        # Use showModalDialog to ensure jogging is stopped
        menu_action.triggered.connect(lambda: self.showModalDialog(QMessageBox.critical, self, "Menu Action Error!", msg))
        menu.addAction(menu_action)

    def buildMenuBar(self, menus):
        """Recursively build menu bar.

        Args:
            menus (list) : List of dicts and lists containing the
                items to add to the menu.

        Returns:
            QMenuBar
        """

        def recursiveAddItems(menu, items):

            for item in items:

                if item == 'separator':
                    menu.addSeparator()
                    continue

                if not isinstance(item, dict):
                    LOG.warn("Skipping unrecognized menu item: %s", item)
                    continue

                title = item.get('title') or ''
                items = item.get('items')
                provider = item.get('provider')
                args = item.get('args') or []
                kwargs = item.get('kwargs') or {}

                if items is not None:
                    new_menu = QMenu(parent=self, title=title)
                    recursiveAddItems(new_menu, items)
                    menu.addMenu(new_menu)

                elif provider is not None:
                    new_menu = _initialize_object_from_dict(item, parent=menu)
                    new_menu.setTitle(title)
                    menu.addMenu(new_menu)

                else:
                    self.getMenuAction(menu, title, item.get('action'),
                                       item.get('shortcut', ''),
                                       item.get('args', []),
                                       item.get('kwargs', {}))

        menu_bar = QMenuBar(self)
        recursiveAddItems(menu_bar, menus)
        return menu_bar

    def initUi(self):
        self.loadSplashGcode()

    @Slot()
    def toggleFullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def closeEvent(self, event):
        # Use showModalDialog to ensure jogging is stopped
        if os.getenv('DESIGNER', False):
            self.close()
        elif self.confirm_exit:
            quit_msg = "Are you sure you want to exit LinuxCNC?"
            reply = self.showModalDialog(QMessageBox.question, self, 'Exit LinuxCNC?',
                                         quit_msg, QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                QApplication.instance().quit()
            else:
                event.ignore()
        else:
            self.app.quit()

    def keyPressEvent(self, event):
        # super(VCPMainWindow, self).keyPressEvent(event)
        # Test for UI LOCK and consume event but do nothing if LOCK in place
        if STATUS.isLocked():
            self.stopAllJogAxes()  # Stop jog if UI is locked (e.g., by modal dialog)
            LOG.debug('Accept keyPressEvent Event')
            event.accept()
            return
        
        if self._keyboard_jog.lower() in ['false', '0', 'f', 'n', 'no']:
            event.accept()
            return
          
        if event.isAutoRepeat():
            return

        if self.app.focusWidget() != None:
            LOG.debug(f"Focus widget = {self.app.focusWidget().objectName()}")
        else:
            LOG.debug(f"Focus widget = None")

        # Determine jog speed: Shift always means rapid jog
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            speed = actions.machine.MAX_JOG_SPEED / 60
        elif self.rapid_jog:
            speed = actions.machine.MAX_JOG_SPEED / 60
        elif self.slow_jog:
            speed = actions.machine.jog_linear_speed() / 60 / 10.0
        else:
            speed = None

        # Consistent jog safety logic
        if self._keyboard_jog_ctrl_off.lower() in ['true', '1', 't', 'y', 'yes']:
            jog_active = 1
        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            jog_active = 1
        else:
            jog_active = 0

        LOG.debug("GLOBAL - Key event processing")

        jog_started = False
        # Only jog if jog_active is set
        if jog_active:
            if self._lathe_mode:
                # Invert X axis for LATHE=1 and not BACK_TOOL_LATHE=1
                x_sign = -1 if (not self._back_tool_lathe and self._lathe_mode) else 1
                if event.key() == Qt.Key_Up:
                    actions.machine.jog.axis('X', 1 * x_sign, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_Down:
                    actions.machine.jog.axis('X', -1 * x_sign, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_Left:
                    actions.machine.jog.axis('Z', -1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_Right:
                    actions.machine.jog.axis('Z', 1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_PageUp:
                    actions.machine.jog.axis('Y', 1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_PageDown:
                    actions.machine.jog.axis('Y', -1, speed=speed)
                    jog_started = True
            else:
                if event.key() == Qt.Key_Up:
                    actions.machine.jog.axis('Y', 1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_Down:
                    actions.machine.jog.axis('Y', -1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_Left:
                    actions.machine.jog.axis('X', -1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_Right:
                    actions.machine.jog.axis('X', 1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_PageUp:
                    actions.machine.jog.axis('Z', 1, speed=speed)
                    jog_started = True
                elif event.key() == Qt.Key_PageDown:
                    actions.machine.jog.axis('Z', -1, speed=speed)
                    jog_started = True

        # Handle jog speed keys regardless of jog_active
        if event.key() == Qt.Key_Minus:
            self.slow_jog = True
            self.rapid_jog = False
        elif event.key() in [Qt.Key_Plus, Qt.Key_Equal]:
            self.rapid_jog = True
            self.slow_jog = False

        if jog_started:
            self._jog_active = True

    def keyReleaseEvent(self, event):
        # Test for UI LOCK and consume event but do nothing if LOCK in place
        if STATUS.isLocked():
            self.stopAllJogAxes()  # Stop jog if UI is locked (e.g., by modal dialog)
            LOG.debug('Accept keyReleaseEvent Event')
            event.accept()
            return

        if self._keyboard_jog.lower() in ['false', '0', 'f', 'n', 'no']:
            event.accept()
            return
        
        if event.isAutoRepeat():
            return

        jog_stopped = False
        if self._lathe_mode:
            x_sign = -1 if (not self._back_tool_lathe and self._lathe_mode) else 1
            if event.key() == Qt.Key_Up:
                actions.machine.jog.axis('X', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Down:
                actions.machine.jog.axis('X', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Left:
                actions.machine.jog.axis('Z', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Right:
                actions.machine.jog.axis('Z', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_PageUp:
                actions.machine.jog.axis('Y', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_PageDown:
                actions.machine.jog.axis('Y', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Minus:
                self.slow_jog = False
            elif event.key() in [Qt.Key_Plus, Qt.Key_Equal]:
                self.rapid_jog = False
        else:
            if event.key() == Qt.Key_Up:
                actions.machine.jog.axis('Y', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Down:
                actions.machine.jog.axis('Y', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Left:
                actions.machine.jog.axis('X', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Right:
                actions.machine.jog.axis('X', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_PageUp:
                actions.machine.jog.axis('Z', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_PageDown:
                actions.machine.jog.axis('Z', 0)
                jog_stopped = True
            elif event.key() == Qt.Key_Minus:
                self.slow_jog = False
            elif event.key() in [Qt.Key_Plus, Qt.Key_Equal]:
                self.rapid_jog = False
        if jog_stopped:
            self._jog_active = False

    def mousePressEvent(self, event):
        #print('Button press')
        # Test for UI LOCK and consume event but do nothing if LOCK in place
        if STATUS.isLocked():
            LOG.debug('Accept mouse Press Event')
            event.accept()
            return 
        focused_widget = self.focusWidget()
        if focused_widget is not None:
            focused_widget.clearFocus()

    def mouseReleaseEvent(self, event):
        if STATUS.isLocked():
            LOG.debug('Accept mouse Release Event')
            event.accept()
            return 
        super().mouseReleaseEvent(event)

    def focusChangedEvent(self, old_w, new_w):
        # Only handle QLineEdit selection, no jog stop needed here anymore
        if issubclass(new_w.__class__, QLineEdit):
            QTimer.singleShot(0, new_w.selectAll)

    def _jogSafetyCheck(self):
        # Only stop axes if keyboard jog is currently active and window is not focused
        if self._jog_active and not self.isActiveWindow():
            self.stopAllJogAxes()
            self._jog_active = False

# ==============================================================================
#  menu action slots
# ==============================================================================

    @Slot()
    def openFile(self):
        self.showModalDialog(_showDialog, 'open_file')

    @Slot(str)
    def showDialog(self, dialog_name):
        self.showModalDialog(_showDialog, dialog_name)

# ==============================================================================
# menu functions
# ==============================================================================



# ==============================================================================
# helper functions
# ==============================================================================

    def loadSplashGcode(self):
        # Load backplot splash code
        splash_code = INFO.getOpenFile()
        #print(splash_code)
        if splash_code is not None and os.path.isfile(splash_code):
            # Load after startup to not cause hang and 'Can't set mode while machine is running' error
            QTimer.singleShot(200, lambda: actions.program.load(splash_code, add_to_recents=False))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec())

