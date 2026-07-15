"""Tests for qtpyvcp.plugins.clock.Clock plugin."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from qtpyvcp.plugins.clock import Clock


class TestClockInit:
    def test_initializes_with_time_and_date_channels(self):
        clock = Clock()
        assert 'time' in clock.channels
        assert 'date' in clock.channels

    def test_time_value_is_datetime_on_init(self):
        clock = Clock()
        assert isinstance(clock.time.value, datetime)

    def test_date_value_is_datetime_on_init(self):
        clock = Clock()
        assert isinstance(clock.date.value, datetime)

    def test_time_and_date_values_are_same_on_init(self):
        clock = Clock()
        # Both should be set to the same datetime.now() call
        diff = abs((clock.time.value - clock.date.value).total_seconds())
        assert diff < 1.0

    def test_timer_is_created(self):
        clock = Clock()
        assert clock.timer is not None

    def test_timer_not_running_before_initialise(self):
        clock = Clock()
        assert not clock.timer.isActive()


class TestClockChannels:
    def test_time_channel_returns_value(self):
        clock = Clock()
        result = clock.time.getValue()
        assert isinstance(result, datetime)

    def test_date_channel_returns_value(self):
        clock = Clock()
        result = clock.date.getValue()
        assert isinstance(result, datetime)

    def test_time_channel_string_conversion(self):
        clock = Clock()
        s = clock.time.getString()
        assert isinstance(s, str)

    def test_date_channel_string_conversion(self):
        clock = Clock()
        s = clock.date.getString()
        assert isinstance(s, str)


class TestClockGetChannel:
    def test_getChannel_time(self, qapp):
        clock = Clock()
        chan_obj, chan_exp = clock.getChannel('time')
        assert chan_obj is not None
        assert chan_exp is not None
        assert callable(chan_exp)
        val = chan_exp()
        assert isinstance(val, datetime)

    def test_getChannel_date(self, qapp):
        clock = Clock()
        chan_obj, chan_exp = clock.getChannel('date')
        assert chan_obj is not None
        assert chan_exp is not None
        assert callable(chan_exp)
        val = chan_exp()
        assert isinstance(val, datetime)

    def test_getChannel_time_with_string_format(self, qapp):
        clock = Clock()
        _, chan_exp = clock.getChannel('time?string')
        result = chan_exp()
        assert isinstance(result, str)

    def test_getChannel_date_with_string_format(self, qapp):
        clock = Clock()
        _, chan_exp = clock.getChannel('date?string')
        result = chan_exp()
        assert isinstance(result, str)

    def test_getChannel_time_with_custom_format(self, qapp):
        clock = Clock()
        _, chan_exp = clock.getChannel('time?string&format=%S')
        result = chan_exp()
        # Should be a two-digit seconds string
        assert len(result) == 2
        assert result.isdigit()

    def test_getChannel_date_with_custom_format(self, qapp):
        clock = Clock()
        _, chan_exp = clock.getChannel('date?string&format=%Y')
        result = chan_exp()
        # Should be a four-digit year string
        assert len(result) == 4
        assert result.isdigit()

    def test_getChannel_returns_none_for_missing(self, qapp):
        clock = Clock()
        chan_obj, chan_exp = clock.getChannel('nonexistent')
        assert chan_obj is None
        assert chan_exp is None


class TestClockToString:
    def test_time_default_format(self):
        clock = Clock()
        # Default format: %I:%M:%S %p (e.g., "02:30:45 PM")
        s = clock.time.getString()
        assert isinstance(s, str)

    def test_time_custom_format_via_getstring(self):
        clock = Clock()
        s = clock.time.getString(format="%Y-%m-%d %H:%M:%S")
        assert '-' in s

    def test_date_default_format(self):
        clock = Clock()
        s = clock.date.getString()
        assert isinstance(s, str)

    def test_date_custom_format_via_getstring(self):
        clock = Clock()
        s = clock.date.getString(format="%d/%m/%Y")
        # Should be DD/MM/YYYY format
        parts = s.split('/')
        assert len(parts) == 3
        assert len(parts[0]) == 2
        assert len(parts[1]) == 2
        assert len(parts[2]) == 4

    def test_time_format_hour_am_pm(self):
        clock = Clock()
        s = clock.time.getString(format="%I:%M %p")
        # Should contain AM or PM

        # Normalize locale-dependent AM/PM formatting: glibc >=2.40 may use
        # narrow non-breaking spaces (U+202F) and dots (e.g. "p.\u202fm.")
        s_normalized = s.replace('\u202f', '').replace('.', '').upper()
        assert 'AM' in s_normalized or 'PM' in s_normalized

class TestClockTick:
    def test_tick_updates_time_value(self):
        clock = Clock()
        old_time = clock.time.value
        clock.tick()
        new_time = clock.time.value
        # Value should have changed (or at least be valid datetime)
        assert isinstance(new_time, datetime)

    def test_tick_updates_date_value(self):
        clock = Clock()
        old_date = clock.date.value
        clock.tick()
        new_date = clock.date.value
        assert isinstance(new_date, datetime)

    def test_tick_sets_current_datetime(self):
        clock = Clock()
        clock.tick()
        now = datetime.now()
        diff = abs((clock.time.value - now).total_seconds())
        assert diff < 2.0


class TestClockInitialise:
    def test_initialise_starts_timer(self):
        clock = Clock()
        clock.initialise()
        assert clock.timer.isActive()

    def test_initialise_starts_with_1000ms_interval(self):
        clock = Clock()
        clock.initialise()
        assert clock.timer.interval() == 1000


class TestClockSignalNotifications:
    def test_time_notify_receives_updates(self, qapp):
        clock = Clock()
        received = []
        clock.time.notify(received.append)
        clock.tick()
        assert len(received) >= 1

    def test_date_notify_receives_updates(self, qapp):
        clock = Clock()
        received = []
        clock.date.notify(received.append)
        clock.tick()
        assert len(received) >= 1


class TestClockChannelValues:
    def test_time_value_can_be_set(self, qapp):
        clock = Clock()
        new_time = datetime(2025, 6, 15, 10, 30, 0)
        clock.time.setValue(new_time)
        assert clock.time.value == new_time

    def test_date_value_can_be_set(self, qapp):
        clock = Clock()
        new_date = datetime(2025, 12, 25)
        clock.date.setValue(new_date)
        assert clock.date.value == new_date

    def test_time_string_after_set(self):
        clock = Clock()
        custom = datetime(2025, 3, 1, 9, 5, 3)
        clock.time.setValue(custom)
        s = clock.time.getString()
        assert isinstance(s, str)

    def test_date_string_after_set(self):
        clock = Clock()
        custom = datetime(2025, 7, 4, 12, 0, 0)
        clock.date.setValue(custom)
        s = clock.date.getString()
        assert isinstance(s, str)


class TestClockChannelProperties:
    def test_time_channel_has_docstring(self):
        clock = Clock()
        assert clock.time.__doc__ is not None
        assert 'current time' in clock.time.__doc__.lower() or 'time' in clock.time.__doc__.lower()

    def test_date_channel_has_docstring(self):
        clock = Clock()
        assert clock.date.__doc__ is not None
        assert 'date' in clock.date.__doc__.lower()

    def test_time_channel_default_format_in_doc(self):
        clock = Clock()
        doc = clock.time.__doc__
        assert '%I:%M:%S %p' in doc

    def test_date_channel_default_format_in_doc(self):
        clock = Clock()
        doc = clock.date.__doc__
        assert '%m/%d/%Y' in doc


class TestClockMultipleTicks:
    def test_multiple_ticks_update_values(self):
        clock = Clock()
        initial = clock.time.value
        for _ in range(5):
            clock.tick()
        # Values should still be valid datetimes
        assert isinstance(clock.time.value, datetime)
        assert isinstance(clock.date.value, datetime)

    def test_tick_values_are_recent(self):
        clock = Clock()
        import time
        time.sleep(0.1)
        clock.tick()
        now = datetime.now()
        diff = abs((clock.time.value - now).total_seconds())
        assert diff < 2.0
