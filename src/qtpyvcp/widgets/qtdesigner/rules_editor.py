# Copyright (c) 2017-2018, SLAC National Accelerator Laboratory

# This file has been adapted from PyDM, and can be redistributed and/or
# modified in accordance with terms in conditions set forth in the BSD
# 3-Clause License. You can find the complete licence text in the LICENCES
# directory.

# Links:
#   PyDM Project: https://github.com/slaclab/pydm
#   PyDM Licence: https://github.com/slaclab/pydm/blob/master/LICENSE.md

import os
import json
import functools
import webbrowser
import re
import html

# Force qtpy to use PySide6
os.environ['QT_API'] = 'pyside6'

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from PySide6 import QtWidgets, QtCore, QtDesigner

from qtpyvcp.utilities import logger
from qtpyvcp import CONFIG, SETTINGS, DEFAULT_CONFIG_FILE
from qtpyvcp.plugins import DataPlugin, DataChannel, getPlugin, iterPlugins
from qtpyvcp.utilities.settings import Setting, addSetting
from qtpyvcp.utilities.machine_parameters import (
    read_parameter_values,
    get_parameter_value,
)
from .plugin_extension import _PluginExtension

IN_DESIGNER = os.getenv('DESIGNER', False)

# Set up logging
LOG = logger.getLogger(__name__)

RULE_PROPERTIES = {
    'None': ['None', None],
    'Enable': ['setEnabled', bool],
    'Visible': ['setVisible', bool],
    'Style Class': ['setStyleClass', str],
    # 'Opacity': ['setOpacity', float]
}

_DESIGNER_SETTINGS_PRELOADED_FILES = set()


def _designer_settings_debug_enabled():
    qtdesigner_cfg = CONFIG.get('qtdesigner') or {}
    return bool(qtdesigner_cfg.get('debug_settings_load', False))


def _designer_settings_fail_fast_enabled():
    qtdesigner_cfg = CONFIG.get('qtdesigner') or {}
    return bool(qtdesigner_cfg.get('fail_fast_settings_load', False))


def _designer_settings_log_debug(message, *args):
    if _designer_settings_debug_enabled():
        LOG.info(message, *args)


def _merge_settings_from_config(config_dict):
    if not isinstance(config_dict, dict):
        return

    cfg_settings = config_dict.get('settings', {})
    if not isinstance(cfg_settings, dict):
        return

    for setting_name, setting_kwargs in cfg_settings.items():
        if setting_name in SETTINGS:
            continue
        try:
            addSetting(setting_name, **setting_kwargs)
        except Exception:
            LOG.debug("Unable to preload designer setting '%s'", setting_name, exc_info=True)


def _iter_designer_yaml_candidates(widget=None):
    candidates = []

    env_files = os.getenv('VCP_CONFIG_FILES', '')
    _designer_settings_log_debug("Designer settings preload VCP_CONFIG_FILES=%s", env_files)
    for path in env_files.split(':'):
        if not path:
            continue
        if path.lower().endswith(('.yml', '.yaml')) and os.path.exists(path):
            candidates.append(path)

    # Allow VCP configs to explicitly provide additional YAML files that
    # should be searched for settings in Designer mode.
    qtdesigner_cfg = CONFIG.get('qtdesigner') or {}
    extra_files = qtdesigner_cfg.get('extra_config_files', [])
    if isinstance(extra_files, str):
        extra_files = [extra_files]

    fail_fast = _designer_settings_fail_fast_enabled()
    for path in extra_files:
        if not path:
            continue
        is_yaml = path.lower().endswith(('.yml', '.yaml'))
        exists = os.path.exists(path)
        if is_yaml and exists:
            candidates.append(path)
        else:
            msg = (
                "Configured qtdesigner.extra_config_files entry is invalid: "
                f"path={path!r}, is_yaml={is_yaml}, exists={exists}"
            )
            if fail_fast:
                raise RuntimeError(msg)
            LOG.warning(msg)

    if widget is not None:
        try:
            form_window = QtDesigner.QDesignerFormWindowInterface.findFormWindow(widget)
        except Exception:
            form_window = None

        if form_window is not None:
            ui_path = form_window.fileName() or ''
            if ui_path:
                ui_root, _ = os.path.splitext(ui_path)
                for ext in ('.yml', '.yaml'):
                    yaml_path = ui_root + ext
                    if os.path.exists(yaml_path):
                        candidates.append(yaml_path)

    deduped = []
    seen = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)

    _designer_settings_log_debug("Designer settings preload candidates=%s", deduped)

    return deduped


def _assert_required_settings_present():
    qtdesigner_cfg = CONFIG.get('qtdesigner') or {}

    required_settings = qtdesigner_cfg.get('required_settings', [])
    if isinstance(required_settings, str):
        required_settings = [required_settings]

    required_prefixes = qtdesigner_cfg.get('required_setting_prefixes', [])
    if isinstance(required_prefixes, str):
        required_prefixes = [required_prefixes]

    missing_settings = [name for name in required_settings if name not in SETTINGS]
    missing_prefixes = []
    if required_prefixes:
        all_setting_names = list(SETTINGS.keys())
        for prefix in required_prefixes:
            if not any(name.startswith(prefix) for name in all_setting_names):
                missing_prefixes.append(prefix)

    if missing_settings or missing_prefixes:
        sample = sorted(SETTINGS.keys())[:25]
        raise RuntimeError(
            "Designer settings fail-fast check failed. "
            f"Missing required_settings={missing_settings}, "
            f"missing required_setting_prefixes={missing_prefixes}. "
            f"Loaded settings count={len(SETTINGS)}. "
            f"Sample settings={sample}"
        )


def _ensure_designer_settings_loaded(widget=None):
    """Populate designer settings channels from loaded YAML CONFIG when needed."""
    if not IN_DESIGNER:
        return

    fail_fast = _designer_settings_fail_fast_enabled()
    _designer_settings_log_debug("Designer settings preload start; fail_fast=%s", fail_fast)

    # Trigger plugin auto-load in Designer mode.
    settings_plugin = getPlugin('settings')

    # 1) Merge already-loaded CONFIG settings first.
    _merge_settings_from_config(CONFIG)
    _designer_settings_log_debug("After CONFIG merge, loaded settings=%d", len(SETTINGS))

    # 2) If needed, merge settings from env and inferred yaml candidates.
    for cfg_file in _iter_designer_yaml_candidates(widget):
        if cfg_file in _DESIGNER_SETTINGS_PRELOADED_FILES:
            continue

        try:
            from qtpyvcp.utilities.config_loader import load_config_files
            loaded_cfg = load_config_files(cfg_file, DEFAULT_CONFIG_FILE)
            if isinstance(loaded_cfg, dict):
                CONFIG.update(loaded_cfg)
            _merge_settings_from_config(loaded_cfg)
            _DESIGNER_SETTINGS_PRELOADED_FILES.add(cfg_file)
            cfg_settings = loaded_cfg.get('settings', {}) if isinstance(loaded_cfg, dict) else {}
            cfg_settings_count = len(cfg_settings) if isinstance(cfg_settings, dict) else 0
            _designer_settings_log_debug(
                "Loaded designer settings source: %s (settings=%d, total_loaded=%d)",
                cfg_file,
                cfg_settings_count,
                len(SETTINGS),
            )
        except Exception:
            LOG.exception("Unable to load designer config file '%s'", cfg_file)
            if fail_fast:
                raise

    if fail_fast:
        _assert_required_settings_present()
        _designer_settings_log_debug("Required settings checks passed")

    # Keep plugin channel table synchronized with the global SETTINGS dict.
    if isinstance(settings_plugin, DataPlugin):
        settings_plugin.channels = SETTINGS


def _build_channel_completer_items():
    items = []

    for plugin, obj in iterPlugins():
        if isinstance(obj, DataPlugin):
            for chan_name in obj.channels:
                items.append('{}:{}'.format(plugin, chan_name))

    for setting_name in SETTINGS:
        items.append('settings:{}'.format(setting_name))

    return sorted(set(items))


class RulesEditorExtension(_PluginExtension):
    def __init__(self, widget):
        super(RulesEditorExtension, self).__init__(widget)
        self.widget = widget
        self.addTaskMenuAction("Edit Widget Rules...", self.editAction)

    def editAction(self, state):
        RulesEditor(self.widget, parent=None).exec()


class ChanInfoDialog(QtWidgets.QDialog):
    def __init__(self, info, parent=None):
        super(ChanInfoDialog, self).__init__(parent)
        ui_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "channel_info_dialog.ui")
        file_path = os.path.join(os.path.dirname(__file__), ui_file)
        ui_file = QFile(file_path)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        loaded_ui = loader.load(ui_file, self)
        ui_file.close()

        if isinstance(loaded_ui, QtWidgets.QDialog) and loaded_ui is not self:
            self.setWindowTitle(loaded_ui.windowTitle())
            loaded_layout = loaded_ui.layout()
            if loaded_layout is not None:
                loaded_layout.setParent(self)
                self.setLayout(loaded_layout)
            loaded_ui.deleteLater()
            self.ui = self
        else:
            self.ui = loaded_ui if loaded_ui is not None else self

        self.lbl_chan_name = self.findChild(QtWidgets.QLabel, 'lbl_chan_name')
        self.tb_chan_doc = self.findChild(QtWidgets.QTextBrowser, 'tb_chan_doc')
        self.lbl_chan_rtn = self.findChild(QtWidgets.QLabel, 'lbl_chan_rtn')
        self.lbl_rtn_typ = self.findChild(QtWidgets.QLabel, 'lbl_rtn_typ')
        self.lbl_can_val = self.findChild(QtWidgets.QLabel, 'lbl_can_val')
        self.buttonBox = self.findChild(QtWidgets.QDialogButtonBox, 'buttonBox')

        if self.buttonBox is not None:
            self.buttonBox.accepted.connect(self.accept)
            self.buttonBox.rejected.connect(self.reject)

        ch_obj, ch_exp, ch_val, ch_doc = info

        doc_text = (ch_doc or '').strip()
        doc_lines = [l.strip() for l in doc_text.splitlines() if l.strip()]
        title = doc_lines[0] if doc_lines else 'Data Channel'

        initial_val = ch_val
        if initial_val is None and ch_obj is not None:
            try:
                initial_val = ch_obj.getValue()
            except Exception:
                initial_val = None
        if self.lbl_rtn_typ is not None:
            self.lbl_rtn_typ.setText(type(initial_val).__name__ if initial_val is not None else 'unknown')

        for line in doc_lines:
            if line.startswith(':returns:'):
                if self.lbl_chan_rtn is not None:
                    self.lbl_chan_rtn.setText(line.replace(':returns:', '').strip())
            elif line.startswith(':rtype:'):
                if self.lbl_rtn_typ is not None:
                    self.lbl_rtn_typ.setText(line.replace(':rtype:', '').strip())

        if self.lbl_chan_name is not None:
            self.lbl_chan_name.setText(title)
        if self.tb_chan_doc is not None:
            self.tb_chan_doc.setText(ch_doc or '')
        val = initial_val
        txt = ''
        if self.lbl_rtn_typ is not None and len(self.lbl_rtn_typ.text().split(',')) > 1:
            txt = ', ' + str(ch_val)
        if self.lbl_can_val is not None:
            self.lbl_can_val.setText(str(val) + txt)


class TableCheckButton(QtWidgets.QWidget):
    def __init__(self, checked=False):
        super(TableCheckButton, self).__init__()
        self.chk_bx = QtWidgets.QCheckBox()
        self.chk_bx.setChecked(checked)
        lay_out = QtWidgets.QHBoxLayout(self)
        lay_out.addWidget(self.chk_bx)
        lay_out.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lay_out.setContentsMargins(0, 0, 0, 0)
        self.setLayout(lay_out)

    def __getattr__(self, attr):
        return getattr(self.chk_bx, attr)


class CompleterDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(CompleterDelegate, self).__init__(parent)

        _ensure_designer_settings_loaded()

        self.completer = QtWidgets.QCompleter(_build_channel_completer_items())
        self.completer.setCompletionColumn(0)
        self.completer.setCompletionRole(QtCore.Qt.ItemDataRole.EditRole)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

    def createEditor(self, parent, option, index):
        # Refresh items so late-loaded settings appear without restarting Designer.
        _ensure_designer_settings_loaded()
        self.completer.setModel(QtCore.QStringListModel(_build_channel_completer_items(), self.completer))

        editor = QtWidgets.QLineEdit(parent)
        editor.setFrame(False)
        editor.setCompleter(self.completer)
        return editor


class RulesEditor(QtWidgets.QDialog):
    """QDialog for user-friendly editing of widget Rules in Qt Designer.

    Args:
        widget (QtPyVCPWidget) : The widget for which we want to edit the
            `rules` property.
    """

    def __init__(self, widget, parent=None):
        super(RulesEditor, self).__init__(parent)

        self.widget = widget
        self.app = QtWidgets.QApplication.instance()

        _ensure_designer_settings_loaded(self.widget)

        if IN_DESIGNER:
            getPlugin('status')  # trigger designer plugin initialization

        self.lst_rule_item = None
        self.loading_data = False

        self.available_properties = widget.RULE_PROPERTIES
        self.default_property = widget.DEFAULT_RULE_PROPERTY

        self.setup_ui()

        try:
            self.rules = json.loads(widget.rules)
        except Exception:
            self.rules = []

        for ac in self.rules:
            self.lst_rules.addItem(ac.get("name", ''))

    def setup_ui(self):
        """Create the UI elements for the form."""

        self.setWindowTitle("QtPyVCP Widget Rules Editor")
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins(5, 5, 5, 5)
        vlayout.setSpacing(5)
        self.setLayout(vlayout)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setSpacing(5)
        vlayout.addLayout(hlayout)

        # Creating the widgets for the String List and
        # buttons to add and remove actions
        list_frame = QtWidgets.QFrame(parent=self)
        list_frame.setMinimumHeight(300)
        list_frame.setMinimumWidth(240)
        list_frame.setLineWidth(1)
        list_frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        list_frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        lf_layout = QtWidgets.QVBoxLayout()
        list_frame.setLayout(lf_layout)

        lf_btn_layout = QtWidgets.QHBoxLayout()
        lf_btn_layout.setContentsMargins(0, 0, 0, 0)
        lf_btn_layout.setSpacing(5)

        self.btn_add_rule = QtWidgets.QPushButton(parent=self)
        self.btn_add_rule.setAutoDefault(False)
        self.btn_add_rule.setDefault(False)
        self.btn_add_rule.setText("Add Rule")
        self.btn_add_rule.clicked.connect(self.add_rule)

        self.btn_del_rule = QtWidgets.QPushButton(parent=self)
        self.btn_del_rule.setAutoDefault(False)
        self.btn_del_rule.setDefault(False)
        self.btn_del_rule.setText("Remove Rule")
        self.btn_del_rule.clicked.connect(self.del_rule)

        lf_btn_layout.addWidget(self.btn_add_rule)
        lf_btn_layout.addWidget(self.btn_del_rule)

        lf_layout.addLayout(lf_btn_layout)

        self.lst_rules = QtWidgets.QListWidget()
        self.lst_rules.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding))
        self.lst_rules.itemSelectionChanged.connect(self.load_from_list)
        lf_layout.addWidget(self.lst_rules)

        hlayout.addWidget(list_frame)

        # open help button
        btn_help = QtWidgets.QPushButton()
        btn_help.setAutoDefault(False)
        btn_help.setDefault(False)
        btn_help.setText("Help")
        btn_help.setStyleSheet("background-color: rgb(176, 227, 255);")
        btn_help.clicked.connect(functools.partial(self.open_help, open=True))

        # save button
        save_btn = QtWidgets.QPushButton("Save", parent=self)
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        save_btn.clicked.connect(self.saveChanges)

        # cancel button
        cancel_btn = QtWidgets.QPushButton("Cancel", parent=self)
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.cancelChanges)

        # add buttons to layout
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(btn_help)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)

        vlayout.addLayout(buttons_layout)

        # Creating the widgets that we will use to compose the
        # rule parameters
        self.frm_edit = QtWidgets.QFrame()
        self.frm_edit.setEnabled(False)
        self.frm_edit.setLineWidth(1)
        self.frm_edit.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frm_edit.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)

        frm_edit_layout = QtWidgets.QVBoxLayout()
        self.frm_edit.setLayout(frm_edit_layout)

        hlayout.addWidget(self.frm_edit)

        edit_name_layout = QtWidgets.QFormLayout()
        edit_name_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        lbl_name = QtWidgets.QLabel("Rule Name:")
        self.txt_name = QtWidgets.QLineEdit()
        self.txt_name.editingFinished.connect(self.name_changed)
        edit_name_layout.addRow(lbl_name, self.txt_name)
        lbl_property = QtWidgets.QLabel("Property:")
        self.cmb_property = QtWidgets.QComboBox()
        for name, prop in list(self.available_properties.items()):
            self.cmb_property.addItem(name, prop)
        self.cmb_property.model().sort(0)
        edit_name_layout.addRow(lbl_property, self.cmb_property)

        frm_edit_layout.addLayout(edit_name_layout)

        btn_add_remove_layout = QtWidgets.QHBoxLayout()
        self.btn_add_channel = QtWidgets.QPushButton()
        self.btn_add_channel.setAutoDefault(False)
        self.btn_add_channel.setDefault(False)
        self.btn_add_channel.setText("Add Channel")
        self.btn_add_channel.setIconSize(QtCore.QSize(16, 16))
        self.btn_add_channel.clicked.connect(self.add_channel)
        self.btn_del_channel = QtWidgets.QPushButton()
        self.btn_del_channel.setAutoDefault(False)
        self.btn_del_channel.setDefault(False)
        self.btn_del_channel.setText("Remove Channel")
        self.btn_del_channel.setIconSize(QtCore.QSize(16, 16))
        self.btn_del_channel.clicked.connect(self.del_channel)
        btn_add_remove_layout.addWidget(self.btn_add_channel)
        btn_add_remove_layout.addWidget(self.btn_del_channel)

        frm_edit_layout.addLayout(btn_add_remove_layout)

        self.tbl_channels = QtWidgets.QTableWidget()
        self.tbl_channels.setMinimumWidth(350)
        self.tbl_channels.setShowGrid(True)
        self.tbl_channels.setCornerButtonEnabled(False)
        delegate = CompleterDelegate(self.tbl_channels)
        self.tbl_channels.setItemDelegateForColumn(0, delegate)
        self.tbl_channels.model().dataChanged.connect(self.tbl_channels_changed)
        headers = ["Channel", "Trigger", "Type"]
        self.tbl_channels.setColumnCount(len(headers))
        self.tbl_channels.setHorizontalHeaderLabels(headers)
        header = self.tbl_channels.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        # header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_channels.setColumnWidth(3, 8)

        frm_edit_layout.addWidget(self.tbl_channels)

        expression_layout = QtWidgets.QFormLayout()
        expression_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        lbl_expected = QtWidgets.QLabel("Exp Type:")
        self.lbl_expected_type = QtWidgets.QLabel(parent=self)
        # self.lbl_expected_type.setText("")
        self.lbl_expected_type.setStyleSheet("color: rgb(0, 128, 255); font-weight: bold;")

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.lbl_expected_type)
        hbox.addStretch()
        self.btn_chan_info = QtWidgets.QPushButton("Info ...")
        self.btn_chan_info.setAutoDefault(False)
        self.btn_chan_info.pressed.connect(self.show_chan_info)
        hbox.addWidget(self.btn_chan_info)

        expression_layout.addRow(lbl_expected, hbox)

        lbl_expression = QtWidgets.QLabel("Expression:")
        expr_help_layout = QtWidgets.QHBoxLayout()
        self.txt_expression = QtWidgets.QLineEdit()
        self.txt_expression.textChanged.connect(self.expression_changed)
        self.txt_expression.editingFinished.connect(self.expression_changed)
        expr_help_layout.addWidget(self.txt_expression)
        expression_layout.addRow(lbl_expression, expr_help_layout)

        self.cmb_property.currentIndexChanged.connect(self.property_changed)
        self.cmb_property.setCurrentText(self.default_property)

        frm_edit_layout.addLayout(expression_layout)

    def clear_form(self):
        """Clear the form and reset the fields."""
        self.loading_data = True
        self.lst_rule_item = None
        self.txt_name.setText("")
        self.cmb_property.setCurrentIndex(-1)
        self.tbl_channels.clearContents()
        self.txt_expression.setText("")
        self.frm_edit.setEnabled(False)
        self.loading_data = False

    def load_from_list(self):
        """Load an entry from the list into the editing form."""
        item = self.lst_rules.currentItem()
        idx = self.lst_rules.indexFromItem(item).row()

        if idx < 0:
            return

        self.loading_data = True
        self.lst_rule_item = item
        data = self.rules[idx]
        self.txt_name.setText(data.get('name', ''))
        prop = data.get('property', '')
        self.cmb_property.setCurrentText(prop)
        self.property_changed(0)
        self.txt_expression.setText(data.get('expression', ''))
        self.txt_expression.setEnabled(
            self.available_properties.get(prop, ['None', None])[1] is not None)


        channels = data.get('channels', [])
        self.tbl_channels.clearContents()
        self.tbl_channels.setRowCount(len(channels))
        vlabel = [str(i) for i in range(len(channels))]
        self.tbl_channels.setVerticalHeaderLabels(vlabel)
        for row, ch in enumerate(channels):
            ch_name = ch.get('url', '')
            ch_tr = ch.get('trigger', False)
            ch_obj, ch_exp, ch_val, ch_desc = self.get_channel_data(ch_name)
            self.tbl_channels.setItem(row, 0,
                                      QtWidgets.QTableWidgetItem(str(ch_name)))

            tr_chk = TableCheckButton(checked=ch_tr)
            self.tbl_channels.setCellWidget(row, 1, tr_chk)

            typ_lbl = QtWidgets.QLabel()
            typ_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

            if ch_val is None:
                typ_lbl.setText("<font color='red'>error</font>")
            else:
                typ_lbl.setText("<font color='green'>{}</font>".format(type(ch_val).__name__))
            self.tbl_channels.setCellWidget(row, 2, typ_lbl)

        self.frm_edit.setEnabled(True)
        self.loading_data = False

    def add_rule(self):
        """Add a new rule to the list of rules."""
        default_name = "New Rule"
        data = {"name": default_name,
                "property": self.default_property,
                "expression": "",
                "channels": []
                }
        self.rules.append(data)
        self.lst_rule_item = QtWidgets.QListWidgetItem()
        self.lst_rule_item.setText(default_name)
        self.lst_rules.addItem(self.lst_rule_item)
        self.lst_rules.setCurrentItem(self.lst_rule_item)
        self.load_from_list()
        self.txt_name.setFocus()

    def get_current_index(self):
        """
        Calculate and return the selected index from the list of rules.

        Returns:
            int : The index selected in the rules list or -1 if the item
                does not exist.
        """
        if self.lst_rule_item is None:
            return -1
        return self.lst_rules.indexFromItem(self.lst_rule_item).row()

    def change_entry(self, entry, value):
        """Change an entry in the rules dictionary.

        Args:
            entry (str) : The key for the dictionary
            value (any) : The value to set on the key. It can be any type,
                depending on the key.
        """
        idx = self.get_current_index()
        self.rules[idx][entry] = value

    def del_rule(self):
        """Delete the rule selected in the rules list."""
        idx = self.get_current_index()
        if idx < 0:
            return
        name = self.lst_rule_item.text()

        confirm_message = "Are you sure you want to delete Rule: {}?".format(
            name)
        reply = QtWidgets.QMessageBox().question(self, 'Message',
                                             confirm_message,
                                             QtWidgets.QMessageBox.StandardButton.Yes,
                                             QtWidgets.QMessageBox.StandardButton.No)

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.lst_rules.takeItem(idx)
            self.lst_rules.clearSelection()
            self.rules.pop(idx)
            self.clear_form()

    def add_channel(self):
        """Add a new empty channel to the table."""
        self.loading_data = True

        # Make the first entry be checked as suggestion
        if self.tbl_channels.rowCount() == 0:
            state = True
        else:
            state = False

        self.tbl_channels.insertRow(self.tbl_channels.rowCount())
        row = self.tbl_channels.rowCount() - 1
        self.tbl_channels.setItem(row, 0, QtWidgets.QTableWidgetItem(""))
        checkBoxItem = TableCheckButton(checked=state)
        self.tbl_channels.setCellWidget(row, 1, checkBoxItem)
        typ_lbl = QtWidgets.QLabel()
        typ_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tbl_channels.setCellWidget(row, 2, typ_lbl)
        vlabel = [str(i) for i in range(self.tbl_channels.rowCount())]
        self.tbl_channels.setVerticalHeaderLabels(vlabel)
        self.loading_data = False
        self.update_channels()

    def del_channel(self):
        """Delete the selected channel at the table."""
        items = self.tbl_channels.selectedIndexes()
        if len(items) == 0:
            return

        c = "channel" if len(items) == 1 else "channels"
        confirm_message = "Delete the selected {}?".format(c)
        reply = QtWidgets.QMessageBox().question(self, 'Message',
                                             confirm_message,
                                             QtWidgets.QMessageBox.StandardButton.Yes,
                                             QtWidgets.QMessageBox.StandardButton.No)

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            for itm in reversed(items):
                row = itm.row()
                self.tbl_channels.removeRow(row)

        self.update_channels()

    def open_help(self, open=True):
        """Open the Help context for Rules.

        The documentation website prefix is given by the `QTPYVCP_DOCS_URL`
        environmnet variable. If not defined it defaults to
        `https://kcjengr.github.io/qtpyvcp`

        Args:
            open (bool) : Whether or not to open the page in a web browser.
        """
        docs_url = os.getenv("QTPYVCP_DOCS_URL", None)
        if docs_url is None:
            docs_url = "https://kcjengr.github.io/qtpyvcp"
        expression_url = "tutorials/widget_rules.html"
        help_url = "{}/{}".format(docs_url, expression_url)
        if open:
            webbrowser.open(help_url, new=2, autoraise=True)
        else:
            return help_url

    def show_chan_info(self):
        selection = self.tbl_channels.selectedIndexes()
        if len(selection) > 0:
            row = selection[0].row()
            model = self.tbl_channels.model()
            chan = model.data(model.index(row, 0))
            info = self.get_channel_data(chan)
            ChanInfoDialog(info).exec()

    def name_changed(self):
        """Callback executed when the rule name is changed."""
        self.lst_rule_item.setText(self.txt_name.text())
        self.change_entry("name", self.txt_name.text())

    def property_changed(self, index):
        """Callback executed when the property is selected."""
        try:
            prop = self.cmb_property.currentData()
            if prop[1] is None:
                self.lbl_expected_type.setText("None")
                self.txt_expression.setEnabled(False)
                self.txt_expression.setToolTip("Expression not used with the 'None' property rule.")
            else:
                self.lbl_expected_type.setText(prop[1].__name__)
                self.txt_expression.setEnabled(True)
            self.change_entry("property", self.cmb_property.currentText())
        except Exception as e:
            print(("error", e))
            self.lbl_expected_type.setText("")

    def tbl_channels_changed(self, table_item):
        """Callback executed when the channels in the table are modified."""
        if self.loading_data:
            return

        row = table_item.row()
        ch_name = table_item.data()
        ch_obj, ch_exp, ch_val, ch_desc = self.get_channel_data(ch_name)

        typ_lbl = self.tbl_channels.cellWidget(row, 2)

        if isinstance(ch_obj, (DataChannel, Setting)) and ch_val is not None:
            typ_lbl.setText("<font color='green'>{}</font>"
                            .format(type(ch_val).__name__))
        else:
            typ_lbl.setText("<font color='red'>error</font>")

        self.update_channels()

    def update_channels(self):
        """Update the JSON format chanels to match the data in the table."""

        new_channels = []

        for row in range(self.tbl_channels.rowCount()):
            ch = self.tbl_channels.item(row, 0).text()
            tr = self.tbl_channels.cellWidget(row, 1).isChecked()
            new_channels.append({"url": ch, "trigger": tr})

        self.change_entry("channels", new_channels)

    def get_channel_data(self, url):

        protocol, sep, item = url.partition(':')
        if protocol == 'settings':
            _ensure_designer_settings_loaded()

        try:
            plugin = getPlugin(protocol)
        except ValueError:
            return None, None, None, None

        chan_obj, chan_exp = plugin.getChannel(item)
        if chan_obj is not None:
            chan_val = chan_exp()
        else:
            chan_val = None

        return chan_obj, chan_exp, chan_val, chan_obj.__doc__

    def expression_changed(self, _=None):
        """Callback executed when the expression is modified."""
        self.change_entry("expression", self.txt_expression.text())

    def is_data_valid(self):
        """
        Sanity check the form data.

        Returns:
            tuple (bool, str) : True and "" in case there is no error or False
                and the error message otherwise.
        """
        errors = []
        params = read_parameter_values()
        param = lambda number, default=0.0: get_parameter_value(params, number, default)
        for idx, rule in enumerate(self.rules):
            name = rule.get("name")
            prop = rule.get("property")
            expression = rule.get("expression")
            channels = rule.get("channels", [])

            channel_values = []

            if name is None or name == "":
                errors.append("Rule #{} has no name.".format(idx))

            if len(channels) == 0:
                errors.append("Rule #{} has no channel.".format(idx))

            if self.available_properties[prop][1] is None:
                # No need to check anything else.
                break

            if expression is None or expression == "":
                errors.append("Rule #{} has no expression.".format(idx))
            else:
                found_trigger = False
                for ch_idx, ch in enumerate(channels):

                    if not ch.get("url", ""):
                        errors.append("Rule #{} - Ch. #{} has no channel.".format(idx, ch_idx))

                    if ch.get("trigger", False) and not found_trigger:
                        found_trigger = True

                    # get chan values for use when checking expression
                    ch_obj, ch_exp, ch_val, ch_desc = self.get_channel_data(ch.get("url", ""))

                    if isinstance(ch_obj, (DataChannel, Setting)):
                        channel_values.append(ch_exp())
                    else:
                        errors.append("Rule #{} is not a valid channel.".format(idx))
                        continue

                if not found_trigger:
                    errors.append(
                        "Rule #{} has no trigger channel.".format(idx))

            try:
                # check python expression
                value = eval(expression, {
                    'ch': channel_values,
                    'params': params,
                    'param': param,
                })

                # check return type
                exp_typ = self.available_properties[prop][1]
                act_typ = type(value)
                if act_typ != exp_typ:
                    errors.append("Rule #{} expression returned '{}', but expected '{}'."
                                  .format(idx + 1, act_typ.__name__, exp_typ.__name__))

            except Exception as e:
                LOG.exception("Error evaluating Rule #{} expression. Exception was: {}".format(idx, e))
                errors.append("Rule #{} expression is not valid.\n{}".format(idx, e))

        if len(errors) > 0:
            error_msg = os.linesep.join(errors)
            return False, error_msg

        return True, ""

    @QtCore.Slot()
    def saveChanges(self):
        """Save the new rules at the widget `rules` property."""
        # If the form is being edited, we make sure self.rules has all the
        # latest values from the form before we try to validate.  This fixes
        # a problem where the last form item changed wouldn't get saved unless
        # the user knew to hit 'enter' or leave the field to end editing before
        # hitting save.
        if self.frm_edit.isEnabled():
            self.expression_changed()
            self.name_changed()
            self.update_channels()
        is_valid, message = self.is_data_valid()
        if is_valid:
            data = json.dumps(self.rules)
            formWindow = QtDesigner.QDesignerFormWindowInterface.findFormWindow(self.widget)
            if not formWindow:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error Saving",
                    "Unable to save widget rules because no Designer form window was found.",
                    QtWidgets.QMessageBox.StandardButton.Ok,
                )
                LOG.error("Rules save aborted: no form window for widget '%s'", self.widget.objectName())
                return

            cursor = formWindow.cursor()

            # Prefer explicit widget-targeted property updates.
            try:
                prop_set = cursor.setWidgetProperty(self.widget, "rules", data)
            except TypeError:
                # Compatibility fallback for Qt bindings that may not expose
                # setWidgetProperty with this signature.
                prop_set = cursor.setProperty("rules", data)

            if prop_set is False:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error Saving",
                    "Designer rejected the rules property update.",
                    QtWidgets.QMessageBox.StandardButton.Ok,
                )
                LOG.error("Rules save failed: setProperty returned False for widget '%s'", self.widget.objectName())
                return

            # Mirror value to the live widget for immediate editor feedback.
            self.widget.setProperty("rules", data)

            # Force persistence in the .ui XML as a reliability fallback for
            # custom widget properties under some Designer/Qt6 combinations.
            self._persist_rules_to_form_contents(formWindow, data)

            formWindow.setDirty(True)

            self.accept()
        else:
            QtWidgets.QMessageBox.critical(self, "Error Saving", message,
                                       QtWidgets.QMessageBox.StandardButton.Ok)

    def _persist_rules_to_form_contents(self, form_window, rules_json):
        """Persist the widget rules property directly into form XML contents."""
        try:
            ui_text = form_window.contents()
            ui_text = ui_text if isinstance(ui_text, str) else str(ui_text)

            widget_name = self.widget.objectName()
            pattern = (
                r'(<widget\\b(?=[^>]*\\bname="' + re.escape(widget_name) + r'")[^>]*>)'
                r'(.*?)'
                r'(</widget>)'
            )
            match = re.search(pattern, ui_text, flags=re.DOTALL)
            if not match:
                LOG.debug("Rules XML persistence skipped: widget '%s' block not found", widget_name)
                return

            opening_tag, body, closing_tag = match.groups()

            escaped_rules = html.escape(rules_json, quote=True)

            # Reuse existing property indentation if present.
            indent_match = re.search(r'\\n(\\s*)<property\\b', body)
            indent = indent_match.group(1) if indent_match else '      '

            prop_block = (
                f"\\n{indent}<property name=\"rules\" stdset=\"0\">"
                f"\\n{indent} <string>{escaped_rules}</string>"
                f"\\n{indent}</property>"
            )

            if re.search(r'<property\\s+name="rules"[^>]*>.*?</property>', body, flags=re.DOTALL):
                body = re.sub(
                    r'<property\\s+name="rules"[^>]*>.*?</property>',
                    prop_block.strip(),
                    body,
                    count=1,
                    flags=re.DOTALL,
                )
            else:
                body = prop_block + body

            new_block = opening_tag + body + closing_tag
            start, end = match.span()
            new_text = ui_text[:start] + new_block + ui_text[end:]

            if new_text != ui_text:
                form_window.beginCommand("Persist Widget Rules")
                form_window.setContents(new_text)
                form_window.endCommand()
        except Exception:
            try:
                form_window.endCommand()
            except Exception:
                pass
            LOG.debug("Rules XML persistence fallback failed", exc_info=True)

    @QtCore.Slot()
    def cancelChanges(self):
        """Abort the changes and close the dialog."""
        self.close()
