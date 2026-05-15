import json
import os
import pickle
import tempfile
from unittest.mock import MagicMock, patch

import pytest


class TestPersistentDataManagerInit:
    def test_default_serialization_is_pickle(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        assert mgr.serialization_method == 'pickle'

    def test_json_serialization(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager(serialization_method='json')
        assert mgr.serialization_method == 'json'

    def test_pickle_serialization(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager(serialization_method='pickle')
        assert mgr.serialization_method == 'pickle'

    def test_default_filename_with_pickle(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        assert '.vcp_persistent_data.pickle' in mgr.persistence_file

    def test_default_filename_with_json(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager(serialization_method='json')
        assert '.vcp_persistent_data.json' in mgr.persistence_file

    def test_custom_persistence_file(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        custom_file = str(tmp_path / "custom_data.pkl")
        mgr = PersistentDataManager(persistence_file=custom_file)
        assert mgr.persistence_file == custom_file

    def test_uses_config_dir_env_var(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        old_config_dir = os.environ.get('CONFIG_DIR')
        os.environ['CONFIG_DIR'] = str(tmp_path)
        try:
            mgr = PersistentDataManager()
            assert mgr.persistence_file.startswith(str(tmp_path))
        finally:
            if old_config_dir is not None:
                os.environ['CONFIG_DIR'] = old_config_dir
            else:
                os.environ.pop('CONFIG_DIR', None)

    def test_data_initialized_as_empty_dict(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        assert mgr.data == {}

    def test_json_serializer_set_correctly(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager(serialization_method='json')
        assert mgr.serializer is json

    def test_pickle_serializer_set_correctly(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager(serialization_method='pickle')
        assert mgr.serializer is pickle


class TestGetData:
    def test_returns_value_for_existing_key(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        mgr.data['key1'] = 'value1'
        result = mgr.getData('key1')
        assert result == 'value1'

    def test_returns_default_for_missing_key(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        result = mgr.getData('missing', 'default_val')
        assert result == 'default_val'

    def test_returns_none_for_missing_key_without_default(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        result = mgr.getData('missing')
        assert result is None

    def test_returns_complex_type(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        mgr.data['list'] = [1, 2, 3]
        result = mgr.getData('list')
        assert result == [1, 2, 3]

    def test_returns_dict_value(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        mgr.data['nested'] = {'a': 1, 'b': 2}
        result = mgr.getData('nested')
        assert result == {'a': 1, 'b': 2}


class TestSetData:
    def test_stores_string_value(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        mgr.setData('key', 'value')
        assert mgr.data['key'] == 'value'

    def test_overwrites_existing_key(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        mgr.setData('key', 'first')
        mgr.setData('key', 'second')
        assert mgr.data['key'] == 'second'

    def test_stores_integer_value(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        mgr.setData('count', 42)
        assert mgr.data['count'] == 42

    def test_stores_list_value(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        mgr.setData('items', [1, 'two', 3.0])
        assert mgr.data['items'] == [1, 'two', 3.0]

    def test_stores_dict_value(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        mgr.setData('config', {'x': 1, 'y': 2})
        assert mgr.data['config'] == {'x': 1, 'y': 2}

    def test_stores_none_value(self):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        mgr = PersistentDataManager()
        mgr.setData('nothing', None)
        assert mgr.data['nothing'] is None


class TestInitialise:
    def test_loads_pickle_data(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = tmp_path / "data.pkl"
        test_data = {'key1': 'val1', 'key2': 42}
        with open(data_file, 'wb') as f:
            pickle.dump(test_data, f)

        mgr = PersistentDataManager(persistence_file=str(data_file))
        mgr.initialise()
        assert mgr.data == test_data

    def test_loads_json_data(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = tmp_path / "data.json"
        test_data = {'key1': 'val1', 'key2': 42}
        with open(data_file, 'w') as f:
            json.dump(test_data, f)

        mgr = PersistentDataManager(serialization_method='json', persistence_file=str(data_file))
        mgr.initialise()
        assert mgr.data == test_data

    def test_noop_when_file_missing(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = str(tmp_path / "nonexistent.pkl")
        mgr = PersistentDataManager(persistence_file=data_file)
        mgr.initialise()
        assert mgr.data == {}

    def test_corrupt_pickle_returns_empty(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = tmp_path / "corrupt.pkl"
        data_file.write_text("not valid pickle data")

        mgr = PersistentDataManager(persistence_file=str(data_file))
        mgr.initialise()
        assert mgr.data == {}

    def test_corrupt_json_returns_empty(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = tmp_path / "corrupt.json"
        data_file.write_text("not valid json {{{")

        mgr = PersistentDataManager(serialization_method='json', persistence_file=str(data_file))
        mgr.initialise()
        assert mgr.data == {}

    def test_preserves_data_on_load_failure(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = tmp_path / "data.pkl"
        # Write corrupt data
        data_file.write_text("corrupt")

        mgr = PersistentDataManager(persistence_file=str(data_file))
        mgr.data['existing'] = 'value'
        mgr.initialise()
        assert mgr.data == {'existing': 'value'}


class TestTerminate:
    def test_writes_pickle_data(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = str(tmp_path / "data.pkl")
        mgr = PersistentDataManager(persistence_file=data_file)
        mgr.data = {'key': 'value', 'num': 123}
        mgr.terminate()

        with open(data_file, 'rb') as f:
            loaded = pickle.load(f)
        assert loaded == {'key': 'value', 'num': 123}

    def test_writes_json_data(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = str(tmp_path / "data.json")
        mgr = PersistentDataManager(serialization_method='json', persistence_file=data_file)
        mgr.data = {'key': 'value', 'num': 123}
        mgr.terminate()

        with open(data_file, 'r') as f:
            loaded = json.load(f)
        assert loaded == {'key': 'value', 'num': 123}

    def test_json_sorted_keys(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = str(tmp_path / "data.json")
        mgr = PersistentDataManager(serialization_method='json', persistence_file=data_file)
        mgr.data = {'z': 1, 'a': 2, 'm': 3}
        mgr.terminate()

        with open(data_file, 'r') as f:
            content = f.read()
        # Check that keys are sorted (a before m before z)
        assert content.index('"a"') < content.index('"m"') < content.index('"z"')

    def test_json_indented(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = str(tmp_path / "data.json")
        mgr = PersistentDataManager(serialization_method='json', persistence_file=data_file)
        mgr.data = {'key': 'value'}
        mgr.terminate()

        with open(data_file, 'r') as f:
            content = f.read()
        assert '\n' in content  # Should be multi-line indented JSON

    def test_pickle_file_is_binary(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = str(tmp_path / "data.pkl")
        mgr = PersistentDataManager(persistence_file=data_file)
        mgr.data = {'key': 'value'}
        mgr.terminate()

        # Verify file is binary (not text)
        with open(data_file, 'rb') as f:
            content = f.read()
        assert isinstance(content, bytes)

    def test_empty_data_writes_correctly_pickle(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = str(tmp_path / "data.pkl")
        mgr = PersistentDataManager(persistence_file=data_file)
        mgr.terminate()

        with open(data_file, 'rb') as f:
            loaded = pickle.load(f)
        assert loaded == {}

    def test_empty_data_writes_correctly_json(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = str(tmp_path / "data.json")
        mgr = PersistentDataManager(serialization_method='json', persistence_file=data_file)
        mgr.terminate()

        with open(data_file, 'r') as f:
            loaded = json.load(f)
        assert loaded == {}

    def test_debug_log_on_terminate(self, tmp_path):
        from qtpyvcp.plugins.persistent_data_manager import PersistentDataManager
        data_file = str(tmp_path / "data.pkl")
        mgr = PersistentDataManager(persistence_file=data_file)

        with patch('qtpyvcp.plugins.persistent_data_manager.LOG') as mock_log:
            mgr.terminate()
            mock_log.debug.assert_called()
            call_args = mock_log.debug.call_args[0]
            assert data_file in call_args[1]
