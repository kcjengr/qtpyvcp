import pytest


class TestAllEncodings:
    def test_returns_list(self):
        from qtpyvcp.utilities.encode_utils import allEncodings
        result = allEncodings()
        assert isinstance(result, list)

    def test_contains_utf8(self):
        from qtpyvcp.utilities.encode_utils import allEncodings
        result = allEncodings()
        assert 'utf_8' in result

    def test_contains_ascii(self):
        from qtpyvcp.utilities.encode_utils import allEncodings
        result = allEncodings()
        assert 'ascii' in result

    def test_contains_latin1(self):
        from qtpyvcp.utilities.encode_utils import allEncodings
        result = allEncodings()
        assert 'latin_1' in result

    def test_contains_common_encodings(self):
        from qtpyvcp.utilities.encode_utils import allEncodings
        result = allEncodings()
        common = ['utf_8', 'utf_16', 'ascii', 'cp1252', 'latin_1', 'shift_jis', 'euc_jp']
        for enc in common:
            assert enc in result, f"Missing expected encoding: {enc}"

    def test_contains_utf_variants(self):
        from qtpyvcp.utilities.encode_utils import allEncodings
        result = allEncodings()
        assert 'utf_32' in result
        assert 'utf_32_be' in result
        assert 'utf_32_le' in result
        assert 'utf_16_be' in result
        assert 'utf_16_le' in result
        assert 'utf_7' in result
        assert 'utf_8_sig' in result

    def test_contains_japanese_encodings(self):
        from qtpyvcp.utilities.encode_utils import allEncodings
        result = allEncodings()
        assert 'shift_jis' in result
        assert 'euc_jp' in result
        assert 'iso2022_jp' in result

    def test_contains_korean_encodings(self):
        from qtpyvcp.utilities.encode_utils import allEncodings
        result = allEncodings()
        assert 'euc_kr' in result
        assert 'cp949' in result

    def test_contains_chinese_encodings(self):
        from qtpyvcp.utilities.encode_utils import allEncodings
        result = allEncodings()
        assert 'gb2312' in result
        assert 'gbk' in result
        assert 'gb18030' in result

    def test_contains_cyrillic_encodings(self):
        from qtpyvcp.utilities.encode_utils import allEncodings
        result = allEncodings()
        assert 'koi8_r' in result
        assert 'cp1251' in result
        assert 'iso8859_5' in result

    def test_contains_cp_encodings(self):
        from qtpyvcp.utilities.encode_utils import allEncodings
        result = allEncodings()
        cp_encodings = ['cp437', 'cp850', 'cp852', 'cp866', 'cp1250', 'cp1252', 'cp1253', 'cp1254', 'cp1255', 'cp1256']
        for enc in cp_encodings:
            assert enc in result, f"Missing expected encoding: {enc}"

    def test_returns_new_list_each_call(self):
        from qtpyvcp.utilities.encode_utils import allEncodings
        result1 = allEncodings()
        result2 = allEncodings()
        assert result1 is not result2

    def test_list_length_is_reasonable(self):
        from qtpyvcp.utilities.encode_utils import allEncodings
        result = allEncodings()
        assert len(result) > 50
