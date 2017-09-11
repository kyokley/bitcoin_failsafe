import unittest
import mock

from failsafe.utils import _get_input, _print
from blessings import Terminal
term = Terminal()

class TestGetInput(unittest.TestCase):
    def setUp(self):
        self.raw_input_patcher = mock.patch('__builtin__.raw_input')
        self.mock_raw_input = self.raw_input_patcher.start()
        self.mock_raw_input.return_value = ''

    def tearDown(self):
        self.raw_input_patcher.stop()

    def test_no_input(self):
        expected = ''
        actual = _get_input('prompt')
        self.assertEqual(expected, actual)
        self.mock_raw_input.assert_called_once_with('prompt')

    def test_input_provided(self):
        self.mock_raw_input.return_value = 'test input'

        expected = 'test input'
        actual = _get_input('prompt')
        self.assertEqual(expected, actual)
        self.mock_raw_input.assert_called_once_with('prompt')

    def test_default(self):
        self.mock_raw_input.return_value = ''

        expected = 'test val'
        actual = _get_input('prompt', default='test val')
        self.assertEqual(expected, actual)
        self.mock_raw_input.assert_called_once_with('prompt')

    def test_input_type_no_default(self):
        self.mock_raw_input.return_value = '123'

        expected = 123
        actual = _get_input('prompt', input_type=int)
        self.assertEqual(expected, actual)
        self.mock_raw_input.assert_called_once_with('prompt')

    def test_input_type_default(self):
        self.mock_raw_input.return_value = ''

        expected = 1
        actual = _get_input('prompt', input_type=int, default=1)
        self.assertEqual(expected, actual)
        self.mock_raw_input.assert_called_once_with('prompt')

    def test_input_type_does_not_match_default(self):
        self.mock_raw_input.return_value = ''

        self.assertRaises(ValueError,
                          _get_input,
                          'prompt',
                          input_type=int,
                          default='asdf')
        self.assertFalse(self.mock_raw_input.called)

class TestPrint(unittest.TestCase):
    def setUp(self):
        self.print_patcher = mock.patch('__builtin__.print')
        self.mock_print = self.print_patcher.start()

    def tearDown(self):
        self.print_patcher.stop()

    def test_plain(self):
        _print('test')
        self.mock_print.assert_has_calls([mock.call('test'),
                                          mock.call(term.normal, end='')])

    def test_multiple_items(self):
        _print('item a', 'item b')
        self.mock_print.assert_has_calls([mock.call('item a', 'item b'),
                                          mock.call(term.normal, end='')])

    def test_sep(self):
        _print('item a', 'item b', sep=',')
        self.mock_print.assert_has_calls([mock.call('item a', 'item b', sep=','),
                                          mock.call(term.normal, end='')])

    def test_end(self):
        _print('item a', 'item b', end='\n')
        self.mock_print.assert_has_calls([mock.call('item a', 'item b', end='\n'),
                                          mock.call(term.normal, end='')])

    def test_formatter(self):
        _print('item a', 'item b', formatters=term.red)
        self.mock_print.assert_has_calls([mock.call(term.red, end=''),
                                          mock.call('item a', 'item b'),
                                          mock.call(term.normal, end='')])

    def test_multiple_formatters(self):
        _print('item a', 'item b', formatters=[term.red, term.bold])
        self.mock_print.assert_has_calls([mock.call(term.red, end=''),
                                          mock.call(term.bold, end=''),
                                          mock.call('item a', 'item b'),
                                          mock.call(term.normal, end='')])
