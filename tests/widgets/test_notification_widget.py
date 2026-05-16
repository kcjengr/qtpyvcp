import pytest


class TestNotificationWidgetInit:
    """Tests for NotificationWidget initialization."""

    def test_widget_created(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget is not None

    def test_has_main_layout(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.main_layout is not None

    def test_has_button_layout(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.button_layout is not None

    def test_all_button_exists(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.all_button is not None

    def test_info_button_exists(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.info_button is not None

    def test_warn_button_exists(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.warn_button is not None

    def test_error_button_exists(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.error_button is not None

    def test_debug_button_exists(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.debug_button is not None

    def test_clear_button_exists(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.clear_button is not None


class TestNotificationWidgetButtons:
    """Tests for NotificationWidget button configuration."""

    def test_all_button_text(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.all_button.text() == "all"

    def test_info_button_text(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.info_button.text() == "info"

    def test_warn_button_text(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.warn_button.text() == "warn"

    def test_error_button_text(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.error_button.text() == "error"

    def test_debug_button_text(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.debug_button.text() == "debug"

    def test_clear_button_text(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.clear_button.text() == "clear"

    def test_all_button_checkable(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.all_button.isCheckable() is True

    def test_info_button_checkable(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.info_button.isCheckable() is True

    def test_warn_button_checkable(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.warn_button.isCheckable() is True

    def test_error_button_checkable(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.error_button.isCheckable() is True

    def test_debug_button_checkable(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.debug_button.isCheckable() is True


class TestNotificationWidgetDefaultState:
    """Tests for NotificationWidget default button states."""

    def test_all_button_checked(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.all_button.isChecked() is True

    def test_info_button_not_checked(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.info_button.isChecked() is False

    def test_warn_button_not_checked(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.warn_button.isChecked() is False

    def test_error_button_not_checked(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.error_button.isChecked() is False

    def test_debug_button_not_checked(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.debug_button.isChecked() is False


class TestNotificationWidgetDisplay:
    """Tests for NotificationWidget display elements."""

    def test_notification_name_label_exists(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.notification_name is not None

    def test_notification_name_default_text(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.notification_name.text() == "All Notifications"

    def test_all_notification_view_exists(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.all_notification_view is not None

    def test_all_notification_model_exists(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.all_notification_model is not None

    def test_all_notification_model_proxy_exists(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.all_notification_model_proxy is not None


class TestNotificationWidgetFiltering:
    """Tests for NotificationWidget filter button behavior."""

    def test_show_all_notifications(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.show_all_notifications()
        assert widget.all_button.isChecked() is True
        assert widget.info_button.isChecked() is False
        assert widget.warn_button.isChecked() is False
        assert widget.error_button.isChecked() is False
        assert widget.debug_button.isChecked() is False

    def test_show_all_sets_title(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.show_all_notifications()
        assert widget.notification_name.text() == "All Notifications"

    def test_show_info_notifications(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.show_info_notifications()
        assert widget.info_button.isChecked() is True
        assert widget.all_button.isChecked() is False

    def test_show_info_sets_title(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.show_info_notifications()
        assert widget.notification_name.text() == "Information Notifications"

    def test_show_warn_notifications(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.show_warn_notifications()
        assert widget.warn_button.isChecked() is True
        assert widget.all_button.isChecked() is False

    def test_show_warn_sets_title(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.show_warn_notifications()
        assert widget.notification_name.text() == "Warning Notifications"

    def test_show_error_notifications(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.show_error_notifications()
        assert widget.error_button.isChecked() is True
        assert widget.all_button.isChecked() is False

    def test_show_error_sets_title(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.show_error_notifications()
        assert widget.notification_name.text() == "Error Notifications"

    def test_show_debug_notifications(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.show_debug_notifications()
        assert widget.debug_button.isChecked() is True
        assert widget.all_button.isChecked() is False

    def test_show_debug_sets_title(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.show_debug_notifications()
        assert widget.notification_name.text() == "Debug Notifications"


class TestNotificationWidgetMessageHandling:
    """Tests for NotificationWidget message handling."""

    def test_on_info_message_adds_item(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.on_info_message("test info message")
        assert widget.all_notification_model.rowCount() > 0

    def test_on_warn_message_adds_item(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.on_warn_message("test warn message")
        assert widget.all_notification_model.rowCount() > 0

    def test_on_error_message_adds_item(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.on_error_message("test error message")
        assert widget.all_notification_model.rowCount() > 0

    def test_on_debug_message_adds_item(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.on_debug_message("test debug message")
        assert widget.all_notification_model.rowCount() > 0

    def test_info_message_contains_prefix(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.on_info_message("test")
        item = widget.all_notification_model.item(0)
        assert "INFO:" in item.text()

    def test_warn_message_contains_prefix(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.on_warn_message("test")
        item = widget.all_notification_model.item(0)
        assert "WARNING:" in item.text()

    def test_error_message_contains_prefix(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.on_error_message("test")
        item = widget.all_notification_model.item(0)
        assert "ERROR:" in item.text()

    def test_debug_message_contains_prefix(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.on_debug_message("test")
        item = widget.all_notification_model.item(0)
        assert "DEBUG" in item.text()

    def test_info_message_contains_time(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.on_info_message("test")
        item = widget.all_notification_model.item(0)
        assert "TIME" in item.text()


class TestNotificationWidgetClear:
    """Tests for NotificationWidget clear functionality."""

    def test_clear_all_cleared(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.on_info_message("test1")
        widget.on_warn_message("test2")
        assert widget.all_notification_model.rowCount() == 2
        widget.clear_all_notifications()
        assert widget.all_notification_model.rowCount() == 0

    def test_clear_button_connected(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.on_info_message("test")
        assert widget.all_notification_model.rowCount() == 1
        widget.clear_button.click()
        assert widget.all_notification_model.rowCount() == 0


class TestNotificationWidgetInheritance:
    """Tests for NotificationWidget inheritance."""

    def test_inherits_from_qwidget(self, qtbot):
        from qtpy.QtWidgets import QWidget
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert isinstance(widget, QWidget)


class TestNotificationWidgetNotifications:
    """Tests for notification channel integration."""

    def test_notification_channel_assigned(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        assert widget.notification_channel is not None

    def test_clear_button_calls_clear_all(self, qtbot):
        from qtpyvcp.widgets.display_widgets.notification_widget import NotificationWidget

        widget = NotificationWidget()
        qtbot.addWidget(widget)
        widget.on_info_message("test")
        widget.clear_all_notifications()
        assert widget.all_notification_model.rowCount() == 0
