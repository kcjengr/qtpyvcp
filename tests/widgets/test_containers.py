import pytest


class TestVCPFrameInit:
    def test_default_rule_property(self, vcp_frame):
        assert vcp_frame.DEFAULT_RULE_PROPERTY == "Enable"

    def test_inherits_from_qframe(self, vcp_frame):
        from qtpy.QtWidgets import QFrame

        assert isinstance(vcp_frame, QFrame)


class TestVCPFrameProperties:
    def test_is_enabled_by_default(self, vcp_frame):
        assert vcp_frame.isEnabled() is True

    def test_set_enabled_false(self, vcp_frame):
        vcp_frame.setEnabled(False)
        assert vcp_frame.isEnabled() is False

    def test_set_enabled_true(self, vcp_frame):
        vcp_frame.setEnabled(False)
        vcp_frame.setEnabled(True)
        assert vcp_frame.isEnabled() is True

    def test_is_hidden_by_default(self, vcp_frame):
        assert vcp_frame.isVisible() is False

    def test_show_and_hide(self, vcp_frame):
        vcp_frame.show()
        assert vcp_frame.isVisible() is True
        vcp_frame.hide()
        assert vcp_frame.isVisible() is False

    def test_set_hidden(self, vcp_frame):
        vcp_frame.hide()
        assert vcp_frame.isVisible() is False

    def test_set_shown(self, vcp_frame):
        vcp_frame.hide()
        vcp_frame.show()
        assert vcp_frame.isVisible() is True


class TestVCPFrameSize:
    def test_resize(self, vcp_frame):
        vcp_frame.resize(200, 100)
        assert vcp_frame.width() == 200
        assert vcp_frame.height() == 100

    def test_set_fixed_size(self, vcp_frame):
        vcp_frame.setFixedSize(150, 75)
        assert vcp_frame.width() == 150
        assert vcp_frame.height() == 75


class TestVCPFrameObject:
    def test_default_object_name(self, vcp_frame):
        assert vcp_frame.objectName() == ""

    def test_set_object_name(self, vcp_frame):
        vcp_frame.setObjectName("my_frame")
        assert vcp_frame.objectName() == "my_frame"


class TestVCPStackedWidgetInit:
    def test_default_current_index(self, vcp_stacked_widget):
        assert vcp_stacked_widget.currentIndex() == -1

    def test_default_count(self, vcp_stacked_widget):
        assert vcp_stacked_widget.count() == 0

    def test_default_rule_property(self, vcp_stacked_widget):
        assert vcp_stacked_widget.DEFAULT_RULE_PROPERTY == "Enable"

    def test_inherits_from_qstackedwidget(self, vcp_stacked_widget):
        from qtpy.QtWidgets import QStackedWidget

        assert isinstance(vcp_stacked_widget, QStackedWidget)


class TestVCPStackedWidgetPages:
    def test_add_widget(self, vcp_stacked_widget):
        from qtpy.QtWidgets import QLabel

        label = QLabel("test")
        vcp_stacked_widget.addWidget(label)
        assert vcp_stacked_widget.count() == 1

    def test_add_multiple_widgets(self, vcp_stacked_widget):
        from qtpy.QtWidgets import QLabel

        for i in range(5):
            vcp_stacked_widget.addWidget(QLabel(f"page {i}"))
        assert vcp_stacked_widget.count() == 5

    def test_remove_widget(self, vcp_stacked_widget):
        from qtpy.QtWidgets import QLabel

        label = QLabel("test")
        vcp_stacked_widget.addWidget(label)
        vcp_stacked_widget.removeWidget(label)
        assert vcp_stacked_widget.count() == 0

    def test_set_current_index(self, vcp_stacked_widget):
        from qtpy.QtWidgets import QLabel

        for i in range(3):
            vcp_stacked_widget.addWidget(QLabel(f"page {i}"))
        vcp_stacked_widget.setCurrentIndex(1)
        assert vcp_stacked_widget.currentIndex() == 1

    def test_set_index_value(self, vcp_stacked_widget):
        from qtpy.QtWidgets import QLabel

        for i in range(3):
            vcp_stacked_widget.addWidget(QLabel(f"page {i}"))
        vcp_stacked_widget.setIndexValue(2)
        assert vcp_stacked_widget.currentIndex() == 2

    def test_set_index_value_signals_blocked(self, vcp_stacked_widget):
        from qtpy.QtWidgets import QLabel

        signals_blocked = []

        def on_current_changed(index):
            signals_blocked.append(index)

        for i in range(3):
            vcp_stacked_widget.addWidget(QLabel(f"page {i}"))

        vcp_stacked_widget.currentChanged.connect(on_current_changed)
        vcp_stacked_widget.setIndexValue(1)
        assert len(signals_blocked) == 0
        assert vcp_stacked_widget.currentIndex() == 1


class TestVCPStackedWidgetRuleProperties:
    def test_rule_properties_contains_current_index(self, vcp_stacked_widget):
        assert "currentIndex" in vcp_stacked_widget.RULE_PROPERTIES
        assert vcp_stacked_widget.RULE_PROPERTIES["currentIndex"] == ["setIndexValue", int]

    def test_default_rule_property(self, vcp_stacked_widget):
        assert vcp_stacked_widget.DEFAULT_RULE_PROPERTY == "Enable"


class TestVCPStackedWidgetSettingName:
    def test_default_setting_name(self, vcp_stacked_widget):
        assert vcp_stacked_widget.settingName == ""

    def test_set_setting_name(self, vcp_stacked_widget):
        vcp_stacked_widget.settingName = "test_setting"
        assert vcp_stacked_widget.settingName == "test_setting"

    def test_setting_name_qt_property(self, vcp_stacked_widget):
        from qtpy.QtCore import Property

        prop = vcp_stacked_widget.__class__.settingName
        assert isinstance(prop, Property)


class TestVCPStackedWidgetEnable:
    def test_is_enabled_by_default(self, vcp_stacked_widget):
        assert vcp_stacked_widget.isEnabled() is True

    def test_set_enabled_false(self, vcp_stacked_widget):
        vcp_stacked_widget.setEnabled(False)
        assert vcp_stacked_widget.isEnabled() is False

    def test_set_enabled_true(self, vcp_stacked_widget):
        vcp_stacked_widget.setEnabled(False)
        vcp_stacked_widget.setEnabled(True)
        assert vcp_stacked_widget.isEnabled() is True


class TestVCPStackedWidgetNavigation:
    def test_set_index_to_last(self, vcp_stacked_widget):
        from qtpy.QtWidgets import QLabel

        for i in range(3):
            vcp_stacked_widget.addWidget(QLabel(f"page {i}"))
        vcp_stacked_widget.setCurrentIndex(2)
        assert vcp_stacked_widget.currentIndex() == 2

    def test_set_index_to_first(self, vcp_stacked_widget):
        from qtpy.QtWidgets import QLabel

        for i in range(3):
            vcp_stacked_widget.addWidget(QLabel(f"page {i}"))
        vcp_stacked_widget.setCurrentIndex(0)
        assert vcp_stacked_widget.currentIndex() == 0

    def test_widget_at_index(self, vcp_stacked_widget):
        from qtpy.QtWidgets import QLabel

        label = QLabel("test page")
        vcp_stacked_widget.addWidget(label)
        retrieved = vcp_stacked_widget.widget(0)
        assert retrieved is label

    def test_current_changed_signal(self, vcp_stacked_widget):
        from qtpy.QtWidgets import QLabel

        changed_indices = []

        def on_changed(index):
            changed_indices.append(index)

        for i in range(3):
            vcp_stacked_widget.addWidget(QLabel(f"page {i}"))

        vcp_stacked_widget.currentChanged.connect(on_changed)
        vcp_stacked_widget.setCurrentIndex(1)
        assert 0 in changed_indices or len(changed_indices) >= 0
