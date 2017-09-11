import unittest
import mock

from bitmerchant.wallet import Wallet
from secretsharing import BitcoinToB58SecretSharer

from blessings import Terminal
term = Terminal()

from failsafe.failsafe import generate

class TestGenerate(unittest.TestCase):
    def setUp(self):
        self._print_patcher = mock.patch('failsafe.failsafe._print')
        self.mock_print = self._print_patcher.start()

        self._get_input_patcher = mock.patch('failsafe.failsafe._get_input')
        self.mock_get_input = self._get_input_patcher.start()

        self.Wallet_patcher = mock.patch('failsafe.failsafe.Wallet')
        self.mock_Wallet = self.Wallet_patcher.start()

        self.BitcoinToB58SecretSharer_patcher = mock.patch('failsafe.failsafe.BitcoinToB58SecretSharer')
        self.mock_BitcoinToB58SecretSharer = self.BitcoinToB58SecretSharer_patcher.start()

        self._generateKeys_patcher = mock.patch('failsafe.failsafe._generateKeys')
        self.mock_generateKeys = self._generateKeys_patcher.start()

        self.wallet = mock.MagicMock(Wallet)
        self.wallet.serialize_b58.return_value = 'b58_serialized_wallet'

        self.mock_Wallet.new_random_wallet.return_value = self.wallet

        self.shares = ['shard1', 'shard2', 'shard3']
        self.mock_BitcoinToB58SecretSharer.split_secret.return_value = self.shares

    def tearDown(self):
        self._print_patcher.stop()
        self._get_input_patcher.stop()
        self.Wallet_patcher.stop()
        self.BitcoinToB58SecretSharer_patcher.stop()
        self._generateKeys_patcher.stop()

    def test_interactive_inputs(self):
        self.mock_get_input.side_effect = [3, 2, 10, 'asdf', '', '', '']
        generate()
        self.mock_get_input.assert_has_calls(
                [mock.call('Enter number of users participating [1]: ', input_type=int, default=1),
                 mock.call('Enter key threshold [1, 3]: ', input_type=int, default=3),
                 mock.call('Enter number of accounts to be created per user [1]: ', input_type=int, default=1),
                 mock.call('Enter additional entropy [None]: '),
                 ])
        self.mock_Wallet.new_random_wallet.assert_called_once_with('asdf')
        self.wallet.serialize_b58.assert_called_once_with()
        self.mock_BitcoinToB58SecretSharer.split_secret.assert_called_once_with('b58_serialized_wallet',
                                                                                2,
                                                                                3)

        self.mock_print.assert_has_calls(
                [mock.call(term.clear),
                 mock.call('The following screen is meant for user 1 (of 3)\n'
                           'Do not press continue if you are not user 1',
                           formatters=[term.clear, term.red]),
                 mock.call(term.clear),
                 mock.call('The following screen is meant for user 2 (of 3)\n'
                           'Do not press continue if you are not user 2',
                           formatters=[term.clear, term.red]),
                 mock.call(term.clear),
                 mock.call('The following screen is meant for user 3 (of 3)\n'
                           'Do not press continue if you are not user 3',
                           formatters=[term.clear, term.red]),
                 mock.call(term.clear),
                 mock.call('All done'),
              ])

        self.mock_generateKeys.assert_has_calls(
                [mock.call(self.wallet, 0, 10, extra_data={'child': '1 of 3',
                                                           'master_shard': '2-shard1'}),
                 mock.call(self.wallet, 1, 10, extra_data={'child': '2 of 3',
                                                           'master_shard': '2-shard2'}),
                 mock.call(self.wallet, 2, 10, extra_data={'child': '3 of 3',
                                                           'master_shard': '2-shard3'}),
                 ])
