import os
import json
import functools
import webbrowser

from qtpy import QtWidgets, QtCore, QtDesigner

import qtpyvcp
from qtpyvcp.plugins import QtPyVCPDataChannel
from plugin_extension import _PluginExtension


# Set up logging
from qtpyvcp.utilities import logger
LOG = logger.getLogger(__name__)

RULE_PROPERTIES = {
    'None': ['None', None],
    'Enable': ['setEnabled', bool],
    'Visible': ['setVisible', bool],
    'Style Class': ['setStyleClass', str],
    # 'Opacity': ['setOpacity', float]
}

class RulesEditorExtension(_PluginExtension):
    def __init__(self, widget):
        super(RulesEditorExtension, self).__init__(widget)
        self.widget = widget
        self.addTaskMenuAction("Edit Widget Rules...", self.editAction)

    def editAction(self, state):
        RulesEditor(self.widget, parent=None).exec_()

class TableCheckButton(QtWidgets.QWidget):
    def __init__(self, checked=False):
        super(TableCheckButton, self).__init__()
        self.chk_bx = QtWidgets.QCheckBox()
        self.chk_bx.setChecked(checked)
        lay_out = QtWidgets.QHBoxLayout(self)
        lay_out.addWidget(self.chk_bx)
        lay_out.setAlignment(QtCore.Qt.AlignCenter)
        lay_out.setContentsMargins(0, 0, 0, 0)
        self.setLayout(lay_out)

    def __getattr__(self, attr):
        return getattr(self.chk_bx, attr)

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

        self.lst_rule_item = None
        self.loading_data = False

        self.available_properties = widget.RULE_PROPERTIES
        self.default_property = widget.DEFAULT_RULE_PROPERTY

        self.setup_ui()

        try:
            self.rules = json.loads(widget.rules)
        except:
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
        list_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        list_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
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
        self.lst_rules.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding))
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
        self.frm_edit.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frm_edit.setFrameShape(QtWidgets.QFrame.StyledPanel)

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
        for name, prop in self.available_properties.items():
            self.cmb_property.addItem(name, prop)
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
        self.tbl_channels.model().dataChanged.connect(self.tbl_channels_changed)
        headers = ["Channel", "Trigger", "Type"]
        self.tbl_channels.setColumnCount(len(headers))
        self.tbl_channels.setHorizontalHeaderLabels(headers)
        header = self.tbl_channels.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        # self.tbl_channels.setColumnWidth(2, 60)

        frm_edit_layout.addWidget(self.tbl_channels)

        expression_layout = QtWidgets.QFormLayout()
        expression_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        lbl_expected = QtWidgets.QLabel("Exp Type:")
        self.lbl_expected_type = QtWidgets.QLabel(parent=self)
        # self.lbl_expected_type.setText("")
        self.lbl_expected_type.setStyleSheet("color: rgb(0, 128, 255); font-weight: bold;")
        expression_layout.addRow(lbl_expected, self.lbl_expected_type)

        lbl_expression = QtWidgets.QLabel("Expression:")
        expr_help_layout = QtWidgets.QHBoxLayout()
        self.txt_expression = QtWidgets.QLineEdit()
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
            ch_obj, ch_val, ch_desc = self.get_channel_data(ch_name)
            self.tbl_channels.setItem(row, 0,
                                      QtWidgets.QTableWidgetItem(str(ch_name)))

            tr_chk = TableCheckButton(checked=ch_tr)
            self.tbl_channels.setCellWidget(row, 1, tr_chk)

            typ_lbl = QtWidgets.QLabel()
            typ_lbl.setAlignment(QtCore.Qt.AlignCenter)
            if ch_val is None:
                typ_lbl.setText("<font color='red'>error</font>")
            else:
                typ_lbl.setText("<font color='green'>{}</font>".format(type(ch_val).__name__))
            self.tbl_channels.setCellWidget(row, 2, typ_lbl)

            # self.tbl_channels.setItem(row, 2, QtWidgets.QTableWidgetItem(type(ch_val).__name__))

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
                                             QtWidgets.QMessageBox.Yes,
                                             QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            self.lst_rules.takeItem(idx)
            self.lst_rules.clearSelection()
            self.rules.pop(idx)
            self.clear_form()

    def add_channel(self):
        """Add a new empty channel to the table."""
        self.loading_data = True

        # Make the first entry be checked as suggestion
        if self.tbl_channels.rowCount() == 0:
            state = QtCore.Qt.Checked
        else:
            state = QtCore.Qt.Unchecked

        self.tbl_channels.insertRow(self.tbl_channels.rowCount())
        row = self.tbl_channels.rowCount() - 1
        self.tbl_channels.setItem(row, 0, QtWidgets.QTableWidgetItem(""))
        checkBoxItem = TableCheckButton(checked=state)
        self.tbl_channels.setCellWidget(row, 1, checkBoxItem)
        typ_lbl = QtWidgets.QLabel()
        typ_lbl.setAlignment(QtCore.Qt.AlignCenter)
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
                                             QtWidgets.QMessageBox.Yes,
                                             QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
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

    def name_changed(self):
        """Callback executed when the rule name is changed."""
        self.lst_rule_item.setText(self.txt_name.text())
        self.change_entry("name", self.txt_name.text())

    def property_changed(self, index):
        """Callback executed when the property is selected."""
        print "prop changed"
        try:
            prop = self.cmb_property.currentData()
            if prop[1] is None:
                self.lbl_expected_type.setText("None")
                self.txt_expression.setEnabled(False)
                self.txt_expression.setToolTip("Expression not used with the 'None' property rule.")
            else:
                self.lbl_expected_type.setText(prop[1].__name__)
                self.txt_expression.setEnabled(True)
            idx = self.get_current_index()
            self.change_entry("property", self.cmb_property.currentText())
        except Exception as e:
            print "error", e
            self.lbl_expected_type.setText("")

    def tbl_channels_changed(self, table_item):
        """Callback executed when the channels in the table are modified."""
        if self.loading_data:
            return

        row = table_item.row()
        ch_name = table_item.data()
        ch_obj, ch_val, ch_desc = self.get_channel_data(ch_name)

        typ_lbl = self.tbl_channels.cellWidget(row, 2)
        if ch_val is None:
            typ_lbl.setText("<font color='red'>error</font>")
        else:
            typ_lbl.setText("<font color='green'>{}</font>".format(type(ch_val).__name__))

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
        chan_obj = None
        chan_val = None
        chan_desc = ''

        try:
            protocol, sep, rest = url.partition(':')
            item, sep, query = rest.partition('?')

            if query == '':
                query = 'value'

            plugin = qtpyvcp.PLUGINS[protocol]
            eval_env = {'plugin': plugin}

            chan_obj = eval("plugin.{}".format(item), eval_env)
            chan_val = chan_obj.handleQuery(query)

        except:
            LOG.exception("Error in eval")

        return chan_obj, chan_val, chan_desc

    def expression_changed(self):
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
                    ch_obj, ch_val, ch_desc = self.get_channel_data(ch.get("url", ""))
                    print ch_obj

                    if isinstance(ch_obj, QtPyVCPDataChannel):
                        channel_values.append(ch_val)
                    else:
                        errors.append("Rule #{} is not a valid channel.".format(idx))
                        continue

                if not found_trigger:
                    errors.append(
                        "Rule #{} has no trigger channel.".format(idx))

            try:
                # check python expression
                value = eval(expression, {'ch': channel_values})

                # check return type
                exp_typ = self.available_properties[prop][1]
                act_typ = type(value)
                if act_typ != exp_typ:
                    errors.append("Rule #{} expression returned '{}', but expected '{}'."
                                  .format(idx + 1, act_typ.__name__, exp_typ.__name__))

            except:
                LOG.exception("Error evaluating Rule #{} expression.".format(idx))
                errors.append("Rule #{} expression is not valid.".format(idx))

        if len(errors) > 0:
            error_msg = os.linesep.join(errors)
            return False, error_msg

        return True, ""

    @QtCore.Slot()
    def saveChanges(self):
        """Save the new rules at the widget `rules` property."""
        # If the form is being edited, we make sure self.rules has all the
        # latest values from the form before we try to validate.  This fixes
        # a problem where the last form item change wouldn't get saved unless
        # the user knew to hit 'enter' or leave the field to end editing before
        # hitting save.
        if self.frm_edit.isEnabled():
            self.expression_changed()
            self.name_changed()
            self.update_channels()
        is_valid, message = self.is_data_valid()
        if is_valid:
            data = json.dumps(self.rules)
            print json.dumps(self.rules, sort_keys=True, indent=4)
            formWindow = QtDesigner.QDesignerFormWindowInterface.findFormWindow(self.widget)
            if formWindow:
                formWindow.cursor().setProperty("rules", data)
            self.accept()
        else:
            QtWidgets.QMessageBox.critical(self, "Error Saving", message,
                                       QtWidgets.QMessageBox.Ok)

    @QtCore.Slot()
    def cancelChanges(self):
        """Abort the changes and close the dialog."""
        self.close()
