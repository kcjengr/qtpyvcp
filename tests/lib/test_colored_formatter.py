import logging
import pytest
from qtpyvcp.lib.colored_formatter import (
    PREFIX, SUFFIX, COLORS, MAPPING, COLORIZE, RE, ColoredFormatter
)


class TestConstants:
    def test_prefix_value(self):
        assert PREFIX == '\033['

    def test_suffix_value(self):
        assert SUFFIX == '\033[0m'

    def test_colors_has_all_standard_colors(self):
        expected = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
        for color in expected:
            assert color in COLORS

    def test_colors_has_special_colors(self):
        assert 'bgred' in COLORS
        assert 'bggrey' in COLORS

    def test_colors_standard_values(self):
        assert COLORS['black'] == 30
        assert COLORS['red'] == 31
        assert COLORS['green'] == 32
        assert COLORS['yellow'] == 33
        assert COLORS['blue'] == 34
        assert COLORS['magenta'] == 35
        assert COLORS['cyan'] == 36
        assert COLORS['white'] == 37

    def test_colors_special_values(self):
        assert COLORS['bgred'] == 41
        assert COLORS['bggrey'] == 100


class TestMapping:
    def test_debug_maps_to_white(self):
        assert MAPPING['DEBUG'] == 'white'

    def test_info_maps_to_cyan(self):
        assert MAPPING['INFO'] == 'cyan'

    def test_warning_maps_to_yellow(self):
        assert MAPPING['WARNING'] == 'yellow'

    def test_error_maps_to_red(self):
        assert MAPPING['ERROR'] == 'red'

    def test_critical_maps_to_bgred(self):
        assert MAPPING['CRITICAL'] == 'bgred'


class TestColorize:
    def test_colorize_default_color_white(self):
        result = COLORIZE('test')
        expected = '\033[37mtest\033[0m'
        assert result == expected

    def test_colorize_with_red(self):
        result = COLORIZE('error', 'red')
        expected = '\033[31merror\033[0m'
        assert result == expected

    def test_colorize_with_green(self):
        result = COLORIZE('ok', 'green')
        expected = '\033[32mok\033[0m'
        assert result == expected

    def test_colorize_with_unknown_color_falls_back_to_white(self):
        result = COLORIZE('test', 'unknown')
        expected = '\033[37mtest\033[0m'
        assert result == expected

    def test_colorize_empty_string(self):
        result = COLORIZE('', 'red')
        expected = '\033[31m\033[0m'
        assert result == expected

    def test_colorize_contains_prefix_and_suffix(self):
        result = COLORIZE('hello', 'blue')
        assert PREFIX in result
        assert SUFFIX in result


class TestRegex:
    def test_re_matches_simple_tag(self):
        match = RE.search('red<error>')
        assert match is not None
        assert match.group(1) == 'red'
        assert match.group(2) == 'error'

    def test_re_matches_multiple_tags(self):
        text = 'red<error> and green<warning>'
        matches = list(RE.finditer(text))
        assert len(matches) == 2
        assert matches[0].group() == 'red<error>'
        assert matches[1].group() == 'green<warning>'

    def test_re_matches_with_spaces_in_text(self):
        text = 'The red<critical error> occurred'
        match = RE.search(text)
        assert match is not None
        assert match.group(2) == 'critical error'

    def test_re_no_match_without_tag_format(self):
        text = 'just plain text without tags'
        matches = list(RE.finditer(text))
        assert len(matches) == 0

    def test_re_no_match_with_brackets_but_not_tags(self):
        text = '[not a tag] (also not)'
        matches = list(RE.finditer(text))
        assert len(matches) == 0


class TestColoredFormatterInit:
    def test_init_accepts_pattern(self):
        fmt = ColoredFormatter('%(message)s')
        assert fmt is not None

    def test_init_with_complex_pattern(self):
        pattern = '[%(name)s][%(levelname)s] %(message)s'
        fmt = ColoredFormatter(pattern)
        assert fmt is not None

    def test_format_output_contains_ansi_codes(self):
        fmt = ColoredFormatter('%(levelname)s: %(message)s')
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='hello', args=(), exc_info=None
        )
        output = fmt.format(record)
        assert '\033[' in output


class TestColoredFormatterFormat:
    def test_format_levelname_is_colored(self):
        fmt = ColoredFormatter('%(levelname)s')
        record = logging.LogRecord(
            name='test', level=logging.ERROR, pathname='', lineno=0,
            msg='test message', args=(), exc_info=None
        )
        output = fmt.format(record)
        assert '\033[' in output

    def test_format_debug_levelname_white(self):
        fmt = ColoredFormatter('%(levelname)s')
        record = logging.LogRecord(
            name='test', level=logging.DEBUG, pathname='', lineno=0,
            msg='debug msg', args=(), exc_info=None
        )
        output = fmt.format(record)
        assert '\033[37mDEBUG\033[0m' in output

    def test_format_info_levelname_cyan(self):
        fmt = ColoredFormatter('%(levelname)s')
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='info msg', args=(), exc_info=None
        )
        output = fmt.format(record)
        assert '\033[36mINFO\033[0m' in output

    def test_format_warning_levelname_yellow(self):
        fmt = ColoredFormatter('%(levelname)s')
        record = logging.LogRecord(
            name='test', level=logging.WARNING, pathname='', lineno=0,
            msg='warn msg', args=(), exc_info=None
        )
        output = fmt.format(record)
        assert '\033[33mWARNING\033[0m' in output

    def test_format_error_levelname_red(self):
        fmt = ColoredFormatter('%(levelname)s')
        record = logging.LogRecord(
            name='test', level=logging.ERROR, pathname='', lineno=0,
            msg='error msg', args=(), exc_info=None
        )
        output = fmt.format(record)
        assert '\033[31mERROR\033[0m' in output

    def test_format_critical_levelname_bgred(self):
        fmt = ColoredFormatter('%(levelname)s')
        record = logging.LogRecord(
            name='test', level=logging.CRITICAL, pathname='', lineno=0,
            msg='critical msg', args=(), exc_info=None
        )
        output = fmt.format(record)
        assert '\033[41mCRITICAL\033[0m' in output

    def test_format_message_preserved(self):
        fmt = ColoredFormatter('%(message)s')
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='hello world', args=(), exc_info=None
        )
        output = fmt.format(record)
        assert 'hello world' in output

    def test_format_message_with_tag_colored(self):
        fmt = ColoredFormatter('%(message)s')
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='status: green<OK>', args=(), exc_info=None
        )
        output = fmt.format(record)
        assert '\033[32mOK\033[0m' in output

    def test_format_message_with_multiple_tags_colored(self):
        fmt = ColoredFormatter('%(message)s')
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='red<fail> and green<pass>', args=(), exc_info=None
        )
        output = fmt.format(record)
        assert '\033[31mfail\033[0m' in output
        assert '\033[32mpass\033[0m' in output

    def test_format_with_name_in_pattern(self):
        fmt = ColoredFormatter('%(name)s: %(message)s')
        record = logging.LogRecord(
            name='mylogger', level=logging.INFO, pathname='', lineno=0,
            msg='test', args=(), exc_info=None
        )
        output = fmt.format(record)
        assert 'mylogger' in output

    def test_format_with_lineno_in_pattern(self):
        fmt = ColoredFormatter('%(lineno)d: %(message)s')
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=42,
            msg='test', args=(), exc_info=None
        )
        output = fmt.format(record)
        assert '42' in output

    def test_format_unknown_levelname_defaults_to_white(self):
        fmt = ColoredFormatter('%(levelname)s')
        record = logging.LogRecord(
            name='test', level=15, pathname='', lineno=0,
            msg='msg', args=(), exc_info=None
        )
        record.levelname = 'CUSTOM'
        output = fmt.format(record)
        assert '\033[37mCUSTOM\033[0m' in output


class TestColorWords:
    def test_color_words_single_tag(self):
        fmt = ColoredFormatter('%(message)s')
        plain, colored = fmt.color_words('red<error>')
        assert plain == 'error'
        assert '\033[31merror\033[0m' in colored

    def test_color_words_multiple_tags(self):
        fmt = ColoredFormatter('%(message)s')
        plain, colored = fmt.color_words('red<bad> green<good>')
        assert plain == 'bad good'
        assert '\033[31mbad\033[0m' in colored
        assert '\033[32mgood\033[0m' in colored

    def test_color_words_no_tags(self):
        fmt = ColoredFormatter('%(message)s')
        plain, colored = fmt.color_words('plain text')
        assert plain == 'plain text'
        assert colored == 'plain text'

    def test_color_words_empty_string(self):
        fmt = ColoredFormatter('%(message)s')
        plain, colored = fmt.color_words('')
        assert plain == ''
        assert colored == ''

    def test_color_words_tag_with_spaces(self):
        fmt = ColoredFormatter('%(message)s')
        plain, colored = fmt.color_words('yellow<warning message>')
        assert plain == 'warning message'
        assert '\033[33mwarning message\033[0m' in colored

    def test_color_words_tag_in_middle_of_text(self):
        fmt = ColoredFormatter('%(message)s')
        plain, colored = fmt.color_words('before blue<middle> after')
        assert plain == 'before middle after'
        assert '\033[34mmiddle\033[0m' in colored

    def test_color_words_unknown_color_defaults_to_white(self):
        fmt = ColoredFormatter('%(message)s')
        plain, colored = fmt.color_words('unknown<text>')
        assert plain == 'text'
        assert '\033[37mtext\033[0m' in colored

    def test_color_words_brackets_but_not_tags(self):
        fmt = ColoredFormatter('%(message)s')
        plain, colored = fmt.color_words('[not a tag] (also not)')
        assert plain == '[not a tag] (also not)'
        assert colored == '[not a tag] (also not)'

    def test_color_words_returns_tuple(self):
        fmt = ColoredFormatter('%(message)s')
        result = fmt.color_words('red<test>')
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestColoredFormatterIntegration:
    def test_full_logging_pipeline(self, capsys):
        log = logging.getLogger('integration_test')
        log.setLevel(logging.DEBUG)
        log.handlers.clear()

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        cf = ColoredFormatter('%(levelname)s: %(message)s')
        ch.setFormatter(cf)
        log.addHandler(ch)

        log.info('status: green<OK>')

        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert '\033[' in output
        assert 'OK' in output

    def test_file_handler_receives_plain_message(self, tmp_path):
        log = logging.getLogger('file_test')
        log.setLevel(logging.DEBUG)
        log.handlers.clear()

        fh = logging.FileHandler(str(tmp_path / 'test.log'))
        ff = logging.Formatter('%(levelname)s: %(message)s')
        fh.setFormatter(ff)
        log.addHandler(fh)

        log.info('red<error> occurred')

        fh.close()
        content = (tmp_path / 'test.log').read_text()
        assert '\033[' not in content
        assert 'error' in content

    def test_colored_and_plain_handlers_together(self, tmp_path):
        log = logging.getLogger('dual_test')
        log.setLevel(logging.DEBUG)
        log.handlers.clear()

        ch = logging.StreamHandler()
        cf = ColoredFormatter('[%(levelname)s] %(message)s')
        ch.setFormatter(cf)
        log.addHandler(ch)

        fh = logging.FileHandler(str(tmp_path / 'dual.log'))
        ff = logging.Formatter('%(levelname)s: %(message)s')
        fh.setFormatter(ff)
        log.addHandler(fh)

        log.warning('red<attention> needed')

        ch.close()
        fh.close()

        content = (tmp_path / 'dual.log').read_text()
        assert '\033[' not in content
        assert 'attention' in content
