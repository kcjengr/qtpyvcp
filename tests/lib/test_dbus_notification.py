import os
import tempfile
from unittest.mock import patch, MagicMock, PropertyMock
import pytest


class TestUrgency:
    def test_urgency_constants(self):
        from qtpyvcp.lib.dbus_notification import Urgency
        assert Urgency.LOW == 0
        assert Urgency.NORMAL == 1
        assert Urgency.CRITICAL == 2

    def test_urgency_values_are_integers(self):
        from qtpyvcp.lib.dbus_notification import Urgency
        assert isinstance(Urgency.LOW, int)
        assert isinstance(Urgency.NORMAL, int)
        assert isinstance(Urgency.CRITICAL, int)


class TestUninitializedError:
    def test_is_runtime_error_subclass(self):
        from qtpyvcp.lib.dbus_notification import UninitializedError
        assert issubclass(UninitializedError, RuntimeError)

    def test_can_be_raised_and_caught(self):
        from qtpyvcp.lib.dbus_notification import UninitializedError
        with pytest.raises(UninitializedError):
            raise UninitializedError("test message")


@pytest.fixture
def dbus_mock():
    mock_dbus = MagicMock()
    mock_dbus.Byte = MagicMock(side_effect=lambda x: f"Byte({x})")
    mock_dbus.SessionBus = MagicMock()
    mock_bus = MagicMock()
    mock_dbus.SessionBus.return_value = mock_bus
    mock_proxy = MagicMock()
    mock_bus.get_object.return_value = mock_proxy
    mock_iface = MagicMock()
    mock_dbus.Interface.return_value = mock_iface
    mock_iface.Notify.return_value = 1
    mock_iface.CloseNotification = MagicMock()
    mock_iface.connect_to_signal = MagicMock()

    with patch.dict("sys.modules", {"dbus": mock_dbus}):
        with patch("qtpyvcp.lib.dbus_notification.DBusQtMainLoop", None):
            # Force reimport to pick up mocked dbus
            import importlib
            import qtpyvcp.lib.dbus_notification as mod
            # Reset globals
            mod.APP_NAME = ""
            mod.DBUS_IFACE = None
            mod.NOTIFICATIONS.clear()

            mod.DBUS_IFACE = mock_iface
            yield mod


@pytest.fixture
def notification(dbus_mock):
    from qtpyvcp.lib.dbus_notification import DBusNotification
    n = DBusNotification.__new__(DBusNotification)
    n.id = 0
    n.timeout = -1
    n._onNotificationClosed = lambda *args: None
    n.title = ""
    n.body = ""
    n.icon = ""
    n.hints = {}
    n.actions = {}
    n.data = {}
    return n


class TestDBusNotificationInit:
    def test_notification_has_default_attributes(self, dbus_mock):
        from qtpyvcp.lib.dbus_notification import DBusNotification
        n = DBusNotification("TestApp")
        assert n.title == ""
        assert n.body == ""
        assert n.icon == ""
        assert n.timeout == -1
        assert n.hints == {}
        assert n.data == {}

    def test_init_sets_app_name(self, dbus_mock):
        from qtpyvcp.lib.dbus_notification import DBusNotification
        DBusNotification("TestApp")
        assert dbus_mock.APP_NAME == "TestApp"


class TestDBusNotificationShow:
    def test_show_raises_when_uninitialized(self):
        from qtpyvcp.lib.dbus_notification import DBusNotification, UninitializedError
        n = DBusNotification.__new__(DBusNotification)
        n.id = 0
        n.timeout = -1
        n._onNotificationClosed = lambda *args: None
        n.title = ""
        n.body = ""
        n.icon = ""
        n.hints = {}
        n.actions = {}
        n.data = {}

        with patch("qtpyvcp.lib.dbus_notification.DBUS_IFACE", None):
            with pytest.raises(UninitializedError):
                n.show("Title")

    def test_show_calls_dbus_notify(self, notification, dbus_mock):
        result = notification.show("Test Title", "Test Body", "icon.png", 3000)
        assert result is True
        dbus_mock.DBUS_IFACE.Notify.assert_called()

    def test_show_stores_notification_in_global_dict(self, notification, dbus_mock):
        from qtpyvcp.lib.dbus_notification import NOTIFICATIONS
        notification.show("Test Title")
        assert 1 in NOTIFICATIONS
        assert NOTIFICATIONS[1] is notification


class TestDBusNotificationClose:
    def test_close_calls_dbus_interface(self, notification, dbus_mock):
        notification.id = 42
        notification.close()
        dbus_mock.DBUS_IFACE.CloseNotification.assert_called_with(42)

    def test_close_does_nothing_when_id_is_zero(self, notification, dbus_mock):
        notification.id = 0
        notification.close()
        dbus_mock.DBUS_IFACE.CloseNotification.assert_not_called()


class TestDBusNotificationOnClose:
    def test_on_close_sets_callback(self, notification):
        callback_called = []

        def my_callback(*args):
            callback_called.append(args)

        notification.onClose(my_callback)
        notification._onNotificationClosed("arg1", "arg2")
        assert len(callback_called) == 1
        assert callback_called[0] == ("arg1", "arg2")


class TestDBusNotificationSetUrgency:
    def test_set_urgency_normal(self, notification, dbus_mock):
        notification.setUrgency(1)
        assert "urgency" in notification.hints

    def test_set_urgency_low(self, notification, dbus_mock):
        notification.setUrgency(0)
        assert "urgency" in notification.hints

    def test_set_urgency_critical(self, notification, dbus_mock):
        notification.setUrgency(2)
        assert "urgency" in notification.hints

    def test_set_urgency_invalid_raises(self, notification):
        with pytest.raises(ValueError):
            notification.setUrgency(5)

    def test_set_urgency_negative_raises(self, notification):
        with pytest.raises(ValueError):
            notification.setUrgency(-1)


class TestDBusNotificationSetSoundFile:
    def test_set_sound_file_sets_hint_when_file_exists(self, notification, tmp_path):
        sound_file = tmp_path / "sound.wav"
        sound_file.write_text("dummy")
        notification.setSoundFile(str(sound_file))
        assert notification.hints["sound-file"] == str(sound_file)

    def test_set_sound_file_does_nothing_when_file_missing(self, notification):
        notification.setSoundFile("/nonexistent/path/sound.wav")
        assert "sound-file" not in notification.hints


class TestDBusNotificationSetSoundName:
    def test_set_sound_name_sets_hint(self, notification):
        notification.setSoundName("message-new-notification")
        assert notification.hints["sound-name"] == "message-new-notification"


class TestDBusNotificationSetIconPath:
    def test_set_icon_path_as_uri_when_file_exists(self, notification, tmp_path):
        icon_file = tmp_path / "icon.png"
        icon_file.write_text("dummy")
        notification.setIconPath(str(icon_file))
        assert notification.hints["image-path"] == f"file://{icon_file}"

    def test_set_icon_path_as_name_when_file_missing(self, notification):
        notification.setIconPath("dialog-error")
        assert notification.hints["image-path"] == "dialog-error"


class TestDBusNotificationSetQIcon:
    def test_set_qicon_raises_not_implemented(self, notification):
        with pytest.raises(NotImplementedError):
            notification.setQIcon(None)


class TestDBusNotificationSetLocation:
    def test_set_location_sets_x_y_hints(self, notification):
        notification.setLocation(100, 200)
        assert notification.hints["x"] == 100
        assert notification.hints["y"] == 200


class TestDBusNotificationSetCategory:
    def test_set_category_sets_hint(self, notification):
        notification.setCategory("device")
        assert notification.hints["category"] == "device"


class TestDBusNotificationSetTimeout:
    def test_set_timeout_sets_value(self, notification):
        notification.setTimeout(5000)
        assert notification.timeout == 5000

    def test_set_timeout_invalid_type_raises(self, notification):
        with pytest.raises(TypeError):
            notification.setTimeout("3000")


class TestDBusNotificationSetHint:
    def test_set_hint_sets_arbitrary_hint(self, notification):
        notification.setHint("custom-key", "custom-value")
        assert notification.hints["custom-key"] == "custom-value"


class TestDBusNotificationAddAction:
    def test_add_action_stores_in_actions_dict(self, notification):
        def callback(n, a):
            pass

        notification.addAction("help", "Help", callback)
        assert "help" in notification.actions

    def test_add_action_stores_label_callback_and_data(self, notification):
        def callback(n, a):
            pass

        notification.addAction("help", "Help", callback, user_data={"key": "value"})
        label, cb, data = notification.actions["help"]
        assert label == "Help"
        assert cb is callback
        assert data == {"key": "value"}


class TestDBusNotificationMakeActionsList:
    def test_make_actions_list_builds_flat_list(self, notification):
        def cb1(n, a):
            pass

        def cb2(n, a, d):
            pass

        notification.actions = {
            "help": ("Help", cb1, None),
            "ignore": ("Ignore", cb2, 12345),
        }
        result = notification._makeActionsList()
        assert result == ["help", "Help", "ignore", "Ignore"]

    def test_make_actions_list_empty(self, notification):
        notification.actions = {}
        result = notification._makeActionsList()
        assert result == []


class TestDBusNotificationOnActionInvoked:
    def test_on_action_invoked_calls_callback_without_data(self, notification):
        called_with = []

        def callback(n, a):
            called_with.append((n, a))

        notification.actions = {"help": ("Help", callback, None)}
        notification._onActionInvoked("help")
        assert len(called_with) == 1
        assert called_with[0][1] == "help"

    def test_on_action_invoked_calls_callback_with_data(self, notification):
        called_with = []

        def callback(n, a, d):
            called_with.append((n, a, d))

        notification.actions = {"ignore": ("Ignore", callback, 42)}
        notification._onActionInvoked("ignore")
        assert len(called_with) == 1
        assert called_with[0][2] == 42

    def test_on_action_invoked_ignores_unknown_action(self, notification):
        notification.actions = {}
        # Should not raise
        notification._onActionInvoked("unknown")


class TestDBusNotificationSetNotify:
    def test_set_notify_calls_show(self, notification, dbus_mock):
        notification.setNotify("Title", "Body")
        dbus_mock.DBUS_IFACE.Notify.assert_called()
