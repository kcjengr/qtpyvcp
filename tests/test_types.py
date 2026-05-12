import pytest
from qtpyvcp.lib.types import DotDict


class TestDotDict:
    def test_initialization(self):
        d = DotDict({'key': 'value', 'nested': {'a': 1}})
        assert d['key'] == 'value'
        assert d['nested'] == {'a': 1}

    def test_dot_access_get(self):
        d = DotDict({'foo': 'bar'})
        assert d.foo == 'bar'

    def test_dot_access_set(self):
        d = DotDict()
        d.new_key = 'new_value'
        assert d['new_key'] == 'new_value'

    def test_dot_access_missing_returns_none(self):
        d = DotDict()
        assert d.nonexistent is None

    def test_delete_item(self):
        d = DotDict({'key': 'value'})
        del d['key']
        assert 'key' not in d

    def test_inheritance_from_dict(self):
        d = DotDict({'a': 1, 'b': 2})
        assert isinstance(d, dict)
        assert len(d) == 2
        assert list(d.keys()) == ['a', 'b']
